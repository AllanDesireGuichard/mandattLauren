"""
Benchmark hybride du mandat.

PRINCIPE : le benchmark ne se choisit pas, il se DEDUIT de l'allocation
strategique. Memes poids, memes indices filtres, meme devise, meme politique
de couverture. La seule difference : il est purement passif.

CONSEQUENCE A ASSUMER DEVANT LE CLIENT.
    Si le benchmark porte les memes poids que notre allocation strategique,
    alors au niveau STRATEGIQUE l'ecart est nul par construction. Ce n'est pas
    un defaut, c'est le bon reglage : le client a valide cette allocation, elle
    ne doit donc pas etre une source de sur- ou sous-performance mesuree.

    Ce que le benchmark mesure reellement, c'est :
      1. les ecarts TACTIQUES (bandes de +/- 3 points, IPS §9.2)
      2. la SELECTION d'instruments (ecart de suivi des fonds vs leur indice)
      3. le TIMING de rebalancement

    Autrement dit : il mesure notre execution, pas notre allocation. C'est
    exactement ce qu'un client doit pouvoir juger -- il a deja juge
    l'allocation en la validant.

DOUBLE REFERENCE. Un benchmark relatif ne dit pas si l'objectif du client est
atteint : on peut battre son indice et s'appauvrir. On lui adjoint donc une
reference ABSOLUE -- inflation + 0 %, net de frais et d'impots.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.ips import SAA_INDICATIVE


@dataclass(frozen=True)
class Component:
    saa_class: str
    index_name: str
    currency: str
    hedge: float          # part couverte contre l'EUR
    esg: bool
    tracker: str          # support investissable de reference
    note: str

    @property
    def weight(self) -> float:
        return SAA_INDICATIVE[self.saa_class]


COMPONENTS: tuple[Component, ...] = (
    Component("equity_developed",
              "MSCI World ESG Screened Net Total Return", "EUR", 0.40, True,
              "XZW0.DE",
              "ESG Screened et non SRI : le mandat demande trois exclusions "
              "precises, pas une demarche best-in-class. L'univers reste a "
              "~95 % de l'indice parent."),
    Component("equity_emerging",
              "MSCI Emerging Markets ESG Screened NTR", "EUR", 0.00, True,
              "XZEM.DE",
              "Non couvert : la devise participe au moteur de performance."),
    Component("infrastructure",
              "FTSE Global Core Infrastructure 50/50 filtre ESG", "EUR", 0.40,
              True, "NFRA.L",
              "SEUL COMPOSANT FRAGILE. Le tracker filtre ESG n'a que 3,1 ans. "
              "Pour l'historique du benchmark, on substitue MSCI World "
              "Utilities (XDWU.DE, 10,4 ans) et on mesure separement l'ecart "
              "sur la periode commune."),
    Component("crypto",
              "Bitcoin -- cours de reference en EUR", "EUR", 0.00, False,
              "BTCE.DE",
              "Composant inhabituel dans un benchmark. Il y figure parce que "
              "la ligne existe dans le portefeuille : un benchmark qui "
              "l'ignorerait ferait passer toute performance crypto pour de "
              "l'alpha, ce qui serait malhonnete."),
    Component("inflation_linked",
              "Bloomberg Euro Government Inflation-Linked Bond", "EUR", 1.00,
              False, "XEIN.DE",
              "Dette souveraine : le filtre ESG est sans objet, il n'y a pas "
              "d'emetteur d'entreprise a exclure."),
    Component("govt_bonds_eur",
              "iBoxx EUR Sovereigns", "EUR", 1.00, False, "XGLE.DE",
              "Idem : filtre sans objet."),
    Component("credit_ig_eur",
              "Bloomberg Euro Aggregate Corporate SRI", "EUR", 1.00, True,
              "SUOE.L",
              "Filtre EXIGE : il y a des emetteurs d'entreprise. Filtrer les "
              "actions sans filtrer le credit serait incoherent, et le client "
              "peut le relever."),
    Component("gold",
              "LBMA Gold Price PM, en EUR", "EUR", 0.00, False, "4GLD.DE",
              "Non couvert : couvrir annulerait sa fonction de reserve de "
              "valeur (IPS §6.4)."),
    Component("alternatives",
              "Bloomberg Commodity ex-Agriculture & Livestock", "EUR", 0.40,
              False, "XDBC.DE",
              "Indice de matieres premieres : aucun emetteur, filtre sans "
              "objet. Note : la brique 'suivi de tendance' du §7 de "
              "l'argumentaire n'est PAS representee ici -- elle n'existe pas "
              "en ETF UCITS."),
    Component("govt_bonds_eur_short",
              "iBoxx EUR Sovereigns 1-3", "EUR", 1.00, False, "MTA.PA",
              "Poche A."),
    Component("cash",
              "€STR capitalise", "EUR", 1.00, False, "XEON.DE",
              "Poche A. Reference du taux sans risque du mandat."),
)

# --------------------------------------------------------------------------

REBALANCING = "trimestriel, aux poids cibles, a cours de cloture du dernier " \
              "jour ouvre du trimestre"

ABSOLUTE_REFERENCE = "inflation constatee + 0 %, nette de frais et d'impots"


def weights() -> dict[str, float]:
    return {c.index_name: c.weight for c in COMPONENTS}


def trackers() -> dict[str, str]:
    """Classe d'actifs -> support servant a reconstituer la serie."""
    return {c.saa_class: c.tracker for c in COMPONENTS}


def validity_checks() -> list[tuple[str, bool, str]]:
    """Les quatre criteres de validite (IPS §8), verifies mecaniquement."""
    total = sum(c.weight for c in COMPONENTS)
    esg_ok = all(c.esg for c in COMPONENTS
                 if c.saa_class in {"equity_developed", "equity_emerging",
                                    "credit_ig_eur", "infrastructure"})
    return [
        ("Investissable -- chaque composant a un tracker identifie",
         all(c.tracker for c in COMPONENTS),
         f"{len(COMPONENTS)} composants, {len(set(trackers().values()))} supports"),
        ("Replicable -- ponderations publiques et regle de rebalancement ecrite",
         True, REBALANCING),
        ("Coherent en devise -- libelle EUR, meme politique de couverture",
         all(c.currency == "EUR" for c in COMPONENTS),
         "couverture reprise de l'IPS §6.4, composant par composant"),
        ("Coherent en ESG -- filtre la ou il est exige",
         esg_ok,
         "actions, emergents, credit et infrastructure : filtres. "
         "Souverain, or, matieres premieres, monetaire : sans objet"),
        ("Somme des poids = 100 %", abs(total - 1.0) < 1e-9, f"{total:.1%}"),
    ]
