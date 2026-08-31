# Spielregeln

Kurz, weil es nicht kompliziert ist. Dies ist keine Moralpredigt, sondern
Risikomanagement: Die Regeln hier trennen das, was dir Geld bringt, von dem,
was dich Geld kostet.

---

## Die drei Regeln

### 1. Ein Beleg, ein Euro, ein Topf

Ein Laptop für 1.499 € ergibt zusammen 1.499 € Abzug — verteilt auf beliebig
viele Töpfe, aber niemals mehr als einmal.

Deshalb bekommt jeder Beleg im Register eine ID, deshalb gibt es je Topf eine
eigene Zeile, und deshalb prüft `steuerbro.py pruefe`, ob die Anteile
zusammen über 100 % liegen. Das ist die einzige Fehlerart, die das Tool als
**Fehler** und nicht als Hinweis meldet.

### 2. Der Nutzungsanteil muss existieren

Die Bandbreite, die du angibst, beschreibt deine tatsächliche Nutzung. Wo
sie innerhalb dieser Bandbreite landet, ist deine Entscheidung — und die
darfst du zu deinen Gunsten treffen. Wo sie liegt, ist Schätzung. **Ob** es
die Nutzung gibt, ist Tatsache.

Konkret:

| Situation | Zulässig? |
|---|---|
| Laptop wirklich für Gewerbe, Uni und Dienst genutzt, Aufteilung 60/30/10 statt 40/40/20 | **Ja.** Schätzung innerhalb der realen Nutzung. |
| Werkzeug real gemischt genutzt, Schwerpunkt auf den Topf mit Vorsteuerabzug gelegt | **Ja.** |
| Größere Renovierung ins nächste Jahr verschoben, um unter der 15-%-Grenze zu bleiben | **Ja.** Timing ist Gestaltung. |
| Handwerkerrechnung noch im Dezember bezahlt, um das § 35a-Budget zu nutzen | **Ja.** |
| Farbe fürs eigene Wohnzimmer als Werbungskosten bei der Mietwohnung | **Nein.** Die Nutzung gibt es nicht. |
| Privater Fernseher als „Monitor fürs Gewerbe" | **Nein.** |

Der Unterschied ist nicht graduell. Bei den ersten vier Fällen streitet man
im schlimmsten Fall über eine Quote und einigt sich. Bei den letzten beiden
geht es um § 370 AO.

### 3. Die Begründung entsteht jetzt, nicht später

Der wirtschaftliche Wert einer sauberen Begründung ist hoch und wird
unterschätzt. Bei einer Rückfrage entscheidet nicht, ob deine Quote objektiv
richtig war — das kann niemand feststellen. Es entscheidet, ob du sie
**plausibel und konsistent** erklären kannst.

Wer sagt „Laptop, hauptsächlich für die Auftragsbearbeitung im Gewerbe,
daneben Seminararbeiten", hat eine Diskussion. Wer nichts sagt, weil er es
nach zwei Jahren nicht mehr weiß, bekommt die Quote gestrichen, die das
Finanzamt für richtig hält.

**Deshalb ist `--begruendung` das wichtigste Feld im ganzen System.** Ein
Satz. Beim Erfassen. Nicht später.

---

## Warum sich das Einhalten rechnet

Eine gestrichene Zuordnung kostet dich die Steuerersparnis zurück, plus
**6 % Zinsen pro Jahr** ab dem 15. Monat nach dem Steuerjahr (§ 233a AO) —
rückwirkend über die gesamte offene Festsetzungsfrist.

Bei einem Nebengewerbe kommt ein zweiter Effekt dazu, der teurer ist als die
Nachzahlung: Fällt bei einer Prüfung ein Beleg auf, der ersichtlich keinen
betrieblichen Bezug hat, wird nicht dieser eine Beleg gestrichen. Es wird die
**Glaubwürdigkeit der gesamten Buchführung** in Frage gestellt, und der
Prüfer schaut sich alles andere sehr viel genauer an. Ein Beleg über 80 €
kann so eine Prüfung auslösen, die vierstellig endet.

Andersherum: Wer sauber dokumentiert, kann eine aggressive Quote selbstbewusst
vertreten. Die Dokumentation ist es, die dir den Spielraum überhaupt erst
gibt.

---

## Was dieses System nicht ist

Es ist **keine Steuerberatung**. Es ist ein Rechen- und Ordnungswerkzeug, das
dir die Größenordnungen zeigt und deine Entscheidungen festhält.

Drei Fragen solltest du einmal verbindlich klären lassen, weil an ihnen
jeweils vierstellige Beträge hängen und das Tool sie nicht für dich
entscheiden kann:

1. **Ist dein Studium Erst- oder Zweitausbildung?**
   Entscheidet, ob deine Studienkosten voll wirksame Werbungskosten mit
   Verlustvortrag sind oder faktisch wertlose Sonderausgaben. Das ist die
   mit Abstand teuerste offene Frage in deinem Fall.
2. **Lohnt sich der Verzicht auf die Kleinunternehmerregelung?**
   Entscheidet über rund 16 Prozentpunkte auf jede Anschaffung — bindet dich
   aber fünf Jahre.
3. **Wie steht dein Gewerbe zur Liebhaberei-Frage?**
   Wenn es dauerhaft Verluste macht, kippt die gesamte Optimierung
   rückwirkend.

Ein Termin. Diese drei Fragen. Danach läuft das System für Jahre.
