#!/bin/sh
# SteuerBro NAS-Sync
#
# Haelt einen Repository-Klon auf dem NAS aktuell und schiebt eingescannte
# Belege in den Eingang.
#
#   nas-sync.sh <repo-verzeichnis> [scan-verzeichnis]
#
#   repo-verzeichnis   Der Klon von SteuerBro auf dem NAS.
#   scan-verzeichnis   Optional. Wohin dein Scanner ablegt. Alles darin
#                      wandert nach belege/_eingang/ und wird hochgeladen.
#
# Beispiel (Synology-Aufgabenplaner, taeglich):
#   /volume1/daten/SteuerBro/tools/nas-sync.sh \
#       /volume1/daten/SteuerBro /volume1/scans/steuer
#
# Bewusst POSIX-sh statt bash: die Busybox-Umgebung vieler NAS-Geraete
# bringt keine bash mit.

set -eu

REPO="${1:-}"
SCANS="${2:-}"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*"; }
fehler() { log "FEHLER: $*" >&2; exit 1; }

[ -n "$REPO" ] || fehler "Kein Repository-Verzeichnis angegeben.
Aufruf: $0 <repo-verzeichnis> [scan-verzeichnis]"
[ -d "$REPO/.git" ] || fehler "$REPO ist kein Git-Repository."
command -v git >/dev/null 2>&1 || fehler "git ist auf diesem NAS nicht installiert.
Synology: Paketzentrum -> Git Server. QNAP: App Center -> Git."

cd "$REPO"
ZWEIG=$(git rev-parse --abbrev-ref HEAD)
log "SteuerBro-Sync auf Zweig $ZWEIG"

# ---------------------------------------------------------------------------
# 1. Neuen Stand holen
# ---------------------------------------------------------------------------
log "Hole Aenderungen von origin ..."
VERSUCH=1
until git fetch --quiet origin "$ZWEIG" 2>/dev/null; do
    [ "$VERSUCH" -ge 4 ] && fehler "Konnte origin nach 4 Versuchen nicht erreichen.
Pruefe die Netzwerkverbindung und den Deploy Key (siehe docs/07-nas-einbindung.md)."
    WARTE=$((VERSUCH * VERSUCH * 2))
    log "  Versuch $VERSUCH fehlgeschlagen, neuer Versuch in ${WARTE}s ..."
    sleep "$WARTE"
    VERSUCH=$((VERSUCH + 1))
done

# Lokale Aenderungen (z. B. Scans vom letzten Lauf) nicht ueberfahren.
if ! git merge --ff-only --quiet "origin/$ZWEIG" >/dev/null 2>&1; then
    log "  Kein einfacher Vorlauf moeglich, versuche Rebase ..."
    git rebase --quiet "origin/$ZWEIG" >/dev/null 2>&1 || fehler "Rebase fehlgeschlagen.
Es gibt widerspruechliche Aenderungen. Loese sie einmal von Hand auf:
  cd $REPO && git status"
fi
log "  Stand ist aktuell."

# ---------------------------------------------------------------------------
# 2. Scans in den Eingang schieben
# ---------------------------------------------------------------------------
NEU=0
LETZTES_ZIEL=""
if [ -n "$SCANS" ]; then
    [ -d "$SCANS" ] || fehler "Scan-Verzeichnis $SCANS existiert nicht."
    EINGANG="$REPO/belege/_eingang"
    mkdir -p "$EINGANG"

    # Nur Belegformate, keine Systemdateien. -maxdepth vermeidet, dass
    # Unterordner des Scanners mit aufgeraeumt werden.
    find "$SCANS" -maxdepth 1 -type f \
        \( -iname '*.pdf' -o -iname '*.jpg' -o -iname '*.jpeg' \
           -o -iname '*.png' -o -iname '*.heic' -o -iname '*.tif' \
           -o -iname '*.tiff' \) \
        ! -name '.*' -print > /tmp/steuerbro-scans.$$ 2>/dev/null || true

    while IFS= read -r DATEI; do
        [ -n "$DATEI" ] || continue
        NAME=$(basename "$DATEI")
        ZIEL="$EINGANG/$NAME"
        # Namenskollision: Zeitstempel anhaengen statt ueberschreiben.
        if [ -e "$ZIEL" ]; then
            BASIS="${NAME%.*}"
            ENDUNG="${NAME##*.}"
            ZIEL="$EINGANG/${BASIS}_$(date '+%Y%m%d%H%M%S').${ENDUNG}"
        fi
        mv "$DATEI" "$ZIEL" && NEU=$((NEU + 1))
        LETZTES_ZIEL="$ZIEL"
        log "  Eingang: $(basename "$ZIEL")"
    done < /tmp/steuerbro-scans.$$
    rm -f /tmp/steuerbro-scans.$$

    if [ "$NEU" -gt 0 ]; then
        log "$NEU neue Datei(en) in den Eingang verschoben."
    else
        log "Keine neuen Scans."
    fi
fi

# ---------------------------------------------------------------------------
# 3. Hochladen
# ---------------------------------------------------------------------------
# Der Warnhinweis muss VOR der Statuspruefung stehen: sind die Belege
# ignoriert, meldet git ueberhaupt keine Aenderung, und die Warnung - die
# einzige Stelle, an der auffaellt, dass die Scans nicht ankommen - waere
# genau dann still, wenn sie gebraucht wird.
if [ "$NEU" -gt 0 ] && [ -n "$LETZTES_ZIEL" ] \
   && git check-ignore -q "$LETZTES_ZIEL" 2>/dev/null; then
    log "ACHTUNG: belege/ ist in .gitignore ausgenommen."
    log "  Die $NEU Datei(en) bleiben auf dem NAS und werden NICHT hochgeladen."
    log "  SteuerBro sieht sie damit nicht. Abhilfe: Repository auf privat"
    log "  stellen, dann die Zeile 'belege/**' in .gitignore auskommentieren."
    log "  Siehe docs/07-nas-einbindung.md, Schritt 1 und 2."
fi

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    if [ -n "$(git diff --cached --name-only)" ]; then
        # Keine Betraege, Haendler oder Dateinamen in die Commit-Message.
        git commit -q -m "NAS-Sync: $NEU Beleg(e) im Eingang" \
                      -m "Automatisch erzeugt von tools/nas-sync.sh."
        log "Lade hoch ..."
        VERSUCH=1
        until git push --quiet origin "$ZWEIG" 2>/dev/null; do
            [ "$VERSUCH" -ge 4 ] && fehler "Push nach 4 Versuchen fehlgeschlagen.
Braucht der Deploy Key Schreibrechte? Siehe docs/07-nas-einbindung.md."
            WARTE=$((VERSUCH * VERSUCH * 2))
            log "  Versuch $VERSUCH fehlgeschlagen, neuer Versuch in ${WARTE}s ..."
            sleep "$WARTE"
            VERSUCH=$((VERSUCH + 1))
        done
        log "Hochgeladen."
    fi
else
    log "Nichts zu uebertragen."
fi

# ---------------------------------------------------------------------------
# 4. Was liegt noch offen?
# ---------------------------------------------------------------------------
OFFEN=$(find "$REPO/belege/_eingang" -type f ! -name '.gitkeep' ! -name '.*' 2>/dev/null | wc -l | tr -d ' ')
if [ "$OFFEN" -gt 0 ]; then
    log "$OFFEN Beleg(e) warten im Eingang auf Erfassung."
fi
log "Fertig."
