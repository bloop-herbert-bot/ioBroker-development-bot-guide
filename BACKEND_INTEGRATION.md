# Backend Integration

> Redis, JSONL, and Simple-API best practices

**Last Updated:** 2026-02-27

---

## 🎯 ioBroker Backend Options

ioBroker supports multiple backends for storing objects and states:

| Backend | Type | Persistence | Speed | Use Case |
|---------|------|-------------|-------|----------|
| **Redis** | In-Memory | Optional | Fast | Production (default) |
| **JSONL** | File-based | Always | Medium | Development, Debugging |
| **File** | File-based | Always | Slow | Legacy (deprecated) |

---

## 🔴 Redis Backend

### Characteristics

- ✅ **Fast:** In-memory storage
- ✅ **Scalable:** Handles many states efficiently
- ❌ **Not persistent by default:** Data lost on Redis restart (unless configured)
- ❌ **Harder to debug:** Binary protocol, needs Redis CLI

### When to Use

- Production systems with many adapters
- High-frequency state updates
- Systems with UPS (protect against power loss)

### Configuration

```bash
# Switch to Redis (if not already)
iobroker setup custom
# Choose: objects = redis, states = redis
```

### Persistence Setup

```bash
# Enable Redis persistence
sudo nano /etc/redis/redis.conf

# Add/uncomment:
save 900 1      # Save after 900 sec if >= 1 key changed
save 300 10     # Save after 300 sec if >= 10 keys changed
save 60 10000   # Save after 60 sec if >= 10000 keys changed

# Restart Redis
sudo systemctl restart redis
```

### Debugging

```bash
# Connect to Redis
redis-cli

# List all keys
KEYS *

# Get specific state
GET io.system-health.0.memory.status

# Get object definition
GET io.system-health.0.memory.status.object
```

---

## 📄 JSONL Backend

### Characteristics

- ✅ **Persistent:** Survives restarts
- ✅ **Human-readable:** Plain-text JSON lines
- ✅ **Easy debugging:** Can `cat` files directly
- ❌ **Slower:** Disk I/O on every write
- ❌ **Append-only:** Files grow over time

### When to Use

- Development/testing systems
- Low-frequency state updates
- Systems where data loss is unacceptable
- Debugging state initialization issues

### Configuration

```bash
# Switch to JSONL
iobroker setup custom
# Choose: objects = jsonl, states = jsonl
```

### File Structure

```
/opt/iobroker/iobroker-data/
├── objects.jsonl    # Object definitions
├── states.jsonl     # State values
└── backup/          # Automatic backups
```

**Format (one JSON object per line):**
```jsonl
{"k":"system-health.0.memory.status","v":{"type":"state","common":{...}}}
{"k":"system-health.0.memory.usedPercent","v":{"type":"state","common":{...}}}
```

### Debugging

```bash
# View all system-health objects
cat /opt/iobroker/iobroker-data/objects.jsonl | grep "system-health.0"

# Pretty-print specific object
cat /opt/iobroker/iobroker-data/objects.jsonl | \
  grep "system-health.0.memory.status" | \
  jq '.'

# View state values
cat /opt/iobroker/iobroker-data/states.jsonl | grep "system-health.0"
```

---

## ❌ Direct JSONL Access Anti-Pattern

### The Wrong Way

```python
# ❌ WRONG - Race conditions!
import subprocess

def get_states_wrong(host, adapter_id):
    cmd = f'ssh user@{host} "cat /opt/iobroker/iobroker-data/states.jsonl | grep {adapter_id}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    states = {}
    for line in result.stdout.split('\n'):
        data = json.loads(line)  # May fail on incomplete lines!
        states[data['k']] = data['v']
    
    return states
```

**Problems:**
1. **Race condition:** Adapter writes while you read → incomplete JSON lines
2. **Duplicate entries:** JSONL is append-only, same key appears multiple times
3. **grep unreliable:** Pattern matching can miss or mismatch
4. **Result fluctuates:** 43 states, then 60, then 47...

### Real-World Impact

**Bug discovered:** State-dump script reported:
```
Run 1: 55 states
Run 2: 43 states (-12!)
Run 3: 60 states (+17!)
Run 4: 47 states (-13!)
```

**Root cause:** SSH grep race conditions during file growth.

**Fix:** Use Simple-API instead (see below).

---

## ✅ Simple-API: The Right Way

### What is Simple-API?

Official ioBroker adapter providing REST endpoints for:
- Reading/writing states
- Listing objects
- Subscribing to state changes
- No authentication by default (designed for local network)

### Installation

```bash
iobroker add simple-api

# Configure port (default: 8087)
iobroker set simple-api.0 --port 8087

# Restart
iobroker restart simple-api.0
```

### API Endpoints

#### Get Objects

```bash
# All objects matching pattern
curl http://localhost:8087/getObjects?pattern=system-health.0.*

# Response: JSON object with all definitions
{
  "system-health.0.memory.status": {
    "type": "state",
    "common": { ... },
    "native": {}
  },
  ...
}
```

#### Get States

```bash
# All states matching pattern
curl http://localhost:8087/getStates?pattern=system-health.0.*

# Response: JSON object with all state values
{
  "system-health.0.memory.status": {
    "val": "ok",
    "ack": true,
    "ts": 1709033400000,
    "from": "system.adapter.system-health.0"
  },
  ...
}
```

#### Get Single State

```bash
curl http://localhost:8087/get/system-health.0.memory.status

# Response:
{
  "val": "ok",
  "ack": true,
  "ts": 1709033400000
}
```

#### Set State

```bash
curl -X POST http://localhost:8087/set/system-health.0.testValue?value=123

# With ack flag:
curl -X POST http://localhost:8087/set/system-health.0.testValue?value=123&ack=true
```

---

## 🐍 Python Client Example

```python
#!/usr/bin/env python3
import requests
import json

class ioBrokerAPI:
    def __init__(self, host, port=8087):
        self.base_url = f"http://{host}:{port}"
    
    def get_objects(self, pattern):
        """Get all objects matching pattern."""
        url = f"{self.base_url}/getObjects?pattern={pattern}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_states(self, pattern):
        """Get all states matching pattern."""
        url = f"{self.base_url}/getStates?pattern={pattern}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_state(self, state_id):
        """Get single state value."""
        url = f"{self.base_url}/get/{state_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def set_state(self, state_id, value, ack=False):
        """Set state value."""
        url = f"{self.base_url}/set/{state_id}?value={value}&ack={ack}"
        response = requests.post(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def find_missing_states(self, adapter_id):
        """Find objects without state values."""
        objects = self.get_objects(f"{adapter_id}.*")
        states = self.get_states(f"{adapter_id}.*")
        
        missing = []
        for obj_id in objects.keys():
            if obj_id not in states or states[obj_id]['val'] is None:
                missing.append(obj_id)
        
        return missing

# Usage
api = ioBrokerAPI('192.168.1.100')

# Get all system-health states
states = api.get_states('system-health.0.*')
print(f"Found {len(states)} states")

# Find missing states
missing = api.find_missing_states('system-health.0')
print(f"Missing: {missing}")
```

---

## 📊 Backend Comparison: Performance

### Test: Read 50 States

| Method | Time | Reliability |
|--------|------|-------------|
| Redis CLI | ~100ms | High |
| JSONL direct read | ~200ms | **Low (race conditions!)** |
| Simple-API REST | ~150ms | High |
| iobroker CLI | ~5000ms | High (but slow) |

### Test: Write 1000 States/sec

| Backend | CPU Usage | Success Rate |
|---------|-----------|--------------|
| Redis | 5% | 100% |
| JSONL | 15% | 100% |

**Recommendation:** Redis for production, JSONL for development.

---

## 🔧 State Monitoring Script (Simple-API)

```python
#!/usr/bin/env python3
"""
Monitor ioBroker adapter states via Simple-API.
Stable, no race conditions, no SSH needed!
"""

import requests
import sys
import json

def fetch_states(host, port, adapter_id):
    """Fetch all states for adapter via Simple-API."""
    api_url = f"http://{host}:{port}"
    
    # Get objects
    objects_url = f"{api_url}/getObjects?pattern={adapter_id}.*"
    objects = requests.get(objects_url, timeout=10).json()
    
    # Get states
    states_url = f"{api_url}/getStates?pattern={adapter_id}.*"
    states = requests.get(states_url, timeout=10).json()
    
    # Filter states with values
    states_with_values = {
        k: v for k, v in states.items() 
        if v is not None and v.get('val') is not None
    }
    
    # Find missing
    missing = [k for k in objects.keys() if k not in states_with_values]
    
    return {
        'objects': objects,
        'states': states_with_values,
        'missing': missing,
        'stats': {
            'total_objects': len(objects),
            'total_states': len(states_with_values),
            'missing_count': len(missing)
        }
    }

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: monitor-states.py <host> <adapter-id>")
        print("Example: monitor-states.py 192.168.1.100 system-health.0")
        sys.exit(1)
    
    host = sys.argv[1]
    adapter_id = sys.argv[2]
    
    data = fetch_states(host, 8087, adapter_id)
    
    print(f"\n📊 Stats:")
    print(f"  Objects: {data['stats']['total_objects']}")
    print(f"  States:  {data['stats']['total_states']}")
    print(f"  Missing: {data['stats']['missing_count']}")
    
    if data['missing']:
        print(f"\n❌ Missing states:")
        for state_id in data['missing']:
            print(f"  - {state_id}")
```

**Run 5x and verify stability:**
```bash
for i in {1..5}; do
  python3 monitor-states.py 192.168.1.100 system-health.0
  sleep 2
done

# All runs should show IDENTICAL numbers!
```

---

## 🔒 Security Considerations

### Simple-API Access Control

**By default:** No authentication! Anyone on network can read/write.

**Secure it:**
```bash
# Bind to localhost only
iobroker set simple-api.0 --bind 127.0.0.1

# Or enable auth
iobroker set simple-api.0 --auth true
```

**For remote access:** Use SSH tunnel
```bash
ssh -L 8087:localhost:8087 user@iobroker-host
# Now access via http://localhost:8087
```

---

## 📚 Resources

- [Simple-API Adapter](https://github.com/ioBroker/ioBroker.simple-api)
- [Redis Persistence](https://redis.io/docs/management/persistence/)
- [JSONL Format](http://jsonlines.org/)

---

## 🎯 Quick Reference

**When to use what:**

| Task | Method | Why |
|------|--------|-----|
| Read many states | Simple-API | Fast, reliable, no race conditions |
| Debug single state | `iobroker state get` | Simple, human-readable |
| Set state manually | `iobroker state set` | CLI available everywhere |
| Automated monitoring | Simple-API + Python | Scriptable, stable |
| Production backend | Redis | Fast, scalable |
| Development backend | JSONL | Persistent, debuggable |

---

_Auto-updated from backend integration learnings_
