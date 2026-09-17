# Documentation

Le périmètre du projet a été recadré le **17 septembre 2026**. L'application
documente désormais une **chaîne d'investissement en cinq étapes**, et la
documentation vit dans l'application elle-même : chaque étape porte ses
encadrés dépliables, rédigés en paragraphes.

```
1. Paramètres d'entrée    ce que le mandat impose
2. Macro top-down         où nous sommes dans le cycle
3. Analyse ligne à ligne   ce qui est investissable
4. Allocation             combien de chaque
5. Backtests              ce que la contrainte donne
```

C'est un choix délibéré : un document Markdown à côté d'une application
divergent toujours, et c'est ce qui s'est produit dans la version précédente.

## Ce qui a été retiré du périmètre

La fiscalité, la transmission et la structuration d'enveloppe. Le travail
correspondant est dans `archive/` et dans l'historique git — il n'est pas
perdu, il n'est simplement plus ce qu'on démontre.

Il faut savoir qu'on y abandonne le résultat le plus puissant du dossier : la
structuration valait environ **50 M€** de patrimoine net transmis, contre
**5,5 M€** pour l'ensemble de l'optimisation d'allocation. Un facteur neuf.

## Les documents de l'ancien périmètre

- `archive/docs/01_concepts_et_process.md` — concepts au format
  *L'idée / Au client / Si on me challenge*
- `archive/docs/02_ips.md` — la politique d'investissement rédigée, avec son
  journal de révision (§11)
- `archive/docs/04_conventions_deck.md` — conventions de présentation reprises
  du document TCP Kenz

## Sources de données

| Source | Accès | Ce qu'elle apporte |
|---|---|---|
| Courbe zéro-coupon AAA zone euro (BCE) | libre, quotidienne | obligataire souverain en direct |
| FRED (St. Louis Fed) | clé gratuite, via `st.secrets` | activité, courbes, spreads, points d'inflation |
| yfinance | libre | prix et fondamentaux actions |

La clé FRED **ne doit jamais entrer dans ce dépôt**, qui est public — c'est la
condition du niveau gratuit de Streamlit Community Cloud. En local elle vit
dans `.streamlit/secrets.toml` (non versionné) ; en ligne dans
*Manage app › Settings › Secrets*.
