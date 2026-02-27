# Debugging ioBroker Adapters

> Tools, logs, SSH tricks, and troubleshooting

**Last Updated:** 2026-02-27

---

## 🎯 Debugging Workflow

```
1. Check adapter status
2. View logs
3. Inspect states
4. Test manually
5. Reproduce issue
6. Fix & verify
```

---

## 🔍 CLI Tools

### Adapter Status

```bash
# Check if adapter is running
iobroker status

# Check specific adapter
iobroker status system-health

# Compact output
iobroker list instances | grep system-health
```

**Output:**
```
+ system.adapter.system-health.0    : system-health - enabled, port: 8081
```

---

### Logs

```bash
# View all logs
iobroker logs

# Watch logs in real-time
iobroker logs --watch

# Filter by adapter
iobroker logs system-health

# Last N lines
iobroker logs --lines 50
```

**Log files location:**
```
/opt/iobroker/log/
├── iobroker.YYYY-MM-DD.log       # System logs
└── system-health.0.log           # Adapter-specific logs
```

---

### State Inspection

```bash
# List all states for adapter
iobroker state list "system-health.0.*"

# Get specific state
iobroker state get system-health.0.memory.status

# Set state (for testing)
iobroker state set system-health.0.memory.status "critical"

# Delete state
iobroker state del system-health.0.testValue
```

---

### Object Inspection

```bash
# List all objects
iobroker object list "system-health.0.*"

# Get object definition
iobroker object get system-health.0.memory.status

# Output JSON
iobroker object get system-health.0.memory.status --json
```

---

## 🖥️ SSH Debugging

### Connect to ioBroker Host

```bash
ssh user@iobroker-host

# Quick status check
ssh user@iobroker-host "iobroker status"
```

---

### Remote Log Viewing

```bash
# Tail adapter log remotely
ssh user@iobroker-host "tail -f /opt/iobroker/log/system-health.0.log"

# Search for errors
ssh user@iobroker-host "grep -i error /opt/iobroker/log/system-health.0.log"

# Last 50 lines
ssh user@iobroker-host "tail -n 50 /opt/iobroker/log/iobroker.log"
```

---

### Remote State Inspection

```bash
# Get all states (via Simple-API)
curl http://iobroker-host:8087/getStates?pattern=system-health.0.*

# Specific state
curl http://iobroker-host:8087/get/system-health.0.memory.status

# Pretty-print JSON
curl -s http://iobroker-host:8087/getStates?pattern=system-health.0.* | jq '.'
```

---

## 🐛 Common Issues & Solutions

### Issue: Adapter Won't Start

**Check status:**
```bash
iobroker status system-health
```

**Possible causes:**

1. **Port conflict:**
   ```bash
   # Check if port already in use
   netstat -tuln | grep 8081
   ```

2. **Missing dependencies:**
   ```bash
   cd /opt/iobroker/node_modules/iobroker.system-health
   npm install
   ```

3. **Syntax error:**
   ```bash
   iobroker logs system-health | grep -i error
   ```

**Fix:**
```bash
# Restart adapter
iobroker restart system-health.0

# If still fails, reinstall
iobroker del system-health
iobroker add system-health
```

---

### Issue: States Not Updating

**Check state value:**
```bash
iobroker state get system-health.0.memory.usedPercent
```

**If null:**
1. State never initialized → Check `onReady()` in adapter code
2. Adapter crashed after startup → Check logs
3. Backend issue → Check Redis/JSONL status

**Manually trigger update:**
```bash
# Set state to test if writes work
iobroker state set system-health.0.memory.usedPercent 42
```

---

### Issue: Admin UI Shows "null"

**Causes:**
1. **Relative OID path:**
   ```json
   // ❌ WRONG
   {"text": "memory.status"}
   
   // ✅ CORRECT
   {"text": "system-health.0.memory.status"}
   ```

2. **State not initialized:**
   ```bash
   # Check if state exists
   iobroker state get system-health.0.memory.status
   ```

3. **Admin cache:**
   ```bash
   # Clear browser cache
   # Or restart admin
   iobroker restart admin.0
   ```

---

### Issue: High CPU Usage

**Check process:**
```bash
# Find ioBroker processes
ps aux | grep iobroker

# Top CPU consumers
top -u iobroker
```

**Causes:**
- Infinite loop in adapter
- Too frequent state updates
- Memory leak

**Debug:**
```bash
# Enable debug logging
iobroker set system-health.0 --loglevel debug

# Watch logs
iobroker logs system-health --watch
```

---

## 📊 Performance Profiling

### Node.js Inspector

**Enable debugging:**
```javascript
// In adapter code
if (process.env.DEBUG) {
  debugger;  // Breakpoint
}
```

**Start with inspector:**
```bash
node --inspect /opt/iobroker/node_modules/iobroker.system-health/main.js
```

**Connect with Chrome DevTools:**
```
chrome://inspect
```

---

### Memory Profiling

```bash
# Start with heap snapshot
node --expose-gc --inspect /opt/iobroker/node_modules/iobroker.system-health/main.js
```

**Take heap snapshot:**
```javascript
// In adapter code
if (global.gc) {
  global.gc();
  const heapUsed = process.memoryUsage().heapUsed;
  this.log.info(`Heap used: ${Math.round(heapUsed / 1024 / 1024)} MB`);
}
```

---

## 🔬 State Dump Script

### Automated State Inspection

```python
#!/usr/bin/env python3
"""
Dump all states for an adapter (via Simple-API).
Useful for debugging missing states.
"""

import requests
import sys
import json

def dump_states(host, adapter_id, port=8087):
    api_url = f"http://{host}:{port}"
    
    # Fetch objects
    objects_url = f"{api_url}/getObjects?pattern={adapter_id}.*"
    objects = requests.get(objects_url, timeout=10).json()
    
    # Fetch states
    states_url = f"{api_url}/getStates?pattern={adapter_id}.*"
    states = requests.get(states_url, timeout=10).json()
    
    # Analyze
    print(f"\n📦 Objects: {len(objects)}")
    print(f"📊 States:  {len([s for s in states.values() if s and s.get('val') is not None])}")
    print(f"❌ Missing: {len([k for k in objects if k not in states or not states[k] or states[k].get('val') is None])}")
    
    # List missing
    print(f"\n❌ States without values:")
    for obj_id in objects:
        if obj_id not in states or not states.get(obj_id) or states[obj_id].get('val') is None:
            print(f"  - {obj_id}")
    
    # Save to file
    with open(f'/tmp/{adapter_id}-dump.json', 'w') as f:
        json.dump({'objects': objects, 'states': states}, f, indent=2)
    print(f"\n💾 Saved to /tmp/{adapter_id}-dump.json")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: dump-states.py <host> <adapter-id>")
        print("Example: dump-states.py 192.168.1.100 system-health.0")
        sys.exit(1)
    
    dump_states(sys.argv[1], sys.argv[2])
```

**Usage:**
```bash
python3 dump-states.py 192.168.1.100 system-health.0
```

---

## 🧪 Test Harness for Integration Tests

### Minimal Test Setup

```javascript
// test/lib/harness.js
const utils = require('@iobroker/adapter-core');

async function startAdapter(config = {}) {
  const adapter = utils.adapter({
    name: 'system-health',
    ...config
  });
  
  await adapter.startAsync();
  return adapter;
}

async function stopAdapter(adapter) {
  await adapter.terminate();
}

module.exports = { startAdapter, stopAdapter };
```

**Usage in tests:**
```javascript
const { startAdapter, stopAdapter } = require('./lib/harness');

describe('State Initialization', function() {
  let adapter;
  
  before(async function() {
    adapter = await startAdapter();
  });
  
  after(async function() {
    await stopAdapter(adapter);
  });
  
  it('should have states', async function() {
    const state = await adapter.getStateAsync('memory.status');
    expect(state).to.not.be.null;
  });
});
```

---

## 📱 Remote Debugging via SSH Tunnel

### Setup Tunnel

```bash
# Forward Simple-API port
ssh -L 8087:localhost:8087 user@iobroker-host

# Now access locally
curl http://localhost:8087/getStates?pattern=system-health.0.*
```

### Multiple Ports

```bash
# Forward multiple services
ssh -L 8087:localhost:8087 \
    -L 8081:localhost:8081 \
    -L 9001:localhost:9001 \
    user@iobroker-host

# 8087: Simple-API
# 8081: Admin UI
# 9001: Other service
```

---

## 🔧 Useful One-Liners

### Find All Adapters

```bash
iobroker list instances | grep enabled
```

### Count States

```bash
iobroker state list "system-health.0.*" | wc -l
```

### Find Non-Acknowledged States

```bash
iobroker state list "system-health.0.*" | while read state; do
  iobroker state get "$state" | grep -q "ack=false" && echo "$state"
done
```

### Check Disk Usage

```bash
du -sh /opt/iobroker/iobroker-data/*
```

### Backup States

```bash
# Export all states to JSON
iobroker backup

# Backup location
ls -lh /opt/iobroker/backups/
```

---

## 📚 Resources

- [ioBroker CLI Reference](https://github.com/ioBroker/ioBroker/wiki/Console-commands)
- [Adapter Debugging Guide](https://github.com/ioBroker/ioBroker.docs/blob/master/docs/en/dev/debugging.md)
- [Simple-API Endpoints](https://github.com/ioBroker/ioBroker.simple-api)

---

## 🎯 Debugging Checklist

When adapter doesn't work:

**Quick checks:**
- [ ] `iobroker status <adapter>` → Running?
- [ ] `iobroker logs <adapter>` → Errors?
- [ ] States initialized? (`iobroker state get`)

**Deep dive:**
- [ ] Admin UI shows data?
- [ ] State bindings correct? (absolute paths)
- [ ] Backend healthy? (Redis/JSONL)
- [ ] Simple-API responding?

**Advanced:**
- [ ] Memory usage normal?
- [ ] CPU usage normal?
- [ ] Disk space available?
- [ ] Network connectivity OK?

---

_Auto-updated from debugging experiences_
