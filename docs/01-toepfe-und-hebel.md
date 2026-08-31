# Die Töpfe und was sie wirklich wert sind

Der Kern der ganzen Sache: **Ein Euro Ausgabe ist nicht überall ein Euro Ausgabe.**
Je nachdem, welchem Topf du eine Rechnung zuordnest, kommen zwischen 0 und
über 45 Cent pro Euro bei dir an. Wer das nicht weiß, verschenkt bei einem
einzigen Laptop schnell 200 bis 600 Euro.

Diese Datei erklärt, warum die Töpfe unterschiedlich viel wert sind. Das Tool
`tools/steuerbro.py` rechnet es dir dann konkret aus.

---

## Die Rangfolge, grob

| Rang | Topf | Kürzel | Wert je Euro brutto |
|---|---|---|---|
| 1 | Nebengewerbe, regelbesteuert | `GEW` | **~41–48 Cent** |
| 2 | Vermietung und Verpachtung | `VUV` | ~30–45 Cent |
| 2 | Fortbildung als Werbungskosten | `FOB` | ~30–45 Cent (aber siehe Pauschbetrag) |
| 3 | Handwerkerleistung § 35a | `P35A` | 20 Cent, **aber nur auf den Lohnanteil** |
| 4 | Arbeitnehmer / Bundeswehr | `AN` | **0 Cent** unterhalb 1.230 € |
| 5 | Erstausbildung als Sonderausgabe | `FOB` | oft **0 Cent** |

Die Rangfolge ist kein Naturgesetz. Sie kippt, sobald Schwellen gerissen sind.
Genau deshalb rechnet das Tool sie bei jedem Beleg neu — auf Basis dessen,
was du im laufenden Jahr schon verbraucht hast.

---

## 1. Nebengewerbe (`GEW`) — meistens der stärkste Hebel

Warum er gewinnt: Er zahlt **zweimal**.

Bei einem Laptop für 1.499 € brutto:

```
Vorsteuer      239,34 €   ← kommt über die Umsatzsteuervoranmeldung zurück,
                            unabhängig von deinem Steuersatz
Steuerersparnis 377,90 €   ← 30 % auf den Nettobetrag von 1.259,66 €
                 --------
zusammen        617,24 €   = 41,2 % des Kaufpreises
```

Der Vorsteuerabzug ist der Grund. Er hängt **nicht** an deinem Grenzsteuersatz,
sondern ist ein fester Zuschlag von rund 16 Prozentpunkten auf den Bruttobetrag.
Kein anderer Topf kann das.

**Die entscheidende Voraussetzung:** Du musst regelbesteuert sein, also
Umsatzsteuer ausweisen. Als Kleinunternehmer nach § 19 UStG gibt es keine
Vorsteuer, und der Topf fällt auf das Niveau der anderen zurück.

> **Prüfe das als Erstes.** Wenn du Kleinunternehmer bist und regelmäßig
> größere Anschaffungen hast, kann der freiwillige Verzicht auf die
> Kleinunternehmerregelung sich rechnen — er bindet dich allerdings fünf
> Jahre und erzeugt laufenden Erklärungsaufwand. Das ist eine Entscheidung
> für den Steuerberater, aber du solltest sie überhaupt einmal stellen.

**Grenzen:**
- Unter 10 % betrieblicher Nutzung ist weder die Zuordnung zum
  Betriebsvermögen noch der volle Vorsteuerabzug möglich.
- Die Rechnung muss ab 250 € brutto auf deinen Namen und deine Anschrift
  lauten (§ 14 UStG). Ein anonymer Kassenbon kostet dich die 16 Prozentpunkte.
- Dauerverluste über Jahre → Risiko „Liebhaberei", dann fällt rückwirkend
  alles weg. Siehe `05-fallstricke.md`.

---

## 2. Vermietung und Verpachtung (`VUV`)

Werbungskosten bei den Einkünften aus Vermietung. Kein Pauschbetrag, keine
Schwelle — **jeder Euro wirkt ab dem ersten**. Das macht diesen Topf sehr
verlässlich.

Kein Vorsteuerabzug, weil Wohnraumvermietung nach § 4 Nr. 12a UStG
umsatzsteuerfrei ist. Dafür wirkt der volle Bruttobetrag.

Für dich als Immobilienbesitzer mit Baumarkt-Rechnungen ist das der
Standardtopf. Zwei Dinge musst du dabei im Blick behalten:

- **Erhaltungsaufwand vs. Herstellungsaufwand.** Reparieren und ersetzen ist
  sofort abziehbar. Erweitern, wesentlich verbessern oder den Standard heben
  ist Herstellungsaufwand und wandert in die Abschreibung über ~50 Jahre.
- **Die 15-Prozent-Falle** in den ersten drei Jahren nach Kauf. Das ist die
  teuerste Falle im ganzen System — siehe `05-fallstricke.md`.

**Werkzeug** ist ein Sonderfall: Ein Akkuschrauber, den du für die
Mietwohnung *und* das Gewerbe *und* privat nutzt, ist ein klassisches
gemischt genutztes Wirtschaftsgut. Genau dafür ist das Tool da.

---

## 3. Fortbildung / Studium (`FOB`) — hier steckt die größte Weiche

Diese eine Unterscheidung entscheidet über tausende Euro:

**Erstausbildung** (du hattest vorher keine abgeschlossene Berufsausbildung
und kein abgeschlossenes Studium):
→ nur **Sonderausgaben**, § 10 Abs. 1 Nr. 7 EStG, maximal 6.000 €.
→ Sonderausgaben sind **nicht vortragsfähig**.
→ Wenn du im Studium wenig verdienst, verfallen sie **ersatzlos**. Wert: 0 €.

**Zweitausbildung oder Fortbildung** (du hast bereits eine abgeschlossene
Ausbildung oder ein abgeschlossenes Studium — oder das Studium ist
berufsbegleitend zu deinem Dienst):
→ **Werbungskosten**, unbegrenzt.
→ Erzeugen bei niedrigem Einkommen einen **Verlustvortrag**, der sich in
  spätere, besser verdienende Jahre mitnehmen lässt.
→ Wert: voller Grenzsteuersatz, unter Umständen sogar der *künftige*, höhere.

> **Das ist der wichtigste Punkt in diesem ganzen Repository.** Wenn du bei
> der Bundeswehr dienst und daneben studierst, spricht viel dafür, dass es
> sich um Fortbildung neben einem Dienstverhältnis handelt — also
> Werbungskosten. Kläre das einmal verbindlich ab. Es ist die eine Frage,
> für die sich ein Steuerberater-Termin garantiert rechnet.

**Der Haken:** Gehören die Fortbildungskosten zu deinen
Arbeitnehmer-Einkünften, teilen sie sich den Pauschbetrag von 1.230 € mit
allen anderen Werbungskosten aus dem Dienst. Die ersten 1.230 € zusammen
bringen null. Das Tool rechnet das mit.

---

## 4. Arbeitnehmer / Bundeswehr (`AN`) — der Topf mit dem toten Boden

Werbungskosten nach § 9 EStG. Aber: § 9a EStG gewährt dir ohnehin pauschal
**1.230 €**, ohne jeden Beleg.

Das heißt im Klartext: **Die ersten 1.230 € Werbungskosten aus dem Dienst
bringen dir exakt null Euro zusätzlich.** Du bekommst sie sowieso.

Daraus folgt eine klare Regel:

> Solange du unter dem Pauschbetrag liegst, gehört **alles**, was auch in
> einen anderen Topf passt, in den anderen Topf. Der `AN`-Topf ist bis 1.230 €
> ein Loch, in das du Belege wirfst, ohne dass etwas passiert.

Und die Umkehrung, die genauso wichtig ist:

> Sobald du sicher über 1.230 € liegst, dreht sich alles um. Ab dann wirkt
> jeder weitere Euro voll, und es lohnt sich, Restbelege gezielt dorthin zu
> legen.

Der Befehl `steuerbro.py auswertung` zeigt dir jederzeit an, wo du stehst.

**Was dich schnell über die Schwelle bringt — und oft vergessen wird:**
- **Verpflegungsmehraufwand** bei Lehrgängen, Übungen und Auswärtstätigkeit:
  14 € ab 8 Stunden Abwesenheit, 28 € bei ganztägiger Abwesenheit.
  **Ohne jeden Beleg.** Bei einem zweiwöchigen Lehrgang sind das schnell
  300–400 € — das ist oft der größte Einzelposten überhaupt.
- Fahrten zum Standort (Entfernungspauschale) und Dienstreisen
  (tatsächlich gefahrene Kilometer, also hin und zurück).
- Doppelte Haushaltsführung, wenn du am Standort eine Zweitunterkunft hast.
- Berufskleidung, Ausrüstung, Umzugskosten bei Versetzung.

---

## 5. Handwerkerleistungen § 35a (`P35A`) — der übersehene Topf

Für die **selbstgenutzte** Wohnung. Genau der Topf für die Farbe, die du für
dein eigenes Haus gekauft hast und von der du dachtest, sie sei verloren.

20 % der Kosten, maximal 1.200 € pro Jahr — und zwar als **Abzug von der
Steuerschuld**, nicht vom Einkommen. Das ist besonders wertvoll: Es wirkt
unabhängig vom Grenzsteuersatz.

**Die drei Bedingungen, an denen es fast immer scheitert:**

1. **Nur Lohn-, Fahrt- und Maschinenkosten zählen. Material nie.**
   Die Farbe selbst ist nicht begünstigt — der Maler, der sie streicht, schon.
2. **Die Rechnung muss Lohn- und Materialanteil getrennt ausweisen.**
   Wenn nicht: beim Handwerker eine aufgeschlüsselte Rechnung nachfordern.
   Das ist ein Anruf und bringt bis zu 1.200 €.
3. **Zwingend per Überweisung zahlen.** Barzahlung wird ausnahmslos nicht
   anerkannt, auch nicht mit Quittung. Das ist die häufigste Ursache dafür,
   dass der Abzug kippt.

Zusätzlich: haushaltsnahe Dienstleistungen (Reinigung, Gartenpflege,
Winterdienst, teilweise Umzugskosten) mit 20 %, maximal 4.000 € pro Jahr.

---

## Wie das Tool daraus eine Entscheidung macht

Für jeden Beleg gibst du an, **in welcher Bandbreite** sich deine
tatsächliche Nutzung bewegt:

```
--anteile "GEW=30-60,FOB=20-50,AN=10-30"
```

Gelesen: „Das Gerät geht zu mindestens 30 % und höchstens 60 % ins Gewerbe,
zu 20–50 % ins Studium, zu 10–30 % in den Dienst."

Das Tool verteilt dann **innerhalb dieser Bandbreite** so, dass am meisten
bei dir hängen bleibt. Die Bandbreite kommt von dir und beschreibt deine
echte Nutzung. Das Tool erfindet sie nicht und geht nicht darüber hinaus —
es holt aus der Nutzung, die du hast, das Maximum.
