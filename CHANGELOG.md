# Changelog

Auto-generated from system-health PRs.

## 2026-03-08

- **PR #170:** Add timestamps to memory, disk and logs monitoring
  - **Learning:** State initialization requires adapter restart (createStates() only runs on startup)
  - **Anti-Pattern:** Assuming states appear immediately after PR merge
  - **Fix:** Always restart adapter after merging state-creation PRs

## 2026-03-07

- **PR #166:** Fix #153: Make dashboard sections collapsible to reduce clutter
  - **Learning:** JSONConfig UI changes (collapsible panels) require manual testing
  - **Pattern:** Use `"newLine": true, "sm": 12` for full-width sections
  - **Enhancement:** Redis section defaults to collapsed (rarely used)

## 2026-03-06

- **PR #165:** Fix #151: Initialize Redis states even when skipped
  - **Learning:** Features with conditional logic (Redis-only) must ALWAYS initialize states
  - **Anti-Pattern:** Early return BEFORE state initialization
  - **Pattern:** State init FIRST, then conditional logic/early return
  - **Example:** `await this.createRedisStates(); if (!isRedis) { await this.setStatus('skipped'); return; }`

## 2026-03-03

- **PR #149:** Fix #143: Improve log severity parsing regex
  - **Learning:** Regex-based log parsing is fragile (different adapters, different formats)
  - **Pattern:** Multiple fallback patterns for severity detection
  - **Anti-Pattern:** Single regex expecting consistent log format

- **PR #148:** Fix #144: Inspector counts show 0 despite aggregated data
  - **Learning:** Aggregated state updates require explicit count recalculation
  - **Pattern:** hasOrphans/hasStale boolean flags for quick checks
  - **Anti-Pattern:** Relying on array length without updating count states

- **PR #141:** Fix #131: Redis detection via iobroker.json
  - **Learning:** iobroker.json is most reliable source for backend config
  - **Priority:** Manual config > iobroker.json > system.host.* objects > null
  - **TDD Success:** Red-Green-Refactor cycle worked perfectly (8 tests first, then implementation)
  - **Pattern:** Client-side JSONL filtering (fetch entire file, then filter) more reliable than grep

## 2026-03-02

- **PR #139:** Fix #137: Initialize inspector.* and stateInspector.* states
  - **Learning:** Nested state structures (inspector.orphanedStates.*, inspector.duplicates.*) must all be initialized
  - **Anti-Pattern:** Only initializing top-level states
  - **Pattern:** Create all 30+ inspector states in createStates() with default values

- **PR #136:** Fix #132: Group states on Dashboard
  - **Learning:** JSONConfig panel organization improves UX dramatically
  - **Pattern:** Group related features in collapsible panels (Memory, Disk, Logs, Inspector)

## 2026-03-01

- **PR #135:** Fix #134: Initialize crashHistory state on adapter startup
  - **Learning:** JSON array states need type: 'json' AND initial value [] (empty array)
  - **Anti-Pattern:** Leaving JSON states undefined (breaks reads)

- **PR #133:** Fix #131: Redis detection not working
  - **Learning:** Redis backend config priority: iobroker.json > system.host.* > manual config
  - **Pattern:** Fallback chain for config detection

- **PR #129:** Fix #128: Hide Redis monitoring when Redis backend is not used
  - **Learning:** Conditional UI rendering based on backend type
  - **Pattern:** Check objectsType/statesType in adapter config

- **PR #124:** Fix #89: Initialize log monitoring states on adapter startup
  - **Learning:** All monitoring states must be initialized on startup (even if no data yet)
  - **Pattern:** createStates() method runs ONCE at adapter start
  - **Anti-Pattern:** Lazy initialization (waiting for first data)

## 2026-02-27

- **PR #77:** Fix #71: Add performance and resource usage analysis
