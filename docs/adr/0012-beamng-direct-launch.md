# ADR 0012: BeamNG Direct Launch Mechanism

**Status:** Accepted
**Date:** 2026-07-29

## Context
TriWorld needs to launch BeamNG and load a specific level for runtime QA and optional "Open in BeamNG" user action. The launch mechanism must be version-pinned and verified.

## Decision
**Launch Script:** `scripts/open-in-beamng.ps1`

**Steps:**
1. Locate exact BeamNG executable (Steam default: `C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\BeamNG.drive.exe`)
2. Locate user folder (from `BeamNG.drive.ini` or default)
3. Verify installed ZIP hash matches built ZIP
4. Detect BeamNG version
5. Use ONLY version-verified launch mechanism
6. Capture PID and new log file
7. Wait for level-load marker with timeout
8. On error: open log report

**Verified Mechanisms (per version):**
- `beamng.drive.exe -level <slug>` (if documented and canary-tested)
- Steam protocol: `steam://rungameid/284160//-level <slug>` (if supported)
- Lua bootstrap script in mod folder (scoped, pinned, removable)
- Fallback: Normal launcher → User loads level → F11 opens World Editor

**Canary Test Required Before Use:**
1. Find official documentation or local command parser
2. Create minimal canary level
3. Test launch mechanism
4. Compare normal launcher vs direct launch
5. Pin working mechanism for that version

**Lua Bootstrap (if created):**
- Scoped to single level
- No global modifications
- Pinned to BeamNG version
- Removable after QA

## Alternatives
- Always use normal launcher → Rejected: Not automatable for CI/runtime QA

## Consequences
- Launch mechanism version-pinned in adapter
- Canary test in `fixtures/runtime-canary/`
- Fallback documented for users

## Evidence
- Master prompt §18.4: "Nehardcoduj neoverený `-level` argument... Najprv: nájdi oficiálnu dokumentáciu... vytvor canary"

## Revisit Trigger
- BeamNG version upgrade
- New launch mechanism discovered
- Direct launch fails in canary