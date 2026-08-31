# Ablage und Dateinamen

Dein größtes Problem ist nach eigener Aussage nicht das Steuerrecht, sondern
die Bürokratie: Du gibst Geld aus, das du absetzen könntest, und tust es
nicht, weil der Aufwand nervt. Dieser Teil des Systems löst genau das.

**Der Grundsatz: Erfassen muss unter 60 Sekunden dauern, sonst passiert es
nicht.**

---

## Die Namenskonvention

```
2026-03-14__GEW__Laptop__Notebooksbilliger__ThinkPad-T14-Gen5__1499-00EUR__B-2026-0001.pdf
└────┬───┘  └┬┘  └──┬──┘  └──────┬───────┘  └───────┬───────┘  └────┬───┘  └─────┬──────┘
   Datum   Topf  Kategorie    Händler        Beschreibung        Betrag       Beleg-ID
```

Getrennt durch doppelte Unterstriche, damit sich die Felder maschinell
wieder auseinandernehmen lassen. Keine Umlaute, keine Leerzeichen, keine
Sonderzeichen — funktioniert damit auf jedem System, in jeder Cloud und in
jedem Backup.

Bei Vermietung kommt das Objektkürzel dazu:

```
2026-04-02__VUV-OBJ1__Instandhaltung__Bauhaus__Fliesenkleber__89-90EUR__B-2026-0002.pdf
```

**Warum diese Reihenfolge?**

- **Datum zuerst** → sortiert sich in jedem Dateimanager chronologisch von
  selbst.
- **Topf an zweiter Stelle** → du siehst auf einen Blick, wohin der Beleg
  gehört, ohne ihn zu öffnen.
- **Betrag drin** → du kannst Summen bilden, ohne jede Datei zu öffnen.
- **Beleg-ID am Ende** → die Verbindung zum Register, eindeutig und
  unveränderlich.

Den Namen erzeugt das Tool automatisch. Du musst dir nichts merken.

### Die Topf-Kürzel

| Kürzel | Bedeutung |
|---|---|
| `GEW` | Nebengewerbe, Betriebsausgabe |
| `VUV` | Vermietung und Verpachtung (immer mit Objektkürzel) |
| `AN` | Arbeitnehmer / Bundeswehr, Werbungskosten |
| `FOB` | Fortbildung / Studium |
| `P35A` | Handwerkerleistung im eigenen Haushalt, § 35a |
| `PRIV` | Privat, nicht absetzbar |

Bei aufgeteilten Belegen steht im Dateinamen der **größte** Anteil. Die
vollständige Aufteilung steht im Register — dort bekommt der Beleg eine Zeile
je Topf, alle unter derselben ID.

---

## Die Ordnerstruktur

```
belege/
├── _eingang/                    ← hier landet alles Neue, unsortiert
└── 2026/
    ├── 01-gewerbe/
    ├── 02-vermietung/
    │   ├── OBJ1/
    │   └── OBJ2/
    ├── 03-bundeswehr/
    ├── 04-studium-fortbildung/
    ├── 05-paragraf-35a/
    └── 06-privat/
```

Nummerierte Ordner, damit die Sortierung der wirtschaftlichen Rangfolge
folgt und nicht dem Alphabet.

---

## Der Workflow im Alltag

### Sofort beim Kauf (10 Sekunden)

Beleg fotografieren oder die PDF-Rechnung direkt speichern, und zwar nach
`belege/_eingang/`. Nicht sortieren, nicht umbenennen, nicht nachdenken.
**Nur reinwerfen.**

Praktisch: Lege dir auf dem Handy einen Sync-Ordner an (Nextcloud, Syncthing,
iCloud, Dropbox — egal), der auf `belege/_eingang/` zeigt. Dann ist
„fotografieren" die einzige Handlung, die du unterwegs machst.

Papierbelege aus dem Baumarkt verblassen innerhalb von Monaten. Der
Thermopapier-Bon vom März ist im Dezember leer. **Fotografiere ihn am Tag
des Kaufs.**

### Einmal pro Woche oder Monat (5 Minuten)

Eingang abarbeiten. Pro Beleg ein Aufruf von `steuerbro.py neu`. Das Tool
bewertet, benennt, verschiebt und registriert in einem Zug.

```bash
python3 tools/steuerbro.py pruefe
```

zeigt dir, was im Eingang liegengeblieben ist, wo Begründungen fehlen und
ob eine Belegdatei verschwunden ist.

### Einmal im Quartal (10 Minuten)

```bash
python3 tools/steuerbro.py auswertung
```

Zeigt Summen je Topf, wie weit du vom Arbeitnehmer-Pauschbetrag entfernt
bist und wie viel vom § 35a-Höchstbetrag noch frei ist.

Das ist der Moment, in dem du **steuern** kannst: Wenn im November noch
600 € vom § 35a-Budget frei sind, ist das der richtige Zeitpunkt, die
Handwerkerrechnung noch in diesem Jahr zu bezahlen statt im Januar.

### Einmal im Jahr, vor der Abgabe (30 Minuten)

```bash
python3 tools/steuerbro.py neuverteilen --jahr 2026
```

Optimiert alle Belege des Jahres gemeinsam, weil sich die Schwellen erst am
Jahresende sicher beurteilen lassen. Siehe `02-entscheidungsregeln.md`.

---

## Das Register

`register/belege.csv`, Semikolon-getrennt, damit Excel und LibreOffice es
im deutschen Sprachraum ohne Nachfrage öffnen.

Ein Beleg mit drei Töpfen ergibt **drei Zeilen mit derselben ID**. Das ist
Absicht: So lässt sich maschinell prüfen, dass die Anteile zusammen 100 %
ergeben und nicht 150 %. Genau das macht `steuerbro.py pruefe`.

Wichtige Spalten:

| Spalte | Warum sie da ist |
|---|---|
| `id` | Klammer über alle Teilzeilen eines Belegs |
| `anteil_prozent` | Die Aufteilung; Summe je ID muss ≤ 100 sein |
| `vorteil_geschaetzt` | Was dieser Teil dir voraussichtlich bringt |
| `bandbreiten` | Deine ursprüngliche Nutzungsangabe — Grundlage für `neuverteilen` |
| `begruendung` | **Die wichtigste Spalte.** Warum diese Aufteilung? |
| `zahlungsart` | Bei § 35a entscheidend: bar = Abzug verloren |

---

## Datenschutz

Belege enthalten Kontonummern, Adressen und dein vollständiges
Ausgabenverhalten. Die `.gitignore` schließt `belege/**` deshalb aus der
Versionierung aus — die Dateien bleiben lokal.

Das Register wird versioniert, weil es dein Arbeitsstand und die Historie
deiner Entscheidungen ist. **Vergewissere dich, dass dieses Repository auf
privat steht.**

## Aufbewahrung

- Privatperson: die Belege bis zum Ende der Festsetzungsfrist, in der Regel
  vier bis sieben Jahre.
- Gewerbetreibender: **zehn Jahre**, § 147 AO. Rechnungen, Buchungsbelege,
  Jahresabschlüsse.
- Vermieter: die Belege zu Herstellungskosten so lange, wie das Gebäude
  abgeschrieben wird — also **bis zu 50 Jahre**. Ein Beleg von heute kann
  2070 noch gebraucht werden.

Ein Scan reicht steuerlich aus, wenn die Wiedergabe bildlich mit dem
Original übereinstimmt und der Scan unveränderbar aufbewahrt wird.
**Backup nicht vergessen** — ein einzelner Rechner ist kein Archiv.
