# Environment report template

Skopíruj do `docs/research/environment-report.md`. Hodnoty zisťuj príkazom, nevypĺňaj z master promptu.

## Run metadata

```text
Generated:
Host OS/build:
Architecture:
Timezone used for logs:
Repository root: <REPO_ROOT>
Git branch:
Git commit or "no commit":
Dirty/untracked files preserved:
Operator/agent:
```

## Toolchain

| Tool | Detected version | Executable placeholder/path | Source of version | Required by lock | Status |
|---|---|---|---|---|---|
| Git | | | command output | | |
| rg | | | command output | | |
| Python | | | command output | | |
| Node | | | command output | | |
| package manager | | | command output/lockfile | | |
| GDAL | | | command output | | |
| PROJ | | | command output | | |
| SUMO/netconvert | | | command output | | |
| Blender | | | command output | | |
| BeamNG.drive | | | build/log | | |
| Hermes | | | command/package | | |

Nikdy nevkladaj secret-bearing command output. Lokálne paths sanitizuj.

## BeamNG

```text
Detected: yes | no
Exact build:
Install root: <BEAMNG_INSTALL>
User path: <BEAMNG_USERPATH>
Log location: <BEAMNG_LOG_DIR>
Target adapter exists:
Starter/editor golden captured:
Direct-launch capability: verified | unavailable | not yet proven
Road Architect capability: verified | unavailable | not yet proven
Clean-profile capability:
```

## SUMO/GIS

```text
SUMO_HOME: <SUMO_HOME>
Bundled docs present:
netcheck.py path/hash:
PROJ data dir:
Grid availability:
GDAL drivers required/present:
Axis-order canary:
Raster warp canary:
```

## Blender

```text
Root: <BLENDER_ROOT>
Exact version:
Background mode:
Python API:
Collada import/export operators:
DAE fallback:
Golden export canary:
```

## Hermes research

```text
Web search backend:
Web extract backend:
Browser exact-source verification:
Delegation max children:
Delegation depth:
Subagent provider/model:
Checkpoints:
Memory write approval:
Secrets storage:
```

Nezapisuj key values.

## NotebookLM

```text
Mode: disabled | manual | enterprise-preview
Authorized by:
Notebook owner:
Workspace/region policy:
Enterprise project/location placeholders:
Source upload restrictions:
Reason disabled, if any:
```

## Capability matrix

| Capability | Available | Version-proof | Canary | State | Blocker |
|---|---:|---|---|---|---|
| offline synthetic ZIP | | | | | |
| BeamNG load | | | | | |
| BeamNG direct open | | | | | |
| Road Architect session load | | | | | |
| Road Architect bake/save/reload | | | | | |
| OSM acquisition | | | | | |
| DEM acquisition | | | | | |
| SUMO compile | | | | | |
| Blender headless | | | | | |
| NotebookLM evidence synthesis | | | | | |

## Sanitization review

- [ ] no API key/token/cookie;
- [ ] no personal username;
- [ ] no proprietary source;
- [ ] no private repository URL;
- [ ] paths replaced by placeholders;
- [ ] only relevant diagnostics included.

