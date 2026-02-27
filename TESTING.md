# Testing Strategies for ioBroker Adapters

> Why dev-server testing alone is not enough

**Last Updated:** 2026-02-27

---

## 🎯 The Two-System Rule

**CRITICAL:** Always test on BOTH systems before creating a PR!

```
1. DEV-SERVER  → Verifies adapter starts + unit tests pass
2. REAL SYSTEM → Verifies UI integration + state bindings work
```

**Both are required!** Dev-server alone catches only ~50% of bugs.

---

## ❌ Common Mistake: Dev-Server Only

**What developers think:**
```bash
npm test  # All green! ✅
# "Ready for PR!" ❌
```

**What actually happens in production:**
- Admin UI shows `null` values
- Buttons don't work
- State bindings fail
- Dashboard empty

**Why?** Dev-server doesn't test:
- Admin UI rendering
- State OID bindings
- JSONConfig `onclick` handlers
- Dashboard state updates
- Real backend interactions

---

## ✅ Correct Testing Workflow

### Step 1: Dev-Server Tests

```bash
# Install dependencies
npm install

# Run linter
npm run lint

# Run unit tests
npm test

# Start dev-server
npm start
```

**What this verifies:**
- ✅ Adapter starts without crashes
- ✅ Code passes linting
- ✅ Unit tests pass
- ✅ Basic functionality works

**What this DOESN'T verify:**
- ❌ Admin UI integration
- ❌ State bindings
- ❌ Real backend behavior
- ❌ User interactions

---

### Step 2: Real System Tests

#### Installation Options

**Option A: Git-based (recommended for development)**
```bash
ssh user@iobroker-host
cd /opt/iobroker
git clone https://github.com/your-user/ioBroker.your-adapter.git
cd ioBroker.your-adapter
npm install
iobroker add .
iobroker upload your-adapter
```

**Option B: npm-based (for stable releases)**
```bash
iobroker add your-adapter@github:your-user/ioBroker.your-adapter
```

**Option C: Local upload (for quick tests)**
```bash
# On dev machine
tar czf adapter.tar.gz .

# On ioBroker system
scp adapter.tar.gz user@iobroker-host:/tmp/
ssh user@iobroker-host
cd /opt/iobroker
tar xzf /tmp/adapter.tar.gz
iobroker upload your-adapter
iobroker restart your-adapter.0
```

#### Test Checklist

**Admin UI:**
- [ ] Tab loads without errors
- [ ] All buttons clickable
- [ ] Form fields saveable
- [ ] No `null` values in UI
- [ ] State bindings show live data

**States:**
- [ ] All states initialized (not `null`)
- [ ] Values update periodically
- [ ] CLI: `iobroker state get your-adapter.0.*`

**Logs:**
- [ ] No errors in adapter log
- [ ] Expected info messages present
- [ ] Debug logs (if enabled) useful

**Dashboard (if applicable):**
- [ ] Widgets show data
- [ ] Graphs render
- [ ] Buttons trigger actions

---

## 🐛 Real-World Testing Bugs

### Bug #80: Dashboard Shows 'null'

**Dev-Server:** ✅ Passed  
**Real System:** ❌ Failed

**Root Cause:** JSONConfig state binding used relative path
```json
// ❌ WRONG (works in dev, fails in prod)
{
  "type": "staticText",
  "text": "memory.status"
}

// ✅ CORRECT
{
  "type": "staticText",
  "text": "system-health.0.memory.status"
}
```

**Lesson:** State bindings need absolute paths with instance ID.

---

### Bug #86: Detail Views Empty

**Dev-Server:** ✅ Passed  
**Real System:** ❌ Failed

**Root Cause:** Inspector data not persisted to states
```javascript
// Scan results stored in memory only
this.inspectorData = await this.scanStates();

// Admin UI requests /inspector/details
// → Adapter already finished startup, data lost
```

**Lesson:** Data needed by Admin UI must be persisted to states!

---

### Bug #78: Filter Buttons Not Working

**Dev-Server:** ✅ Passed (no UI interaction testing)  
**Real System:** ❌ Failed

**Root Cause:** JSONConfig uses `addEventListener` (security restricted)
```html
<!-- ❌ WRONG - doesn't execute in JSONConfig -->
<script>
  document.getElementById('btn').addEventListener('click', () => { ... });
</script>

<!-- ✅ CORRECT - use onclick attribute -->
<button onclick="filterTable('orphaned')">Show Orphaned</button>
```

**Lesson:** JSONConfig has security restrictions on dynamic script execution!

---

## 🧪 Test System Setup

### Hardware Requirements

**Minimum:**
- Raspberry Pi 3B+ / equivalent
- 2GB RAM
- 8GB SD card / storage
- Ethernet connection

**Recommended:**
- Raspberry Pi 4 / x86 VM
- 4GB+ RAM
- 16GB+ SSD
- Gigabit Ethernet

### Software Setup

```bash
# Install ioBroker
curl -sL https://iobroker.net/install.sh | bash -

# Enable Simple-API (for monitoring)
iobroker add simple-api

# Optional: Enable Admin on custom port
iobroker set admin.0 --enabled true --port 8081
```

### Backend Choice

**Redis (default):**
- ✅ Fast
- ✅ Good for production
- ❌ Data lost on Redis restart

**JSONL (file-based):**
- ✅ Data persists across restarts
- ✅ Easy to debug (readable files)
- ❌ Slightly slower

**For testing:** JSONL recommended (easier debugging)

```bash
# Switch to JSONL backend
iobroker setup custom
# Choose: objects = jsonl, states = jsonl
```

---

## 🔬 Debugging on Real System

### SSH Access

```bash
ssh user@iobroker-host

# Check adapter status
iobroker status

# View logs
iobroker logs --watch

# Restart adapter
iobroker restart your-adapter.0

# Check states
iobroker state get your-adapter.0.*
```

### Log Analysis

```bash
# View adapter-specific logs
tail -f /opt/iobroker/log/your-adapter.0.log

# Search for errors
grep -i error /opt/iobroker/log/your-adapter.0.log

# Check startup
grep "Starting" /opt/iobroker/log/your-adapter.0.log
```

### State Inspection

**Method 1: CLI**
```bash
# List all states
iobroker object list "your-adapter.0.*"

# Get specific state
iobroker state get your-adapter.0.memory.status

# Set state manually (for testing)
iobroker state set your-adapter.0.memory.status "critical"
```

**Method 2: Simple-API**
```bash
# All objects
curl http://localhost:8087/getObjects?pattern=your-adapter.0.*

# All states
curl http://localhost:8087/getStates?pattern=your-adapter.0.*

# Specific state
curl http://localhost:8087/get/your-adapter.0.memory.status
```

**Method 3: Admin UI**
1. Open Admin → Objects
2. Navigate to your adapter instance
3. Inspect state values visually

---

## 📊 Test Automation

### Unit Tests

```javascript
// test/unit.js
const expect = require('chai').expect;
const setup = require('./lib/setup');

describe('Memory Monitoring', function() {
  it('should calculate used percentage correctly', function() {
    const adapter = setup.createAdapter();
    const result = adapter.calculateMemoryPercent(1024, 512);
    expect(result).to.equal(50);
  });
});
```

### Integration Tests

```javascript
// test/integration.js
const { startAdapter, stopAdapter } = require('./lib/harness');

describe('State Initialization', function() {
  this.timeout(5000);

  let adapter;

  before(async function() {
    adapter = await startAdapter();
  });

  after(async function() {
    await stopAdapter(adapter);
  });

  it('should initialize memory.status state', async function() {
    const state = await adapter.getStateAsync('memory.status');
    expect(state).to.not.be.null;
    expect(state.val).to.be.a('string');
  });
});
```

### Automated Real-System Tests

**QA Script (Python):**
```python
#!/usr/bin/env python3
import requests
import sys

def test_adapter_states(host, adapter_id):
    """Test if all expected states are initialized."""
    api_url = f"http://{host}:8087"
    
    # Fetch states
    response = requests.get(f"{api_url}/getStates?pattern={adapter_id}.*")
    states = response.json()
    
    # Expected states
    expected = [
        f"{adapter_id}.memory.status",
        f"{adapter_id}.memory.usedPercent",
        f"{adapter_id}.disk.status"
    ]
    
    # Check each expected state
    missing = []
    for state_id in expected:
        if state_id not in states or states[state_id]['val'] is None:
            missing.append(state_id)
    
    if missing:
        print(f"❌ Missing states: {missing}")
        sys.exit(1)
    else:
        print(f"✅ All {len(expected)} states initialized")
        sys.exit(0)

if __name__ == '__main__':
    test_adapter_states('192.168.1.100', 'your-adapter.0')
```

**Run via cron:**
```bash
# Daily QA test
0 7 * * * python3 /path/to/qa-test.py >> /var/log/qa-test.log 2>&1
```

---

## 🎯 Pre-PR Testing Checklist

Before creating a pull request:

**Dev-Server:**
- [ ] `npm run lint` passes
- [ ] `npm test` passes (all unit tests green)
- [ ] Adapter starts without errors

**Real System:**
- [ ] Adapter installs successfully
- [ ] All states initialized (no `null` values)
- [ ] Admin UI tab loads
- [ ] All buttons/forms work
- [ ] State bindings show live data
- [ ] No errors in adapter log
- [ ] Tested on target backend (Redis/JSONL)

**Documentation:**
- [ ] README updated (if new features)
- [ ] CHANGELOG updated
- [ ] Code comments added

**Security:**
- [ ] No credentials in code
- [ ] No hardcoded IPs/hostnames
- [ ] Input validation present

---

## 🔧 Common Test System Issues

### Issue: Admin UI not accessible

```bash
# Check admin adapter status
iobroker status admin

# Restart admin
iobroker restart admin.0

# Check firewall
sudo ufw allow 8081/tcp
```

### Issue: States not updating

```bash
# Check if adapter is running
iobroker status your-adapter

# Check for errors
iobroker logs your-adapter.0

# Restart adapter
iobroker restart your-adapter.0
```

### Issue: Simple-API not responding

```bash
# Check if simple-api is enabled
iobroker list instances | grep simple-api

# Enable if needed
iobroker add simple-api

# Restart
iobroker restart simple-api.0
```

---

## 📚 Resources

- [ioBroker Testing Guide](https://github.com/ioBroker/ioBroker.docs/blob/master/docs/en/dev/testing.md)
- [Adapter Development Workflow](https://github.com/ioBroker/ioBroker.docs/blob/master/docs/en/dev/adapterdev.md)
- [Simple-API Documentation](https://github.com/ioBroker/ioBroker.simple-api)

---

_Auto-updated from real-world testing experiences_
