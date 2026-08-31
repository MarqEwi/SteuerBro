# SteuerBro

Ein System, das für jeden Beleg ausrechnet, **in welchem Steuertopf er dir am
meisten Geld bringt** — und das die Entscheidung samt Begründung so ablegt,
dass sie in vier Jahren noch nachvollziehbar ist.

Gebaut für die Situation: Nebengewerbe + vermietete Immobilien + Studium +
Dienst bei der Bundeswehr. Also vier Töpfe, in die derselbe Laptop, dasselbe
Werkzeug, dasselbe Fachbuch passen könnte.

---

## Das Problem

Ein Laptop für 1.499 €, genutzt für Gewerbe, Studium und Dienst. Je nachdem,
wohin du ihn buchst, bleiben bei dir:

| Zuordnung | bleibt bei dir |
|---|---|
| Nebengewerbe (regelbesteuert) | **617 €** |
| Vermietung | 450 € |
| Bundeswehr, unter Pauschbetrag | **0 €** |
| Erststudium als Sonderausgabe, ohne Einkommen | **0 €** |

Derselbe Kaufpreis. Derselbe Laptop. **617 € Unterschied.**

Der Grund ist nicht Trickserei, sondern Struktur: Der Gewerbetopf zahlt
zweimal (Vorsteuer **und** Steuerersparnis), der Arbeitnehmertopf hat einen
toten Boden von 1.230 €, und Sonderausgaben verfallen, wenn kein Einkommen
da ist. Das weiß niemand auswendig, und deshalb rechnet es hier ein Programm
aus.

---

## Schnellstart

```bash
# 1. Profil ausfüllen (einmalig, 15 Minuten)
$EDITOR profil/profil.json          # alle TODO-Felder

# 2. Beleg bewerten, bevor du ihn ablegst
python3 tools/steuerbro.py bewerte \
  --brutto 1499 \
  --anteile "GEW=30-60,FOB=20-50,AN=10-30" \
  --kategorie Laptop

# 3. Beleg erfassen, benennen, ablegen
python3 tools/steuerbro.py neu \
  --datei belege/_eingang/rechnung.pdf \
  --datum 2026-03-14 --haendler "Notebooksbilliger" \
  --beschreibung "ThinkPad T14" --brutto 1499 \
  --kategorie Laptop --anteile "GEW=30-60,FOB=20-50,AN=10-30" \
  --begruendung "Überwiegend Auftragsbearbeitung Nebengewerbe, daneben Seminararbeiten" \
  --zahlungsart ueberweisung

# 4. Zwischenstand: Wo stehe ich, was ist noch frei?
python3 tools/steuerbro.py auswertung

# 5. Einmal vor der Abgabe: alles gemeinsam optimieren
python3 tools/steuerbro.py neuverteilen --jahr 2026
```

Kein `pip install`, keine Abhängigkeiten. Python 3.8 genügt.

---

## Wie die Optimierung funktioniert

Du gibst für jeden Beleg an, **in welcher Bandbreite** sich deine tatsächliche
Nutzung bewegt:

```
--anteile "GEW=30-60,FOB=20-50,AN=10-30"
```

Gelesen: *„Das Gerät geht zu 30–60 % ins Gewerbe, zu 20–50 % ins Studium, zu
10–30 % in den Dienst."*

Das Tool verteilt **innerhalb dieser Bandbreite** so, dass am meisten bei dir
hängen bleibt. Dabei berücksichtigt es Vorsteuerabzug, Pauschbeträge,
Höchstbeträge und Verlustvorträge — und zwar auf dem aktuellen Stand deines
Jahres, weil sich der Wert eines Topfes ändert, sobald Schwellen gerissen
sind.

Die Bandbreite kommt von dir und beschreibt deine echte Nutzung. Das Tool
erfindet sie nicht und geht nicht darüber hinaus. Es holt aus der Nutzung,
die du hast, das Maximum heraus.

**Beispielausgabe:**

```
WAS JEDER TOPF PRO EURO BRINGT:

  GEW     41.2 Cent/EUR   Nebengewerbe (Betriebsausgabe)
        Vorsteuer 16.0 % sofort zurück, zusätzlich 30.0 %
        Steuerersparnis auf den Nettobetrag.

  AN       0.0 Cent/EUR   Arbeitnehmer / Bundeswehr
        WIRKUNGSLOS: Der Arbeitnehmer-Pauschbetrag von 1230 EUR ist
        noch nicht ausgeschöpft. Diese Kosten bekommst du ohnehin
        pauschal - sie bringen keinen einzigen Euro zusätzlich.

EMPFOHLENE AUFTEILUNG:
  GEW    60.0 %     899.40 EUR   Vorteil  370.34 EUR  <- Obergrenze
  FOB    30.0 %     449.70 EUR   Vorteil    0.00 EUR
  AN     10.0 %     149.90 EUR   Vorteil    0.00 EUR

  ERGEBNIS: 370.34 EUR bleiben bei dir.
  DIFFERENZ ALLEIN DURCH DIE ZUORDNUNG: 185.17 EUR.
```

---

## Aufbau

```
CLAUDE.md                 Arbeitsanweisung. Wird bei jedem Session-Start
                          geladen und ist damit das Gedächtnis über
                          Gespräche hinweg.
profil/verhaeltnisse.json Chronik der Arbeits-, Ausbildungs- und
                          Einkunftsverhältnisse mit Zeiträumen.
config/parameter.json     Steuerliche Grenzwerte, mit Fundstelle und Stand.
                          Jährlich prüfen - deshalb nicht im Code.
profil/profil.json        Deine Situation: Grenzsteuersatz, Gewerbe,
                          Objekte, Art der Ausbildung.
register/belege.csv       Alle Belege mit Aufteilung und Begründung.
                          Ein Beleg = eine Zeile je Topf, gleiche ID.
belege/                   Die Dateien selbst. Nicht versioniert.
  _eingang/               Posteingang: hier alles reinwerfen, unsortiert.
tools/steuerbro.py        Das Werkzeug.
tools/nas-sync.sh         Läuft auf dem NAS: holt neue Belege ab und
                          schiebt Scans in den Eingang.
docs/                     Warum das alles so ist.
```

---

## Die Befehle

| Befehl | Wofür |
|---|---|
| `bewerte` | Nur rechnen. Was bringt welcher Topf? |
| `neu` | Beleg bewerten, benennen, ablegen, registrieren. |
| `auswertung` | Summen je Topf, Restbudgets, Schwellen. |
| `neuverteilen` | Alle Belege eines Jahres gemeinsam optimieren. |
| `pruefe` | Doppelzuordnungen, fehlende Belege, fehlende Begründungen. |

`python3 tools/steuerbro.py <befehl> --help` für die Details.

---

## Dokumentation

| Datei | Inhalt |
|---|---|
| [`docs/01-toepfe-und-hebel.md`](docs/01-toepfe-und-hebel.md) | Die Töpfe und warum sie unterschiedlich viel wert sind |
| [`docs/02-entscheidungsregeln.md`](docs/02-entscheidungsregeln.md) | Wohin gehört dieser Beleg? Mit den typischen Fällen |
| [`docs/03-ablage-und-namen.md`](docs/03-ablage-und-namen.md) | Namenskonvention, Ordner, Alltags-Workflow |
| [`docs/04-spielregeln.md`](docs/04-spielregeln.md) | Was geht, was nicht, und warum sich das rechnet |
| [`docs/05-fallstricke.md`](docs/05-fallstricke.md) | Die acht teuersten Fehler, nach Kosten sortiert |
| [`docs/06-so-arbeiten-wir.md`](docs/06-so-arbeiten-wir.md) | Der Chat-Workflow: Rechnung schicken, Rest passiert |
| [`docs/07-nas-einbindung.md`](docs/07-nas-einbindung.md) | NAS als Archiv und Scan-Eingang anbinden |

---

## Die drei Fragen, die du einmal klären solltest

Das Tool kann sie nicht für dich entscheiden, und an jeder hängt ein
vierstelliger Betrag:

1. **Ist dein Studium Erst- oder Zweitausbildung?**
   Entscheidet zwischen voll wirksamen Werbungskosten mit Verlustvortrag und
   faktisch wertlosen Sonderausgaben. Die teuerste offene Frage.
2. **Lohnt sich der Verzicht auf die Kleinunternehmerregelung?**
   Rund 16 Prozentpunkte auf jede Anschaffung — bindet aber fünf Jahre.
3. **Wie steht dein Gewerbe zur Liebhaberei-Frage?**
   Dauerverluste können die gesamte Optimierung rückwirkend kippen.

Ein Steuerberater-Termin, diese drei Fragen. Danach läuft das System für
Jahre allein.

---

## Wichtig

Dies ist ein Rechen- und Ordnungswerkzeug, **keine Steuerberatung**. Die
Werte in `config/parameter.json` sind nach bestem Wissen erfasst, mit
Fundstelle und Stand versehen, aber ohne Gewähr — prüfe sie jährlich.

Belege enthalten personenbezogene Daten. Sie sind per `.gitignore` von der
Versionierung ausgenommen. **Vergewissere dich, dass dieses Repository auf
privat steht.**
