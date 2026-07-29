# Version lock template

Skopíruj do `docs/research/version-lock.md`. Lock je ľudsky čitateľný companion k machine lockfiles a source manifestu.

## Release target

```text
TriWorld release:
Git commit:
Build profile:
Target OS/architecture:
Target BeamNG exact build:
Created:
Reviewed:
```

## Runtime/tool locks

| Component | Required version | Detected version | Distribution/source | Resolved SHA/checksum | Licence | Upgrade policy |
|---|---|---|---|---|---|---|
| Python | | | | | | |
| Node | | | | | | |
| GDAL | | | | | | |
| PROJ | | | | | | |
| SUMO | | | | | | |
| Blender | | | | | | |
| BeamNG | | | local licensed install | N/A/private | proprietary | explicit adapter |
| Hermes | | | official repo/release | | | research only |

## Code dependencies

Machine lockfile je authority pre exact transitive versions. Tu zapíš kritické native/GIS/security dependencies, ich source a dôvod.

| Package | Ecosystem | Exact version | Lockfile | Native data/runtime | Licence | Reason |
|---|---|---|---|---|---|---|

## External code references

| Repository | Tag | Resolved commit SHA | Retrieved | Licence | Use |
|---|---|---|---|---|---|

`main`, `master` alebo branch bez SHA nie je lock.

## Data inputs

| Dataset | Product/version/date | AOI | Provider | Original owner | Checksum | CRS | Vertical datum | Licence/attribution |
|---|---|---|---|---|---|---|---|---|

## Target-format adapters

```text
BeamNG adapter:
Supported exact builds:
Source/golden evidence IDs:
Terrain format version:
DecalRoad width conversion:
Road Architect capability flags:
SUMO adapter:
Blender/DAE adapter:
```

## Seeds and deterministic policy

```text
Global generation seed:
Per-stage seed derivation:
Locale:
Timezone:
Float/rounding policy:
JSON canonicalization:
ZIP ordering:
ZIP timestamp:
Compression implementation/version:
```

## Upgrade trigger

Novú verziu prijmi iba po:

- migration research;
- updated evidence;
- golden diff review;
- negative tests;
- BeamNG load/drive/reload;
- deterministic rebuild;
- license/security review;
- ADR/update notes.

