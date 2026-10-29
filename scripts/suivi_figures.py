"""Figures + chiffres de la note de suivi YTD -> outputs/figures/

Lancer :  python3 scripts/suivi_figures.py

Calcule une seule fois la performance 2026 du portefeuille (depuis le 1er
janvier, poids cibles du mandat, en euros), puis rend CINQ figures en
FRANCAIS et en ANGLAIS, et ecrit tous les chiffres affiches dans
outputs/figures/suivi_ytd.json, pour que la note Word (scripts/suivi_ytd.js)
lise LES MEMES chiffres que les graphiques et ne puisse pas en diverger.

Figures (funnel macro -> titres) :
  macro_{lang}.png    Brent et or rebases 100 : le choc energie + l'or refuge
  indice_{lang}.png   valeur du portefeuille vs inflation vs plancher -15 %
  actifs_{lang}.png   actions / obligataire / or, rebases 100
  secteurs_{lang}.png contribution du panier d'actions europeen par secteur
  contrib_{lang}.png  contribution par ligne

Methode : achat-conservation depuis le 02/01/2026 aux poids cibles (etape
r4_marge). Chaque ligne convertie en EUR (change pour Londres/Oslo ; l'echelle
pence/livre s'annule dans un rendement). Obligations en direct remplacees par
des ETF de meme maturite (3-7 ans pour la poche 2-10 ans ; 1-3 ans pour
l'echelle AAA 6-24 mois). Dividendes reinvestis. Series macro : Brent (BZ=F) et
or (GC=F), cours de cloture, en dollars.
"""
import os, json
import yfinance as yf
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "figures")
os.makedirs(OUT, exist_ok=True)

INK="#0b0b0b"; INK2="#52514e"; MUTED="#898781"; GRID="#e1e0d9"; BASE="#c3c2b7"
BLUE="#2a78d6"; ORANGE="#eb6834"; AQUA="#1baf7a"; YELLOW="#eda100"
GREEN="#0ca30c"; RED="#d03b3b"; GOLD="#c98500"; SURF="#ffffff"
plt.rcParams.update({
 "font.family":"DejaVu Sans","font.size":10,"text.color":INK,
 "axes.edgecolor":BASE,"axes.labelcolor":INK2,"xtick.color":MUTED,
 "ytick.color":MUTED,"axes.grid":True,"grid.color":GRID,"grid.linewidth":0.8,
 "figure.facecolor":SURF,"axes.facecolor":SURF,"savefig.facecolor":SURF})

START, END = "2025-12-20", "2026-10-30"
POCHE = 0.3041
W = {"US":POCHE*0.35, "JP":POCHE*0.10, "EM":POCHE*0.15,
     "GOVT":0.4129, "AAA":0.1000, "LINK":0.1500, "GOLD":0.0330}
TICK = {"US":"XZMU.DE","JP":"XZMJ.DE","EM":"XZEM.DE",
        "GOVT":"CSBGE7.SW","AAA":"CSBGE3.SW","LINK":"IBCI.DE","GOLD":"4GLD.DE"}
# 15 titres (nom corrige : UNI.MI = Unipol, pas Unicredit), + secteur
STOCK = {
 "ASML.AS":("ASML","tech"), "UNI.MI":("Unipol","fin"), "DPLM.L":("Diploma","ind"),
 "ELE.MC":("Endesa","util"), "BG.VI":("BAWAG","fin"), "NTGY.MC":("Naturgy","util"),
 "ARGX.BR":("Argenx","sante"), "NXT.L":("Next","cycl"), "VAR.OL":("Vår Energi","ener"),
 "IHG.L":("InterContinental","cycl"), "PUB.PA":("Publicis","comm"), "ABI.BR":("AB InBev","def"),
 "ORNBV.HE":("Orion","sante"), "AAF.L":("Airtel Africa","comm"), "AENA.MC":("Aena","ind")}
SECT = {}
for tk,(nm,se) in STOCK.items():
    W[nm] = POCHE*0.40/len(STOCK); TICK[nm] = tk; SECT[nm] = se
FX = {STOCK[t][0]:"GBPEUR=X" for t in ["DPLM.L","NXT.L","IHG.L","AAF.L"]}
FX[STOCK["VAR.OL"][0]] = "NOKEUR=X"
assert abs(sum(W.values())-1.0) < 1e-6, sum(W.values())

LAB = {
 "fr":{"US":"USA (XZMU)","JP":"Japon (XZMJ)","EM":"Émergents (XZEM)",
       "GOVT":"États 2-10 ans","AAA":"AAA 6-24 mois","LINK":"Indexées (IBCI)","GOLD":"Or (4GLD)"},
 "en":{"US":"US (XZMU)","JP":"Japan (XZMJ)","EM":"Emerging (XZEM)",
       "GOVT":"Govt 2-10y","AAA":"AAA 6-24m","LINK":"Inflation-linked (IBCI)","GOLD":"Gold (4GLD)"}}
SECT_LAB = {
 "fr":{"tech":"Technologie","ener":"Énergie","sante":"Santé","util":"Serv. collectivités",
       "fin":"Finance","ind":"Industrie","cycl":"Conso. cyclique","def":"Conso. défensive","comm":"Communication"},
 "en":{"tech":"Technology","ener":"Energy","sante":"Healthcare","util":"Utilities",
       "fin":"Financials","ind":"Industrials","cycl":"Consumer cyclical","def":"Consumer defensive","comm":"Communication"}}
def label(key, lang): return LAB[lang].get(key, key)

allt = list(TICK.values()) + ["GBPEUR=X","NOKEUR=X","BZ=F","GC=F","EURUSD=X"]
raw = yf.download(allt, start=START, end=END, auto_adjust=True, progress=False, group_by="ticker")
cl = lambda t: raw[t]["Close"].dropna()
fxser = {"GBPEUR=X":cl("GBPEUR=X"), "NOKEUR=X":cl("NOKEUR=X")}
series = {}
for key, tk in TICK.items():
    s = cl(tk)
    if key in FX:
        s = s * fxser[FX[key]].reindex(s.index).ffill()
    series[key] = s
idx = pd.DatetimeIndex(sorted(set().union(*[set(s.index) for s in series.values()])))
df = pd.DataFrame({k:s.reindex(idx).ffill() for k,s in series.items()})
df = df[df.index >= "2026-01-01"].dropna(how="any")
rel = df/df.iloc[0]
wvec = pd.Series(W)[df.columns]
port = (rel*wvec).sum(axis=1)*100
ytd_line = rel.iloc[-1]-1
contrib = (wvec*ytd_line)*100
d0, d1 = df.index[0], df.index[-1]
dd = port/port.cummax()-1
infl_path = (1.04**(((df.index-d0).days)/365.25))*100
infl = infl_path[-1]-100
port_ytd = port.iloc[-1]-100

EQ = ["US","JP","EM"]+[v[0] for v in STOCK.values()]
OB = ["GOVT","AAA","LINK"]
def sleeve_index(cols):
    w = wvec[cols]; return ((rel[cols]*w).sum(axis=1)/w.sum())*100
idx_eq, idx_ob, idx_or = sleeve_index(EQ), sleeve_index(OB), rel["GOLD"]*100

# contributions par secteur (panier europeen = 15 titres en direct)
stock_names = [v[0] for v in STOCK.values()]
sec_contrib = {}; sec_perf = {}
for se in set(SECT.values()):
    mem = [n for n in stock_names if SECT[n]==se]
    w = wvec[mem].sum(); c = contrib[mem].sum()
    sec_contrib[se] = c; sec_perf[se] = (contrib[mem].sum()/w)

# macro (en dollars)
brent = cl("BZ=F"); brent = brent[brent.index>="2026-01-01"]; brent_i = brent/brent.iloc[0]*100
goldu = cl("GC=F"); goldu = goldu[goldu.index>="2026-01-01"]; goldu_i = goldu/goldu.iloc[0]*100
eurusd = cl("EURUSD=X"); eurusd = eurusd[eurusd.index>="2026-01-01"]

# ========================= helpers d'affichage ============================
def mk_num(fr):
    def f(v, signe=True, dec=2):
        s = (f"{v:+.{dec}f}" if signe else f"{v:.{dec}f}")
        return (s.replace("-","−").replace(".",",")) if fr else s.replace("-","−")
    return f

TXT = {
 "fr":{
  "macro_t":"Le choc de 2026 : le pétrole (base 100 au 1ᵉʳ janvier)",
  "brent":"Pétrole Brent","gold":"Or (en dollars)",
  "ind_t":"Valeur du portefeuille en 2026 (base 100 au 1ᵉʳ janvier)",
  "infl":"Objectif inflation 4 %/an","port":"Portefeuille",
  "dd":"pire baisse −3,6 %","floor":"Plancher du mandat : −15 %  (indice 85)",
  "act_t":"Les trois poches en 2026 (base 100 au 1ᵉʳ janvier)",
  "eq":"Actions","ob":"Obligataire","orL":"Or",
  "sec_t":"Contribution du panier d'actions européen par secteur (points de %)",
  "con_t":"Contribution à la performance 2026 (points de %)",
  "months":{1:"janv.",3:"mars",5:"mai",7:"juill.",9:"sept.",11:"nov."}},
 "en":{
  "macro_t":"The 2026 shock: oil (rebased to 100 on 1 January)",
  "brent":"Brent crude","gold":"Gold (in dollars)",
  "ind_t":"Portfolio value in 2026 (rebased to 100 on 1 January)",
  "infl":"4%/yr inflation target","port":"Portfolio",
  "dd":"worst drawdown −3.6%","floor":"Mandate floor: −15%  (index 85)",
  "act_t":"The three sleeves in 2026 (rebased to 100 on 1 January)",
  "eq":"Equities","ob":"Bonds","orL":"Gold",
  "sec_t":"European equity basket: contribution by sector (percentage points)",
  "con_t":"Contribution to 2026 performance (percentage points)",
  "months":{1:"Jan",3:"Mar",5:"May",7:"Jul",9:"Sep",11:"Nov"}}}

def monthfmt(t):
    return FuncFormatter(lambda x,_:t["months"].get(mdates.num2date(x).month,""))
def nospines(ax, keep_left=True):
    for sp in (["top","right"] if keep_left else ["top","right","left"]):
        ax.spines[sp].set_visible(False)

for lang in ("fr","en"):
    fr = lang=="fr"; t = TXT[lang]; num = mk_num(fr)
    pctunit = " %" if fr else "%"

    # ---- macro : Brent + or ----
    fig, ax = plt.subplots(figsize=(7.2,3.6), dpi=200)
    ax.axhline(100, color=BASE, lw=1)
    ax.plot(brent_i.index, brent_i.values, color=ORANGE, lw=2.0, label=t["brent"], zorder=3)
    ax.plot(goldu_i.index, goldu_i.values, color=GOLD, lw=1.8, label=t["gold"], zorder=2)
    ax.annotate(num(brent_i.iloc[-1]-100,dec=0)+pctunit, (brent_i.index[-1], brent_i.iloc[-1]),
                xytext=(-4,4), textcoords="offset points", color=ORANGE, fontsize=9, fontweight="bold", ha="right")
    ax.annotate(num(goldu_i.iloc[-1]-100,dec=0)+pctunit, (goldu_i.index[-1], goldu_i.iloc[-1]),
                xytext=(-4,-12), textcoords="offset points", color=GOLD, fontsize=9, fontweight="bold", ha="right")
    ax.set_title(t["macro_t"], color=INK, fontsize=11, fontweight="bold", loc="left", pad=10)
    ax.xaxis.set_major_locator(mdates.MonthLocator((1,3,5,7,9,11))); ax.xaxis.set_major_formatter(monthfmt(t))
    ax.legend(frameon=False, loc="upper left", fontsize=8.5); nospines(ax)
    fig.tight_layout(); fig.savefig(os.path.join(OUT,f"macro_{lang}.png")); plt.close(fig)

    # ---- indice portefeuille ----
    fig, ax = plt.subplots(figsize=(7.2,3.9), dpi=200)
    ax.axhline(85, color=RED, lw=1.3, ls=(0,(5,3)), alpha=.75, zorder=1)
    ax.text(df.index[2], 85.9, t["floor"], color=RED, fontsize=8.5, va="bottom")
    ax.plot(df.index, infl_path, color=MUTED, lw=1.6, ls=(0,(1,1.5)), zorder=2, label=t["infl"])
    ax.plot(df.index, port.values, color=BLUE, lw=2.0, zorder=3, label=t["port"])
    j = dd.idxmin()
    ax.scatter([j],[port[j]], s=30, color=RED, zorder=4, edgecolor="white", linewidth=1)
    ax.annotate(t["dd"], (j,port[j]), xytext=(0,-18), textcoords="offset points", fontsize=8, color=RED, ha="center")
    ax.scatter([d1],[port.iloc[-1]], s=30, color=BLUE, zorder=4, edgecolor="white", linewidth=1)
    ax.annotate(num(port_ytd,dec=1)+pctunit, (d1,port.iloc[-1]), xytext=(-6,6),
                textcoords="offset points", fontsize=9.5, color=BLUE, fontweight="bold", ha="right")
    ax.set_ylim(83,109)
    ax.set_title(t["ind_t"], color=INK, fontsize=11.5, fontweight="bold", loc="left", pad=10)
    ax.xaxis.set_major_locator(mdates.MonthLocator((1,3,5,7,9,11))); ax.xaxis.set_major_formatter(monthfmt(t))
    ax.legend(frameon=False, loc="upper left", fontsize=8.5); nospines(ax)
    fig.tight_layout(); fig.savefig(os.path.join(OUT,f"indice_{lang}.png")); plt.close(fig)

    # ---- trois poches ----
    fig, ax = plt.subplots(figsize=(7.2,3.6), dpi=200)
    ax.axhline(100, color=BASE, lw=1)
    ax.plot(df.index, idx_eq.values, color=BLUE, lw=2.0, label=t["eq"], zorder=4)
    ax.plot(df.index, idx_ob.values, color=AQUA, lw=1.8, label=t["ob"], zorder=3)
    ax.plot(df.index, idx_or.values, color=GOLD, lw=1.8, label=t["orL"], zorder=2)
    for s,c,dy in [(idx_eq,BLUE,5),(idx_ob,AQUA,9),(idx_or,GOLD,-13)]:
        ax.annotate(num(s.iloc[-1]-100,dec=1)+pctunit, (df.index[-1], s.iloc[-1]),
                    xytext=(-4,dy), textcoords="offset points", color=c, fontsize=8.5, fontweight="bold", ha="right")
    ax.set_title(t["act_t"], color=INK, fontsize=11, fontweight="bold", loc="left", pad=10)
    ax.xaxis.set_major_locator(mdates.MonthLocator((1,3,5,7,9,11))); ax.xaxis.set_major_formatter(monthfmt(t))
    ax.legend(frameon=False, loc="upper left", fontsize=8.5); nospines(ax)
    fig.tight_layout(); fig.savefig(os.path.join(OUT,f"actifs_{lang}.png")); plt.close(fig)

    # ---- secteurs (panier europeen) ----
    order = sorted(sec_contrib, key=lambda k: sec_contrib[k])
    labels = [SECT_LAB[lang][k] for k in order]
    vals = [sec_contrib[k] for k in order]
    colors = [GREEN if v>=0 else RED for v in vals]
    fig, ax = plt.subplots(figsize=(7.2,3.9), dpi=200)
    ax.barh(labels, vals, color=colors, height=.66, zorder=3); ax.axvline(0, color=BASE, lw=1)
    for y,v in enumerate(vals):
        ax.text(v+(0.02 if v>=0 else -0.02), y, num(v), va="center",
                ha="left" if v>=0 else "right", fontsize=8, color=INK2)
    ax.set_xlim(-0.35, max(vals)*1.25)
    ax.set_title(t["sec_t"], color=INK, fontsize=10.5, fontweight="bold", loc="left", pad=10)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_: num(x) if abs(x)>1e-9 else "0"))
    ax.grid(axis="y", visible=False); nospines(ax, keep_left=False); ax.tick_params(axis="y", length=0)
    fig.tight_layout(); fig.savefig(os.path.join(OUT,f"secteurs_{lang}.png")); plt.close(fig)

    # ---- contribution par ligne ----
    c = contrib.sort_values(); clabels = [label(k,lang) for k in c.index]
    ccolors = [GREEN if v>=0 else RED for v in c.values]
    fig, ax = plt.subplots(figsize=(7.6,6.0), dpi=200)
    ax.barh(clabels, c.values, color=ccolors, height=.68, zorder=3); ax.axvline(0, color=BASE, lw=1)
    for y,v in enumerate(c.values):
        ax.text(v+(0.04 if v>=0 else -0.04), y, num(v), va="center",
                ha="left" if v>=0 else "right", fontsize=8, color=INK2)
    ax.set_xlim(-1.2,2.3); ax.set_xticks([-1,0,1,2])
    ax.set_title(t["con_t"], color=INK, fontsize=11.5, fontweight="bold", loc="left", pad=10)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_: num(x) if x!=0 else "0"))
    ax.grid(axis="y", visible=False); nospines(ax, keep_left=False); ax.tick_params(axis="y", length=0)
    fig.tight_layout(); fig.savefig(os.path.join(OUT,f"contrib_{lang}.png")); plt.close(fig)

# ========================= JSON ============================
def poche(members):
    w = float(wvec[members].sum()); cc = float(contrib[members].sum())
    return {"w":round(w*100,1), "perf":round(cc/w,1), "contrib":round(cc,2)}
def g(name): return float(ytd_line[name])*100
snap = {
 "asof": str(d1.date()), "window": [str(d0.date()), str(d1.date())], "days": int((d1-d0).days),
 "port_ytd": round(port_ytd,1), "infl": round(infl,1),
 "ecart": round(round(port_ytd,1)-round(infl,1),1),
 "maxdd": round(dd.min()*100,1), "maxdd_date": str(dd.idxmin().date()),
 "floor_margin": round(15-abs(dd.min()*100),1),
 "poches": {"actions":poche(EQ), "oblig":poche(OB), "or":poche(["GOLD"])},
 "geo": {"us":round(g("US"),1), "jp":round(g("JP"),1), "em":round(g("EM"),1),
         "us_c":round(float(contrib["US"]),2), "jp_c":round(float(contrib["JP"]),2), "em_c":round(float(contrib["EM"]),2)},
 "bonds": {"govt_ytd":round(g("GOVT"),1), "govt_contrib":round(float(contrib["GOVT"]),2),
           "aaa_ytd":round(g("AAA"),1), "link_ytd":round(g("LINK"),1)},
 "sectors": {k:{"contrib":round(sec_contrib[k],2), "perf":round(sec_perf[k],1)} for k in sec_contrib},
 "stocks": {v[0]:{"ytd":round(g(v[0]),1), "contrib":round(float(contrib[v[0]]),2), "sector":v[1]}
            for v in STOCK.values()},
 "macro": {"brent_ytd":round(brent_i.iloc[-1]-100,0), "brent_peak":round(brent_i.max()-100,0),
           "brent_peak_date":str(brent.idxmax().date()),
           "gold_usd_ytd":round(goldu_i.iloc[-1]-100,1), "gold_usd_peak":round(goldu_i.max()-100,0),
           "gold_eur_ytd":round(g("GOLD"),1),
           "eurusd_ytd":round((eurusd.iloc[-1]/eurusd.iloc[0]-1)*100,1)},
}
json.dump(snap, open(os.path.join(OUT,"suivi_ytd.json"),"w"), ensure_ascii=False, indent=1)
print("5 figures FR/EN + suivi_ytd.json ecrits dans outputs/figures/")
print(json.dumps(snap, ensure_ascii=False))
