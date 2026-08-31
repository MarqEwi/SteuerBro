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

### Schritt 1: Repository auf privat stellen

`github.com/MarqEwi/SteuerBro` -> Settings -> General -> ganz unten
"Change repository visibility" -> Private.

**Vor dem ersten echten Beleg.** Ohne diesen Schritt keinen der nächsten.

### Schritt 2: Belegdateien versionieren

Solange das Repository öffentlich war, waren die Belege bewusst von der
Versionierung ausgenommen. Sobald es privat ist, wird die Zeile `belege/**`
in `.gitignore` auskommentiert — erst dann kommen die Scans überhaupt beim
System an. Sag Bescheid, dann mache ich das.

`tools/nas-sync.sh` warnt ausdrücklich, solange das noch aussteht: sonst
liefe der Sync scheinbar erfolgreich, während die Scans den NAS nie
verlassen.

### Schritt 3: Das Einrichtungsskript laufen lassen

Per SSH auf dem NAS anmelden, dann:

```bash
git clone https://github.com/MarqEwi/SteuerBro.git /tmp/sb-setup
sh /tmp/sb-setup/tools/nas-setup.sh
```

Das Skript erledigt den Rest: Schlüssel erzeugen, SSH einrichten, Repository
klonen, Scan-Ordner anlegen, täglichen Sync eintragen, Testlauf. Es fragt
nur nach den Verzeichnissen und hält einmal an, damit du den angezeigten
Deploy Key bei GitHub einträgst — mit **Häkchen bei "Allow write access"**,
sonst kann der NAS nichts hochladen.

Das Skript ist idempotent: Ein zweiter Lauf repariert eine unvollständige
Einrichtung, statt etwas doppelt anzulegen.

Kann das Skript den Cron-Eintrag nicht selbst setzen (auf Synology der
Normalfall), gibt es die fertige Befehlszeile aus. Die trägst du ein unter
Systemsteuerung -> Aufgabenplaner -> Erstellen -> Geplante Aufgabe ->
Benutzerdefiniertes Skript, täglich um 3:00 Uhr.

### Schritt 4: Scanner umstellen

Multifunktionsdrucker so einstellen, dass er in den Scan-Ordner aus Schritt 3
scannt. Für unterwegs dasselbe mit der NAS-App auf dem Handy (Synology DS
file, QNAP Qfile): Foto in den Ordner, fertig.

**Ab hier ist dein einziger Handgriff im Alltag: Rechnung einlegen, Knopf
drücken.**

---

## Warum kein VPN, kein WireGuard, kein Direktzugriff

Die naheliegende Frage. Die Antwort ist nein, aus drei Gründen — und keiner
davon kostet dich etwas.

**1. Die Session ist flüchtig.** Jedes Gespräch läuft in einem neuen
Container. Ein Tunnel müsste bei jedem Gespräch neu aufgebaut werden, mit
Schlüsseln, die dafür dauerhaft irgendwo liegen müssten — also im
Repository. Ein WireGuard-Private-Key in der Git-Historie ist unwiderruflich
drin und öffnet jedem, der das Repository je zu sehen bekommt, einen Weg ins
Heimnetz. Das ist schlechter als jede Alternative hier.

**2. Der Netzverkehr läuft absichtlich über einen kontrollierten Proxy.**
Ein Tunnel wäre die Umgehung genau dieser Grenze.

**3. Es würde keinen einzigen Handgriff sparen.** Das ist der eigentliche
Punkt. Das Ziel ist, keine Dateien anfassen zu müssen. Der Cron-Job erledigt
das vollständig. Ob eine Datei per VPN geholt oder per Git geschickt wird,
ist von außen betrachtet derselbe Vorgang: null Handgriffe.

Der Aufwand steckt nicht im Weg, sondern in der einmaligen Einrichtung — und
die nimmt `tools/nas-setup.sh` ab.

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
