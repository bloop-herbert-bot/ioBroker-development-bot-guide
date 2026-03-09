# State Management in ioBroker

> How to properly define, initialize, and persist states

**Last Updated:** 2026-02-27

---

## 🎯 The Three-Step Rule

**CRITICAL:** Defining a state in `io-package.json` is NOT enough!

```
1. DEFINE  → io-package.json (state structure)
2. INIT    → setObjectNotExistsAsync() (create in DB)
3. SET     → setStateAsync() (give it a value)
```

**All three steps are required** for a state to work!

---

## ❌ Common Mistake: Definition Without Initialization

**What developers think:**
```json
// io-package.json
"objects": [
  {
    "_id": "memory.status",
    "type": "state",
    "common": {
      "name": "Memory status",
      "type": "string",
      "role": "text",
      "read": true,
      "write": false
    }
  }
]
```

"Done! State is defined, should work now." ❌

**What actually happens:**
- Object appears in object tree (`iobroker object list`)
- State has **no value** (`iobroker state get` returns empty)
- Admin UI shows `null` or nothing

---

## ✅ Correct Approach: Define + Init + Set

### Step 1: Define in `io-package.json`

```json
{
  "native": {},
  "objects": [
    {
      "_id": "memory.status",
      "type": "state",
      "common": {
        "name": "Memory status",
        "type": "string",
        "role": "text",
        "read": true,
        "write": false,
        "states": {
          "ok": "OK",
          "warning": "Warning",
          "critical": "Critical"
        }
      },
      "native": {}
    }
  ]
}
```

### Step 2: Initialize in `onReady()`

```javascript
class SystemHealth extends utils.Adapter {
  async onReady() {
    // Create object if it doesn't exist
    await this.setObjectNotExistsAsync('memory.status', {
      type: 'state',
      common: {
        name: 'Memory status',
        type: 'string',
        role: 'text',
        read: true,
        write: false,
        states: {
          'ok': 'OK',
          'warning': 'Warning',
          'critical': 'Critical'
        }
      },
      native: {}
    });

    // Set initial value
    await this.setStateAsync('memory.status', { 
      val: 'ok', 
      ack: true 
    });

    // Start monitoring
    this.startMemoryMonitoring();
  }
}
```

### Step 3: Update Periodically

```javascript
async checkMemory() {
  const memInfo = await this.getMemoryInfo();
  const status = this.calculateStatus(memInfo);

  // Update state value
  await this.setStateAsync('memory.status', {
    val: status,
    ack: true
  });
}
```

---

## 🔍 Real-World Example: Missing State Bug

**Issue #105: Redis Monitoring States Not Initialized**

**Problem:**
```json
// io-package.json - 9 states defined
{
  "_id": "redis.status",
  "type": "state",
  "common": { "type": "string", "role": "text" }
}
// ... 8 more states
```

**Code:**
```javascript
// ❌ WRONG - No initialization!
async checkRedis() {
  const info = await this.getRedisInfo();
  // Tries to update states that don't exist yet
  await this.setStateAsync('redis.status', { val: info.status, ack: true });
}
```

**Result:**
- `iobroker object list` shows 9 objects ✅
- `iobroker state get redis.status` returns empty ❌
- Admin UI shows `null` ❌

**✅ Fix:**
```javascript
async onReady() {
  // Initialize ALL Redis states
  await this.setObjectNotExistsAsync('redis.status', { ... });
  await this.setObjectNotExistsAsync('redis.connected', { ... });
  // ... 7 more states

  // Set initial values
  await this.setStateAsync('redis.status', { val: 'unknown', ack: true });
  await this.setStateAsync('redis.connected', { val: false, ack: true });
  // ... 7 more states

  this.startRedisMonitoring();
}
```

---

## 📊 State Lifecycle

```
Adapter Start
    ↓
onReady()
    ↓
setObjectNotExistsAsync()  ← Creates object in DB
    ↓
setStateAsync()            ← Sets initial value
    ↓
Monitoring Loop
    ↓
setStateAsync()            ← Updates value periodically
    ↓
onUnload()
```

---

## 🛠️ Testing State Initialization

### Method 1: CLI Check

```bash
# Check if object exists
iobroker object list system-health.0.redis.*

# Check if state has value
iobroker state get system-health.0.redis.status
```

**Expected output:**
```
system-health.0.redis.status = "ok" (ack=true)
```

**If empty:** State not initialized!

### Method 2: Simple-API Check

```bash
curl http://<host>:8087/getStates?pattern=system-health.0.*
```

**Expected JSON:**
```json
{
  "system-health.0.redis.status": {
    "val": "ok",
    "ack": true,
    "ts": 1709033400000,
    ...
  }
}
```

**If `val: null`:** State not set!

### Method 3: Admin UI Visual Check

1. Open Admin → Objects
2. Navigate to `system-health.0`
3. Check state values

**If shows "null" or blank:** Not initialized!

---

## 🔧 Common State Types & Initialization

### String State

```javascript
await this.setObjectNotExistsAsync('status', {
  type: 'state',
  common: {
    name: 'Status',
    type: 'string',
    role: 'text',
    read: true,
    write: false,
    states: {
      'ok': 'OK',
      'warning': 'Warning',
      'error': 'Error'
    }
  },
  native: {}
});

await this.setStateAsync('status', { val: 'ok', ack: true });
```

### Number State

```javascript
await this.setObjectNotExistsAsync('usedPercent', {
  type: 'state',
  common: {
    name: 'Used Percent',
    type: 'number',
    role: 'value',
    unit: '%',
    min: 0,
    max: 100,
    read: true,
    write: false
  },
  native: {}
});

await this.setStateAsync('usedPercent', { val: 36.5, ack: true });
```

### Boolean State

```javascript
await this.setObjectNotExistsAsync('leakDetected', {
  type: 'state',
  common: {
    name: 'Memory Leak Detected',
    type: 'boolean',
    role: 'indicator.alarm',
    read: true,
    write: false,
    states: {
      'false': 'No leak',
      'true': 'Leak detected'
    }
  },
  native: {}
});

await this.setStateAsync('leakDetected', { val: false, ack: true });
```

### JSON State

```javascript
await this.setObjectNotExistsAsync('details', {
  type: 'state',
  common: {
    name: 'Details',
    type: 'string',  // JSON stored as string!
    role: 'json',
    read: true,
    write: false
  },
  native: {}
});

await this.setStateAsync('details', { 
  val: JSON.stringify({ foo: 'bar' }), 
  ack: true 
});
```

---

## ⚠️ State Persistence Across Restarts

**Question:** Do states persist after adapter restart?

**Answer:** Depends on backend!

### Redis Backend
- ✅ States persist across restarts
- ✅ Values stay in Redis memory
- ❌ Lost if Redis restarts (unless persistence configured)

### JSONL Backend
- ✅ States persist across restarts
- ✅ Written to `states.jsonl` file
- ✅ Survives adapter AND system restart

**Best practice:** Always initialize states in `onReady()`, even if they persist!

---

## 🐛 Debugging Missing States

### Symptom 1: Admin UI shows "null"

**Possible causes:**
1. State never initialized → Call `setStateAsync()` in `onReady()`
2. State binding uses wrong OID → Use absolute path `system-health.0.memory.status`
3. Adapter crashed before initialization → Check logs

### Symptom 2: `iobroker object list` shows object, but `state get` is empty

**Diagnosis:**
```bash
iobroker object get system-health.0.redis.status  # Shows object definition
iobroker state get system-health.0.redis.status   # Empty or null
```

**Cause:** Object defined, state never set.

**Fix:** Add `setStateAsync()` call in adapter code.

### Symptom 3: State count fluctuates

**Example:** 43 states, then 60 states, then 47 states...

**Cause:** JSONL-backend race condition (reading file while adapter writes)

**Fix:** Use Simple-API REST endpoint instead of direct JSONL access.

---

## 📚 Resources

- [ioBroker State Roles](https://github.com/ioBroker/ioBroker.docs/blob/master/docs/en/dev/stateroles.md)
- [Adapter Development Docs](https://github.com/ioBroker/ioBroker.docs/blob/master/docs/en/dev/adapterdev.md)
- [Simple-API Adapter](https://github.com/ioBroker/ioBroker.simple-api)

---

## 🎯 Quick Checklist

Before creating a PR with new states:

- [ ] State defined in `io-package.json`
- [ ] `setObjectNotExistsAsync()` called in `onReady()`
- [ ] `setStateAsync()` called with initial value
- [ ] State updated periodically (if monitoring)
- [ ] Tested on real ioBroker system (not just dev-server)
- [ ] Admin UI bindings use absolute paths
- [ ] Boolean states have `states`-mappings

---

## 🚨 Critical Learning: State Init BEFORE Conditional Logic (PR #165)

**Problem:** Features with conditional logic (e.g., Redis-only) that return early BEFORE initializing states.

**Anti-Pattern:**
```javascript
async runRedisCheck() {
  const config = await this.detectRedisConfig();
  
  // ❌ WRONG: Early return before state init!
  if (!config.objectsIsRedis && !config.statesIsRedis) {
    await this.setStateAsync('redis.status', 'skipped', true);
    return; // States never initialized!
  }
  
  // State initialization here (never reached if skipped)
  await this.createRedisStates();
}
```

**Correct Pattern:**
```javascript
async runRedisCheck() {
  // ✅ CORRECT: State init FIRST!
  await this.createRedisStates();
  
  const config = await this.detectRedisConfig();
  
  if (!config.objectsIsRedis && !config.statesIsRedis) {
    // States exist, just set status
    await this.setStateAsync('redis.status', 'skipped', true);
    return;
  }
  
  // Continue with actual monitoring
}
```

**Why This Matters:**
- States defined in `io-package.json` but never get values
- QA tools report "object_missing" (Object exists, State missing)
- Features appear broken even on systems where they don't apply

**Rule:** State initialization MUST happen before any `return` statement!

---

## 🔄 State Creation Requires Adapter Restart (PR #170)

**Learning:** `createStates()` runs ONCE at adapter startup. New states don't appear until restart!

**Scenario:**
1. PR #170 adds `memory.timestamp` and `disk.timestamp` states
2. PR gets merged
3. Code updated via `git pull` on live system
4. **States still missing!** ❌

**Why:**
- `onReady()` method (where `createStates()` is called) only runs when adapter starts
- `git pull` updates code, but doesn't restart adapter
- New states defined in code, but never initialized

**Solution:**
```bash
# After merging PR with new states:
iobroker restart system-health.0
```

**Automation Idea:**
- Add post-merge hook to restart adapter automatically
- Or: Check for state schema changes, prompt restart if needed

**Anti-Pattern:** Assuming states appear immediately after code update

---

_Auto-updated from issue feedback and PR reviews (Last update: 2026-03-09)_
