# Phase gate report template

```text
Phase:
Gate:
Started:
Completed:
Owner:
Code commit:
Build ID:
Target versions:
Input manifest SHA-256:
Output manifest SHA-256:
```

## Objective

Jedna veta: čo má táto fáza dokázať.

## Inputs

| Input | Version/checksum | Provenance | Validated |
|---|---|---|---:|

## Outputs

| Artifact | Path | Schema/version | SHA-256 | Published |
|---|---|---|---|---:|

## Claims closed

| Claim ID | Previous state | Evidence/test | New state |
|---|---|---|---|

## Tests

| Test ID/command | Scope | Exit code | Result | Log/evidence |
|---|---|---:|---|---|

Uveď aj zlyhané testy. „All tests pass“ bez command/log/exit code nestačí.

## Required gate checks

- [ ] input contracts validated;
- [ ] output contracts validated;
- [ ] deterministic repeat compared;
- [ ] negative fixtures executed;
- [ ] warnings classified;
- [ ] licences/provenance complete;
- [ ] secrets/path sanitization complete;
- [ ] next phase assumptions explicit.

## Runtime and visual evidence

```text
Runtime required: yes | no
Runtime target:
Runtime result:
Visual inspection required:
Visual result:
Log SHA:
Screenshot/video paths:
```

## Truthful status

```text
Implemented:
Statically validated:
Integration tested:
Runtime verified:
Visually inspected:
Not yet proven:
```

## Failures and residual risk

| Risk/defect | Severity | Reproducer | Owner | Blocks next phase | Action |
|---|---|---|---|---:|---|

## Decision

```text
Gate: pass | fail | blocked
Reason:
Approved by:
Next falsifiable milestone:
```

