#!/bin/sh
# SteuerBro NAS-Einrichtung
#
# Einmal auf dem NAS ausfuehren. Danach ist der einzige verbleibende
# Handgriff im Alltag: Rechnung scannen.
#
#   sh nas-setup.sh
#
# Das Skript legt einen Deploy Key an, klont das Repository, richtet den
# Scan-Ordner ein und traegt den taeglichen Sync ein. Es ist idempotent -
# ein zweiter Lauf repariert eine unvollstaendige Einrichtung, statt etwas
# doppelt anzulegen.
#
# POSIX-sh, weil viele NAS-Geraete nur Busybox mitbringen.

set -eu

REPO_URL="git@github.com:MarqEwi/SteuerBro.git"
ZWEIG="claude/tax-deduction-optimization-33uzqq"
SCHLUESSEL="$HOME/.ssh/steuerbro"

log()    { echo "  $*"; }
titel()  { echo; echo "--- $* ---"; }
fehler() { echo; echo "FEHLER: $*" >&2; exit 1; }

frage() {
    # frage <text> <standard>
    printf "%s [%s]: " "$1" "$2"
    read -r ANTWORT || ANTWORT=""
    [ -n "$ANTWORT" ] || ANTWORT="$2"
}

echo "================================================================"
echo "  SteuerBro — NAS einrichten"
echo "================================================================"

# ---------------------------------------------------------------------------
titel "1. Voraussetzungen"
# ---------------------------------------------------------------------------
for WERKZEUG in git ssh-keygen; do
    command -v "$WERKZEUG" >/dev/null 2>&1 || fehler "$WERKZEUG fehlt.
  Synology: Paketzentrum -> Git Server installieren.
  QNAP:     App Center -> Git.
  Danach dieses Skript erneut ausfuehren."
done
log "git und ssh-keygen vorhanden."

# ---------------------------------------------------------------------------
titel "2. Wohin soll alles?"
# ---------------------------------------------------------------------------
# Uebliche Wurzelverzeichnisse erkennen, damit niemand raten muss.
for KANDIDAT in /volume1 /share /shares /mnt/HDA_ROOT /data "$HOME"; do
    [ -d "$KANDIDAT" ] && { VORGABE="$KANDIDAT"; break; }
done
: "${VORGABE:=$HOME}"

frage "Verzeichnis fuer das Repository" "$VORGABE/SteuerBro"
REPO="$ANTWORT"
frage "Verzeichnis fuer eingehende Scans" "$VORGABE/scans-steuer"
SCANS="$ANTWORT"

# ---------------------------------------------------------------------------
titel "3. Zugangsschluessel"
# ---------------------------------------------------------------------------
if [ -f "$SCHLUESSEL" ]; then
    log "Schluessel existiert bereits: $SCHLUESSEL"
else
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    ssh-keygen -t ed25519 -N "" -C "steuerbro-nas" -f "$SCHLUESSEL" >/dev/null
    log "Neuen Schluessel erzeugt."
fi

# GitHub ueber diesen Schluessel ansprechen, ohne den globalen SSH-Zugang
# des NAS anzufassen.
KONFIG="$HOME/.ssh/config"
if ! grep -q "Host github-steuerbro" "$KONFIG" 2>/dev/null; then
    cat >> "$KONFIG" <<KONFIGENDE

Host github-steuerbro
    HostName github.com
    User git
    IdentityFile $SCHLUESSEL
    IdentitiesOnly yes
KONFIGENDE
    chmod 600 "$KONFIG"
    log "SSH-Konfiguration ergaenzt."
fi
REPO_URL_SSH=$(echo "$REPO_URL" | sed 's|git@github.com:|git@github-steuerbro:|')

echo
echo "================================================================"
echo "  JETZT BIST DU DRAN — einmalig, dauert eine Minute:"
echo "================================================================"
echo
echo "  1. Oeffne im Browser:"
echo "     https://github.com/MarqEwi/SteuerBro/settings/keys"
echo
echo "  2. 'Add deploy key', Titel z. B. 'NAS'"
echo
echo "  3. HAEKCHEN bei 'Allow write access' setzen."
echo "     Ohne das kann der NAS deine Scans nicht hochladen."
echo
echo "  4. Diesen Schluessel vollstaendig hineinkopieren:"
echo
echo "----------------------------------------------------------------"
cat "$SCHLUESSEL.pub"
echo "----------------------------------------------------------------"
echo
printf "  Fertig? Dann Enter druecken. "
read -r _ || true

# ---------------------------------------------------------------------------
titel "4. Verbindung pruefen"
# ---------------------------------------------------------------------------
# GitHub antwortet auf SSH immer mit Exit-Code 1, auch im Erfolgsfall -
# entscheidend ist der Text.
ANTWORT_SSH=$(ssh -o StrictHostKeyChecking=accept-new -T github-steuerbro 2>&1 || true)
case "$ANTWORT_SSH" in
    *successfully\ authenticated*) log "Verbindung zu GitHub steht." ;;
    *Permission\ denied*) fehler "GitHub weist den Schluessel ab.
  Wurde der Deploy Key wirklich gespeichert? Vollstaendig kopiert,
  inklusive 'ssh-ed25519' am Anfang?" ;;
    *) log "Unklare Antwort von GitHub:"; log "$ANTWORT_SSH"
       printf "  Trotzdem weitermachen? [j/N]: "
       read -r W || W="n"
       case "$W" in j|J|y|Y) ;; *) fehler "Abgebrochen." ;; esac ;;
esac

# ---------------------------------------------------------------------------
titel "5. Repository holen"
# ---------------------------------------------------------------------------
if [ -d "$REPO/.git" ]; then
    log "Repository ist schon da, hole nur den aktuellen Stand."
    (cd "$REPO" && git remote set-url origin "$REPO_URL_SSH" && git fetch --quiet origin "$ZWEIG")
else
    mkdir -p "$(dirname "$REPO")"
    git clone --quiet --branch "$ZWEIG" "$REPO_URL_SSH" "$REPO" \
        || fehler "Klonen fehlgeschlagen. Steht das Repository auf privat und
  hat der Deploy Key Zugriff?"
    log "Repository geklont nach $REPO"
fi
mkdir -p "$SCANS"
log "Scan-Verzeichnis bereit: $SCANS"

# ---------------------------------------------------------------------------
titel "6. Taeglichen Sync einrichten"
# ---------------------------------------------------------------------------
BEFEHL="$REPO/tools/nas-sync.sh $REPO $SCANS"
chmod +x "$REPO/tools/nas-sync.sh" 2>/dev/null || true

CRON_OK=0
if command -v crontab >/dev/null 2>&1; then
    BESTAND=$(crontab -l 2>/dev/null || true)
    if echo "$BESTAND" | grep -qF "nas-sync.sh"; then
        log "Ein Sync-Eintrag existiert bereits, lasse ihn unveraendert."
        CRON_OK=1
    else
        printf "  Taeglichen Eintrag um 3:00 Uhr anlegen? [J/n]: "
        read -r W || W="j"
        case "$W" in
            n|N) log "Uebersprungen." ;;
            *)  { [ -n "$BESTAND" ] && echo "$BESTAND"
                  echo "0 3 * * * $BEFEHL >> $REPO/nas-sync.log 2>&1"
                } | crontab - 2>/dev/null && { log "Eingetragen."; CRON_OK=1; } \
                  || log "crontab liess sich nicht schreiben (auf Synology normal)." ;;
        esac
    fi
fi

if [ "$CRON_OK" -eq 0 ]; then
    echo
    log "Bitte von Hand eintragen:"
    log ""
    log "  Synology: Systemsteuerung -> Aufgabenplaner -> Erstellen"
    log "            -> Geplante Aufgabe -> Benutzerdefiniertes Skript"
    log "            Zeitplan taeglich 3:00 Uhr, als Befehl:"
    log ""
    log "    $BEFEHL"
    log ""
    log "  QNAP / andere: derselbe Befehl per crontab -e"
fi

# ---------------------------------------------------------------------------
titel "7. Testlauf"
# ---------------------------------------------------------------------------
printf "  Sync jetzt einmal testen? [J/n]: "
read -r W || W="j"
case "$W" in
    n|N) log "Uebersprungen." ;;
    *)   echo; sh "$REPO/tools/nas-sync.sh" "$REPO" "$SCANS" || fehler "Testlauf fehlgeschlagen." ;;
esac

echo
echo "================================================================"
echo "  Fertig."
echo "================================================================"
echo
echo "  Ab jetzt ist dein einziger Handgriff:"
echo "  Rechnung scannen oder fotografieren -> $SCANS"
echo
echo "  Alles Weitere passiert von allein. Beim naechsten Gespraech"
echo "  liegen die Belege im Eingang und werden abgearbeitet."
echo
