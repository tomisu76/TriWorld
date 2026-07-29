# BeamNG runtime and packaging gate

Statický validátor nevie dokázať jazditeľnosť. Release candidate musí prejsť presnou cieľovou verziou BeamNG v čistom alebo kontrolovanom user profile.

## A. Preflight

- [ ] Target BeamNG exact build je zapísaný.
- [ ] ZIP SHA-256 je zapísaný.
- [ ] Testuje sa ZIP, nie iba working directory.
- [ ] Staršia kópia mapy je odstránená z aktívnych mod locations bezpečným, explicitným spôsobom.
- [ ] Cache behavior je zdokumentovaný; test nezávisí od starého cache.
- [ ] User profile a log start time sú zaznamenané a sanitizované.
- [ ] Žiadny stock Italy asset nebol kopírovaný do balíka.
- [ ] Ak mapa deklaruje external stock dependencies, každá je explicitná, povolená a testovaná.
- [ ] Runtime launch adapter zodpovedá verzii alebo sa použije manuálny fallback.

## B. ZIP static gate

- [ ] Root entry je `levels/<slug>/...`, bez extra wrapper directory.
- [ ] `info.json` je na správnom mieste a parsuje sa.
- [ ] Moderný scene tree je v správnom `main/` layout pre target version.
- [ ] `items.level.json` rešpektuje target formát; pri line objects je každý riadok úplný JSON objekt.
- [ ] Referenced `.ter`, materials, DAE, textures, thumbnails a gameplay files existujú.
- [ ] VFS paths sú portable, relatívne a case-consistent.
- [ ] Žiadne `C:\...`, používateľské meno, temp/cache/source/autosave.
- [ ] Žiadne traversal, duplicate entries, case collisions alebo neobmedzený decompression ratio.
- [ ] Attribution/licence sú v metadata/credits.
- [ ] ZIP ordering/timestamps sú deterministic podľa policy.

## C. Load gate

- [ ] Level sa objaví v selector/loader.
- [ ] `info.json` metadata, preview a názov sú správne.
- [ ] Level sa načíta bez crashu a timeoutu.
- [ ] Default spawn existuje a názov presne sedí.
- [ ] Vehicle spawnne nad fyzickým road surface, nie pod/vo vzduchu.
- [ ] Vehicle heading je v správnom smere pruhu.
- [ ] Log nemá missing file/material/mesh/terrain errors.
- [ ] Log nemá JSON parse alebo unsupported terrain version errors.
- [ ] Level po fresh start nereferencuje working-directory paths.

Evidence:

```text
Load start/end timestamps:
PID/build:
Log file + SHA:
Level-loaded marker:
Screenshot:
Result:
```

## D. Road physics gate

Vyber automaticky aj manuálne:

- reprezentatívnu rovnú cestu;
- horizontálny oblúk;
- crest a sag;
- veľkú križovatku;
- rampu;
- bridge/tunnel, ak existuje;
- terrain transition;
- okraj mapy.

Kontroly:

- [ ] continuous collision po celej trase;
- [ ] žiadne prepadnutie, invisible wall alebo step na chunk seam;
- [ ] render/collision sa geometricky nerozchádzajú;
- [ ] šírka zodpovedá RoadIR a meraniu;
- [ ] grade a crossfall majú správnu orientáciu;
- [ ] wheel contact nenaráža do nesprávne deformovaného terrainu;
- [ ] bridge surface nekolabuje na terrain pod ním;
- [ ] tunnel neobsahuje falošný terrain wall;
- [ ] curb/barrier/shoulder collision je zámerná;
- [ ] off-road escape a map boundary sú bezpečné.

Automatický drive scenár má limit rýchlosti/čas, zaznamenané stations a toleranciu. Manuálny drive QA dopĺňa, nenahrádza numeriku.

## E. Visual/material gate

- [ ] Road material nie je oranžový/missing.
- [ ] `mapTo`/material name zodpovedá mesh slotom.
- [ ] Normals/tangents nie sú invertované.
- [ ] Decal projection je viditeľná na podporovanom povrchu.
- [ ] Markings nemajú z-fighting alebo extrémne sink/float.
- [ ] Terrain nemá nodata spikes, švy alebo prevrátenú os.
- [ ] Textúry majú rozumný texel density.
- [ ] LOD transition/pop a shadow sú akceptovateľné.
- [ ] Scenery neblokuje jazdnú dráhu.
- [ ] Spawn/readable route funguje deň/noc podľa scope.

## F. AI/navigation gate

- [ ] Iba autoritatívna AI road/lane vrstva má kladnú drivability.
- [ ] Edge/marking/wear decals nemajú kladnú drivability.
- [ ] One-way route je prejazdná iba zámerným smerom.
- [ ] Node order a target fields sú overené canary.
- [ ] AI nevyberá paralelnú vizuálnu vrstvu.
- [ ] Junction lane connections zodpovedajú legal movements.
- [ ] Bridge/tunnel crossing bez junction nevytvára false turn.
- [ ] U-turn/roundabout/ramp behavior zodpovedá RoadIR.
- [ ] Random origin/destination route suite má definovanú úspešnosť.
- [ ] Traffic sa nespawnuje do protismeru alebo mimo surface.

`map.json` je iba connectivity/nav artefakt. Jeho prítomnosť nedokazuje viditeľnú alebo kolíznu cestu.

## G. Road Architect persistence gate

Ak sa použil Road Architect:

- [ ] session načítaná v správnej mape/terraine;
- [ ] profiles a junctions skontrolované;
- [ ] Render/finalize dokončený;
- [ ] collision/navgraph generated podľa target workflow;
- [ ] level saved;
- [ ] editor zatvorený alebo level úplne unloaded;
- [ ] level reloaded v novom runtime cykle;
- [ ] generated roads stále existujú;
- [ ] collision a AI po reload fungujú;
- [ ] packaged ZIP obsahuje persisted runtime artifacts, nie iba session;
- [ ] handshake report skončil `persistence_verified`/`complete`.

Session file alebo UI screenshot pred save/reload nie je dôkaz.

## H. Performance gate

Definuj hardware/profile a thresholds:

- [ ] load time;
- [ ] peak working set/VRAM proxy, ak dostupné;
- [ ] FPS/frame-time na scénach;
- [ ] object/material/draw-call budgets;
- [ ] collision complexity;
- [ ] AI/traffic scale;
- [ ] texture memory;
- [ ] stutter pri chunk/LOD transition.

Pri výkonnostnom zlyhaní zníž komplexitu systematicky cez LOD, batching, instancing, chunking a material atlas policy; neodstráň fyzickú alebo QA vrstvu bez ADR.

## I. Clean-profile and portability gate

- [ ] Presuň/odstráň working copy.
- [ ] Otestuj iba ZIP.
- [ ] Použi nový/čistý test profile.
- [ ] Reštartuj BeamNG.
- [ ] Loadni, spawnni, jazdi, AI route, reloadni.
- [ ] Skontroluj log od nového timestampu.
- [ ] Otestuj na druhej ceste/user path bez hardcoded root, ak je dostupné.
- [ ] Znovu vypočítaj ZIP hash.

## J. Release evidence

Release QA report:

```text
Target BeamNG:
ZIP:
ZIP SHA-256:
Static validator:
Load:
Spawn:
Collision route:
AI route:
Road Architect reload:
Visual inspection:
Clean profile:
Performance:
Log SHA-256:
Known warnings:
Not yet proven:
Release decision:
Reviewer:
```

Ak je kritický bod unchecked, build nie je „verified drivable ZIP“.

