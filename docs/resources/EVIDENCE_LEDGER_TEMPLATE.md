# Evidence ledger template

Skopíruj túto šablónu do `docs/research/evidence-ledger.md`. Ledger je verzovaný index tvrdení, nie úložisko cudzích dokumentov.

## Metadata

```text
Project: TriWorld
Research window:
Target release:
Target BeamNG:
Target SUMO:
Target Blender:
Target GDAL/PROJ:
Ledger owner:
Last reviewed:
```

## Claim ledger

| Claim ID | Domain | Exact claim | Decision/contract affected | Target version | Evidence IDs | Contradiction | Canary/test | Confidence | State | Owner |
|---|---|---|---|---|---|---|---|---|---|---|
| BNG-001 | BeamNG | Example only | Serializer | 0.38.6.0 | SRC-001, CAN-001 | open | CAN-001 | low | not yet proven | TBD |

Pravidlá:

- jeden riadok = jedno atomické tvrdenie;
- „BeamNG roads work“ nie je atomické tvrdenie;
- exact claim obsahuje jednotku a polarity, ak sú relevantné;
- confidence nie je state dôkazu;
- claim bez target version je neplatný pre verzovo nestabilné API;
- runtime claim bez canary/logu zostáva `not yet proven`.

## Source registry

| Evidence ID | Kind | Title/path | Canonical URL or repo-relative path | Owner/publisher | Version/tag/SHA | Locator | Retrieved | Licence | Checksum | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| SRC-001 | official-docs | Example | https://example.invalid | Vendor | 1.2.3 | Heading | YYYY-MM-DD | N/A | N/A | Replace |

`Kind`:

```text
installed-source
editor-golden
runtime-log
official-docs
official-standard
official-repo
official-release
maintainer-issue
secondary
notebooklm-brief
```

NotebookLM brief nikdy nie je jediný evidence ID pre implementačný contract; musí odkazovať na skontrolované primary source IDs.

## Contradiction register

| Conflict ID | Claim | Source A | Source B | Why they differ | Risk | Resolving canary/decision | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| CON-001 | DecalRoad fourth scalar semantics | current docs | legacy contract | version/terminology unknown | critical | measured editor golden + reload | TBD | open |

Status:

```text
open
experiment scheduled
resolved for target version
accepted risk
blocked
```

## Canary register

| Canary ID | Hypothesis falsified | Target | Input SHA-256 | Procedure | Expected | Observed | Log/artifact SHA | Result | Evidence state |
|---|---|---|---|---|---|---|---|---|---|
| CAN-001 | Example | version | sha | link | result | pending | pending | blocked | not yet proven |

## License/provenance register

| Asset/data ID | Source | Licence/terms | Allowed use | Redistribution | Attribution | Share-alike | Account/key | Checksum | Release decision |
|---|---|---|---|---|---|---|---|---|---|

Nejasná redistribúcia = asset sa nebalí.

## Decision bridge

Každé ADR musí uviesť claims, ktoré ho podporujú:

```text
ADR:
Accepted claims:
Rejected claims:
Target versions:
Canaries:
Residual risk:
Revisit trigger:
```

## Research query log

| Timestamp | Research question | Query | Results opened | Rejected and why | Accepted evidence IDs |
|---|---|---|---|---|---|

## Subagent packet log

| Task ID | Role | Scope | Packet received | Primary URLs parent-opened | Conflicts added | Integrated by | Status |
|---|---|---|---|---|---|---|---|

## NotebookLM log

| Brief ID | Notebook | Mode | Source manifest SHA | Exact prompt stored | Citations reviewed | Claims imported | Reviewer | File |
|---|---|---|---|---|---|---|---|---|

## Release evidence summary

Pred release vyplň:

```text
Critical claims total:
Critical claims runtime verified:
Critical claims not yet proven:
Open critical conflicts:
Licences unresolved:
Canaries failed:
Clean-profile BeamNG run:
ZIP SHA-256:
Evidence bundle path:
Release allowed: yes | no
Reviewer:
```

