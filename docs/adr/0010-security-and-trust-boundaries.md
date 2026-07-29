# ADR 0010: Security and Trust Boundaries

**Status:** Accepted
**Date:** 2026-07-29

## Context
TriWorld runs locally but fetches external data, spawns subprocesses, and writes to the filesystem. We must define trust boundaries.

## Decision
**Network:**
- Default: localhost-only API binding (127.0.0.1)
- Outbound allowlist: Overpass mirrors, Terrarium S3, OpenTopography API, Nominatim
- No arbitrary URLs from client
- Download size limits per provider
- Rate limits per provider (Overpass: 1 req/s, Nominatim: 1 req/s)

**Subprocess:**
- Allowlist: `netconvert`, `duarouter`, `sumo`, `gdalwarp`, `blender` (headless), `python`
- No `shell=True` with user input
- Arguments as array, not string
- Timeout per subprocess
- Process tree termination on cancel/timeout

**Filesystem:**
- Job workspace containment: all paths resolve under `artifacts/jobs/<job-id>/`
- ZIP slip protection: validate entry paths on extract
- No absolute paths from client
- Atomic writes (temp + rename)

**Data:**
- XML: disable external entities (XXE)
- JSON: size limits, depth limits
- Secrets: only in `.env`, never logged, never in browser bundle

**Blender/Hermes MCP:**
- Treat as terminal-equivalent trust
- Read-only audit before install
- Pin version
- Disable external asset services/telemetry
- Bind socket localhost only
- WSL2 ↔ Windows networking verified
- User consent for config changes
- Dedicated workspace only

**BeamNG Install:**
- Resolve exact mods target
- Verify target stays in BeamNG user root
- Detect duplicate level roots
- Timestamped backup before write
- Atomic copy
- Verify source/installed SHA256
- Restore backup on error
- Never delete entire mods/user folder
- Never kill running BeamNG without consent

## Alternatives
- Full sandbox/container → Rejected: Overkill for local tool, breaks GPU/BeamNG

## Consequences
- Clear allowlists maintained in config
- Security audit checklist per release

## Evidence
- Master prompt §28: "Bezpečnosť a supply chain"

## Revisit Trigger
- New provider added
- New subprocess needed
- Security incident