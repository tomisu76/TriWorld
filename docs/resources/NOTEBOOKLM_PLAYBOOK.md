# NotebookLM playbook for TriWorld

NotebookLM je voliteľná evidence workbench pre človeka a Hermesa. Nepatrí do kritickej build cesty. Generátor musí fungovať aj vtedy, keď NotebookLM nie je dostupný.

Kontrolný dátum možností: **2026-07-29**. Limity a funkcie sa menia; pred použitím ich over v oficiálnom Help Centre.

## 1. Povolené režimy

### `disabled`

Použi, ak nie je účet/prístup, zdroje nemožno legálne nahrať alebo research je dostatočne malý. Všetky evidence procesy musia fungovať lokálne bez NotebookLM.

### `manual`

Predvolený režim. Používateľ alebo autorizovaný operátor ručne:

- vytvorí notebook;
- importuje sanitizované zdroje;
- spustí research prompts;
- otvorí citations;
- exportuje skontrolovaný briefing.

Hermes pripraví source manifest a prompt pack, ale neobchádza login, consent ani súkromné consumer endpoints.

### `enterprise-preview`

Povoľ iba ak používateľ výslovne poskytol:

- Gemini Notebook Enterprise/Google Cloud projekt;
- vhodnú licenciu;
- IAM role a schválené credentials;
- data residency/security approval;
- súhlas použiť Preview/Pre-GA `v1alpha`.

Integrácia musí byť:

- za feature flagom;
- izolovaná adapterom;
- voliteľná;
- auditovaná;
- testovaná proti sandbox projektu;
- bez predpokladu API stability.

Oficiálne enterprise API momentálne dokumentuje notebook/source management a niektoré artefakty. Neimplementuj chat/Q&A, reporty alebo iné consumer Studio funkcie cez nezdokumentované endpointy.

## 2. Čo NotebookLM vie a čo z toho vyplýva

Oficiálne podporované desktop sources zahŕňajú web URL, PDF, Markdown/TXT, DOCX, PPTX, CSV, ePub, audio, obrázky, Google Docs/Slides/Sheets, public YouTube a pasted text. Web import typicky zachytí text stránky; YouTube pracuje s transcriptom. Formáty a limity over pred každým sprintom.

Orientačné Standard/Free limity overené 2026-07-29:

| Limit | Hodnota v čase kontroly |
|---|---:|
| notebooks na používateľa | 100 |
| sources na notebook | 50 |
| veľkosť jedného source | 500 000 slov |
| local upload | 200 MB |
| chat queries za deň | 50 |
| Audio Overviews za deň | 3 |

Google limity mení a platené/Workspace/Enterprise tiers sa líšia. Build ani plánovanie nesmie závisieť od presného počtu.

Praktické dôsledky:

- import je snapshot alebo riadená synchronizácia, nie záruka živého upstreamu;
- footnotes/comments alebo embedded content nemusia byť importované;
- paywall/nested pages nemusia byť dostupné;
- jeden notebook nedokáže automaticky odpovedať cez zdroje iného notebooku;
- odpoveď je grounded vo vybraných zdrojoch, ale inference môže byť stále chybná;
- citation je locator, nie automatický dôkaz správnej interpretácie;
- exportovaný Doc/Sheet/PDF/PPTX má vlastné permissions a nesynchronizuje rozhodnutia späť do repozitára.

## 3. Notebook topology

Vytvor päť menších notebookov:

### `TriWorld — BeamNG Runtime & World Editor`

Obsah:

- BeamNG level formats/classes;
- testing/packaging;
- target-version notes;
- vlastné sanitizované canary reports;
- World Editor/Road Architect docs;
- version conflicts.

### `TriWorld — SUMO, OSM & GIS`

Obsah:

- SUMO pinned docs/source notes;
- OSM tagging/licensing/service policies;
- PROJ/GDAL;
- MapFrame contract;
- DEM provider metadata.

### `TriWorld — Civil Geometry, Terrain & Drainage`

Obsah:

- RoadIR contract;
- ASAM/selected civil references;
- vertical alignment, crossfall, superelevation;
- cut/fill, junction surface, bridge/tunnel;
- numerical QA.

### `TriWorld — Blender, Assets & Materials`

Obsah:

- Blender exact-version manual/API;
- BeamNG DAE/material pipeline;
- collision/LOD conventions;
- asset license manifests;
- golden export reports.

### `TriWorld — Architecture, QA & Evidence`

Obsah:

- master prompt;
- ADR;
- risk register;
- test matrix;
- state machine;
- sanitized evidence ledger;
- phase-gate reports.

Rozdelenie znižuje šum. Keď otázka presahuje dve domény, vytvor dočasný cross-domain source pack s relevantnými dokumentmi; nepredpokladaj cross-notebook retrieval.

## 4. Source intake

Pred importom vyplň riadok v `docs/research/source-manifest.csv`:

```csv
source_id,title,canonical_url,local_file,owner,version_or_sha,retrieved,license,sensitivity,notebook,checksum,status
```

Povolené:

- vlastné Markdown evidence summaries;
- verejné oficiálne docs;
- redistribuovateľné standardy/datasety podľa terms;
- sanitizované vlastné test reports;
- odkazy na public source.

Zakázané bez samostatného právneho a bezpečnostného súhlasu:

- celé BeamNG proprietary source alebo stock Italy assets;
- game archives;
- API keys, cookies, session tokens;
- osobné alebo crash/telemetry dáta;
- používateľské home paths;
- private Git repositories;
- logy obsahujúce identifikátory;
- cudzie PDF bez práva na upload;
- license-gated dataset po prijatí terms za inú osobu.

Pred uploadom:

1. odstráň secrets a osobné údaje;
2. nahraď absolútne cesty tokenmi ako `<BEAMNG_ROOT>`;
3. over licenciu a sharing scope;
4. vypočítaj checksum lokálneho snapshotu;
5. zapíš verziu/retrieval date;
6. vyber iba potrebný notebook.

## 5. Manual research workflow

Ak je používateľom autorizovaný NotebookLM dostupný, tento krok je povinný pre kritický cross-source research sprint. Ak dostupný nie je, zapíš `NotebookLM mode: disabled` a dôvod; nezastavuj core build.

1. Vytvor notebook s presným release/sprint názvom.
2. Importuj source manifest ako prvý zdroj.
3. Pridaj oficiálne sources, ideálne immutable PDF/Markdown snapshot alebo versioned URL.
4. Zdrojom daj názvy s prefixom:

```text
[BNG-0386] DecalRoad class docs — retrieved 2026-07-29
[SUMO-1271] netconvert docs — bundled/pinned
[TW-CANARY] CAN-BNG-DECAL-WIDTH-001 report
```

5. Vypni zdroje, ktoré nie sú relevantné pre konkrétnu otázku.
6. Najprv žiadaj evidence table, nie súhrnný príbeh.
7. Otvor každú citáciu, ktorá ovplyvňuje code, security, licensing alebo release.
8. Rozpory prenes do evidence ledgeru.
9. Až potom vytvor briefing/report.
10. Export manuálne, sanitizuj a ulož do `docs/research/notebooklm/`.
11. V exporte zapíš notebook name, date, selected source IDs, exact prompt, reviewer a stav tvrdení.

## 6. Prompt pack

### Evidence matrix

```text
Using only the selected sources, build a table:
Claim ID | exact claim | supporting source(s) | citation | target version |
contradicting source(s) | confidence | direct fact vs inference | required test.
Do not resolve contradictions by majority. Say "not in sources" when absent.
```

### Version drift

```text
Compare every statement about <COMPONENT> across the selected sources.
Separate behavior for each product version/tag/date. List renamed, deprecated,
WIP, undocumented, or mutually inconsistent fields. For each mismatch propose
the smallest runtime canary that could falsify the newer assumption.
```

### API contract extraction

```text
Extract only documented input fields, units, coordinate conventions, defaults,
output artifacts, error modes, and save/reload behavior for <API/FORMAT>.
For every row provide a citation. Do not invent omitted defaults.
Mark any claim based on an example rather than normative text.
```

### Contradiction audit

```text
Act as a skeptical release reviewer. Find contradictions, missing target
versions, unsupported inferences, circular citations, and cases where a saved
authoring artifact is confused with a runtime artifact. Return blockers first.
```

### Test derivation

```text
From the selected normative sources, derive positive, boundary, negative,
round-trip, save/reload, clean-profile, and determinism tests.
Map every test to the exact cited requirement and state what observable failure
would prove the implementation wrong.
```

### License/provenance review

```text
For every data or asset source, extract licence/terms URL, attribution,
redistribution, commercial-use, share-alike, modification notice, service-policy
and account/key requirements. If a source does not explicitly answer a field,
write UNKNOWN; do not infer permission.
```

### Road quality gap

```text
Compare TriWorld's stated runtime/visual requirements with the selected official
BeamNG level creation, testing, materials, terrain and road sources.
Return a gap matrix grouped by topology, physics, visuals, AI, metadata,
performance, packaging and clean-profile validation. Never recommend copying
protected Italy assets.
```

## 7. Citation QA

Pre každé významné tvrdenie:

- klikni citáciu;
- prečítaj odsek pred/po;
- over, že source popisuje správnu verziu;
- odliš normatívny text od príkladu;
- over jednotky a polarity;
- skontroluj, či source netvrdí opak v inom odseku;
- pri licencii otvor originálne terms;
- pri Git source otvor tag/SHA;
- pri dynamickej stránke zapíš retrieval date;
- pri presnom field/defaulte porovnaj s canary.

Ak citation ukazuje iba krátky source ako celok, nájdi presný text manuálne.

## 8. Sharing and privacy

- Notebook nechaj private, kým nie je sanitizovaný.
- „Chat View“ nepovažuj za redakciu; viewer môže získať prístup k sources/artifacts.
- Verejne zdieľaj iba samostatný sanitizovaný derivative notebook.
- Exportované Google Docs/Sheets a stiahnuté súbory majú vlastné permissions.
- Shared notebook permissions nezabezpečujú export.
- Pri Workspace/Enterprise rešpektuj admin policy, region a retention.
- Do verejného notebooku nevkladaj lokálne source paths, logs alebo internal issue notes.

## 9. Enterprise API guardrail

Adapter interface smie vyzerať napríklad:

```text
NotebookEvidenceProvider
  create_notebook()
  add_source()
  list_sources()
  delete_source()
  get_manifest()
```

Core pipeline nesmie volať provider priamo. `NOTEBOOKLM_MODE=disabled` musí byť plne funkčný default. Preview endpoint, project ID, location a credentials sú runtime configuration mimo Git.

Nepredpokladaj dokumentovaný endpoint pre:

- consumer NotebookLM login;
- Q&A chat s citations;
- reports/notes;
- video/slide/infographic generation;
- export;
- všeobecné Studio artifacts.

Ak oficiálna dokumentácia tieto možnosti neskôr pridá, vytvor novú ADR a contract test; neobchádzaj to reverse engineeringom.

## 10. Export template

Každý kontrolovaný export začína:

```text
Notebook:
Mode: manual | enterprise-preview
Generated:
Reviewed:
Selected source IDs:
Source manifest checksum:
Prompt:
Purpose:
Verified claims:
Unverified claims:
Contradictions:
Canaries required:
Implementation decision:
```

Filename:

```text
YYYY-MM-DD_<domain>_<question-id>_<short-title>.md
```

NotebookLM text bez source manifestu, prompts, citations a review statusu sa nesmie používať ako implementačný evidence.
