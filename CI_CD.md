# CI/CD for ioBroker Adapters

> GitHub Actions, ESLint, Testing Automation

**Last Updated:** 2026-02-27

---

## 🎯 Standard CI/CD Pipeline

Typical ioBroker adapter CI/CD workflow:

```
1. Lint Check (ESLint)
2. Unit Tests (npm test)
3. Integration Tests (optional)
4. Build (if TypeScript)
5. Release (automated versioning)
```

---

## ⚙️ GitHub Actions Workflow

### Basic Workflow

**`.github/workflows/test.yml`:**
```yaml
name: Test and Release

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linter
        run: npm run lint
      
      - name: Run tests
        run: npm test
```

---

## 🔍 ESLint Configuration

### ESLint 9 (Modern)

**⚠️ Breaking change from ESLint 8!**

**`eslint.config.js` (NEW format):**
```javascript
import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.node,
        ...globals.mocha
      }
    },
    rules: {
      'indent': ['error', 2],
      'quotes': ['error', 'single'],
      'semi': ['error', 'always']
    }
  }
];
```

### ESLint 8 (Legacy)

**`.eslintrc.json` (OLD format):**
```json
{
  "env": {
    "node": true,
    "es6": true,
    "mocha": true
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": 2022
  },
  "rules": {
    "indent": ["error", 2],
    "quotes": ["error", "single"],
    "semi": ["error", "always"]
  }
}
```

---

## ❌ CI Anti-Pattern: Assuming Failure = Your Code

### Bug from PR #109

**Symptom:** All CI checks failed

**Initial assumption:** "My code is broken"

**Reality:** Repository-wide ESLint 9 migration incomplete
- ESLint 9 config missing (`eslint.config.js`)
- Test scripts missing (`test:integration`)
- **Not PR-specific!**

**How to verify:**
```bash
# Checkout main branch
git checkout main

# Run same checks
npm run lint
npm run test:integration

# Same errors? → Repository issue, not your code!
```

**Lesson:** Always verify if CI failure exists on main branch!

---

## 🐛 Common CI/CD Issues

### Issue 1: Missing Scripts in package.json

**Error:**
```
npm error Missing script: "test:integration"
```

**Cause:** CI workflow calls script that doesn't exist:
```yaml
- name: Run integration tests
  run: npm run test:integration  # ❌ Script missing!
```

**Fix:** Add to `package.json`:
```json
{
  "scripts": {
    "test": "mocha test/unit.js",
    "test:integration": "mocha test/integration.js",
    "lint": "eslint ."
  }
}
```

---

### Issue 2: ESLint Config Mismatch

**Error:**
```
ESLint couldn't find an eslint.config.(js|mjs|cjs) file.
```

**Cause:** ESLint 9 requires new config format

**Migration:**
```bash
# Remove old config
rm .eslintrc.json

# Create new config
touch eslint.config.js
```

**Update `package.json`:**
```json
{
  "devDependencies": {
    "eslint": "^9.0.0",  // Update version
    "@eslint/js": "^9.0.0",
    "globals": "^14.0.0"
  }
}
```

---

### Issue 3: Node Version Incompatibility

**Error:**
```
Error: The engine "node" is incompatible with this module.
```

**Fix:** Update `package.json`:
```json
{
  "engines": {
    "node": ">=16.0.0"
  }
}
```

---

## 🧪 Testing Setup

### Unit Tests

**`test/unit.js`:**
```javascript
const { expect } = require('chai');
const { calculatePercentage } = require('../lib/utils');

describe('Utils', function() {
  describe('calculatePercentage()', function() {
    it('should calculate percentage correctly', function() {
      expect(calculatePercentage(50, 100)).to.equal(50);
    });
    
    it('should handle zero total', function() {
      expect(calculatePercentage(0, 0)).to.equal(0);
    });
  });
});
```

**Run:**
```bash
npm test
```

---

### Integration Tests

**`test/integration.js`:**
```javascript
const { startAdapter, stopAdapter } = require('./lib/harness');

describe('Adapter Integration', function() {
  this.timeout(10000);
  
  let adapter;
  
  before(async function() {
    adapter = await startAdapter();
  });
  
  after(async function() {
    await stopAdapter(adapter);
  });
  
  it('should initialize all states', async function() {
    const states = await adapter.getStatesAsync('*');
    expect(Object.keys(states).length).to.be.above(0);
  });
});
```

---

## 🚀 Automated Releases

### Semantic Release

**`.github/workflows/release.yml`:**
```yaml
name: Release

on:
  push:
    branches:
      - main

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Semantic Release
        uses: cycjimmy/semantic-release-action@v3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**`release.config.js`:**
```javascript
module.exports = {
  branches: ['main'],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    '@semantic-release/changelog',
    '@semantic-release/npm',
    '@semantic-release/github',
    '@semantic-release/git'
  ]
};
```

---

## 🔒 Secrets Management

### GitHub Secrets

**Add secrets via:**
```
Repository Settings → Secrets and variables → Actions
```

**Common secrets:**
- `NPM_TOKEN` - For npm publishing
- `SENTRY_DSN` - Error tracking
- `API_KEY` - External services

**Access in workflow:**
```yaml
env:
  NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

---

## 📊 Code Coverage

### Istanbul/NYC

**Install:**
```bash
npm install --save-dev nyc
```

**`package.json`:**
```json
{
  "scripts": {
    "test": "nyc mocha test/**/*.js",
    "coverage": "nyc report --reporter=html"
  },
  "nyc": {
    "reporter": ["text", "html"],
    "exclude": ["test/**"]
  }
}
```

**GitHub Action:**
```yaml
- name: Run tests with coverage
  run: npm run test

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
```

---

## 🔧 Bot-Specific CI Constraints

### What Bots Can't Change

**From AGENTS_CONTRIBUTORS.md:**
- ❌ `.github/workflows/*` (CI config)
- ❌ `eslint.config.js` (Linting config)
- ❌ `package.json` scripts (Build tools)
- ❌ `.gitignore` / `.npmignore`

**Reason:** Repository-wide infrastructure = maintainer responsibility

**What to do when CI fails:**
1. Check if issue exists on main branch
2. Comment on PR explaining the failure
3. Ask maintainer to fix infrastructure
4. **Don't try to fix it yourself!**

---

## 🎯 Pre-Commit Checks

### Husky + lint-staged

**Install:**
```bash
npm install --save-dev husky lint-staged
npx husky install
```

**`.husky/pre-commit`:**
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx lint-staged
```

**`package.json`:**
```json
{
  "lint-staged": {
    "*.js": [
      "eslint --fix",
      "git add"
    ]
  }
}
```

**Effect:** Auto-lint before every commit

---

## 📦 Build Process (TypeScript Adapters)

### TypeScript Setup

**`tsconfig.json`:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true
  }
}
```

**`package.json`:**
```json
{
  "scripts": {
    "build": "tsc",
    "prebuild": "npm run lint",
    "prepublishOnly": "npm run build"
  }
}
```

**GitHub Action:**
```yaml
- name: Build TypeScript
  run: npm run build
```

---

## 🐛 Debugging CI Failures

### View Logs

```bash
# View recent workflow runs
gh run list --repo owner/repo

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

### Re-run Failed Jobs

```bash
gh run rerun <run-id>

# Or via PR:
gh pr checks <pr-number> --watch
```

---

## 📚 Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [ESLint Configuration](https://eslint.org/docs/latest/use/configure/)
- [Semantic Release](https://github.com/semantic-release/semantic-release)
- [Mocha Testing](https://mochajs.org/)

---

## 🎯 CI/CD Checklist

Before submitting PR:

**Local checks:**
- [ ] `npm run lint` passes
- [ ] `npm test` passes
- [ ] Build succeeds (if TypeScript)

**CI checks:**
- [ ] All GitHub Actions green
- [ ] Code coverage acceptable
- [ ] No security vulnerabilities

**Infrastructure issues:**
- [ ] If CI fails, verify on main branch first
- [ ] Comment on PR explaining infrastructure issues
- [ ] Don't modify CI files unless explicitly requested

---

_Auto-updated from CI/CD learnings_
