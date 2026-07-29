# ADR 0011: Blender QA vs Hermes MCP

**Status:** Accepted
**Date:** 2026-07-29

## Context
Blender serves two distinct roles in TriWorld: deterministic headless QA and optional interactive MCP-guided exploration.

## Decision
**Two Separate Blender Integrations:**

### 1. Deterministic Blender QA (Production, `packages/blender_qa/`)
- **Purpose:** Numerical validation of meshes, terrain, collision
- **Execution:** Headless, factory startup, scripted
- **Scripts:** `audit_scene.py`, `render_diagnostics.py`, `capability_probe.py`
- **Output:** JSON report with metrics (degenerate tris, flipped normals, NaN, non-manifold, penetration, seams, LOD bounds, collision deviation)
- **Renders:** Orthographic top/side/perspective for visual audit (supplement, not gate)
- **Pass/Fail:** Determined by numeric thresholds, not screenshots
- **Required for:** High/Studio quality profiles
- **Optional for:** Portable MVP (if internal mesh validator covers same checks)

**Invocation:**
```bash
blender.exe --background --factory-startup \
  --python packages/blender_qa/audit_scene.py -- \
  --input artifacts/<build>/qa/world.glb \
  --terrain artifacts/<build>/qa/terrain.glb \
  --report artifacts/<build>/reports/blender-audit.json \
  --renders artifacts/<build>/reports/blender-renders
```

### 2. Hermes Blender MCP (Optional Lab, `optional-skills/creative/blender-mcp/`)
- **Purpose:** Interactive exploration, asset authoring, material preview, scene inspection
- **Capabilities:** `get_scene_info`, `get_object_info`, `get_viewport_screenshot`, `execute_blender_code`
- **Trust Level:** Terminal-equivalent (unsandboxed Python exec)
- **Usage:** Manual investigation, asset creation, debugging
- **NOT for:** Build pipeline, release gate, automated geometry generation
- **Installation:** User consent, read-only audit first, pin version, disable telemetry, localhost bind only

**Boundary:**
- Blender QA = CI/CD compatible, deterministic, numeric
- Hermes MCP = Human-in-the-loop, creative, exploratory
- Never confuse the two

## Alternatives
- Use MCP for QA → Rejected: Non-deterministic, requires UI, security risk
- Skip Blender QA → Rejected: Mesh pathologies only caught in Blender/BeamNG

## Consequences
- Two Blender entry points maintained
- Blender QA can run on headless CI runner
- MCP remains optional developer tool

## Evidence
- Master prompt §17: "Blender rozdeľ na dve úplne odlišné funkcie"

## Revisit Trigger
- Blender QA metrics insufficient
- MCP gains sandboxing
- Blender version breaks Collada