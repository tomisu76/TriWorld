# TriWorld research and execution pack

Tento adresár je povinný sprievodný balík k `HERMES_TRIWORLD_MASTER_PROMPT_2026.md`. Je navrhnutý pre Hermesa aj ľudského integrátora. Odkazy sú štartovacie body; živý web sa musí pri každom release znovu overiť.

## Čítaj v tomto poradí

1. [`RESEARCH_PLAYBOOK.md`](RESEARCH_PLAYBOOK.md) — ako z neistoty vytvoriť overené rozhodnutie.
2. [`RESEARCH_SNAPSHOT_2026-07-29.md`](RESEARCH_SNAPSHOT_2026-07-29.md) — čo bolo overené pri vytvorení balíka.
3. [`PRIMARY_SOURCES.md`](PRIMARY_SOURCES.md) — oficiálne docs, Git repozitáre a lokálne zdroje.
4. [`SEARCH_QUERIES.md`](SEARCH_QUERIES.md) — pripravené dotazy pre web a Git research.
5. [`SUBAGENT_PLAYBOOK.md`](SUBAGENT_PLAYBOOK.md) — bezpečná paralelná delegácia.
6. [`NOTEBOOKLM_PLAYBOOK.md`](NOTEBOOKLM_PLAYBOOK.md) — voliteľná evidence workbench.
7. [`TOOLS_AND_COMMANDS.md`](TOOLS_AND_COMMANDS.md) — nástroje, detekcia prostredia a príkazy.
8. [`BEAMNG_RUNTIME_CHECKLIST.md`](BEAMNG_RUNTIME_CHECKLIST.md) — load, drive, AI, collision a packaging gate.
9. [`SUMO_GIS_QA_CHECKLIST.md`](SUMO_GIS_QA_CHECKLIST.md) — CRS, DEM, topológia a SUMO gate.
10. [`EVIDENCE_LEDGER_TEMPLATE.md`](EVIDENCE_LEDGER_TEMPLATE.md) — šablóna tvrdení a dôkazov.
11. [`ENVIRONMENT_REPORT_TEMPLATE.md`](ENVIRONMENT_REPORT_TEMPLATE.md) — sanitizovaný audit nástrojov.
12. [`VERSION_LOCK_TEMPLATE.md`](VERSION_LOCK_TEMPLATE.md) — pinned build inputs a targety.
13. [`PHASE_GATE_REPORT_TEMPLATE.md`](PHASE_GATE_REPORT_TEMPLATE.md) — pravdivý report jednej fázy.
14. [`../hints/HERMES_EXECUTION_HINTS.md`](../hints/HERMES_EXECUTION_HINTS.md) — praktické skratky a známe pasce.

## Hierarchia pravdy

Pri rozpore vždy rozhoduj v tomto poradí:

1. pozorované správanie presnej cieľovej inštalácie a reprodukovateľný canary;
2. source alebo editorom uložený golden artefakt presnej cieľovej verzie;
3. aktuálna oficiálna dokumentácia;
4. oficiálny Git tag, release alebo standard;
5. oficiálne issue/discussion s potvrdením maintainerom;
6. sekundárny zdroj;
7. AI zhrnutie, search snippet alebo pamäť modelu.

Nižšia úroveň môže pomôcť objaviť problém, ale nesmie prehlasovať vyššiu bez nového dôkazu.

## Povinné výstupy researchu

Do repozitára patria iba sanitizované a redistribuovateľné výsledky:

```text
docs/research/
  environment-report.md
  evidence-ledger.md
  version-lock.md
  source-manifest.csv
  decisions/
  canaries/
  notebooklm/
```

Nevkladaj sem stiahnuté chránené hry, cache, cookies, API kľúče, osobné údaje ani celé cudzie datasety. Pre veľké verejné dáta ulož manifest s URL, licenciou, checksumom a transformačným receptom.

## Význam stavov dôkazu

- `implemented` — kód alebo artefakt existuje; nehovorí nič o správnosti.
- `statically validated` — schema, parser, linter alebo offline invariant prešiel.
- `integration tested` — dve alebo viac vrstiev prešli automatizovaným testom mimo cieľového runtime.
- `runtime verified` — cieľová verzia BeamNG/SUMO/Blender načítala a vykonala scenár s logom.
- `visually inspected` — človek alebo kontrolovaný vizuálny QA krok skontroloval obrazový výsledok.
- `not yet proven` — tvrdenie je hypotéza alebo chýba požadovaný gate.

Stavy sa nekumulujú automaticky. Napríklad `runtime verified` bez čistej vizuálnej kontroly nemusí byť `visually inspected`.
