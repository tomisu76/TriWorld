# Verified research snapshot — 2026-07-29

Tento súbor zachytáva stav overený pri tvorbe master promptu. Je to discovery snapshot, **nie release version lock**. Hermes musí živé zdroje a presnú lokálnu inštaláciu znovu skontrolovať.

## BeamNG

- Verejný current release bol overený ako BeamNG.drive **0.38.6**; budúca 0.39 bola ohlásená na neskôr v roku 2026. Target musí byť exact build, nie iba major/minor.
- Aktuálne format/class docs používajú moderný `levels/<slug>/main/` scene tree a `levels/<slug>/info.json`; staršie docs môžu ešte spomínať legacy `level.json`. Najlepší bootstrap je target editorom uložený minimal/starter level.
- `items.level.json` je podľa current docs line-object formát, nie JSON array.
- `DecalRoad` je projected visual road bez fyzickej collision. Fyzická road a AI navigation ostávajú samostatné layers.
- Current public DecalRoad docs pomenúvajú štvrtý node scalar `width`; historický TriWorld/internal contract ho používa ako `halfWidth`. Target serializer preto vyžaduje measured editor save/reload canary.
- MeshRoad node docs uvádzajú position, width, depth a normal; twisting/collision/material sa musí overiť runtime.
- `.terrain.json` nenahrádza binary `.ter`; direct writer je version-sensitive.
- `info.json` spawn name musí presne súhlasiť so `SpawnSphere`.
- ZIP root musí byť `levels/<slug>/...`; working-copy úspech nestačí, testuje sa ZIP na clean profile.
- Road Architect je WIP. Session JSON je authoring input; runtime dôkaz vyžaduje Render/finalize → save → full reload → collision/AI/persistence test.
- Shared stock `assets/` a `.link` paths sa vyvíjajú. Nespájaj prenosný release s neoverenou stock cestou.

Primárne URL sú v `PRIMARY_SOURCES.md`.

## SUMO, GIS and OSM

- SUMO online docs môžu sledovať development; pinned release má používať vlastné bundled docs/source.
- OSM `netconvert` guesses pre lanes, ramps, junction join, TLS a connections sú heuristiky a vyžadujú audit.
- Custom `--type-files` môžu nahradiť defaults; vypíš všetky required typemaps.
- `netcheck.py` default weak connectivity neoveruje directed/vclass routability. Spúšťaj passenger/source/destination checks a OD routing.
- Internal edges modelujú junction movement. Neodstraňuj ich bez ADR, ak chceš intersection/crash fidelity.
- SUMO raw `x,y` sú projected coordinates posunuté cez `<location netOffset>`; nepovažuj ich za absolute UTM.
- EPSG:4326 axis metadata a bežný `(lon, lat)` application contract sa môžu rozchádzať; TriWorld používa explicitnú convention a `always_xy=True` s round-trip testami.
- Horizontal reprojection sám nerieši vertical datum.
- DEM môže byť DSM s budovami/vegetáciou. Road profile musí byť civilne navrhnutý a terrain sa mu conformuje.
- Public OSM tiles nie sú offline/bulk map source; public Nominatim má striktnú fair-use policy. Použi cache a provider/self-host abstraction.

## Hermes Agent

Oficiálne docs overili:

- natívne `web_search` a `web_extract`;
- viac search/extract backendov a možnosť konfigurovať ich oddelene;
- dlhý `web_extract` môže prejsť modelovou kompresiou, preto exact schema/table/version detail treba overiť raw source/browser snapshotom;
- natívny `delegate_task`;
- default max 3 children;
- child potrebuje sebestačný task context;
- flat delegation je bezpečný default;
- paralelní agents môžu zdieľať workspace/container;
- delegácia nie je durable background queue.

Git snapshot získaný cez `git ls-remote`:

```text
NousResearch/hermes-agent HEAD:
3334db67a47b3e74d49c2d96d2206d9bea42f65d

NousResearch/hermes-agent tag v2026.7.20:
c7d08de287556b3d339df336b180a39d4980ebd7
```

Tieto SHA sa nesmú automaticky stať release lockom; najprv vyber kompatibilný tag a over source.

## NotebookLM

- NotebookLM chat je grounded vo vybraných notebook sources a poskytuje citations; každú kritickú citáciu treba otvoriť v kontexte.
- Notebooky sú oddelené; nepredpokladaj cross-notebook retrieval.
- Current Standard/Free limity overené v deň snapshotu: 100 notebooks, 50 sources/notebook, 500 000 words/source, local upload 200 MB, 50 chats/day, 3 audio generations/day. Limity sa menia.
- Podporované sources zahŕňajú web, PDF, Markdown/TXT, Office files, CSV, ePub, audio, images, public YouTube a Google Drive typy; import nemusí zachovať footnotes/comments/embedded content.
- Exportovaný artifact má vlastné permissions a nemusí sa synchronizovať späť.
- „Chat View“ nie je bezpečnostná redakcia sources/artifacts.
- Nezistilo sa stabilné oficiálne consumer NotebookLM API.
- Oficiálne Gemini Notebook Enterprise API existuje ako Preview/Pre-GA `v1alpha`, vyžaduje Google Cloud project, licenciu a IAM. Je voliteľné, feature-flagged a nie je core build dependency.
- Current enterprise API surface sa nesmie zamieňať s consumer chat/Studio API; nezdokumentované endpoints sa nepoužívajú.

## Git reference snapshot

`git ls-remote ... HEAD` 2026-07-29:

```text
eclipse-sumo/sumo:
2b1281c4c241d4619a0cfa9fc46cef9e5c33dffc

ahujasid/blender-mcp:
e3ece087adecce4242d4dc3e4db28c33010b51c4

tordanik/OSM2World:
0509ac37d6fa20088bb567c90cf251310602adae
```

Moving HEAD je discovery evidence. Produkcia vyberie tag/commit podľa licence, compatibility a canary.

## Najdôležitejšie otvorené dôkazy

```text
CON-001 DecalRoad full-width vs half-width target semantics
CON-002 exact BeamNG direct-level launch mechanism
CON-003 exact Road Architect automation symbols and persistence
CON-004 direct .ter writer compatibility with target build
CON-005 stock/shared asset path stability and legal portability
CON-006 vertical datum policy per DEM source
```

Kým sa conflict nevyrieši exact-version source/golden/runtime canary, stav je `not yet proven`.
