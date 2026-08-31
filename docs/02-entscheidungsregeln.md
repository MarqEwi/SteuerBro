# Entscheidungsregeln: Wohin gehört dieser Beleg?

Ein Beleg landet in vier Schritten im richtigen Topf. Die Reihenfolge ist
wichtig — Schritt 1 kommt immer zuerst.

---

## Schritt 1: Wofür nutzt du es wirklich?

Nicht: „Wo wäre es am günstigsten?"
Sondern: **„Was mache ich damit tatsächlich?"**

Schreibe die tatsächliche Nutzung als Bandbreite auf, ehrlich und aus dem
Bauch heraus. Eine Bandbreite, weil niemand seine Laptop-Nutzung auf das
Prozent genau kennt — eine Schätzung mit Spielraum ist der Normalfall und
auch das, was das Finanzamt erwartet.

```
Laptop:  Gewerbe 30–60 %, Studium 20–50 %, Dienst 10–30 %
```

Diese Bandbreite ist die Grenze der Optimierung. Alles Weitere findet
**innerhalb** statt.

**Wenn ein Topf gar nicht vorkommt, kommt er nicht in die Liste.** Ein
Fernseher fürs Wohnzimmer hat keine Gewerbe-Bandbreite, auch keine von
0–10 %. Er ist `PRIV`.

## Schritt 2: Bandbreite ins Tool geben

```bash
python3 tools/steuerbro.py bewerte \
  --brutto 1499 \
  --anteile "GEW=30-60,FOB=20-50,AN=10-30" \
  --kategorie Laptop
```

Das Tool zeigt dir, was jeder Topf **pro Euro** bringt, empfiehlt die
Aufteilung und rechnet vor, was die schlechteste Variante gekostet hätte.

## Schritt 3: Begründung festhalten

Das ist der Schritt, den alle auslassen und der später alles entscheidet.

Nicht der Dateiname rettet dich bei einer Rückfrage, sondern der Satz, warum
der Nutzungsanteil so gewählt wurde. In zwei Jahren weißt du das nicht mehr.

Gut:
> „Laptop wird überwiegend für die Auftragsbearbeitung im Nebengewerbe
> genutzt (Kundenkommunikation, Angebote, Buchhaltung), daneben für
> Seminararbeiten im Studium und gelegentlich für dienstliche Fortbildung."

Nutzlos:
> „Laptop."

## Schritt 4: Erfassen und ablegen

```bash
python3 tools/steuerbro.py neu \
  --datei belege/_eingang/scan.pdf \
  --datum 2026-03-14 --haendler "Notebooksbilliger" \
  --beschreibung "ThinkPad T14 Gen5" --brutto 1499 \
  --kategorie Laptop --anteile "GEW=30-60,FOB=20-50,AN=10-30" \
  --begruendung "..." --zahlungsart ueberweisung
```

Benennt die Datei, legt sie ab, schreibt das Register.

---

## Die wiederkehrenden Fälle

### Laptop, Tablet, Monitor, Software

**Regel: fast immer `GEW`, soweit die Bandbreite es hergibt.**

Grund: Vorsteuerabzug. 16 Prozentpunkte, die kein anderer Topf bietet.

Sonderregel, die viel wert ist: Computerhardware und Software dürfen mit
einer **Nutzungsdauer von einem Jahr** angesetzt werden (BMF-Schreiben vom
22.02.2022). Damit ist auch ein Laptop für 2.500 € **im Anschaffungsjahr
sofort voll abziehbar**. Die 800-€-GWG-Grenze spielt hier keine Rolle.

Achte auf die Rechnungsadresse: ab 250 € brutto muss dein Name und deine
Anschrift drauf, sonst ist der Vorsteuerabzug weg.

### Baumarkt, Werkzeug, Material

**Regel: `VUV` für das Objekt, an dem du arbeitest.**

Aber unterscheide sauber:

| Was | Wohin |
|---|---|
| Material für die vermietete Wohnung | `VUV`, voll |
| Material für dein eigenes Haus | `PRIV` — Material ist nie § 35a |
| Handwerkerrechnung eigenes Haus | `P35A`, aber nur der Lohnanteil |
| Werkzeug, das du überall nutzt | gemischt — Bandbreite angeben |

Bei Werkzeug lohnt es sich fast immer, den `GEW`-Anteil so hoch anzusetzen,
wie es der Wahrheit entspricht — wegen der Vorsteuer.

**Warnung bei frisch gekauften Immobilien:** Prüfe die 15-Prozent-Grenze,
bevor du größere Maßnahmen beauftragst. Siehe `05-fallstricke.md`. Hier
geht es um vierstellige Beträge.

### Handy und Mobilfunkvertrag

Klassischer Mischfall. Wenn du es dienstlich, geschäftlich und privat nutzt,
gib alle drei an. Ohne Einzelnachweis wird ein beruflicher Anteil von 50 %
in der Praxis breit akzeptiert; wer mehr will, sollte es mit einem
Einzelverbindungsnachweis über drei Monate belegen können.

### Fachliteratur, Seminare, Prüfungsgebühren

Hängt daran, ob dein Studium Erst- oder Zweitausbildung ist. Bei
Zweitausbildung/Fortbildung: `FOB` als Werbungskosten, voll wirksam und
vortragsfähig. Bei Erstausbildung und wenig Einkommen: wertlos — dann prüfe,
ob ein Bezug zum Gewerbe besteht und der Beleg dort hingehört.

### Fahrten

- Zum Standort / zur ersten Tätigkeitsstätte: Entfernungspauschale,
  **einfache** Strecke, 0,30 €/km (ab dem 21. km 0,38 €).
- Dienstreise, Lehrgang, Auswärtstätigkeit: **tatsächlich gefahrene**
  Kilometer, also hin und zurück, 0,30 €/km.
- Fahrten zur Mietwohnung: `VUV`, tatsächliche Kilometer.
- Fahrten für das Gewerbe: `GEW`.

Fahrten brauchen keinen Beleg, aber eine nachvollziehbare Aufstellung.
Ein simples Fahrtenprotokoll im Handy reicht.

### Arbeitszimmer und Homeoffice

Die Tagespauschale von 6 € pro Tag (maximal 1.260 € im Jahr) gibt es ohne
separates Zimmer und ohne Nachweis. Wird der Einkunftsart zugeordnet, für
die du zu Hause arbeitest. Bei mehreren Tätigkeiten ist der Höchstbetrag
**insgesamt** gedeckelt, nicht je Tätigkeit.

### Alles, was privat aussieht

Bevor du etwas als `PRIV` abhakst, geh diese Liste durch:

- Handwerker im eigenen Haus → § 35a, 20 % des Lohnanteils
- Reinigungskraft, Gartenpflege, Winterdienst → § 35a haushaltsnah
- Umzug aus beruflichen Gründen → Werbungskosten
- Spenden, Kirchensteuer, bestimmte Versicherungen → Sonderausgaben
- Krankheitskosten über der zumutbaren Belastung → außergewöhnliche Belastung

Erfasse `PRIV`-Belege trotzdem im Register. Erstens für die Gewährleistung,
zweitens weil `auswertung` dir am Jahresende anzeigt, wie viel privates
Volumen da liegt — und ob sich ein zweiter Blick lohnt.

---

## Die Jahresend-Regel

Beleg-für-Beleg zu entscheiden ist kurzsichtig, weil der
Arbeitnehmer-Pauschbetrag eine **Schwelle** ist. Lass deshalb einmal vor der
Abgabe der Erklärung laufen:

```bash
python3 tools/steuerbro.py neuverteilen --jahr 2026
```

Das Tool optimiert dann alle Belege des Jahres **gemeinsam** und vergleicht
zwei Strategien:

- **Szenario A:** Den Pauschbetrag ignorieren und alles in die starken Töpfe
  legen.
- **Szenario B:** Gezielt so viel in den `AN`-Topf schieben, dass die
  1.230 € gerissen werden — ab dann wirkt dort jeder weitere Euro voll.

Es nimmt automatisch das bessere und zeigt dir die Differenz. Mit
`--schreiben` übernimmst du das Ergebnis ins Register.

**Danach die Begründungen anpassen.** Eine umgeschichtete Zuordnung braucht
eine Begründung, die zur neuen Zuordnung passt.
