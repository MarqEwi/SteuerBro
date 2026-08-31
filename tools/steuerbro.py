#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SteuerBro - Beleg-Einordnung und Zuordnungs-Optimierung.

Beantwortet die Frage: "Ich habe X gekauft und nutze es fuer mehreres.
Wo setze ich es an, damit netto am meisten bei mir haengen bleibt?"

Das Tool rechnet den tatsaechlichen Euro-Vorteil pro Topf aus - inklusive
Vorsteuer, Pauschbetraegen, Hoechstbetraegen und Verlustvortrag - und
verteilt den Betrag optimal INNERHALB der Nutzungsbandbreite, die du
angibst. Es erfindet keine Nutzung. Es holt aus der Nutzung, die du hast,
das Maximum heraus.

Keine externen Abhaengigkeiten. Python 3.8+.

Befehle:
    bewerte      Was bringt welcher Topf? Reine Rechnung, ohne Erfassung.
    neu          Beleg erfassen: bewerten, benennen, ablegen, registrieren.
    auswertung   Summen je Topf, Restbudgets, Warnungen.
    pruefe       Plausibilitaet des Registers (Doppelzuordnung, fehlende Dateien).
"""

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFAD_PARAMETER = os.path.join(BASIS, "config", "parameter.json")
PFAD_PROFIL = os.path.join(BASIS, "profil", "profil.json")
PFAD_REGISTER = os.path.join(BASIS, "register", "belege.csv")
PFAD_BELEGE = os.path.join(BASIS, "belege")
PFAD_EINGANG = os.path.join(PFAD_BELEGE, "_eingang")

FELDER = [
    "id", "datum", "haendler", "beschreibung", "brutto", "ust_satz", "netto",
    "kategorie", "topf", "objekt", "anteil_prozent", "betrag_zugeordnet",
    "vorteil_geschaetzt", "bandbreiten", "begruendung", "dateiname", "zahlungsart",
    "status", "erfasst_am",
]

# Topf-Kuerzel -> Klartext
TOEPFE = {
    "GEW":  "Nebengewerbe (Betriebsausgabe)",
    "VUV":  "Vermietung und Verpachtung (Werbungskosten)",
    "AN":   "Arbeitnehmer / Bundeswehr (Werbungskosten)",
    "FOB":  "Fortbildung / Studium",
    "P35A": "Handwerkerleistung eigener Haushalt (Paragraf 35a)",
    "PRIV": "Privat, nicht absetzbar",
}


# --------------------------------------------------------------------------
# Laden
# --------------------------------------------------------------------------

def _lade_json(pfad, was):
    if not os.path.exists(pfad):
        sys.exit("FEHLER: %s nicht gefunden unter %s" % (was, pfad))
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def lade_kontext():
    param = _lade_json(PFAD_PARAMETER, "Parameterdatei")
    profil = _lade_json(PFAD_PROFIL, "Profildatei")
    warnungen = []

    roh = json.dumps(profil, ensure_ascii=False)
    if "TODO" in roh:
        warnungen.append(
            "Dein Profil enthaelt noch TODO-Platzhalter. Die Empfehlungen "
            "rechnen mit Annahmen und koennen deutlich danebenliegen. "
            "Bitte profil/profil.json ausfuellen."
        )
    return param, profil, warnungen


def effektiver_steuersatz(profil, satz=None):
    """ESt-Grenzsteuersatz inklusive Soli und Kirchensteuer."""
    s = satz if satz is not None else profil["grenzsteuersatz"]["aktuell"]
    zuschlag = 0.0
    if profil.get("soli_faellig"):
        zuschlag += 0.055
    kirche = profil.get("kirchensteuer", {})
    if kirche.get("faellig"):
        zuschlag += kirche.get("satz", 0.09)
    return s * (1.0 + zuschlag)


# --------------------------------------------------------------------------
# Register
# --------------------------------------------------------------------------

def lade_register():
    if not os.path.exists(PFAD_REGISTER):
        return []
    with open(PFAD_REGISTER, "r", encoding="utf-8", newline="") as f:
        return [z for z in csv.DictReader(f, delimiter=";")
                if z.get("id") and not z["id"].startswith("#")]


def schreibe_register(zeilen):
    os.makedirs(os.path.dirname(PFAD_REGISTER), exist_ok=True)
    with open(PFAD_REGISTER, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FELDER, delimiter=";")
        w.writeheader()
        for z in zeilen:
            w.writerow({k: z.get(k, "") for k in FELDER})


def _f(wert, standard=0.0):
    try:
        return float(str(wert).replace(",", "."))
    except (TypeError, ValueError):
        return standard


def verbrauch_im_jahr(zeilen, jahr):
    """Wie viel ist je Topf in diesem Jahr schon zugeordnet?

    Entscheidet ueber Pauschbetraege und Hoechstbetraege - und damit
    darueber, ob der naechste Euro in einem Topf ueberhaupt noch wirkt.
    """
    summe = {k: 0.0 for k in TOEPFE}
    for z in zeilen:
        if not str(z.get("datum", "")).startswith(str(jahr)):
            continue
        topf = z.get("topf", "")
        if topf in summe:
            summe[topf] += _f(z.get("betrag_zugeordnet"))
    return summe


def naechste_id(zeilen, jahr):
    hoechste = 0
    muster = re.compile(r"^B-%s-(\d+)$" % jahr)
    for z in zeilen:
        treffer = muster.match(z.get("id", ""))
        if treffer:
            hoechste = max(hoechste, int(treffer.group(1)))
    return "B-%s-%04d" % (jahr, hoechste + 1)


# --------------------------------------------------------------------------
# Bewertung: was bringt der naechste Euro in diesem Topf?
# --------------------------------------------------------------------------

def grenzvorteil(topf, param, profil, verbraucht, ust_satz, lohnanteil_quote=0.0):
    """Vorteil in Euro pro 1 EUR BRUTTO-Ausgabe in diesem Topf.

    Gibt (vorteil_pro_euro, erlaeuterung) zurueck. Beruecksichtigt, was in
    diesem Topf im laufenden Jahr schon verbraucht ist - deshalb ist der
    Wert ein GRENZ-, kein Durchschnittsvorteil.
    """
    est = effektiver_steuersatz(profil)

    if topf == "GEW":
        if not profil.get("gewerbe", {}).get("aktiv"):
            return 0.0, "Kein Gewerbe im Profil hinterlegt."
        if profil["gewerbe"].get("regelbesteuert"):
            netto_quote = 1.0 / (1.0 + ust_satz)
            vorsteuer_quote = ust_satz / (1.0 + ust_satz)
            v = vorsteuer_quote + netto_quote * est
            return v, ("Vorsteuer %.1f %% sofort zurueck, zusaetzlich %.1f %% "
                       "Steuerersparnis auf den Nettobetrag."
                       % (vorsteuer_quote * 100, est * 100))
        return est, ("Kleinunternehmer: keine Vorsteuer, dafuer ist der volle "
                     "Bruttobetrag Betriebsausgabe.")

    if topf == "VUV":
        return est, ("Werbungskosten bei Vermietung. Kein Vorsteuerabzug, da "
                     "Wohnraumvermietung umsatzsteuerfrei ist - der Bruttobetrag "
                     "wirkt aber voll.")

    if topf == "AN":
        if not profil.get("arbeitnehmer", {}).get("aktiv"):
            return 0.0, "Keine nichtselbstaendige Taetigkeit im Profil."
        pausch = param["arbeitnehmer_pauschbetrag"]["betrag"]
        schon = verbraucht.get("AN", 0.0) + verbraucht.get("FOB_AN", 0.0)
        if schon < pausch:
            return 0.0, ("WIRKUNGSLOS: Der Arbeitnehmer-Pauschbetrag von "
                         "%d EUR ist noch nicht ausgeschoepft (bisher %.0f EUR). "
                         "Diese Kosten bekommst du ohnehin pauschal - sie "
                         "bringen keinen einzigen Euro zusaetzlich."
                         % (pausch, schon))
        return est, ("Pauschbetrag von %d EUR ist ueberschritten, jeder "
                     "weitere Euro wirkt mit %.1f %%." % (pausch, est * 100))

    if topf == "FOB":
        aus = profil.get("ausbildung", {})
        if not aus.get("aktiv"):
            return 0.0, "Keine Ausbildung/Fortbildung im Profil."

        if aus.get("typ") == "erstausbildung":
            if aus.get("zve_voraussichtlich_null"):
                return 0.0, ("WERTLOS: Erstausbildungskosten sind nur "
                             "Sonderausgaben. Sonderausgaben sind nicht "
                             "vortragsfaehig und verfallen bei zu versteuerndem "
                             "Einkommen von null ersatzlos.")
            hoechst = param["sonderausgaben_erstausbildung"]["hoechstbetrag"]
            schon = verbraucht.get("FOB", 0.0)
            if schon >= hoechst:
                return 0.0, ("Hoechstbetrag fuer Sonderausgaben (%d EUR) ist "
                             "bereits ausgeschoepft." % hoechst)
            return est, ("Sonderausgabe, wirksam bis zum Hoechstbetrag von "
                         "%d EUR (noch %.0f EUR frei)." % (hoechst, hoechst - schon))

        # Zweitausbildung / Fortbildung -> Werbungskosten
        if aus.get("zve_voraussichtlich_null"):
            kuenftig = effektiver_steuersatz(
                profil, profil["grenzsteuersatz"].get("erwartet_kuenftig", 0.42))
            barwert = kuenftig * 0.92   # grober Abschlag fuer Wartezeit
            return barwert, ("Werbungskosten ohne laufendes Einkommen -> "
                             "Verlustvortrag. Wirkt spaeter mit rund %.1f %%, "
                             "hier mit einem Abschlag fuer die Wartezeit "
                             "bewertet." % (kuenftig * 100))

        if aus.get("zugehoerige_einkunftsart") == "gewerbe":
            return grenzvorteil("GEW", param, profil, verbraucht, ust_satz)

        # Gehoert zu den Arbeitnehmer-Einkuenften -> teilt sich den Pauschbetrag
        pausch = param["arbeitnehmer_pauschbetrag"]["betrag"]
        schon = verbraucht.get("AN", 0.0) + verbraucht.get("FOB", 0.0)
        if schon < pausch:
            return 0.0, ("WIRKUNGSLOS: Fortbildungskosten zaehlen hier zu den "
                         "Arbeitnehmer-Werbungskosten und teilen sich den "
                         "Pauschbetrag von %d EUR (bisher %.0f EUR verbraucht)."
                         % (pausch, schon))
        return est, ("Fortbildung als Werbungskosten, Pauschbetrag bereits "
                     "ueberschritten - wirkt voll mit %.1f %%." % (est * 100))

    if topf == "P35A":
        if not profil.get("selbstgenutzte_immobilie", {}).get("vorhanden"):
            return 0.0, "Keine selbstgenutzte Immobilie im Profil."
        if lohnanteil_quote <= 0:
            return 0.0, ("Paragraf 35a beguenstigt NUR Lohn-, Fahrt- und "
                         "Maschinenkosten. Reines Material bringt null. Gib den "
                         "Lohnanteil mit --lohnanteil an.")
        p = param["paragraf_35a"]
        rest = p["handwerkerleistung_hoechstbetrag"] - verbraucht.get("P35A", 0.0) * p["handwerkerleistung_satz"]
        if rest <= 0:
            return 0.0, ("Hoechstbetrag nach Paragraf 35a (%d EUR Steuerabzug) "
                         "ist bereits ausgeschoepft."
                         % p["handwerkerleistung_hoechstbetrag"])
        return p["handwerkerleistung_satz"] * lohnanteil_quote, (
            "20 %% des Lohnanteils werden DIREKT von der Steuerschuld "
            "abgezogen - nicht vom Einkommen. Nur der Lohnanteil zaehlt "
            "(hier %.0f %% angesetzt), Material nie. Zwingend per Ueberweisung "
            "zahlen." % (lohnanteil_quote * 100))

    return 0.0, "Nicht absetzbar."


# --------------------------------------------------------------------------
# Optimierer
# --------------------------------------------------------------------------

def optimiere(brutto, bandbreiten, param, profil, verbraucht, ust_satz,
              lohnanteil_quote=0.0, schritte=200):
    """Verteilt den Betrag optimal innerhalb der angegebenen Bandbreiten.

    bandbreiten: {"GEW": (0.4, 0.6), "FOB": (0.2, 0.4), ...}
    Die Untergrenzen werden zuerst bedient (das ist die Nutzung, die du
    ohnehin hast). Der verbleibende Spielraum geht schrittweise an den
    Topf mit dem hoechsten GRENZvorteil - so werden Pauschbetraege und
    Hoechstbetraege korrekt beruecksichtigt.
    """
    summe_min = sum(b[0] for b in bandbreiten.values())
    if summe_min > 1.0001:
        sys.exit("FEHLER: Die Untergrenzen ergeben %.0f %% - das ist mehr als "
                 "100 %%. Bitte Bandbreiten korrigieren." % (summe_min * 100))
    if sum(b[1] for b in bandbreiten.values()) < 0.9999:
        sys.exit("FEHLER: Die Obergrenzen ergeben zusammen weniger als 100 %%. "
                 "Der Beleg liesse sich nicht vollstaendig zuordnen.")

    lokal = dict(verbraucht)
    quote = {t: b[0] for t, b in bandbreiten.items()}
    for topf, q in quote.items():
        lokal[topf] = lokal.get(topf, 0.0) + brutto * q

    rest = 1.0 - summe_min
    inkrement = rest / schritte if schritte else 0.0

    for _ in range(schritte):
        bester, bester_wert = None, 0.0
        for topf, (_lo, hi) in bandbreiten.items():
            if quote[topf] + inkrement > hi + 1e-9:
                continue
            wert, _ = grenzvorteil(topf, param, profil, lokal, ust_satz,
                                   lohnanteil_quote)
            if wert > bester_wert + 1e-12:
                bester, bester_wert = topf, wert
        if bester is None:
            # Kein Topf bringt noch etwas -> Rest an den mit dem meisten
            # Luft, damit die Zuordnung vollstaendig bleibt.
            for topf, (_lo, hi) in bandbreiten.items():
                if quote[topf] + inkrement <= hi + 1e-9:
                    bester = topf
                    break
            if bester is None:
                break
        quote[bester] += inkrement
        lokal[bester] = lokal.get(bester, 0.0) + brutto * inkrement

    return {t: q for t, q in quote.items() if q > 1e-6}


def gesamtvorteil(brutto, quote, param, profil, verbraucht, ust_satz,
                  lohnanteil_quote=0.0):
    """Rechnet den Euro-Vorteil einer konkreten Aufteilung nach."""
    lokal = dict(verbraucht)
    gesamt = 0.0
    detail = {}
    # In kleinen Schritten, damit Pauschbetrags-Schwellen sauber greifen.
    for topf, q in sorted(quote.items(), key=lambda kv: -kv[1]):
        betrag = brutto * q
        teil, n = 0.0, 40
        for _ in range(n):
            v, _ = grenzvorteil(topf, param, profil, lokal, ust_satz,
                                lohnanteil_quote)
            teil += v * betrag / n
            lokal[topf] = lokal.get(topf, 0.0) + betrag / n
        detail[topf] = teil
        gesamt += teil
    return gesamt, detail


# --------------------------------------------------------------------------
# Dateinamen
# --------------------------------------------------------------------------

def entschaerfe(text, maxlen=40):
    text = unicodedata.normalize("NFKD", str(text))
    ersatz = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
              "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
    for a, b in ersatz.items():
        text = text.replace(a, b)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")
    return text[:maxlen].strip("-")


def dateiname(datum, topf, objekt, kategorie, haendler, beschreibung,
              brutto, beleg_id, endung=".pdf"):
    """Ein Name, der sortierbar, suchbar und selbsterklaerend ist.

    2026-03-14__GEW__Arbeitsmittel__Notebooksbilliger__Laptop-T14__1499-00EUR__B-2026-0042.pdf
    """
    topf_teil = "%s-%s" % (topf, entschaerfe(objekt, 16)) if objekt else topf
    return "__".join([
        datum,
        topf_teil,
        entschaerfe(kategorie, 24),
        entschaerfe(haendler, 24),
        entschaerfe(beschreibung, 40),
        ("%.2f" % brutto).replace(".", "-") + "EUR",
        beleg_id,
    ]) + endung


def zielordner(jahr, topf, objekt=""):
    unter = {"GEW": "01-gewerbe", "VUV": "02-vermietung",
             "AN": "03-bundeswehr", "FOB": "04-studium-fortbildung",
             "P35A": "05-paragraf-35a", "PRIV": "06-privat"}.get(topf, "99-unklar")
    teile = [PFAD_BELEGE, str(jahr), unter]
    if topf == "VUV" and objekt:
        teile.append(entschaerfe(objekt, 20))
    return os.path.join(*teile)


# --------------------------------------------------------------------------
# Ausgabe
# --------------------------------------------------------------------------

def bandbreiten_parsen(text):
    """'gew=40-60,fob=20-40,an=10-30' -> {"GEW": (0.4,0.6), ...}"""
    ergebnis = {}
    for teil in text.split(","):
        teil = teil.strip()
        if not teil:
            continue
        if "=" not in teil:
            sys.exit("FEHLER: '%s' - erwartet wird TOPF=min-max, z.B. GEW=40-60" % teil)
        topf, spanne = teil.split("=", 1)
        topf = topf.strip().upper()
        if topf not in TOEPFE:
            sys.exit("FEHLER: Unbekannter Topf '%s'. Erlaubt: %s"
                     % (topf, ", ".join(TOEPFE)))
        if "-" in spanne:
            lo, hi = spanne.split("-", 1)
        else:
            lo = hi = spanne
        ergebnis[topf] = (float(lo) / 100.0, float(hi) / 100.0)
    if not ergebnis:
        sys.exit("FEHLER: Keine Bandbreiten angegeben.")
    return ergebnis


def zeige_bewertung(brutto, ust_satz, bandbreiten, param, profil, verbraucht,
                    lohnanteil_quote):
    netto = brutto / (1.0 + ust_satz)
    print("=" * 72)
    print("BELEG: %.2f EUR brutto (%.2f netto, %.2f EUR USt bei %.0f %%)"
          % (brutto, netto, brutto - netto, ust_satz * 100))
    print("=" * 72)

    print("\nWAS JEDER TOPF PRO EURO BRINGT (beim aktuellen Stand des Jahres):\n")
    einzeln = []
    for topf in bandbreiten:
        v, erl = grenzvorteil(topf, param, profil, verbraucht, ust_satz,
                              lohnanteil_quote)
        einzeln.append((v, topf, erl))
    for v, topf, erl in sorted(einzeln, reverse=True):
        print("  %-5s %6.1f Cent/EUR   %s" % (topf, v * 100, TOEPFE[topf]))
        for zeile in _umbruch(erl, 62):
            print("        %s" % zeile)
        print()

    quote = optimiere(brutto, bandbreiten, param, profil, verbraucht,
                      ust_satz, lohnanteil_quote)
    vorteil, detail = gesamtvorteil(brutto, quote, param, profil, verbraucht,
                                    ust_satz, lohnanteil_quote)

    print("-" * 72)
    print("EMPFOHLENE AUFTEILUNG (Maximum innerhalb DEINER Bandbreiten):\n")
    for topf, q in sorted(quote.items(), key=lambda kv: -kv[1]):
        lo, hi = bandbreiten[topf]
        marke = "  <- Obergrenze deiner Bandbreite" if q >= hi - 1e-6 else ""
        print("  %-5s %5.1f %%   %8.2f EUR   Vorteil %7.2f EUR%s"
              % (topf, q * 100, brutto * q, detail.get(topf, 0.0), marke))
    print("\n  ERGEBNIS: %.2f EUR bleiben bei dir. Das sind %.1f %% des Kaufpreises."
          % (vorteil, vorteil / brutto * 100 if brutto else 0))

    # Vergleich: was waere die schlechteste vertretbare Wahl?
    schlecht = _schlechteste_variante(brutto, bandbreiten, param, profil,
                                      verbraucht, ust_satz, lohnanteil_quote)
    if schlecht is not None and vorteil - schlecht > 0.5:
        print("  Die ungeschickteste Zuordnung innerhalb derselben Bandbreiten "
              "braechte nur %.2f EUR." % schlecht)
        print("  DIFFERENZ ALLEIN DURCH DIE ZUORDNUNG: %.2f EUR." % (vorteil - schlecht))
    print("-" * 72)
    return quote, vorteil


def _schlechteste_variante(brutto, bandbreiten, param, profil, verbraucht,
                           ust_satz, lohnanteil_quote):
    """Gegenprobe: wie viel verschenkt man mit der schlechtesten Aufteilung?"""
    invertiert = {}
    lokal = dict(verbraucht)
    quote = {t: b[0] for t, b in bandbreiten.items()}
    rest = 1.0 - sum(quote.values())
    schritte = 100
    ink = rest / schritte if schritte else 0
    for topf, q in quote.items():
        lokal[topf] = lokal.get(topf, 0.0) + brutto * q
    for _ in range(schritte):
        schlechtester, wert_min = None, None
        for topf, (_lo, hi) in bandbreiten.items():
            if quote[topf] + ink > hi + 1e-9:
                continue
            w, _ = grenzvorteil(topf, param, profil, lokal, ust_satz,
                                lohnanteil_quote)
            if wert_min is None or w < wert_min:
                schlechtester, wert_min = topf, w
        if schlechtester is None:
            break
        quote[schlechtester] += ink
        lokal[schlechtester] = lokal.get(schlechtester, 0.0) + brutto * ink
    invertiert = {t: q for t, q in quote.items() if q > 1e-6}
    v, _ = gesamtvorteil(brutto, invertiert, param, profil, verbraucht,
                         ust_satz, lohnanteil_quote)
    return v


def _umbruch(text, breite):
    worte, zeilen, aktuell = text.split(), [], ""
    for w in worte:
        if len(aktuell) + len(w) + 1 > breite:
            zeilen.append(aktuell)
            aktuell = w
        else:
            aktuell = (aktuell + " " + w).strip()
    if aktuell:
        zeilen.append(aktuell)
    return zeilen


def warnungen_zum_beleg(brutto, netto, kategorie, param, profil, quote):
    """Kontextabhaengige Hinweise auf Fallstricke."""
    hinweise = []
    kat = kategorie.lower()

    # Abschreibung betrifft nur angeschaffte Wirtschaftsgueter. Eine
    # Dienstleistung wird immer sofort abgezogen, egal wie teuer sie ist.
    dienstleistung = (
        "P35A" in quote
        or any(w in kat for w in (
            "handwerk", "dienstleist", "reparatur", "wartung", "montage",
            "miete", "gebuehr", "gebuhr", "beitrag", "seminar", "kurs",
            "reise", "fahrt", "porto", "versicherung", "beratung",
            "reinigung", "strom", "telefon", "internet"))
    )

    if netto > param["gwg"]["grenze_netto"] and not dienstleistung:
        if any(w in kat for w in ("laptop", "computer", "notebook", "pc",
                                  "monitor", "software", "tablet", "hardware")):
            hinweise.append(
                "ueber der GWG-Grenze von %d EUR netto - ABER: Computerhardware "
                "und Software duerfen mit 1 Jahr Nutzungsdauer angesetzt werden "
                "(BMF 22.02.2022). Damit ist der Betrag im Anschaffungsjahr "
                "trotzdem sofort voll abziehbar."
                % param["gwg"]["grenze_netto"])
        else:
            hinweise.append(
                "ueber der GWG-Grenze von %d EUR netto: NICHT sofort abziehbar, "
                "sondern ueber die Nutzungsdauer abzuschreiben. Der Vorteil "
                "verteilt sich dann auf mehrere Jahre."
                % param["gwg"]["grenze_netto"])

    if "VUV" in quote:
        objekte = profil.get("immobilien", [])
        for obj in objekte:
            ak = _f(obj.get("gebaeude_ak_netto"))
            datum_ak = str(obj.get("anschaffung_datum", ""))
            if ak > 0 and re.match(r"^\d{4}-\d{2}-\d{2}$", datum_ak):
                jahre = (date.today() - datetime.strptime(datum_ak, "%Y-%m-%d").date()).days / 365.25
                if jahre <= param["anschaffungsnaher_herstellungsaufwand"]["zeitraum_jahre"]:
                    grenze = ak * param["anschaffungsnaher_herstellungsaufwand"]["grenze_anteil_gebaeude_ak"]
                    hinweise.append(
                        "ACHTUNG anschaffungsnaher Herstellungsaufwand bei %s: "
                        "Objekt ist erst %.1f Jahre in deinem Besitz. Sobald die "
                        "Instandsetzungskosten binnen 3 Jahren %.0f EUR (15 %% der "
                        "Gebaeude-AK) uebersteigen, sind sie ZWINGEND zu aktivieren "
                        "und nur ueber ~50 Jahre abschreibbar. Groessere Massnahmen "
                        "wenn moeglich hinter diese Frist legen."
                        % (obj.get("kuerzel", "?"), jahre, grenze))

    if "P35A" in quote:
        hinweise.append(
            "Paragraf 35a nur bei UEBERWEISUNG - Barzahlung wird ausnahmslos "
            "nicht anerkannt. Die Rechnung muss Lohn- und Materialanteil "
            "getrennt ausweisen. Falls nicht: beim Handwerker eine "
            "aufgeschluesselte Rechnung nachfordern.")

    if "GEW" in quote and profil.get("gewerbe", {}).get("regelbesteuert"):
        hinweise.append(
            "Fuer den Vorsteuerabzug muss die Rechnung ALLE Pflichtangaben nach "
            "Paragraf 14 UStG enthalten - ab 250 EUR brutto zwingend mit deinem "
            "Namen und deiner Anschrift als Leistungsempfaenger. Ein Kassenbon "
            "ohne Adressat kostet dich den Vorsteuerabzug.")

    if "GEW" in quote and quote["GEW"] < 0.10:
        hinweise.append(
            "Betrieblicher Nutzungsanteil unter 10 %%: Eine Zuordnung zum "
            "Betriebsvermoegen und der volle Vorsteuerabzug sind dann nicht "
            "moeglich.")

    return hinweise


# --------------------------------------------------------------------------
# Befehle
# --------------------------------------------------------------------------

def befehl_bewerte(args):
    param, profil, warn = lade_kontext()
    for w in warn:
        print("[HINWEIS] %s\n" % w)
    zeilen = lade_register()
    jahr = args.jahr or profil.get("steuerjahr", date.today().year)
    verbraucht = verbrauch_im_jahr(zeilen, jahr)
    bandbreiten = bandbreiten_parsen(args.anteile)
    ust = args.ust / 100.0 if args.ust is not None else param["umsatzsteuer"]["regelsatz"]

    quote, _ = zeige_bewertung(args.brutto, ust, bandbreiten, param, profil,
                               verbraucht, args.lohnanteil / 100.0)

    hinweise = warnungen_zum_beleg(args.brutto, args.brutto / (1 + ust),
                                   args.kategorie or "", param, profil, quote)
    if hinweise:
        print("\nFALLSTRICKE ZU DIESEM BELEG:\n")
        for h in hinweise:
            for i, zeile in enumerate(_umbruch(h, 66)):
                print("  %s %s" % ("*" if i == 0 else " ", zeile))
            print()


def befehl_neu(args):
    param, profil, warn = lade_kontext()
    for w in warn:
        print("[HINWEIS] %s\n" % w)
    zeilen = lade_register()
    jahr = int(args.datum[:4])
    verbraucht = verbrauch_im_jahr(zeilen, jahr)
    bandbreiten = bandbreiten_parsen(args.anteile)
    ust = args.ust / 100.0 if args.ust is not None else param["umsatzsteuer"]["regelsatz"]

    quote, vorteil = zeige_bewertung(args.brutto, ust, bandbreiten, param,
                                     profil, verbraucht, args.lohnanteil / 100.0)
    _, detail = gesamtvorteil(args.brutto, quote, param, profil, verbraucht,
                              ust, args.lohnanteil / 100.0)

    hinweise = warnungen_zum_beleg(args.brutto, args.brutto / (1 + ust),
                                   args.kategorie or "", param, profil, quote)
    if hinweise:
        print("\nFALLSTRICKE ZU DIESEM BELEG:\n")
        for h in hinweise:
            for i, zeile in enumerate(_umbruch(h, 66)):
                print("  %s %s" % ("*" if i == 0 else " ", zeile))
            print()

    beleg_id = naechste_id(zeilen, jahr)
    haupttopf = max(quote, key=quote.get)
    endung = os.path.splitext(args.datei)[1] if args.datei else ".pdf"
    name = dateiname(args.datum, haupttopf, args.objekt, args.kategorie,
                     args.haendler, args.beschreibung, args.brutto,
                     beleg_id, endung)
    ordner = zielordner(jahr, haupttopf, args.objekt)
    ziel = os.path.join(ordner, name)

    print("\nABLAGE:")
    print("  Datei:  %s" % name)
    print("  Ordner: %s" % os.path.relpath(ordner, BASIS))

    if args.trocken:
        print("\n[TROCKENLAUF] Nichts geschrieben, nichts verschoben.")
        return

    os.makedirs(ordner, exist_ok=True)
    if args.datei:
        if not os.path.exists(args.datei):
            sys.exit("FEHLER: Datei nicht gefunden: %s" % args.datei)
        os.replace(args.datei, ziel)
        print("  -> verschoben nach %s" % os.path.relpath(ziel, BASIS))
    else:
        print("  -> keine Datei angegeben (--datei), nur Registereintrag.")

    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M")
    for topf, q in sorted(quote.items(), key=lambda kv: -kv[1]):
        zeilen.append({
            "id": beleg_id,
            "datum": args.datum,
            "haendler": args.haendler,
            "beschreibung": args.beschreibung,
            "brutto": "%.2f" % args.brutto,
            "ust_satz": "%.2f" % ust,
            "netto": "%.2f" % (args.brutto / (1 + ust)),
            "kategorie": args.kategorie,
            "topf": topf,
            "objekt": args.objekt if topf == "VUV" else "",
            "anteil_prozent": "%.1f" % (q * 100),
            "betrag_zugeordnet": "%.2f" % (args.brutto * q),
            "vorteil_geschaetzt": "%.2f" % detail.get(topf, 0.0),
            "bandbreiten": args.anteile,
            "begruendung": args.begruendung,
            "dateiname": name,
            "zahlungsart": args.zahlungsart,
            "status": "erfasst",
            "erfasst_am": jetzt,
        })
    schreibe_register(zeilen)
    print("  -> %d Zeile(n) im Register unter %s" % (len(quote), beleg_id))

    if not args.begruendung:
        print("\n  [WICHTIG] Du hast keine --begruendung angegeben. Genau die "
              "brauchst du in zwei Jahren, wenn jemand fragt, warum der "
              "Nutzungsanteil so gewaehlt wurde. Bitte im Register nachtragen.")


def befehl_auswertung(args):
    param, profil, _ = lade_kontext()
    zeilen = lade_register()
    jahr = args.jahr or profil.get("steuerjahr", date.today().year)
    verbraucht = verbrauch_im_jahr(zeilen, jahr)

    print("=" * 72)
    print("AUSWERTUNG %s" % jahr)
    print("=" * 72)

    gesamt_aufwand = sum(verbraucht.values())
    gesamt_vorteil = sum(_f(z.get("vorteil_geschaetzt"))
                         for z in zeilen if str(z.get("datum", "")).startswith(str(jahr)))
    anzahl = len({z["id"] for z in zeilen if str(z.get("datum", "")).startswith(str(jahr))})

    print("\n  %d Belege erfasst, %.2f EUR zugeordnet, davon geschaetzt "
          "%.2f EUR Steuervorteil.\n" % (anzahl, gesamt_aufwand, gesamt_vorteil))

    print("  ZUORDNUNG JE TOPF:\n")
    for topf, betrag in sorted(verbraucht.items(), key=lambda kv: -kv[1]):
        if betrag <= 0:
            continue
        print("    %-5s %10.2f EUR   %s" % (topf, betrag, TOEPFE[topf]))

    print("\n  RESTBUDGETS UND SCHWELLEN:\n")
    pausch = param["arbeitnehmer_pauschbetrag"]["betrag"]
    an_summe = verbraucht.get("AN", 0.0)
    aus = profil.get("ausbildung", {})
    if aus.get("typ") != "erstausbildung" and aus.get("zugehoerige_einkunftsart") == "arbeitnehmer":
        an_summe += verbraucht.get("FOB", 0.0)
    if an_summe < pausch:
        print("    Arbeitnehmer-Pauschbetrag: %.2f von %d EUR verbraucht."
              % (an_summe, pausch))
        print("      -> Die naechsten %.2f EUR in AN/FOB bringen NICHTS."
              % (pausch - an_summe))
        print("      -> Alles, was auch in einen anderen Topf passt, gehoert\n             in den anderen Topf.")
    else:
        print("    Arbeitnehmer-Pauschbetrag mit %.2f EUR UEBERSCHRITTEN."
              % an_summe)
        print("      -> Ab jetzt wirkt jeder weitere Euro dort voll. Jetzt "
              "lohnt es sich, Restbelege in diesen Topf zu legen.")

    p35 = param["paragraf_35a"]
    genutzt = verbraucht.get("P35A", 0.0) * p35["handwerkerleistung_satz"]
    print("    Paragraf 35a Handwerker: %.2f von %d EUR Steuerabzug genutzt "
          "(noch %.2f EUR frei)."
          % (genutzt, p35["handwerkerleistung_hoechstbetrag"],
             max(0.0, p35["handwerkerleistung_hoechstbetrag"] - genutzt)))

    if aus.get("typ") == "erstausbildung":
        h = param["sonderausgaben_erstausbildung"]["hoechstbetrag"]
        print("    Sonderausgaben Erstausbildung: %.2f von %d EUR."
              % (verbraucht.get("FOB", 0.0), h))

    priv = verbraucht.get("PRIV", 0.0)
    if priv > 0:
        print("\n  %.2f EUR sind als privat erfasst. Pruefe, ob davon etwas "
              "unter Paragraf 35a faellt - das ist der am haeufigsten "
              "uebersehene Topf." % priv)
    print()


def befehl_pruefe(_args):
    param, profil, warn = lade_kontext()
    zeilen = lade_register()
    fehler, hinweise = [], list(warn)

    nach_id = {}
    for z in zeilen:
        nach_id.setdefault(z["id"], []).append(z)

    for beleg_id, gruppe in sorted(nach_id.items()):
        summe = sum(_f(z.get("anteil_prozent")) for z in gruppe)
        if summe > 100.5:
            fehler.append(
                "%s: Die Anteile ergeben %.1f %%. Das waere eine Mehrfach"
                "absetzung desselben Belegs - unbedingt korrigieren."
                % (beleg_id, summe))
        elif summe < 99.5:
            hinweise.append(
                "%s: Nur %.1f %% zugeordnet. %.1f %% sind noch offen - "
                "moeglicherweise verschenkt." % (beleg_id, summe, 100 - summe))

        bruttos = {z.get("brutto") for z in gruppe}
        if len(bruttos) > 1:
            fehler.append("%s: uneinheitlicher Bruttobetrag %s" % (beleg_id, bruttos))

        for z in gruppe:
            if not z.get("begruendung", "").strip() and z.get("topf") != "PRIV":
                hinweise.append(
                    "%s (%s): keine Begruendung hinterlegt. Bei Rueckfragen "
                    "des Finanzamts ist genau das der Punkt, an dem eine "
                    "Zuordnung faellt." % (beleg_id, z.get("topf")))
                break

        name = gruppe[0].get("dateiname", "")
        if name:
            gefunden = False
            for wurzel, _d, dateien in os.walk(PFAD_BELEGE):
                if name in dateien:
                    gefunden = True
                    break
            if not gefunden:
                fehler.append("%s: Belegdatei '%s' liegt nirgends unter belege/. "
                              "Ohne Beleg keine Anerkennung." % (beleg_id, name))

    if os.path.isdir(PFAD_EINGANG):
        offen = [d for d in os.listdir(PFAD_EINGANG) if not d.startswith(".")]
        if offen:
            hinweise.append("%d Datei(en) liegen unbearbeitet in belege/_eingang/: %s"
                            % (len(offen), ", ".join(offen[:5])))

    print("=" * 72)
    print("PRUEFUNG: %d Belege, %d Registerzeilen" % (len(nach_id), len(zeilen)))
    print("=" * 72)
    if fehler:
        print("\nFEHLER (muessen behoben werden):\n")
        for f in fehler:
            for i, zeile in enumerate(_umbruch(f, 66)):
                print("  %s %s" % ("!" if i == 0 else " ", zeile))
    if hinweise:
        print("\nHINWEISE:\n")
        for h in hinweise:
            for i, zeile in enumerate(_umbruch(h, 66)):
                print("  %s %s" % ("-" if i == 0 else " ", zeile))
    if not fehler and not hinweise:
        print("\n  Alles sauber.")
    print()
    return 1 if fehler else 0



# --------------------------------------------------------------------------
# Jahressicht: globale Neuverteilung ueber alle Belege
# --------------------------------------------------------------------------

def _szenario(belege, param, profil, vorab=None):
    """Verteilt die freien Anteile ALLER Belege global.

    vorab: Liste von Toepfen, die zuerst bis zu ihrer Obergrenze gefuellt
    werden. Damit laesst sich gezielt eine Schwelle (Pauschbetrag)
    ueberspringen, die ein rein gieriges Verfahren nie erreichen wuerde.
    """
    verbraucht = {k: 0.0 for k in TOEPFE}
    quoten = []
    for b in belege:
        q = {t: bb[0] for t, bb in b["bandbreiten"].items()}
        for t, v in q.items():
            verbraucht[t] = verbraucht.get(t, 0.0) + b["brutto"] * v
        quoten.append(q)

    def fuellen(nur=None, schritte=400):
        gesamt_frei = sum(
            b["brutto"] * (1.0 - sum(quoten[i].values()))
            for i, b in enumerate(belege))
        if gesamt_frei <= 0.01:
            return
        ink_eur = gesamt_frei / schritte
        for _ in range(schritte):
            bester, bester_wert = None, 0.0
            for i, b in enumerate(belege):
                offen = 1.0 - sum(quoten[i].values())
                if offen * b["brutto"] < ink_eur - 1e-9:
                    continue
                for t, (_lo, hi) in b["bandbreiten"].items():
                    if nur and t not in nur:
                        continue
                    if quoten[i][t] * b["brutto"] + ink_eur > hi * b["brutto"] + 1e-9:
                        continue
                    w, _ = grenzvorteil(t, param, profil, verbraucht,
                                        b["ust"], b["lohnanteil"])
                    if w > bester_wert + 1e-12:
                        bester, bester_wert = (i, t), w
            if bester is None:
                break
            i, t = bester
            quoten[i][t] += ink_eur / belege[i]["brutto"]
            verbraucht[t] = verbraucht.get(t, 0.0) + ink_eur

    if vorab:
        # Schwelle bewusst ansteuern, auch wenn der Grenzvorteil noch 0 ist.
        pausch = param["arbeitnehmer_pauschbetrag"]["betrag"]
        while verbraucht.get("AN", 0.0) + verbraucht.get("FOB", 0.0) < pausch:
            gesetzt = False
            for i, b in enumerate(belege):
                offen = 1.0 - sum(quoten[i].values())
                if offen <= 1e-6:
                    continue
                for t in vorab:
                    if t not in b["bandbreiten"]:
                        continue
                    hi = b["bandbreiten"][t][1]
                    luft = min(hi - quoten[i][t], offen)
                    if luft <= 1e-6:
                        continue
                    quoten[i][t] += luft
                    verbraucht[t] = verbraucht.get(t, 0.0) + b["brutto"] * luft
                    gesetzt = True
                    break
                if gesetzt:
                    break
            if not gesetzt:
                break

    fuellen()

    # Reste, die keinen Vorteil mehr bringen, muessen trotzdem irgendwo hin.
    for i, b in enumerate(belege):
        offen = 1.0 - sum(quoten[i].values())
        if offen > 1e-6:
            for t, (_lo, hi) in b["bandbreiten"].items():
                luft = min(hi - quoten[i][t], offen)
                if luft > 1e-6:
                    quoten[i][t] += luft
                    verbraucht[t] = verbraucht.get(t, 0.0) + b["brutto"] * luft
                    offen -= luft
                if offen <= 1e-6:
                    break

    gesamt = 0.0
    for i, b in enumerate(belege):
        v, _ = gesamtvorteil(b["brutto"], quoten[i], param, profil,
                             {k: 0.0 for k in TOEPFE}, b["ust"], b["lohnanteil"])
        gesamt += v
    # Sauber nachrechnen mit fortlaufendem Verbrauch statt isoliert:
    lauf = {k: 0.0 for k in TOEPFE}
    gesamt = 0.0
    for i, b in enumerate(belege):
        v, _ = gesamtvorteil(b["brutto"], quoten[i], param, profil, lauf,
                             b["ust"], b["lohnanteil"])
        gesamt += v
        for t, q in quoten[i].items():
            lauf[t] = lauf.get(t, 0.0) + b["brutto"] * q
    return gesamt, quoten, verbraucht


def befehl_neuverteilen(args):
    """Optimiert die Zuordnung ueber ALLE Belege eines Jahres gemeinsam.

    Einmal vor der Abgabe laufen lassen. Beleg-fuer-Beleg-Entscheidungen
    sind kurzsichtig: solange der Arbeitnehmer-Pauschbetrag nicht
    ueberschritten ist, sieht jeder einzelne Beleg dort einen Vorteil von
    null - obwohl es sich lohnen kann, ihn gezielt zu ueberspringen.
    """
    param, profil, warn = lade_kontext()
    for w in warn:
        print("[HINWEIS] %s\n" % w)
    zeilen = lade_register()
    jahr = args.jahr or profil.get("steuerjahr", date.today().year)

    gruppen = {}
    for z in zeilen:
        if not str(z.get("datum", "")).startswith(str(jahr)):
            continue
        gruppen.setdefault(z["id"], []).append(z)

    belege = []
    ohne_bandbreite = []
    for beleg_id, gruppe in sorted(gruppen.items()):
        roh = gruppe[0].get("bandbreiten", "").strip()
        if not roh:
            ohne_bandbreite.append(beleg_id)
            continue
        try:
            bb = bandbreiten_parsen(roh)
        except SystemExit:
            ohne_bandbreite.append(beleg_id)
            continue
        belege.append({
            "id": beleg_id,
            "brutto": _f(gruppe[0].get("brutto")),
            "ust": _f(gruppe[0].get("ust_satz"), param["umsatzsteuer"]["regelsatz"]),
            "lohnanteil": 0.0,
            "bandbreiten": bb,
            "beschreibung": gruppe[0].get("beschreibung", ""),
            "aktuell": {z["topf"]: _f(z.get("anteil_prozent")) / 100.0 for z in gruppe},
        })

    if not belege:
        print("Keine Belege mit hinterlegten Bandbreiten fuer %s gefunden." % jahr)
        if ohne_bandbreite:
            print("Ohne Bandbreiten (nicht optimierbar): %s"
                  % ", ".join(ohne_bandbreite))
        return 0

    lauf = {k: 0.0 for k in TOEPFE}
    ist = 0.0
    for b in belege:
        v, _ = gesamtvorteil(b["brutto"], b["aktuell"], param, profil, lauf,
                             b["ust"], b["lohnanteil"])
        ist += v
        for t, q in b["aktuell"].items():
            lauf[t] = lauf.get(t, 0.0) + b["brutto"] * q

    a_wert, a_quoten, a_verbrauch = _szenario(belege, param, profil)
    b_wert, b_quoten, b_verbrauch = _szenario(belege, param, profil,
                                              vorab=["AN", "FOB"])

    if b_wert > a_wert + 0.01:
        wert, quoten, verbrauch, name = b_wert, b_quoten, b_verbrauch, \
            "Pauschbetrag gezielt ueberschritten"
    else:
        wert, quoten, verbrauch, name = a_wert, a_quoten, a_verbrauch, \
            "Pauschbetrag bewusst NICHT angesteuert"

    print("=" * 72)
    print("JAHRESOPTIMIERUNG %s - %d Belege" % (jahr, len(belege)))
    print("=" * 72)
    print("\n  Szenario A (Pauschbetrag ignorieren):        %9.2f EUR" % a_wert)
    print("  Szenario B (Pauschbetrag gezielt reissen):   %9.2f EUR" % b_wert)
    print("  -> gewaehlt: %s\n" % name)
    print("  Aktuelle Zuordnung im Register:  %9.2f EUR" % ist)
    print("  Optimierte Zuordnung:            %9.2f EUR" % wert)
    print("  MEHRERTRAG DURCH UMSCHICHTEN:    %9.2f EUR\n" % (wert - ist))

    # Unter 1 EUR Mehrertrag ist die Differenz reines Rechenrauschen des
    # Schrittverfahrens - dafuer schichtet niemand ein Register um.
    lohnt_sich = (wert - ist) > 1.0

    aenderungen = []
    if lohnt_sich:
        for i, b in enumerate(belege):
            alt, neu_q = b["aktuell"], quoten[i]
            toepfe = set(alt) | set(neu_q)
            if any(abs(alt.get(t, 0.0) - neu_q.get(t, 0.0)) > 0.01 for t in toepfe):
                aenderungen.append((b, alt, neu_q))

    if aenderungen:
        print("  VORGESCHLAGENE UMSCHICHTUNGEN:\n")
        for b, alt, neu_q in aenderungen:
            print("    %s  %s (%.2f EUR)" % (b["id"], b["beschreibung"][:34], b["brutto"]))
            for t in sorted(set(alt) | set(neu_q)):
                a, n = alt.get(t, 0.0) * 100, neu_q.get(t, 0.0) * 100
                if abs(a - n) > 0.5:
                    print("        %-5s %5.1f %% -> %5.1f %%" % (t, a, n))
            print()
    else:
        print("  Keine Umschichtung noetig - die Zuordnung ist bereits optimal.\n")

    pausch = param["arbeitnehmer_pauschbetrag"]["betrag"]
    an_ges = verbrauch.get("AN", 0.0) + verbrauch.get("FOB", 0.0)
    if an_ges < pausch:
        print("  Hinweis: AN + FOB liegen zusammen bei %.2f EUR und damit unter "
              "dem Pauschbetrag\n  von %d EUR. Diese %.2f EUR bringen dir "
              "rechnerisch nichts - sie sind\n  durch den Pauschbetrag bereits "
              "abgegolten. Wenn du im Rest des Jahres\n  noch groessere "
              "berufliche Ausgaben erwartest, kann sich das drehen.\n"
              % (an_ges, pausch, an_ges))

    if ohne_bandbreite:
        print("  Nicht optimierbar (keine Bandbreiten im Register): %s\n"
              % ", ".join(ohne_bandbreite))

    if not args.schreiben:
        if lohnt_sich:
            print("  [VORSCHAU] Nichts geaendert. Mit --schreiben ins Register "
                  "uebernehmen.\n")
        return 0

    if not lohnt_sich:
        print("  Nichts zu tun - der Mehrertrag liegt unter 1 EUR.\n")
        return 0

    behalten = [z for z in zeilen
                if not (str(z.get("datum", "")).startswith(str(jahr))
                        and z["id"] in {b["id"] for b in belege})]
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M")
    lauf = {k: 0.0 for k in TOEPFE}
    for i, b in enumerate(belege):
        vorlage = gruppen[b["id"]][0]
        _, detail = gesamtvorteil(b["brutto"], quoten[i], param, profil, lauf,
                                  b["ust"], b["lohnanteil"])
        for t, q in sorted(quoten[i].items(), key=lambda kv: -kv[1]):
            if q <= 1e-6:
                continue
            zeile = dict(vorlage)
            zeile.update({
                "topf": t,
                "objekt": vorlage.get("objekt", "") if t == "VUV" else "",
                "anteil_prozent": "%.1f" % (q * 100),
                "betrag_zugeordnet": "%.2f" % (b["brutto"] * q),
                "vorteil_geschaetzt": "%.2f" % detail.get(t, 0.0),
                "status": "jahresoptimiert",
                "erfasst_am": jetzt,
            })
            behalten.append(zeile)
            lauf[t] = lauf.get(t, 0.0) + b["brutto"] * q
    schreibe_register(behalten)
    print("  Register aktualisiert. %d Belege neu verteilt.\n" % len(belege))
    print("  WICHTIG: Pruefe jede Umschichtung daraufhin, ob sie noch zu deiner\n"
          "  tatsaechlichen Nutzung passt, und passe die Begruendung im Register an.\n")
    return 0


# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        prog="steuerbro",
        description="Ordnet Belege dem wirtschaftlich besten Steuertopf zu.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Beispiele:

  Laptop 1499 EUR, genutzt fuer Gewerbe, Studium und Dienst:
    steuerbro.py bewerte --brutto 1499 --anteile "GEW=30-60,FOB=20-50,AN=10-30" \\
        --kategorie Arbeitsmittel

  Baumarkt 340 EUR fuer die vermietete Wohnung:
    steuerbro.py bewerte --brutto 340 --anteile "VUV=70-100,GEW=0-30" \\
        --kategorie Instandhaltung

  Beleg erfassen und ablegen:
    steuerbro.py neu --datei belege/_eingang/scan.pdf --datum 2026-03-14 \\
        --haendler "Notebooksbilliger" --beschreibung "ThinkPad T14" \\
        --brutto 1499 --kategorie Arbeitsmittel \\
        --anteile "GEW=30-60,FOB=20-50,AN=10-30" \\
        --begruendung "Hauptsaechlich Auftragsbearbeitung Nebengewerbe, daneben Seminararbeiten"
""")
    unter = p.add_subparsers(dest="befehl", required=True)

    def gemeinsam(sp):
        sp.add_argument("--brutto", type=float, required=True, help="Bruttobetrag in EUR")
        sp.add_argument("--anteile", required=True,
                        help='Nutzungsbandbreiten, z.B. "GEW=30-60,FOB=20-50,AN=10-30". '
                             'Gib an, in welchem Rahmen sich die tatsaechliche Nutzung '
                             'bewegt - das Tool optimiert INNERHALB dieses Rahmens.')
        sp.add_argument("--ust", type=float, default=None,
                        help="Umsatzsteuersatz in Prozent (Standard 19)")
        sp.add_argument("--lohnanteil", type=float, default=0.0,
                        help="Anteil Lohnkosten in Prozent (nur fuer Paragraf 35a relevant)")
        sp.add_argument("--kategorie", default="", help="z.B. Arbeitsmittel, Instandhaltung, Fachliteratur")
        sp.add_argument("--jahr", type=int, default=None)

    sp = unter.add_parser("bewerte", help="Nur rechnen, nichts erfassen")
    gemeinsam(sp)
    sp.set_defaults(func=befehl_bewerte)

    sp = unter.add_parser("neu", help="Beleg bewerten, benennen, ablegen, registrieren")
    gemeinsam(sp)
    sp.add_argument("--datum", required=True, help="Rechnungsdatum JJJJ-MM-TT")
    sp.add_argument("--haendler", required=True)
    sp.add_argument("--beschreibung", required=True)
    sp.add_argument("--datei", default="", help="Pfad zur Belegdatei (wird verschoben)")
    sp.add_argument("--objekt", default="", help="Objektkuerzel bei Vermietung")
    sp.add_argument("--begruendung", default="",
                    help="WARUM diese Aufteilung? Der wichtigste Satz im ganzen System.")
    sp.add_argument("--zahlungsart", default="", help="ueberweisung / karte / bar")
    sp.add_argument("--trocken", action="store_true", help="Nur anzeigen, nichts schreiben")
    sp.set_defaults(func=befehl_neu)

    sp = unter.add_parser("auswertung", help="Summen, Restbudgets, Schwellen")
    sp.add_argument("--jahr", type=int, default=None)
    sp.set_defaults(func=befehl_auswertung)

    sp = unter.add_parser("neuverteilen",
                          help="Alle Belege eines Jahres gemeinsam optimieren")
    sp.add_argument("--jahr", type=int, default=None)
    sp.add_argument("--schreiben", action="store_true",
                    help="Ergebnis ins Register uebernehmen (sonst nur Vorschau)")
    sp.set_defaults(func=befehl_neuverteilen)

    sp = unter.add_parser("pruefe", help="Register auf Plausibilitaet pruefen")
    sp.set_defaults(func=befehl_pruefe)

    args = p.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
