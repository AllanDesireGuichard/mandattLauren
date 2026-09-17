"""
Moteur de transmission.

CHANGEMENT DE FONCTION OBJECTIF. Le client ne cherche pas a maximiser sa
fortune, mais CE QUI ARRIVE A SES ENFANTS. Ce n'est pas le meme probleme :

    objectif classique    max  E[ patrimoine final ]
    objectif du dossier   max  E[ patrimoine final x (1 - cout de transmission) ]

Entre les deux il peut y avoir 45 points d'ecart. Aucune decision d'allocation
ne produira jamais un gain de cette ampleur -- c'est pourquoi ce module compte
davantage que l'optimiseur.

RESERVE, a enoncer aussi en rendez-vous. Ce module applique des regles
fiscales a ma connaissance exactes au 17 septembre 2026. Il ne remplace pas
un notaire. Trois sujets ne sont deliberement PAS modelises :
  - le regime matrimonial et les droits du conjoint survivant (exonere de
    droits de succession, mais sa part reduit celle des enfants)
  - la reserve hereditaire et la quotite disponible
  - le rapport fiscal des donations anterieures de moins de 15 ans
Ils changent les montants, pas la hierarchie des leviers.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.ips import (AV_ALLOWANCE_PER_BENEFICIARY, AV_RATE_HIGH, AV_RATE_LOW,
                      AV_THRESHOLD, DONATION_ALLOWANCE, SUCCESSION_ALLOWANCE,
                      SUCCESSION_SCALE, bare_ownership_value)


def bareme_ligne_directe(taxable: float) -> float:
    """Bareme progressif des mutations a titre gratuit en ligne directe."""
    if taxable <= 0:
        return 0.0
    tax, lower = 0.0, 0.0
    for upper, rate in SUCCESSION_SCALE:
        if taxable <= lower:
            break
        tax += (min(taxable, upper) - lower) * rate
        lower = upper
    return tax


def droits_succession(montant: float, n_enfants: int = 2) -> float:
    """Droits de succession, montant reparti egalement entre les enfants."""
    part = montant / n_enfants
    return n_enfants * bareme_ligne_directe(max(part - SUCCESSION_ALLOWANCE, 0.0))


def droits_donation_np(montant_pp: float, age: int, n_enfants: int = 2,
                       n_parents: int = 2,
                       abattement_dispo: bool = True) -> tuple[float, float]:
    """
    Donation de la NUE-PROPRIETE d'un actif de valeur `montant_pp`.

    Le levier tient en deux effets :
      1. la base taxable n'est pas 100 % de l'actif mais la seule valeur de la
         nue-propriete, selon le bareme legal de l'age du donateur (art. 669
         CGI) -- 50 % a 60 ans, 60 % des 61 ans
      2. TOUTE L'APPRECIATION FUTURE appartient deja aux enfants, et
         l'usufruit s'eteint au deces SANS DROIT

    Retourne (droits dus, base taxable).
    """
    base = montant_pp * bare_ownership_value(age)
    part = base / n_enfants
    abat = (DONATION_ALLOWANCE * n_parents) if abattement_dispo else 0.0
    droits = n_enfants * bareme_ligne_directe(max(part - abat, 0.0))
    return droits, base


def droits_assurance_vie(capital: float, n_beneficiaires: int = 2) -> float:
    """
    Art. 990 I CGI -- primes versees AVANT 70 ans.

    Abattement de 152 500 EUR par beneficiaire, puis 20 % jusqu'a 700 000 EUR
    et 31,25 % au-dela. A comparer a un bareme successoral qui monte a 45 %.
    """
    part = capital / n_beneficiaires
    taxable = max(part - AV_ALLOWANCE_PER_BENEFICIARY, 0.0)
    if taxable <= AV_THRESHOLD:
        t = taxable * AV_RATE_LOW
    else:
        t = AV_THRESHOLD * AV_RATE_LOW + (taxable - AV_THRESHOLD) * AV_RATE_HIGH
    return n_beneficiaires * t


def taux_effectif(droits: float, transmis: float) -> float:
    return droits / transmis if transmis > 0 else 0.0


# --------------------------------------------------------------------------

@dataclass
class Poche:
    """Une enveloppe, son encours, et la regle fiscale qui s'y applique."""
    nom: str
    montant: float
    regime: str            # "succession" | "av_990i" | "deja_transmis"
    note: str = ""

    def croitre(self, taux: float, annees: float) -> None:
        self.montant *= (1 + taux) ** annees

    def droits_au_deces(self, n_enfants: int = 2) -> float:
        if self.regime == "succession":
            return droits_succession(self.montant, n_enfants)
        if self.regime == "av_990i":
            return droits_assurance_vie(self.montant, n_enfants)
        return 0.0            # deja transmis : l'usufruit s'eteint sans droit
