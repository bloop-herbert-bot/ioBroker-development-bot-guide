# Examples

This directory contains practical scripts and examples for ioBroker adapter development and testing.

---

## 📊 State Monitoring

### `state-dump-api.py`

Dump all states for an adapter via Simple-API REST endpoint.

**Features:**
- ✅ Atomic snapshots (no race conditions)
- ✅ No SSH filesystem access needed
- ✅ Stable, consistent results
- ✅ JSON output

**Usage:**
```bash
python3 state-dump-api.py <host> <adapter-id> [port]

# Example:
python3 state-dump-api.py 192.168.1.100 system-health.0 8087
```

**Output:**
```json
{
  "adapter": "system-health.0",
  "host": "192.168.1.100",
  "objects": { ... },
  "states": { ... },
  "missing": ["system-health.0.redis.status", ...],
  "stats": {
    "total_objects": 50,
    "total_states": 34,
    "missing_count": 16
  }
}
```

---

## 🧪 Automated QA Testing

### `qa-automation.py`

Automated testing script that finds missing/null states.

**Features:**
- ✅ Feature-based bug grouping
- ✅ Critical vs. Info classification
- ✅ Human-readable reports
- ✅ Configurable via JSON

**Usage:**
```bash
python3 qa-automation.py <host> <adapter-id> <config-file>

# Example:
python3 qa-automation.py 192.168.1.100 system-health.0 qa-config.json
```

**Config file (`qa-config.json`):**
```json
{
  "features": {
    "memory.status": {
      "name": "Memory Monitoring",
      "critical": true
    },
    "redis.connected": {
      "name": "Redis Monitoring",
      "critical": true
    }
  }
}
```

**Output:**
```
🧪 **QA Report: system-health.0**

🐛 **Bugs found:** 15 states in 2 features

🔴 **Log Monitoring** (6 states)
   Critical: 3, Info: 3
   🔴 `logs.totalErrors` - Missing State
   🔴 `logs.totalWarnings` - Missing State
   ...

🔴 **Redis Monitoring** (9 states)
   Critical: 2, Info: 7
   🔴 `redis.status` - Missing State
   ...
```

---

## 🔄 Cron Integration

Run QA tests automatically via cron:

```bash
# Daily QA test at 7 AM
0 7 * * * python3 /path/to/qa-automation.py 192.168.1.100 system-health.0 /path/to/qa-config.json >> /var/log/qa-test.log 2>&1
```

---

## 🎯 Exit Codes

Both scripts use standard exit codes:

- `0` - Success (no issues found)
- `1` - Issues found (QA) or Error (state-dump)

**Use in CI/CD:**
```bash
if ! python3 qa-automation.py localhost system-health.0 config.json; then
  echo "QA tests failed!"
  exit 1
fi
```

---

## 📚 Requirements

```bash
pip install requests
```

---

## 🔒 Security Note

These scripts use placeholders like `<host>` in comments.

**Never hardcode:**
- IP addresses
- Usernames
- Passwords
- API tokens

**Always pass as arguments:**
```bash
python3 script.py $HOST $ADAPTER_ID
```

---

## 📖 Related Documentation

- [STATE_MANAGEMENT.md](../STATE_MANAGEMENT.md) - State initialization patterns
- [BACKEND_INTEGRATION.md](../BACKEND_INTEGRATION.md) - Simple-API usage
- [TESTING.md](../TESTING.md) - Testing strategies

---

_Auto-updated from real-world usage_
