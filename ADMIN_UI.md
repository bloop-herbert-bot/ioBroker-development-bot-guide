# Admin UI Development

> JSONConfig vs. Legacy Materialize

**Last Updated:** 2026-02-27

---

## 🎯 Modern Admin UI: JSONConfig

Since ioBroker.js-controller 4.x, **JSONConfig** is the standard for Admin UI configuration.

**Advantages:**
- ✅ Declarative JSON format
- ✅ Automatic form generation
- ✅ Built-in validation
- ✅ Responsive design
- ✅ Easy translation (i18n)
- ✅ No HTML/CSS knowledge required

**Legacy Materialize is deprecated!**

---

## ❌ Anti-Pattern: Legacy Materialize UI

### The Wrong Way (Deprecated)

**File structure:**
```
admin/
├── index_m.html      # HTML template (deprecated!)
├── words.js          # Translations (deprecated format!)
├── custom.css        # Custom styles
└── admin.js          # JavaScript logic
```

**Example `index_m.html`:**
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="../../css/adapter.css"/>
    <script type="text/javascript" src="../../lib/js/jquery-3.2.1.min.js"></script>
    <script type="text/javascript" src="../../js/adapter-settings.js"></script>
</head>
<body>
    <div class="m adapter-container">
        <div class="row">
            <div class="col s12">
                <ul class="tabs">
                    <li class="tab col s2"><a href="#tab-main" class="translate">Main settings</a></li>
                </ul>
            </div>
        </div>
        <!-- Form fields... -->
    </div>
</body>
</html>
```

**Why it's wrong:**
- Manual HTML maintenance
- No automatic validation
- Hard to extend
- Not responsive by default
- Deprecated since 2021

---

## ✅ Correct Approach: JSONConfig

### File Structure

```
admin/
├── jsonConfig.json       # UI definition (main file!)
└── i18n/
    ├── en.json          # English translations
    ├── de.json          # German translations
    ├── ru.json          # Russian translations
    └── ...
```

### Basic Example

**`admin/jsonConfig.json`:**
```json
{
  "type": "panel",
  "label": "Main settings",
  "items": {
    "checkInterval": {
      "type": "number",
      "label": "Check interval (seconds)",
      "min": 10,
      "max": 3600,
      "default": 60
    },
    "enableMemoryCheck": {
      "type": "checkbox",
      "label": "Enable memory monitoring"
    },
    "memoryThreshold": {
      "type": "number",
      "label": "Memory threshold (MB)",
      "min": 100,
      "max": 8192,
      "hidden": "!data.enableMemoryCheck"
    }
  }
}
```

**`admin/i18n/de.json`:**
```json
{
  "Main settings": "Haupteinstellungen",
  "Check interval (seconds)": "Prüfintervall (Sekunden)",
  "Enable memory monitoring": "Speicherüberwachung aktivieren",
  "Memory threshold (MB)": "Speicherschwellenwert (MB)"
}
```

---

## 📋 JSONConfig Components

### Text Input

```json
{
  "instanceName": {
    "type": "text",
    "label": "Instance name",
    "placeholder": "My system health",
    "maxLength": 50
  }
}
```

### Number Input

```json
{
  "threshold": {
    "type": "number",
    "label": "Threshold",
    "min": 0,
    "max": 100,
    "default": 80,
    "step": 5,
    "unit": "%"
  }
}
```

### Checkbox

```json
{
  "enabled": {
    "type": "checkbox",
    "label": "Enable feature",
    "default": true
  }
}
```

### Select / Dropdown

```json
{
  "logLevel": {
    "type": "select",
    "label": "Log level",
    "options": [
      {"value": "debug", "label": "Debug"},
      {"value": "info", "label": "Info"},
      {"value": "warn", "label": "Warning"},
      {"value": "error", "label": "Error"}
    ]
  }
}
```

### Textarea

```json
{
  "customScript": {
    "type": "textarea",
    "label": "Custom script",
    "rows": 10
  }
}
```

### Password

```json
{
  "apiKey": {
    "type": "password",
    "label": "API Key",
    "repeat": true
  }
}
```

---

## 🎨 Advanced Features

### Conditional Visibility

```json
{
  "useCustomServer": {
    "type": "checkbox",
    "label": "Use custom server"
  },
  "serverUrl": {
    "type": "text",
    "label": "Server URL",
    "hidden": "!data.useCustomServer"
  }
}
```

### Tabs

```json
{
  "type": "tabs",
  "items": {
    "tab1": {
      "type": "panel",
      "label": "General",
      "items": { ... }
    },
    "tab2": {
      "type": "panel",
      "label": "Advanced",
      "items": { ... }
    }
  }
}
```

### Tables

```json
{
  "instances": {
    "type": "table",
    "label": "Monitored instances",
    "items": [
      {
        "type": "text",
        "title": "Instance ID",
        "attr": "id",
        "width": "50%"
      },
      {
        "type": "checkbox",
        "title": "Enabled",
        "attr": "enabled",
        "width": "25%"
      }
    ]
  }
}
```

---

## 🖼️ Custom HTML (Advanced)

### Embedding HTML in JSONConfig

**⚠️ Security restrictions apply!**

```json
{
  "dashboard": {
    "type": "custom",
    "url": "custom.html",
    "i18n": true
  }
}
```

**`admin/custom.html`:**
```html
<div>
  <h3>System Health Dashboard</h3>
  <button onclick="refreshData()">Refresh</button>
  <div id="status"></div>
</div>

<script>
  // ⚠️ addEventListener doesn't work in JSONConfig!
  // Use onclick attributes instead

  function refreshData() {
    // Fetch data via sendTo
    sendTo('system-health.0', 'getStatus', {}, function(result) {
      document.getElementById('status').innerText = result;
    });
  }
</script>
```

### JSONConfig Security Restrictions

**❌ Doesn't work:**
```javascript
// Dynamic event listeners (security restricted!)
document.getElementById('btn').addEventListener('click', handler);

// External scripts
<script src="https://external.com/lib.js"></script>
```

**✅ Works:**
```javascript
// Inline onclick handlers
<button onclick="myFunction()">Click</button>

// Inline scripts (local functions)
<script>
  function myFunction() { ... }
</script>
```

**Lesson from Issue #78:** Always use `onclick` attributes, not `addEventListener`!

---

## 📊 State Bindings in Admin UI

### Displaying Live State Values

**❌ Wrong (relative path):**
```json
{
  "type": "staticText",
  "text": "memory.status"
}
```

**Result:** Shows "null" because relative path doesn't resolve.

**✅ Correct (absolute path with instance):**
```json
{
  "type": "staticText",
  "text": "system-health.0.memory.status"
}
```

**Lesson from Issue #80:** Always use full OID path: `adapter-name.instance.state-id`

---

## 🎨 Styling Custom HTML

### Inline CSS

```html
<style>
  .status-ok { color: green; }
  .status-warning { color: orange; }
  .status-error { color: red; }
</style>

<div class="status-ok">System OK</div>
```

### Material Design Icons

```html
<!-- Use Material Icons (built-in) -->
<i class="material-icons">check_circle</i>
<i class="material-icons">warning</i>
<i class="material-icons">error</i>
```

---

## 🔧 Adapter Settings vs. State Bindings

### Configuration (Saved Settings)

```json
// jsonConfig.json
{
  "checkInterval": {
    "type": "number",
    "label": "Check interval"
  }
}
```

**Accessed in adapter code:**
```javascript
const interval = this.config.checkInterval;
```

### State Bindings (Live Data)

**Display state value in Admin UI:**
```json
{
  "type": "staticText",
  "text": "system-health.0.memory.usedPercent",
  "label": "Memory Used"
}
```

**Access in adapter code:**
```javascript
await this.getStateAsync('memory.usedPercent');
```

---

## 🐛 Common Admin UI Bugs

### Bug #78: Filter Buttons Not Working

**Problem:**
```html
<button id="filter-btn">Filter</button>

<script>
  // ❌ Doesn't execute in JSONConfig!
  document.getElementById('filter-btn').addEventListener('click', () => {
    console.log('clicked');
  });
</script>
```

**Fix:**
```html
<!-- ✅ Use onclick attribute -->
<button onclick="filterTable()">Filter</button>

<script>
  function filterTable() {
    console.log('clicked');
  }
</script>
```

### Bug #87: Boolean States Show Raw Values

**Problem:** Admin UI shows "WAHR" / "FALSCH" (German) instead of human-readable text.

**Fix:** Add `states` mapping in state definition:
```json
{
  "type": "boolean",
  "role": "indicator",
  "states": {
    "false": "No leak detected",
    "true": "Leak detected"
  }
}
```

---

## 📚 JSONConfig Reference

### Full Example: system-health

**`admin/jsonConfig.json`:**
```json
{
  "type": "tabs",
  "items": {
    "options": {
      "type": "panel",
      "label": "General Settings",
      "items": {
        "checkInterval": {
          "type": "number",
          "label": "Check interval (seconds)",
          "min": 10,
          "max": 3600,
          "default": 60
        },
        "_divider1": {
          "type": "divider"
        },
        "enableMemory": {
          "type": "checkbox",
          "label": "Enable memory monitoring",
          "default": true
        },
        "memoryThreshold": {
          "type": "number",
          "label": "Free memory threshold (MB)",
          "min": 100,
          "max": 8192,
          "default": 512,
          "hidden": "!data.enableMemory"
        }
      }
    },
    "dashboard": {
      "type": "panel",
      "label": "Dashboard",
      "items": {
        "customDashboard": {
          "type": "custom",
          "url": "custom.html",
          "i18n": true
        }
      }
    }
  }
}
```

---

## 🎯 Migration Checklist: Materialize → JSONConfig

- [ ] Remove `admin/index_m.html`
- [ ] Remove `admin/words.js`
- [ ] Create `admin/jsonConfig.json`
- [ ] Create `admin/i18n/*.json` files
- [ ] Convert form fields to JSON schema
- [ ] Test all input validation
- [ ] Test conditional visibility
- [ ] Verify state bindings use absolute paths
- [ ] Replace `addEventListener` with `onclick`
- [ ] Test on multiple Admin versions

---

## 📚 Resources

- [JSONConfig Documentation](https://github.com/ioBroker/ioBroker.admin/blob/master/packages/jsonConfig/SCHEMA.md)
- [JSONConfig Examples](https://github.com/ioBroker/ioBroker.admin/tree/master/packages/jsonConfig/EXAMPLES)
- [Adapter Dev Guide](https://github.com/ioBroker/ioBroker.docs/blob/master/docs/en/dev/adapterdev.md)

---

## 🎨 Collapsible Sections for Large Dashboards (PR #166)

**Problem:** Large dashboards with 20+ widgets become cluttered and hard to navigate.

**Solution:** Use collapsible panels to group related features.

**Pattern:**
```json5
{
  "type": "panel",
  "label": "Memory Monitoring",
  "collapsible": true,
  "collapsed": false,
  "items": {
    "memory_totalMB": {
      "type": "staticText",
      "label": "Total RAM",
      "text": "{{ val: 'memory.totalMB' }} MB",
      "newLine": true,
      "sm": 6
    },
    "memory_usedMB": {
      "type": "staticText", 
      "label": "Used RAM",
      "text": "{{ val: 'memory.usedMB' }} MB",
      "sm": 6
    }
  }
}
```

**Key Properties:**
- `collapsible: true` - Makes panel expandable/collapsible
- `collapsed: false` - Default state (expanded)
- `collapsed: true` - Start collapsed (useful for rarely-used features)

**When to Use:**
- **Expanded by default:** Core features (Memory, Disk, Logs)
- **Collapsed by default:** Optional features (Redis, Advanced Settings)
- **Benefits:** Reduced visual clutter, faster page load, better UX

**Layout Tips:**
- Use `"newLine": true, "sm": 12` for full-width elements
- Use `"sm": 6` for side-by-side widgets (2 columns)
- Use `"sm": 4` for 3 columns (on larger screens)

**Example:** system-health dashboard has 5 collapsible sections:
1. Memory (expanded)
2. Disk (expanded)
3. Redis (collapsed - only relevant if Redis backend)
4. Logs (expanded)
5. State Inspector (expanded)

---

_Auto-updated from Admin UI learnings (Last update: 2026-03-09)_
