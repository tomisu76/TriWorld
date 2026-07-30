# Hermes verification rules

Tento dokument dopĺňa `.hermes.md`, `HERMES_START_HERE.md` a master prompt.
Nemení cieľ TriWorldu, architektúru ani poradie implementačných fáz. Určuje,
aký dôkaz je potrebný pred tvrdením, že kontrola alebo fáza prešla.

## 1. Pravda má prednosť pred zeleným reportom

Neoptimalizuj implementáciu ani validator na výsledok `PASS`. Hľadaj dôvody,
pre ktoré môže chybný artefakt nesprávne prejsť. Ak dôkaz chýba, použi
`not yet proven`, nie odhad ani optimistické zhrnutie.

`87 tests passed` znamená iba to, že prešlo 87 konkrétnych testov. Nedokazuje
BeamNG kompatibilitu, vykreslenie, kolíziu, AI navigáciu ani jazditeľnosť.

## 2. Povinné stavy tvrdení

Každé významné tvrdenie označ presne jedným alebo viacerými stavmi:

- `implemented` — kód existuje;
- `unit tested` — prešli izolované testy;
- `statically validated` — nezávislá statická kontrola artefaktu prešla;
- `stock compared` — presná schéma, cesta alebo bajty boli porovnané so
  stock obsahom rovnakej nainštalovanej verzie;
- `integration tested` — komponenty spolu vytvorili očakávaný artefakt;
- `runtime verified` — cieľový program artefakt skutočne načítal a splnil
  definovaný runtime gate;
- `visually inspected` — vzhľad bol skontrolovaný človekom alebo obrazovým
  dôkazom;
- `not yet proven` — potrebný dôkaz ešte neexistuje.

Nižší stav nikdy automaticky neznamená vyšší stav.

## 3. Zakázané kruhové overovanie

Generátor a validator nesmú vychádzať iba z rovnakého neovereného predpokladu.
Príklady neplatného dôkazu:

- writer zapíše vlastný binárny layout a jeho test iba rovnakým layoutom
  prečíta tie isté bajty;
- generátor vytvorí vlastnú JSON schému a validator skontroluje iba túto
  vlastnú schému;
- validator prijme každú `/levels/...` cestu ako stock asset bez kontroly
  presnej položky v nainštalovanom stock balíku;
- kontrola geometrie porovná jednu súradnicu, hoci tvrdí zhodu celých tvarov;
- kontrola prehľadá iba jeden scene súbor, hoci tvrdí unikátnosť v celom ZIP-e.

Pri version-sensitive formáte vyžaduj aspoň jeden nezávislý oracle:

1. golden fixture uloženú cieľovým programom;
2. lokálny stock súbor presne rovnakej verzie;
3. oficiálnu dokumentáciu doplnenú realistickou fixture;
4. runtime load/save/reload dôkaz.

## 4. Adversarial test je súčasť validatora

Každý dôležitý validator check musí mať:

- pozitívnu fixture, ktorá prejde;
- minimálne jednu poškodenú fixture, ktorá musí zlyhať;
- test, že chyba ovplyvní celkový výsledok gate;
- správu uvádzajúcu presný súbor, objekt, pole alebo bajtový offset.

Pred označením validatora za hotový odpovedz:

1. Ako by chybný artefakt mohol týmto checkom prejsť?
2. Kontroluje sa celý deklarovaný rozsah alebo iba jeho časť?
3. Overuje sa referencia v skutočnom ZIP-e alebo source balíku?
4. Používa test nezávislý oracle?
5. Existuje negatívna fixture dokazujúca, že check vie zlyhať?

Ak je odpoveď na niektorú otázku nie, check nie je dokončený.

## 5. Pravidlá pre stock porovnanie

Tvrdenie `matches Italy`, `stock compatible` alebo podobné musí obsahovať:

- presnú BeamNG verziu a build;
- presný source ZIP a vnútornú cestu;
- príkaz alebo skript použitý na porovnanie;
- relevantnú schému, rozmery, bajtové offsety alebo objektové polia;
- vysvetlenie rozdielov, nie iba podobností.

Existencia podobného názvu nestačí. Asset cesta musí byť overená
case-sensitive proti presnému nainštalovanému balíku. Italy asset môže byť
lokálna runtime závislosť, ale nesmie byť bez licencie kopírovaný do
prenosného TriWorld ZIP-u.

## 6. BeamNG acceptance dimensions

Reportuj tieto výsledky samostatne:

1. ZIP structure;
2. metadata a level discovery;
3. terrain binary load;
4. terrain rendering;
5. spawn;
6. visual road;
7. physical collision;
8. AI graph a route;
9. materials a texture references;
10. save/reload persistence;
11. log errors;
12. deterministický hash.

Úspech jednej dimenzie nedokazuje ostatné. `Static gate passed` nepouži,
ak niektorý povinný statický check zostáva `not yet proven`.

## 7. Stav fázy

Používaj tieto formulácie:

- `IMPLEMENTATION IN PROGRESS`
- `STATIC WORK COMPLETE — RUNTIME GATE PENDING`
- `RUNTIME VERIFIED`
- `BLOCKED: <presný dôvod>`

`COMPLETE` alebo `READY FOR RELEASE` použi iba po všetkých gates definovaných
pre danú fázu. Ak fáza vyžaduje BeamNG load-and-drive test, bez neho nie je
runtime complete.

## 8. Povinný záverečný report

Každý phase/gate report musí uviesť:

```text
Exact HEAD:
Working tree state:
Files changed:
Commands actually executed:
Artifacts and SHA-256:
Checks passed:
Checks failed:
Negative fixtures exercised:
Stock/golden evidence:
Runtime evidence:
Proven facts:
Unproven assumptions:
Known limitations:
Recommended next action:
Commit/push performed: yes | no
```

Nevkladaj do reportu skrátený príkaz s `...` a potom ho neoznačuj za vykonaný
dôkaz. Uveď reprodukovateľný príkaz alebo odkaz na verzovaný skript.

## 9. Git a bezpečnosť

- Pred zmenami aj pred reportom vykonaj `git status`.
- Zachovaj nesúvisiace používateľské zmeny.
- Bez povolenia nepoužívaj reset, rebase, plošné mazanie, čistenie BeamNG
  cache/mods ani prepis existujúceho ZIP-u.
- `git add -A` nie je dôkaz, že ignorovaný evidence súbor bude commitnutý.
  Over ho cez `git check-ignore` a `git status`.
- Commit ani push nevyhlasuj, kým hash HEAD a remote stav tvrdenie nepotvrdia.

## 10. Stop pravidlo

Pred odoslaním slov `PASS`, `COMPLETE`, `matches stock`, `compatible`,
`ready for runtime` alebo `ready for release` vykonaj posledný self-review:

> Ktorý nezávislý dôkaz toto tvrdenie potvrdzuje a ktorý negatívny test by
> odhalil jeho najpravdepodobnejšiu chybu?

Ak nevieš uviesť oboje, zmeň tvrdenie na `not yet proven` a pokračuj
najmenším bezpečným experimentom, ktorý neistotu odstráni.
