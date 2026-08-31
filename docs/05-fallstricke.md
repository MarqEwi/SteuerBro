# Fallstricke

Sortiert nach dem, was es kostet, wenn man sie übersieht.

---

## 1. Der anschaffungsnahe Herstellungsaufwand (bis zu fünfstellig)

**Die teuerste Falle für dich als Immobilienbesitzer.**

Übersteigen die Instandsetzungs- und Modernisierungskosten **innerhalb von
drei Jahren** nach dem Kauf einer Immobilie **15 % der Gebäude-Anschaffungs-
kosten** (netto, ohne Grund und Boden), dann sind sie zwingend zu aktivieren
(§ 6 Abs. 1 Nr. 1a EStG).

Was das konkret bedeutet:

```
Gebäude-AK netto:              200.000 €
15-%-Grenze:                    30.000 €

Renovierung Jahr 1:             12.000 €
Renovierung Jahr 2:             19.000 €
                               ---------
zusammen:                       31.000 €   ← Grenze gerissen

Folge: statt 31.000 € sofortigem Abzug nur noch
       31.000 € ÷ 50 Jahre = 620 € pro Jahr.
```

Bei einem Grenzsteuersatz von 40 % sind das **12.400 € Steuerersparnis, die
zu 248 € pro Jahr werden.** Wegen 1.000 € über der Grenze.

**Was hilft:**
- Die Grenze für jedes Objekt kennen, bevor du beauftragst. Trage
  `gebaeude_ak_netto` und `anschaffung_datum` ins Profil ein — dann warnt
  dich das Tool automatisch.
- Größere Maßnahmen über die Drei-Jahres-Grenze hinausschieben. Das ist
  legitime Gestaltung und der Grund, warum Timing hier so viel wert ist.
- Nicht mitgerechnet werden: Erhaltungsaufwendungen, die jährlich üblicherweise
  anfallen, und Erweiterungen. Die Abgrenzung ist streitanfällig — bei großen
  Beträgen vorher fragen.

---

## 2. Erstausbildung statt Fortbildung (vierstellig, jährlich)

Erstausbildungskosten sind nur Sonderausgaben, maximal 6.000 €, und **nicht
vortragsfähig**. Wer im Studium wenig verdient, verliert sie vollständig.

Fortbildungs- und Zweitausbildungskosten sind Werbungskosten, unbegrenzt, und
erzeugen einen **Verlustvortrag**, der sich in spätere Jahre mit höherem
Einkommen mitnehmen lässt.

Bei 4.000 € Studienkosten pro Jahr über vier Jahre ist das der Unterschied
zwischen **0 €** und **rund 6.700 €** bei einem späteren Satz von 42 %.

Kläre diese Einordnung einmal verbindlich. Setze danach `ausbildung.typ` im
Profil korrekt — das Tool rechnet danach völlig anders.

---

## 3. Der Arbeitnehmer-Pauschbetrag (drei- bis vierstellig)

1.230 € Werbungskosten bekommst du ohne jeden Beleg. Alles, was du darunter
im `AN`-Topf sammelst, bringt **null Euro zusätzlich**.

Zwei Fehler sind hier üblich:

- **Belege dort ablegen, die auch woanders hinpassen.** Solange du unter der
  Schwelle bist, ist jeder Euro dort verschenkt.
- **Nicht merken, dass man knapp darunter liegt.** Bei 1.100 € gesammelten
  Werbungskosten bringen die nächsten 130 € nichts — aber der 131. Euro
  bringt plötzlich den vollen Satz, und rückwirkend werden auch die 1.230 €
  wirksam. Es kann sich also lohnen, gezielt darüber zu springen.

Nicht vergessen, was ohne Beleg zählt und schnell über die Schwelle bringt:
**Verpflegungsmehraufwand** bei Lehrgängen und Übungen (14 € ab 8 Stunden,
28 € ganztags), Fahrten, doppelte Haushaltsführung.

`steuerbro.py auswertung` zeigt dir laufend, wo du stehst.
`steuerbro.py neuverteilen` rechnet beide Strategien durch.

---

## 4. § 35a: Barzahlung und Materialanteil (bis 1.200 € jährlich)

Drei Fehler, jeder einzelne kostet den kompletten Abzug:

- **Bar bezahlt.** Wird ausnahmslos nicht anerkannt, auch nicht mit Quittung.
  Ohne Ausnahme, ohne Ermessen. Immer überweisen.
- **Material eingerechnet.** Nur Lohn-, Fahrt- und Maschinenkosten sind
  begünstigt. Die Farbe nicht, der Maler schon.
- **Rechnung weist nichts getrennt aus.** Dann ist gar nichts absetzbar.
  Lösung: beim Handwerker anrufen und eine aufgeschlüsselte Rechnung
  nachfordern. Ein Anruf, bis zu 1.200 €.

Der Höchstbetrag verfällt jedes Jahr neu und lässt sich nicht vortragen.
Wenn im November noch Budget frei ist: Maßnahme vorziehen. Ist es
ausgeschöpft: ins nächste Jahr schieben.

---

## 5. Fehlende Rechnungsangaben (16 Prozentpunkte je Beleg)

Für den Vorsteuerabzug muss die Rechnung alle Pflichtangaben nach § 14 UStG
enthalten. Ab 250 € brutto zwingend **deinen Namen und deine Anschrift** als
Leistungsempfänger.

Ein Kassenbon über 900 € ohne Adressat kostet dich rund 144 € Vorsteuer.

**Beim Kauf daran denken**, nicht hinterher. Nachträglich lässt sich eine
Rechnung zwar berichtigen, aber das ist Arbeit und manchmal nicht mehr
möglich.

---

## 6. Liebhaberei beim Nebengewerbe (rückwirkend alles)

Erwirtschaftet dein Gewerbe über Jahre nur Verluste und ist keine
Gewinnerzielungsabsicht erkennbar, kann das Finanzamt es als „Liebhaberei"
einstufen. Dann werden **sämtliche Betriebsausgaben rückwirkend gestrichen** —
und mit ihnen die gesamte Optimierung.

Das ist das Risiko, das entsteht, wenn man Anschaffungen zu aggressiv ins
Gewerbe schiebt: Der Topf mit dem stärksten Hebel ist auch der, der als
Ganzes kippen kann.

**Was hilft:** Eine plausible Prognose, dass über die Totalperiode ein
Gewinn entsteht. Ab dem dritten bis fünften Verlustjahr ernst nehmen. Wenn
dein Gewerbe strukturell Verluste macht, ist es besser, Anschaffungen dort
zurückhaltend anzusetzen — der sichere Abzug im `VUV`-Topf ist mehr wert als
der riskante im `GEW`-Topf.

---

## 7. GWG-Grenze und Abschreibung (Verzögerung, kein Verlust)

Über 800 € netto ist ein Wirtschaftsgut nicht sofort abziehbar, sondern über
die Nutzungsdauer abzuschreiben. Der Vorteil geht nicht verloren, aber er
verteilt sich über Jahre.

**Die wichtige Ausnahme:** Computerhardware und Software dürfen mit einer
Nutzungsdauer von einem Jahr angesetzt werden (BMF-Schreiben vom 22.02.2022).
Damit sind sie im Anschaffungsjahr **sofort voll abziehbar** — unabhängig vom
Preis. Ein Laptop für 2.500 € wirkt komplett im Kaufjahr.

Bei anderen Wirtschaftsgütern über 800 € netto lohnt sich der Blick auf den
Zeitpunkt: Ein Kauf im Januar bringt bei zeitanteiliger Abschreibung im
ersten Jahr mehr als einer im Dezember.

---

## 8. Thermopapier (unbezifferbar, weil der Beleg dann weg ist)

Baumarkt- und Tankbons auf Thermopapier verblassen binnen Monaten
vollständig. Ein leerer Zettel ist kein Beleg.

**Am Tag des Kaufs fotografieren.** Das ist der billigste Fehler, den man in
diesem ganzen System vermeiden kann, und der am häufigsten gemachte.
