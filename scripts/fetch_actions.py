"""
Univers actions en direct : STOXX Europe 600 -> data/actions/

Lancer :  python3 scripts/fetch_actions.py            (tout, ~20 min)
          python3 scripts/fetch_actions.py --reprise  (ne refait que les échecs)

Étapes, chacune mise en cache dans data/actions/ :
  1. composition.csv  — composition officielle, lue dans le fichier de
     positions de l'ETF iShares STOXX Europe 600 (EXSA, site allemand : le
     site britannique ne sert plus ce fichier depuis sa refonte) ;
  2. tickers.csv      — conversion au format Yahoo (suffixe de place) et
     VÉRIFICATION : le nom renvoyé par Yahoo doit partager un mot significatif
     avec le nom iShares. Un ticker mal converti pointe vers une autre société
     sans que rien ne s'allume (cas CTA.L, voir notes du projet) ;
  3. fondamentaux.csv — ratios Yahoo : valorisation, croissance, qualité,
     secteur et industrie (pour les exclusions), description d'activité ;
  4. momentum.csv     — performances sur 12 mois hors dernier mois et sur
     6 mois, en devise locale ;
  5. prix_hebdo.csv   — cours hebdomadaires depuis 2019 (dividendes
     réinvestis), plus l'indice (ETF EXSA, en euros), pour le pilier
     Résistance et le contrôle du panier face à l'indice ;
     risque.csv       — volatilité sur 3 ans, pertes maximales en 2020 et en
     2022, bêta sur 3 ans face à l'indice ;
  6. change.csv       — cours de référence de la BCE, pour convertir les
     capitalisations en euros (filtre des grandes capitalisations).
     Yahoo exprime la capitalisation des titres londoniens en LIVRES, même
     quand le cours est coté en pence (vérifié sur AstraZeneca : 1,93e11).

Aucune note n'est calculée ici : la notation est faite par core/scoring.py,
à partir de ces fichiers, pour rester instantanée et lisible dans l'app.

LIMITES CONNUES, traitées en aval (core/scoring.py) :
  - Yahoo publie certains ratios britanniques en pence au lieu de livres :
    un PER ou un rendement faux d'un facteur 100 est possible. D'où des
    bornes de plausibilité et une winsorisation avant notation ;
  - les ratios d'endettement et de flux de trésorerie n'ont pas de sens pour
    les banques et assurances : ils sont ignorés pour la finance.
"""
from __future__ import annotations

import io
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

RACINE = Path(__file__).resolve().parents[1]
DOSSIER = RACINE / "data" / "actions"
URL_EXSA = ("https://www.ishares.com/de/privatanleger/de/produkte/251931/"
            "ishares-stoxx-europe-600-ucits-etf-de-fund/1478358465952.ajax"
            "?fileType=csv&fileName=EXSA_holdings&dataType=fund")

SUFFIXE = {
    "London Stock Exchange": ".L", "Xetra": ".DE", "Deutsche Börse AG": ".DE",
    "Nyse Euronext - Euronext Paris": ".PA", "SIX Swiss Exchange": ".SW",
    "Nasdaq Omx Nordic": ".ST", "Borsa Italiana": ".MI",
    "Euronext Amsterdam": ".AS", "Bolsa De Madrid": ".MC",
    "Oslo Bors Asa": ".OL", "Omx Nordic Exchange Copenhagen A/S": ".CO",
    "Nasdaq Omx Helsinki Ltd.": ".HE",
    "Warsaw Stock Exchange/Equities/Main Market": ".WA",
    "Nyse Euronext - Euronext Brussels": ".BR", "Wiener Boerse Ag": ".VI",
    "Irish Stock Exchange - All Market": ".IR",
    "Nyse Euronext - Euronext Lisbon": ".LS",
}
SECTEUR_FR = {
    "Industrie": "Industrie", "Finanzwesen": "Finance",
    "Zyklische Konsumgüter": "Consommation discrétionnaire",
    "Materialien": "Matériaux", "Gesundheitsversorgung": "Santé",
    "Nichtzyklische Konsumgüter": "Consommation de base", "IT": "Technologie",
    "Versorger": "Services aux collectivités",
    "Kommunikation": "Télécoms et médias", "Immobilien": "Immobilier",
    "Energie": "Énergie",
}
MOTS_VIDES = {"PLC", "AG", "SA", "NV", "SE", "ASA", "AB", "OYJ", "SPA", "GROUP",
              "HOLDING", "HOLDINGS", "CLASS", "THE", "AND", "INC", "LTD", "CO",
              "COMPANY", "N.V.", "S.A.", "S.P.A.", "A/S", "REG", "SHS", "DE",
              "OF", "PLC.", "LIMITED", "INTERNATIONAL", "BANK", "BANCO"}
CHAMPS = ["longName", "currency", "sector", "industry", "marketCap",
          "trailingPE", "forwardPE", "priceToBook", "enterpriseToEbitda",
          "dividendYield", "freeCashflow", "returnOnEquity", "returnOnAssets",
          "profitMargins", "operatingMargins", "debtToEquity",
          "earningsGrowth", "revenueGrowth", "trailingEps", "forwardEps",
          "longBusinessSummary"]


def _essayer(fn, essais=4):
    for i in range(essais):
        try:
            return fn()
        except Exception:                            # noqa: BLE001
            if i == essais - 1:
                raise
            time.sleep(2 + 3 * i)


# --------------------------------------------------------------------------
# 1. Composition
# --------------------------------------------------------------------------

def composition() -> pd.DataFrame:
    r = requests.get(URL_EXSA, headers={"User-Agent": "Mozilla/5.0"},
                     timeout=120)
    r.raise_for_status()
    lignes = r.content.decode("utf-8-sig").splitlines()
    quand = re.search(r'"(\d{2}\.\w+\.\d{4})"', lignes[0])
    debut = next(i for i, l in enumerate(lignes)
                 if l.startswith("Emittententicker"))
    d = pd.read_csv(io.StringIO("\n".join(lignes[debut:])), thousands=".",
                    decimal=",")
    d = d[d["Anlageklasse"] == "Aktien"].rename(columns={
        "Emittententicker": "ticker_ishares", "Name": "nom",
        "Sektor": "secteur_de", "Gewichtung (%)": "poids",
        "Standort": "pays", "Börse": "place", "Marktwährung": "devise"})
    # certains libellés iShares finissent par une espace insécable (\xa0),
    # invisible à l'œil : sans ce nettoyage, 58 titres n'ont pas de secteur
    d["secteur"] = d["secteur_de"].str.strip().map(SECTEUR_FR)
    d["date_composition"] = quand.group(1) if quand else None
    return d[["ticker_ishares", "nom", "secteur", "poids", "pays", "place",
              "devise", "date_composition"]].reset_index(drop=True)


# --------------------------------------------------------------------------
# 2. Tickers Yahoo, vérifiés
# --------------------------------------------------------------------------

TRANSLIT = {"Ä": "AE", "Ö": "OE", "Ü": "UE", "Æ": "AE", "Ø": "OE", "Å": "AA"}


def _formes(nom: str) -> list[str]:
    """Deux formes sans accents : « Münchener » -> MUNCHENER et MUENCHENER."""
    haut = nom.upper().replace("'", "").replace("’", "")
    translit = "".join(TRANSLIT.get(ch, ch) for ch in haut)
    simple = haut.replace("Ø", "O").replace("Æ", "AE")
    return [unicodedata.normalize("NFKD", f).encode("ascii", "ignore").decode()
            for f in (simple, translit)]


def _mots(nom: str) -> set[str]:
    return {m for f in _formes(nom) for m in re.split(r"[^A-Z0-9]+", f)
            if len(m) >= 2 and m not in MOTS_VIDES}


def _sigle(nom: str) -> str:
    """Initiales des mots significatifs : Bayerische Motoren Werke -> BMW."""
    mots = [m for m in re.split(r"[^A-Z0-9]+", _formes(nom)[0])
            if m and m not in MOTS_VIDES and m != "AKTIENGESELLSCHAFT"]
    return "".join(m[0] for m in mots)


def meme_societe(nom: str, nom_yahoo: str, ticker: str) -> bool:
    """
    Le nom Yahoo désigne-t-il la même société que le nom iShares ?
    Mot commun (ou l'un préfixe de l'autre, 4 lettres au moins), ou ticker
    égal à un mot du nom Yahoo (GSK), ou sigle (BMW, PZU).
    """
    a, b = _mots(nom), _mots(nom_yahoo)
    if a & b:
        return True
    if any(len(x) >= 4 and len(y) >= 4 and (x.startswith(y) or y.startswith(x))
           for x in a for y in b):
        return True
    racine = re.sub(r"[^A-Z0-9]", "", ticker.split(".")[0].split("-")[0].upper())
    return len(racine) >= 2 and (racine in b or _sigle(nom_yahoo).startswith(racine))


# Correspondances qu'aucune règle générale ne reconnaît, vérifiées à la main.
VERIFIES_A_LA_MAIN = {
    "PEO.WA": "Bank Pekao : « Pekao » abrège Polska Kasa Opieki",
    "SDF.DE": "K+S : nom réduit à deux lettres, identique des deux côtés",
    "MNG.L": "M&G plc : nom réduit à deux lettres, identique des deux côtés",
}


def candidat(ticker: str, place: str) -> str:
    t = ticker.strip().rstrip(".").replace(" ", "-").replace(".", "-")
    return t + SUFFIXE.get(place, "")


def verifier(ticker_yahoo: str, nom: str) -> tuple[bool, str]:
    info = _essayer(lambda: yf.Ticker(ticker_yahoo).info, essais=2)
    nom_y = info.get("longName") or info.get("shortName") or ""
    ok = ticker_yahoo in VERIFIES_A_LA_MAIN or meme_societe(nom, nom_y,
                                                            ticker_yahoo)
    return ok, nom_y


def rechercher(nom: str, suffixe: str) -> tuple[str | None, str]:
    """Repli : recherche Yahoo par nom, restreinte à la bonne place."""
    try:
        res = yf.Search(nom, max_results=10).quotes
    except Exception:                                # noqa: BLE001
        return None, ""
    for q in res:
        s = q.get("symbol", "")
        if s.endswith(suffixe) and q.get("quoteType") == "EQUITY":
            return s, q.get("longname") or q.get("shortname") or ""
    return None, ""


def tickers(comp: pd.DataFrame, ancien: pd.DataFrame | None) -> pd.DataFrame:
    connus = {} if ancien is None else {
        (r.ticker_ishares, r.place): r for r in ancien.itertuples()
        if r.statut == "vérifié" and "place" in ancien.columns}
    out = []
    for i, r in enumerate(comp.itertuples(), 1):
        if (r.ticker_ishares, r.place) in connus:
            k = connus[(r.ticker_ishares, r.place)]
            out.append({"ticker_ishares": r.ticker_ishares, "place": r.place,
                        "ticker": k.ticker, "nom_yahoo": k.nom_yahoo,
                        "statut": k.statut})
            continue
        t = candidat(r.ticker_ishares, r.place)
        try:
            ok, nom_y = verifier(t, r.nom)
        except Exception:                            # noqa: BLE001
            ok, nom_y = False, ""
        if not ok:
            t2, nom2 = rechercher(r.nom, SUFFIXE.get(r.place, ""))
            if t2 and meme_societe(r.nom, nom2, t2):
                t, nom_y, ok = t2, nom2, True
        out.append({"ticker_ishares": r.ticker_ishares, "place": r.place,
                    "ticker": t, "nom_yahoo": nom_y,
                    "statut": "vérifié" if ok else "non résolu"})
        if i % 50 == 0:
            print(f"    tickers : {i}/{len(comp)}")
    return pd.DataFrame(out)


# --------------------------------------------------------------------------
# 3 et 4. Fondamentaux et momentum
# --------------------------------------------------------------------------

def fondamentaux(t: str) -> dict:
    info = _essayer(lambda: yf.Ticker(t).info)
    return {c: info.get(c) for c in CHAMPS}


def momentum(t: str) -> dict:
    h = _essayer(lambda: yf.Ticker(t).history(period="14mo", auto_adjust=True))
    s = h["Close"].dropna()
    s.index = s.index.tz_localize(None)
    fin = s.index[-1]

    def a(mois):
        v = s[s.index <= fin - pd.DateOffset(months=mois)]
        return float(v.iloc[-1]) if len(v) else None

    p1, p6, p12 = a(1), a(6), a(12)
    return {"mom_12_1": (p1 / p12 - 1) * 100 if p1 and p12 else None,
            "mom_6": (s.iloc[-1] / p6 - 1) * 100 if p6 else None,
            "date_prix": fin.date().isoformat()}


DEBUT_PRIX = "2019-01-01"
INDICE = "EXSA.DE"


def prix_hebdo(t: str) -> pd.Series:
    h = _essayer(lambda: yf.Ticker(t).history(start=DEBUT_PRIX,
                                              auto_adjust=True))
    s = h["Close"].dropna()
    s.index = s.index.tz_localize(None).normalize()
    return s.resample("W-FRI").last().dropna()


def perte_max(s: pd.Series, debut: str, fin: str) -> float | None:
    """Plus forte baisse de pic à creux à l'intérieur de la fenêtre."""
    x = s[debut:fin]
    if len(x) < 20 or s.index[0] > pd.Timestamp(debut) + pd.Timedelta(days=14):
        return None                                  # coté après le début
    return float((x / x.cummax() - 1).min() * 100)


def risque(prix: pd.DataFrame) -> pd.DataFrame:
    r = prix.pct_change(fill_method=None)
    trois_ans = r[r.index >= r.index[-1] - pd.DateOffset(years=3)]
    ind = trois_ans[INDICE]
    lignes = []
    for t in prix.columns:
        if t == INDICE:
            continue
        x = trois_ans[t].dropna()
        ok = len(x) >= 100
        beta = (x.cov(ind.loc[x.index]) / ind.loc[x.index].var()) if ok else None
        s = prix[t].dropna()
        lignes.append({
            "ticker": t,
            "vol_3a": float(x.std() * 52 ** 0.5 * 100) if ok else None,
            "dd_2020": perte_max(s, "2020-01-01", "2020-12-31"),
            "dd_2022": perte_max(s, "2022-01-01", "2022-12-31"),
            "beta_3a": float(beta) if beta is not None else None,
        })
    return pd.DataFrame(lignes)


def change() -> pd.DataFrame:
    r = requests.get(
        "https://data-api.ecb.europa.eu/service/data/EXR/"
        "D.GBP+CHF+SEK+NOK+DKK+PLN+USD.EUR.SP00.A",
        params={"lastNObservations": 1, "format": "csvdata"}, timeout=180)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    out = d[["CURRENCY", "OBS_VALUE", "TIME_PERIOD"]].rename(columns={
        "CURRENCY": "devise", "OBS_VALUE": "unites_pour_1_eur",
        "TIME_PERIOD": "date"})
    return pd.concat([out, pd.DataFrame([{"devise": "EUR",
                                          "unites_pour_1_eur": 1.0,
                                          "date": out["date"].iloc[0]}])])


def change_hebdo() -> pd.DataFrame:
    """Historique hebdomadaire des cours BCE, pour convertir les prix en euros."""
    r = requests.get(
        "https://data-api.ecb.europa.eu/service/data/EXR/"
        "D.GBP+CHF+SEK+NOK+DKK+PLN+USD.EUR.SP00.A",
        params={"startPeriod": DEBUT_PRIX, "format": "csvdata"}, timeout=300)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    p = d.pivot_table(index="TIME_PERIOD", columns="CURRENCY",
                      values="OBS_VALUE")
    p.index = pd.to_datetime(p.index)
    p = p.resample("W-FRI").last().ffill()
    p["EUR"] = 1.0
    p.index.name = "date"
    return p


def collecter(tk: pd.DataFrame, fichier: Path, fn, nom: str,
              reprise: bool) -> pd.DataFrame:
    deja = (pd.read_csv(fichier) if reprise and fichier.exists()
            else pd.DataFrame(columns=["ticker"]))
    faits = set(deja["ticker"])
    lignes = [] if deja.empty else deja.to_dict("records")
    a_faire = [t for t in tk.loc[tk.statut == "vérifié", "ticker"]
               if t not in faits]
    echecs = 0
    for i, t in enumerate(a_faire, 1):
        try:
            lignes.append({"ticker": t} | fn(t))
        except Exception:                            # noqa: BLE001
            echecs += 1
        if i % 50 == 0:
            print(f"    {nom} : {i}/{len(a_faire)}  ({echecs} échecs)")
    d = pd.DataFrame(lignes)
    d.to_csv(fichier, index=False)
    print(f"  {nom} : {len(d)} titres, {echecs} échecs")
    return d


def main() -> int:
    reprise = "--reprise" in sys.argv
    DOSSIER.mkdir(parents=True, exist_ok=True)

    comp = composition()
    comp.to_csv(DOSSIER / "composition.csv", index=False)
    print(f"  composition : {len(comp)} titres au "
          f"{comp['date_composition'].iloc[0]}")

    f_tk = DOSSIER / "tickers.csv"
    ancien = pd.read_csv(f_tk) if f_tk.exists() else None
    tk = tickers(comp, ancien)
    tk.to_csv(f_tk, index=False)
    nr = tk[tk.statut != "vérifié"]
    print(f"  tickers : {len(tk) - len(nr)} vérifiés, {len(nr)} non résolus")
    if len(nr):
        print("    non résolus : " + ", ".join(nr["ticker_ishares"].astype(str)))

    collecter(tk, DOSSIER / "fondamentaux.csv", fondamentaux, "fondamentaux",
              reprise)
    collecter(tk, DOSSIER / "momentum.csv", momentum, "momentum", reprise)

    f_px = DOSSIER / "prix_hebdo.csv"
    prix = (pd.read_csv(f_px, index_col=0, parse_dates=True)
            if reprise and f_px.exists() else pd.DataFrame())
    a_faire = [t for t in [INDICE, *tk.loc[tk.statut == "vérifié", "ticker"]]
               if t not in prix.columns]
    series, echecs = {}, 0
    for i, t in enumerate(a_faire, 1):
        try:
            series[t] = prix_hebdo(t)
        except Exception:                            # noqa: BLE001
            echecs += 1
        if i % 100 == 0:
            print(f"    prix : {i}/{len(a_faire)}  ({echecs} échecs)")
    if series:
        prix = pd.concat([prix, pd.DataFrame(series)], axis=1)
    prix.index.name = "date"
    prix.round(4).to_csv(f_px)
    print(f"  prix hebdomadaires : {prix.shape[1]} séries, {echecs} échecs")
    risque(prix).round(3).to_csv(DOSSIER / "risque.csv", index=False)
    print("  risque : calculé")
    change().to_csv(DOSSIER / "change.csv", index=False)
    change_hebdo().round(5).to_csv(DOSSIER / "change_hebdo.csv")
    print("  change : cours BCE relevés")
    (DOSSIER / "releve.txt").write_text(date.today().isoformat() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
