# NAS einbinden

Der NAS ist die richtige Idee — aber nicht als Ort, an den ich schreibe.

---

## Warum ich nicht direkt an den NAS komme

Ich laufe in einem Container in der Cloud. Dein NAS steht bei dir zu Hause
hinter deinem Router. Zwischen beiden gibt es keine Verbindung, und das ist
gut so:

Damit ich direkt schreiben könnte, müsstest du den NAS aus dem Internet
erreichbar machen (Portfreigabe oder VPN) **und** mir Zugangsdaten geben.
Beides für ein Gerät, auf dem deine Steuerbelege liegen. Der Sicherheitsgewinn
gegenüber der Lösung unten ist null, das Risiko erheblich. Deshalb: nein.

## Die Architektur, die funktioniert

```
    Du                     GitHub (privat)              NAS (bei dir)
     │                           │                           │
     ├── Rechnung im Chat ──▶ ich erfasse ──▶ push ──▶ │      │
     │                           │                     └─ pull ─▶ Archiv
     │                           │                           │
     └── Scanner/Handy ──────────────────────────────────▶ _eingang/
                                 ◀──── push ────────────────┘
```

**GitHub ist die Drehscheibe, der NAS ist Archiv und Eingang.**

Was du dadurch bekommst:

| | |
|---|---|
| Belege liegen bei dir | ✔ vollständige Kopie auf dem NAS, automatisch |
| Ich sehe sie in jeder Session | ✔ über den geklonten Stand |
| Versionierung und Historie | ✔ jede Änderung nachvollziehbar |
| Backup | ✔ zwei Orte, ohne dass du etwas tust |
| Scanner-Workflow | ✔ Drucker scannt direkt in den Eingang |
| Zugriff vom Handy | ✔ über die NAS-App |

Der einzige Preis: Eine verschlüsselte Kopie liegt bei GitHub. **Deshalb muss
das Repository privat sein** — das ist keine Formalie, sondern die
Voraussetzung dieser gesamten Konstruktion.

---

## Einrichtung

### 1. Repository auf privat stellen

`github.com/MarqEwi/SteuerBro` → Settings → General → ganz unten
"Change repository visibility" → Private.

**Vor dem ersten echten Beleg.** Ohne diesen Schritt keinen der nächsten.

### 2. Belegdateien versionieren

Standardmäßig sind die Belege von der Versionierung ausgenommen — solange das
Repository öffentlich war, wäre alles andere fahrlässig gewesen. Sobald es
privat ist, kannst du die Dateien mitversionieren, damit der NAS sie ziehen
kann und ich sie in künftigen Sessions sehe.

In `.gitignore` diese Zeile auskommentieren:

```
# belege/**
```

Sag mir Bescheid, dann mache ich das und committe es.

### 3. Zugang für den NAS anlegen

Der NAS braucht Leserechte auf das private Repository. Zwei Wege:

**Deploy Key (empfohlen).** Gilt nur für dieses eine Repository, nicht für
deinen ganzen GitHub-Account.

Auf dem NAS per SSH:
```bash
ssh-keygen -t ed25519 -C "nas-steuerbro" -f ~/.ssh/steuerbro
cat ~/.ssh/steuerbro.pub
```
Den ausgegebenen Schlüssel bei GitHub eintragen unter
Repository → Settings → Deploy keys → Add deploy key.
Häkchen bei "Allow write access" nur setzen, wenn der NAS auch pushen soll
(brauchst du für den Scanner-Workflow in Schritt 5).

**Personal Access Token.** Einfacher, aber weitreichender. Nur nehmen, wenn
SSH auf dem NAS nicht geht.

### 4. Repository auf den NAS klonen

```bash
cd /volume1/daten          # Synology; bei QNAP z. B. /share/daten
git clone git@github.com:MarqEwi/SteuerBro.git
```

### 5. Automatisch synchronisieren

Im Repository liegt `tools/nas-sync.sh`. Das Skript holt neue Belege ab,
schiebt eingescannte Dateien in den Eingang und lädt sie hoch.

Auf dem NAS einrichten:

**Synology:** Systemsteuerung → Aufgabenplaner → Erstellen → Geplante Aufgabe
→ Benutzerdefiniertes Skript. Täglich, z. B. 3:00 Uhr:
```
/volume1/daten/SteuerBro/tools/nas-sync.sh /volume1/daten/SteuerBro /volume1/scans/steuer
```

**QNAP:** Systemsteuerung → Hardware → Energieplan, oder direkt per crontab.

**Generisch (crontab):**
```
0 3 * * * /pfad/zu/SteuerBro/tools/nas-sync.sh /pfad/zu/SteuerBro /pfad/zu/scans
```

Der zweite Parameter ist optional. Gibst du ihn an, verschiebt das Skript
alles aus diesem Ordner nach `belege/_eingang/` und lädt es hoch — dann
landen Scans automatisch bei mir.

### 6. Scanner einrichten

Stell deinen Multifunktionsdrucker so ein, dass er auf den NAS scannt, in
genau den Ordner aus Schritt 5. Ab da gilt: **Rechnung einlegen, Knopf
drücken, fertig.** Beim nächsten Lauf des Skripts liegt sie im Eingang, und
ich arbeite sie ab, sobald du dich meldest.

Für unterwegs dasselbe mit der NAS-App auf dem Handy (Synology DS file /
QNAP Qfile): Foto in den Scan-Ordner, Rest passiert von allein.

---

## Wenn du GitHub gar nicht willst

Verständlich, ist aber eine echte Einschränkung. Dann bleibt: Du behältst
alles auf dem NAS, schickst mir Rechnungen im Chat, ich rechne und gebe dir
den Registereintrag und den Dateinamen zurück — ablegen musst du selbst.

Was du dabei verlierst: Ich sehe deine Historie nicht, kann `neuverteilen`
nicht über vergangene Belege laufen lassen, und die Quartalsauswertung
funktioniert nur, soweit du mir das Register jedes Mal mitschickst.

Der Kern des Systems — die Optimierung über alle Belege eines Jahres — lebt
davon, dass ich den Bestand sehe. Ohne ihn bleibt ein Taschenrechner.

---

## Was auf keinen Fall passieren sollte

- **NAS per Portfreigabe ins Internet öffnen**, damit irgendwer (auch ich)
  direkt zugreifen kann. NAS-Geräte sind ein beliebtes Ziel für
  Verschlüsselungstrojaner, und deine Steuerbelege sind genau die Art von
  Daten, die man nicht zurückkaufen möchte.
- **Zugangsdaten zum NAS in den Chat oder ins Repository schreiben.**
  Brauche ich nicht, will ich nicht, und im Repository stünden sie dauerhaft
  in der Historie.
- **Das Repository öffentlich lassen** und trotzdem Belege versionieren.
