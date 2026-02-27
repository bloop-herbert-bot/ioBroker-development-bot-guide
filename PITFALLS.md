# Anti-Patterns & Pitfalls

> Common mistakes encountered during ioBroker adapter development

**Last Updated:** 2026-02-27

---

## 🚨 Critical Anti-Patterns

### ❌ Using Legacy Materialize Admin UI

**What happened:**
- Created `admin/index_m.html` + `admin/words.js` for Issue #15
- Reviewer rejected: "Outdated patterns! Use JSONConfig"

**Why it's wrong:**
- Materialize UI is deprecated since ioBroker.js-controller 4.x
- Hard to maintain, verbose code
- Not compatible with modern admin UI

**✅ Correct approach:**
```
admin/
├── jsonConfig.json        # UI definition
└── i18n/
    ├── en.json           # English translations
    └── de.json           # German translations
```

**See:** [ADMIN_UI.md](./ADMIN_UI.md) for details

---

### ❌ Inverted Logic in Threshold Checks

**What happened (Issue #28):**
- Config said: "Alert when **free** memory drops below X"
- Code checked: "Alert when **used** memory exceeds X"
- Result: Inverted alerts!

**Example:**
```javascript
// ❌ WRONG
if (usedMB > threshold) {
  this.log.warn(`Memory high: ${usedMB}MB`);
}

// ✅ CORRECT
if (freeMB < threshold) {
  this.log.warn(`Memory low: ${freeMB}MB free`);
}
```

**Lesson:** Config text must match code logic exactly!

---

### ❌ Defining States Without Initialization

**What happened (Issues #88, #105, #107):**
- States defined in `io-package.json`
- Never called `setObjectNotExists()` or `setStateAsync()`
- Result: States appear as "objects" but have no values

**Example:**
```json
// io-package.json
"objects": [
  {
    "_id": "memory.status",
    "type": "state",
    "common": { ... }
  }
]
```

```javascript
// ❌ WRONG - Only definition, no initialization
// (Adapter starts but state stays undefined)

// ✅ CORRECT - Initialize state
await this.setObjectNotExistsAsync('memory.status', {
  type: 'state',
  common: { ... }
});
await this.setStateAsync('memory.status', { val: 'ok', ack: true });
```

**Lesson:** Defining != Initializing! Always call `setStateAsync()` at least once.

**See:** [STATE_MANAGEMENT.md](./STATE_MANAGEMENT.md)

---

### ❌ Crash Detection: Misunderstanding `ack` Flag

**What happened (PR #7):**
- Initial code: `if (!state.ack)` → treat as crash
- Reviewer: "Crashes have `ack=false`, but scheduled restarts have `ack=true`"

**Correct logic:**
```javascript
// ✅ CORRECT
const isCrash = !state.ack;  // ack=false means unacknowledged (crash)
const isScheduled = state.ack;  // ack=true means acknowledged (intentional restart)
```

**Lesson:** `ack=true` means "acknowledged by adapter" (intentional), `ack=false` means error/crash.

---

### ❌ Boolean States Without Translations

**What happened (Issue #87):**
- State value: `true`
- Admin UI showed: "WAHR" (German) / "FALSCH" (German)
- Expected: "Yes/No" or "On/Off"

**Root cause:**
```json
// ❌ WRONG - No states mapping
{
  "type": "boolean",
  "role": "indicator",
  "read": true,
  "write": false
}
```

**✅ CORRECT:**
```json
{
  "type": "boolean",
  "role": "indicator",
  "read": true,
  "write": false,
  "states": {
    "false": "OK",
    "true": "Leak detected"
  }
}
```

**Lesson:** Always add `states`-mappings for boolean values to control display text.

---

## ⚠️ Testing Pitfalls

### ❌ Dev-Server Testing Only

**What happened:**
- Code passed `npm test` on dev machine
- Failed in production (real ioBroker system)
- Admin UI showed "null" values, buttons didn't work

**Why:**
- Dev-server only verifies adapter **starts**, not UI integration
- JSONConfig OID bindings need absolute paths: `system-health.0.memory.status`
- Admin UI `onclick` handlers don't work with `addEventListener` (security restrictions)

**✅ Correct approach:**
1. Dev-server: Verify adapter starts + unit tests pass
2. Real system: Test Admin UI, state bindings, user interactions
3. Both: Required before PR!

**See:** [TESTING.md](./TESTING.md)

---

### ❌ JSONL-Backend Race Conditions

**What happened:**
- State-dump script via SSH: `ssh user@host "cat objects.jsonl | grep ..."`
- Results fluctuated: 43-60 states across runs
- Root cause: Race conditions during file read + incomplete JSON lines

**Why it's wrong:**
- JSONL files are append-only
- Adapter writes while script reads → incomplete lines
- grep-based filtering unreliable

**✅ Correct approach:**
Use Simple-API REST endpoint instead:
```python
import requests
objects = requests.get('http://<host>:8087/getObjects?pattern=system-health.0.*').json()
states = requests.get('http://<host>:8087/getStates?pattern=system-health.0.*').json()
```

**Benefits:**
- Atomic snapshots (no race conditions)
- No SSH needed
- Stable results

**See:** [BACKEND_INTEGRATION.md](./BACKEND_INTEGRATION.md)

---

## 🛠️ Workflow Pitfalls

### ❌ Ignoring Review Feedback Priority

**What happened (PR #7):**
- Bot received review comments
- Bot started working on new issues instead of fixing PR
- Violates workflow rule: "Review feedback FIRST"

**✅ Correct workflow:**
1. Check all open PRs for comments (`gh pr list --author bot`)
2. Fix review feedback (`gh pr view <num> --comments`)
3. Push fixes, add reply comment
4. THEN start new issues

**Lesson:** Open PR feedback > New issues!

---

### ❌ Modifying CI/Tooling Files

**What happened:**
- PR #109 failed CI (ESLint config missing)
- Bot tried to fix `.github/workflows/` + `.eslintrc.*`
- Reviewer: "Bots must not touch CI config"

**✅ Correct approach:**
- Comment on PR explaining CI failure
- Ask maintainer to fix infrastructure
- Wait for fix before continuing

**Lesson:** Repository-wide infrastructure = maintainer responsibility!

---

## 📊 CI/CD Pitfalls

### ❌ Assuming CI Failure = Code Problem

**What happened (PR #109):**
- All CI checks failed
- Root cause: Repository-wide ESLint 9 migration incomplete
- Not PR-specific!

**How to verify:**
```bash
# Test on main branch
git checkout main
npm run lint  # Same error? → Repository issue!
```

**Lesson:** Always verify if CI failure exists on main branch before fixing "your" code.

---

## 🔒 Security Pitfalls

### ❌ Credentials in GitHub Issues/Comments

**What happened:**
- QA script embedded: `ssh martin@192.168.0.18`
- Username + IP visible in public GitHub comments

**✅ Correct approach:**
```python
# ❌ WRONG
user = "martin"
host = "192.168.0.18"

# ✅ CORRECT
user = sys.argv[1]  # Pass as parameter
host = sys.argv[2]

# In documentation/comments:
python3 script.py <YOUR_HOST> <YOUR_USER>
```

**Lesson:** NEVER hardcode credentials, IPs, or usernames in public repos/comments!

---

## 📝 Documentation Pitfalls

### ❌ `words.js` Format Errors

**What happened (PR #24):**
- Created: `{"en": {...}, "de": {...}}`
- Expected: `var systemDictionary = {"key": {"en": "...", "de": "..."}}`

**✅ Correct format:**
```javascript
// words.js (Legacy Materialize)
var systemDictionary = {
  "Memory Status": {
    "en": "Memory Status",
    "de": "Speicherstatus"
  },
  "Check interval": {
    "en": "Check interval (seconds)",
    "de": "Prüfintervall (Sekunden)"
  }
};
```

**Note:** With JSONConfig, use `i18n/*.json` instead!

---

## 🎯 Summary: Top 5 Pitfalls

1. **States:** Define → Initialize → Persist (all 3 required!)
2. **Testing:** Dev-server + Real system (both mandatory)
3. **Admin UI:** Use JSONConfig (NOT Materialize)
4. **Backend:** Use Simple-API (NOT JSONL direct access)
5. **Security:** NO credentials in public repos!

---

_Auto-updated from PR reviews and issue feedback_
