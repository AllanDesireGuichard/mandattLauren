# Mandat Lauren — gestion privée 100 M€

Cas de pitch private banking. Livrables : **PowerPoint** (pitch client) et
**app Streamlit**.

---

## Le cas

M. Lauren, 60 ans, marié, 2 enfants, résident fiscal français. 100 M€ après
cession d'une startup tech. Besoin de liquidité de 10 M€ sous 2 ans. Objectif :
protéger le reste contre une inflation de 4 %. Contrainte : perte maximum 15 %.
Exclusions ESG tabac / armement / charbon. Transmission progressive aux enfants.
Le fils veut de la crypto, le père hésite. Client inquiet sur l'Europe **et**
sur les États-Unis.

> **Hypothèse de travail :** le patrimoine est déjà en euros. Pas de décision
> de conversion du notionnel ; la couverture de change des actifs étrangers
> reste une décision d'allocation.

---

## Où en est le projet

| Étape | État |
|---|---|
| 0 — IPS chiffré, budget de risque | ✅ |
| Passe de validation empirique | ✅ 4 corrections majeures |
| 1 — Univers investissable | ✅ 226 candidats → 48 supports |
| 2 — Capital Market Assumptions | ✅ |
| 3 — Optimisation SAA | ✅ |
| 4 — Stress tests et drawdown approfondi | ⬜ prochaine |
| 5 — Benchmark hybride | ⬜ |
| 6 — Backtest | ⬜ |
| 7 — Modules fiscalité / transmission | ⬜ |
| 8 — App Streamlit (8 onglets) | ⬜ |
| 9 — Export PowerPoint | ⬜ |

## Les chiffres actuels

```
Actifs                   100 M€        Volatilité            9,86 %
Besoin de liquidité       10 M€        Drawdown P90          12,0 %   < 15 %
Rendement requis          4,85 %       Pire cas (2008)       24,6 %   ← à dire
Rendement attendu         5,98 %       Actifs de croissance    50 %
Marge                    +1,13 %       Plafond crypto           2 %
```

## L'allocation stratégique

```
actions développées      26 %          indexées inflation    14 %
actions émergentes       12 %  plafond souverain EUR          8 %  plancher
infrastructure           10 %  plafond crédit IG EUR          8 %
crypto                    2 %  figé
                       ──────                              ──────
croissance               50 %          obligataire          30 %

or                        6 %  plancher   poche A           10 %  (5 % monétaire
alternatifs               4 %                                      + 5 % souv. court)
```

---

## Structure

### Documents

| Fichier | Contenu |
|---|---|
| `docs/01_concepts_et_process.md` | **Support de préparation orale.** 14 concepts au format *L'idée / Au client / Si on me challenge*. Version publiée : `outputs/argumentaire.html` |
| `docs/02_ips.md` | Investment Policy Statement, v1.3, avec journal de révision |
| `docs/04_conventions_deck.md` | Convention de présentation reprise du pitch TCP Kenz |

### Code

| Module | Rôle |
|---|---|
| `core/ips.py` | **Source unique de vérité.** Le mandat en code, auto-testé à l'exécution |
| `core/cma.py` | Hypothèses de marché. Blocs constitutifs, provenance étiquetée, coefficients de répercussion de l'inflation |
| `core/optimizer.py` | Black-Litterman, parité de risque, resampling de Michaud |
| `core/esg.py` | Exclusions et **portée** du filtre (exigé / sans objet / sous condition) |
| `core/universe.py` | Univers retenu, trous identifiés, pièges de ticker |
| `core/metrics.py` | Métriques de sélection d'instruments |
| `core/quality.py` | **Contrôle qualité des prix.** Indispensable |
| `core/data.py` | Chargeur robuste (retry, replis, cache incrémental) |

### Scripts

```
build_universe.py       construit les candidats (equitydb2 + extension)
fetch_candidates.py     récupère les prix
enrich_names.py         complète les libellés via yfinance
select_instruments.py   sélectionne principal + suppléants par classe
estimate_dd_ratio.py    relation volatilité / perte maximale
validate_saa_risk.py    teste l'allocation contre la contrainte de 15 %
estimate_cma.py         volatilités, corrélations, test de l'objectif
optimize_saa.py         optimisation en deux passages
```

---

## Pièges à ne pas réapprendre

**Les données d'equitydb2 sont partiellement corrompues.** Les séries Yahoo des
lignes londoniennes mélangent les devises de cotation — `SPXS.L` chute de 99 %
le 2014-01-02 (passage pence → livres), `SGLN.L` oscille entre deux lignes.
Sans filtre, un ETF d'obligations d'État 1-3 ans affiche 29 % de volatilité.
**Toujours passer par `core/quality.py`.**

**Vérifier les libellés, jamais deviner sur le ticker.** `CTA.L` est
*CT Automotive Group plc*, pas un fonds de tendance. `XZEC.DE` et `EEDS.L` sont
des fonds d'actions, pas du crédit.

**yfinance échoue par intermittence, ticker par ticker.** Un ticker qui répond
peut échouer vingt minutes plus tard. Ne pas utiliser `yf.download()` sur une
liste — passer par `core/data.py`.

**La parité de risque dégénère si le monétaire est dans l'univers** (82 % de
monétaire). La poche de liquidité est une décision de politique, jamais un
arbitrage d'optimisation.

**Le suivi de tendance n'est pas achetable en ETF UCITS.** Vérifié sur 226
candidats. Passe par un fonds logé dans le contrat luxembourgeois.

---

## Points ouverts

- Barème art. 669 CGI à faire confirmer par un notaire — l'argument du
  calendrier de donation en dépend
- Hypothèses de rendement actions / émergents / infrastructure à recouper avec
  JPM LTCMA et BlackRock CMA
- Brique « suivi de tendance » : retirer du §7 de l'argumentaire, ou assumer
  qu'elle passe par un fonds
- Fenêtre de corrélation limitée à 6,2 ans (couvre 2022, ni 2008 ni 2011)

---

## Lancer

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

PYTHONPATH=. python3 core/ips.py              # contrôles de cohérence
PYTHONPATH=. python3 scripts/optimize_saa.py  # optimisation (~10 min)
```
