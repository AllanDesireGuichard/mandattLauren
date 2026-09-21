/*
 * Dossier technique du mandat Lauren -> outputs/Mandat_Lauren_dossier_technique.docx
 *
 * Lancer :  node scripts/dossier_technique.js
 *
 * A QUOI IL SERT. Le deck repond a « qu'est-ce que vous proposez ». Ce
 * document repond a « pourquoi, et comment le savez-vous ». Il est fait pour
 * etre lu AVANT la soutenance et garde sous la main pendant les questions,
 * pas pour etre projete.
 *
 * Les chiffres sont ecrits en dur ici, et c'est assume : c'est une PHOTO
 * datee de l'etat du dossier, pas une sortie vivante de l'application. Si
 * les donnees changent, ce document se refait, il ne se met pas a jour.
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, TableOfContents, LevelFormat,
} = require("docx");

// --- raccourcis -----------------------------------------------------------
const ENCRE = "14304F";
const GRIS = "5A6069";

const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 160 } });
const H2 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 120 } });
const H3 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_3,
  spacing: { before: 200, after: 100 } });

/* Paragraphe avec gras en ligne : le texte est decoupe sur ** ** */
const P = (t, opts = {}) => {
  const morceaux = String(t).split("**");
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: opts.justify === false ? undefined : AlignmentType.JUSTIFIED,
    children: morceaux.map((m, i) => new TextRun({ text: m, bold: i % 2 === 1 })),
  });
};

const PUCE = (t) => {
  const morceaux = String(t).split("**");
  return new Paragraph({
    numbering: { reference: "puces", level: 0 },
    spacing: { after: 80, line: 276 },
    children: morceaux.map((m, i) => new TextRun({ text: m, bold: i % 2 === 1 })),
  });
};

/* Encadre : un fond gris clair, pour une mise en garde ou une reponse type */
const CADRE = (titre, texte) => new Table({
  columnWidths: [9360],
  width: { size: 9360, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 2, color: "C9CFD6" },
    bottom: { style: BorderStyle.SINGLE, size: 2, color: "C9CFD6" },
    left: { style: BorderStyle.SINGLE, size: 12, color: ENCRE },
    right: { style: BorderStyle.SINGLE, size: 2, color: "C9CFD6" },
    insideHorizontal: { style: BorderStyle.NONE },
    insideVertical: { style: BorderStyle.NONE },
  },
  rows: [new TableRow({
    children: [new TableCell({
      width: { size: 9360, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: "F2F4F7" },
      margins: { top: 160, bottom: 160, left: 200, right: 200 },
      children: [
        new Paragraph({ spacing: { after: 80 },
          children: [new TextRun({ text: titre, bold: true, color: ENCRE })] }),
        ...String(texte).split("|").map((t) => P(t)),
      ],
    })],
  })],
});

/* Tableau simple : entetes + lignes. Largeurs en DXA, somme = 9360. */
const TAB = (entetes, lignes, largeurs) => {
  const cell = (t, opts = {}) => new TableCell({
    width: { size: opts.w, type: WidthType.DXA },
    shading: opts.head
      ? { type: ShadingType.CLEAR, fill: ENCRE }
      : { type: ShadingType.CLEAR, fill: opts.alt ? "F7F8FA" : "FFFFFF" },
    margins: { top: 90, bottom: 90, left: 130, right: 130 },
    children: [new Paragraph({
      alignment: opts.right ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: String(t).split("**").map((m, i) => new TextRun({
        text: m, bold: opts.head || i % 2 === 1,
        color: opts.head ? "FFFFFF" : undefined, size: 19,
      })),
    })],
  });
  return new Table({
    columnWidths: largeurs,
    width: { size: 9360, type: WidthType.DXA },
    rows: [
      new TableRow({ tableHeader: true, children: entetes.map((t, i) =>
        cell(t, { w: largeurs[i], head: true, right: i > 0 })) }),
      ...lignes.map((ligne, n) => new TableRow({ children: ligne.map((t, i) =>
        cell(t, { w: largeurs[i], alt: n % 2 === 1, right: i > 0 })) })),
    ],
  });
};

const ESPACE = () => new Paragraph({ spacing: { after: 160 }, text: "" });

// ==========================================================================
const corps = [];

// --- page de titre --------------------------------------------------------
corps.push(
  new Paragraph({ spacing: { before: 2400, after: 80 }, children: [
    new TextRun({ text: "Mandat Lauren", bold: true, size: 56, color: ENCRE })] }),
  new Paragraph({ spacing: { after: 400 }, children: [
    new TextRun({ text: "Dossier technique", size: 36, color: GRIS })] }),
  P("Gestion privée · 100 M€ · préserver le pouvoir d'achat sous contrainte de perte maximum de 15 %"),
  ESPACE(),
  P("**À quoi sert ce document.** Le PowerPoint répond à « qu'est-ce que vous proposez ». Celui-ci répond à « pourquoi, et comment le savez-vous ». Il est fait pour être lu avant la soutenance et gardé sous la main pendant les questions. Chaque chiffre y est accompagné de sa méthode, de sa source et de sa limite."),
  P("**État au 21 septembre 2026.** Données de marché relevées le 18/09/2026. Application en ligne : mandat-lauren.streamlit.app"),
  new Paragraph({ children: [new PageBreak()] }),
);

// --- sommaire -------------------------------------------------------------
corps.push(H1("Sommaire"),
  new TableOfContents("Sommaire", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("1. Le cas, et la façon dont il a été lu"));

corps.push(H2("1.1 L'énoncé"));
corps.push(P("M. Lauren, 60 ans, marié, deux enfants, résident fiscal français, vient de céder sa startup. Il dispose de 100 M€. Il aura besoin de 10 M€ dans les deux ans. Il veut protéger le reste contre une inflation de 4 %, sans jamais perdre plus de 15 %. Il exclut le tabac, l'armement et le charbon. Son fils voudrait de la crypto, lui hésite. Il est inquiet sur l'Europe comme sur les États-Unis."));

corps.push(H2("1.2 La lecture retenue, et pourquoi elle n'est pas neutre"));
corps.push(P("Trois décisions de lecture commandent tout le reste. Elles sont contestables, et c'est pour cela qu'elles sont écrites ici."));

corps.push(P("**Le 4 % est un taux d'inflation, pas un objectif de performance.** L'énoncé dit « protéger contre une inflation de 4 % » : le 4 % qualifie l'inflation. L'objectif est donc de préserver le pouvoir d'achat, soit un rendement réel de zéro, soit 4 % nominal. Une autre lecture existe — 4 % **au-dessus** de l'inflation, donc 8 % nominal — et elle a été testée : elle est hors d'atteinte sous la contrainte de perte (voir § 6.4)."));

corps.push(P("**La perte de 15 % se mesure depuis le plus haut atteint, sur les 100 M€ consolidés en euros, et doit tenir au pire cas des crises passées.** C'est la lecture la plus exigeante possible. Une limite sur douze mois glissants, ou une limite en probabilité, auraient toutes deux autorisé nettement plus de rendement. Le choix du pire cas est un choix de prudence assumé, pas une nécessité mathématique."));

corps.push(P("**Les 10 M€ ne participent pas à la recherche de rendement.** Un décaissement quasi certain à moins de deux ans ne peut pas être exposé. On investit donc réellement 90 M€ pour l'objectif, mais la limite de perte se mesure bien sur les 100 M€."));

corps.push(CADRE("Hypothèse de travail sur la devise",
  "Le patrimoine est déjà en euros et il n'y a pas de décision de conversion du notionnel. La couverture de change des actifs étrangers reste, elle, une décision d'allocation : elle est traitée à l'étape 3 (§ 4.4).|Toutes les performances de ce dossier sont exprimées en euros, dividendes réinvestis. C'est ce qu'aurait vécu le client."));

corps.push(H2("1.3 Les questions que l'énoncé laisse ouvertes"));
corps.push(P("Elles sont posées dans l'application plutôt que tranchées en silence. Faute de réponse du client, chacune a reçu une hypothèse de travail, énoncée à l'étape où elle intervient."));
corps.push(PUCE("**La perte de 15 %** : sur quelle durée, et est-ce une limite absolue ou tolérable si rare ? Une limite « jamais » est impossible à garantir pour un portefeuille investi."));
corps.push(PUCE("**L'inflation à 4 %** : prévision ou scénario de prudence ? Quelle inflation, française ou européenne ? Et « protéger » veut-il dire chaque année, ou en moyenne sur dix ans ?"));
corps.push(PUCE("**L'horizon** : à 60 ans, avec une transmission en vue, l'horizon réel dépasse probablement celui du client."));
corps.push(PUCE("**Les 10 M€** : pour quoi faire, et à quelle date ? Un achat immobilier daté ne se gère pas comme une réserve."));

corps.push(H2("1.4 Ce qui est hors périmètre"));
corps.push(P("La fiscalité et la transmission font partie du cas mais pas de cet exercice, qui porte uniquement sur la chaîne d'investissement. C'est une restriction volontaire : traiter les deux superficiellement aurait affaibli l'ensemble. Conséquence à assumer en séance : les rendements présentés sont **bruts de fiscalité**, et le seuil de 4 % est un objectif net. Voir § 9.3."));

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("2. L'architecture : cinq étapes séquentielles"));

corps.push(P("La chaîne va du plus général au plus détaillé, puis vérifie sur le passé. **La sortie de chaque étape est l'entrée de la suivante** : c'est la propriété qui rend le dossier défendable, parce qu'elle permet de remonter n'importe quel chiffre jusqu'à sa source."));

corps.push(TAB(
  ["Étape", "La question", "Ce qu'elle produit"],
  [
    ["1 — Paramètres", "Que demande le client ?", "Contraintes et hypothèses chiffrées"],
    ["2 — Macro", "Où en est l'économie ?", "Un rendement espéré par classe d'actifs"],
    ["3 — Ligne à ligne", "Dans quoi investir ?", "Un support par classe"],
    ["4 — Allocation", "Combien sur chacun ?", "Le portefeuille en millions d'euros"],
    ["5 — Backtests", "Aurait-il tenu ?", "Durée des baisses, mauvaise année"],
  ], [2000, 3400, 3960]));

corps.push(ESPACE());
corps.push(P("C'est le processus d'un fonds multi-actifs. La version précédente du dossier juxtaposait neuf onglets sans ordre lisible ; c'est le reproche principal auquel cette architecture répond."));

corps.push(CADRE("Principe de calcul, à savoir si on vous interroge sur l'outil",
  "L'application **lit** des résultats calculés hors ligne (fichiers `data/`) plutôt que de les recalculer : l'optimisation prend une dizaine de minutes. Ce qui se recalcule en direct le fait sur des formules fermées, donc instantanément.|Conséquence : l'application ne peut pas mentir sur ses chiffres sans qu'on le voie dans le dépôt. Chaque fichier de données porte la date de son relevé."));

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("3. Étape 2 — D'où viennent les rendements espérés"));

corps.push(P("C'est le cœur technique du dossier, et la première chose qu'un jury attaquera. Le principe général : **on n'a rien prévu.** Aucune prévision macroéconomique n'entre dans ces chiffres. Chaque rendement espéré est soit un taux lu sur le marché, soit une valorisation traduite en rendement, soit une hypothèse explicitement identifiée comme telle."));

corps.push(H2("3.1 Les obligations : on lit, on ne prévoit pas"));
corps.push(P("Pour une obligation portée jusqu'à l'échéance, le rendement à maturité **est** le rendement attendu, aux défauts près. Il n'y a donc rien à modéliser : on lit la courbe."));
corps.push(PUCE("**Monétaire** : taux €STR du jour, 2,44 %. Réserve : si 4 % d'inflation s'installait durablement, ce taux monterait ; ce supplément n'est pas compté."));
corps.push(PUCE("**États zone euro** : courbe zéro-coupon de la BCE, modèle de Svensson à six paramètres, publiée quotidiennement. On **price** l'obligation plutôt que d'en chercher une cotation, faute de source fiable et gratuite sur les lignes nommées. La formule redonne les taux publiés à 0,0005 point près (vérifié le 18/09/2026)."));
corps.push(PUCE("**Crédit euro bien noté** : rendement du fonds retenu, moins les pertes sur défauts estimées d'après l'historique Moody's, soit 3,50 − 0,11 = 3,39 %."));
corps.push(PUCE("**Obligations indexées** : taux réel mesuré sur le marché (1,43 %) plus l'inflation de l'énoncé (4 %), soit 5,43 %. Ce sont les seules qui suivent l'inflation par construction."));

corps.push(CADRE("Le point de méthode le plus important de l'étape 2",
  "Le seuil à battre (4 %) est formulé dans un monde à 4 % d'inflation. Les rendements espérés doivent donc l'être aussi, sinon on compare une exigence d'un monde à une performance d'un autre. **Toutes les classes sont donc ramenées à un régime d'inflation de 4 %.**|Une version antérieure du dossier comparait un seuil bâti sur 4 % d'inflation à des rendements bâtis implicitement sur 2 %. Le mandat paraissait alors beaucoup plus difficile qu'il ne l'est. C'est la correction la plus importante de tout le projet."));

corps.push(H2("3.2 Les actions : deux méthodes, moyennées"));
corps.push(P("Aucune prévision de bénéfices, aucun modèle de croissance par zone. On part du prix payé aujourd'hui."));

corps.push(H3("Méthode 1 — par les bénéfices"));
corps.push(P("Rendement réel ≈ 1 / PER. À un PER de 20, on achète 5 % de bénéfices par an. Sur longue période, c'est une bonne estimation du rendement au-delà de l'inflation."));
corps.push(H3("Méthode 2 — par le dividende et la croissance"));
corps.push(P("Rendement réel ≈ dividende + croissance réelle des bénéfices. La croissance retenue est **2,0 % par an, la même pour toutes les zones** : c'est la croissance réelle des bénéfices du S&P 500 depuis 1900 (Shiller)."));
corps.push(P("Rendement espéré = moyenne des deux, plus 4 % d'inflation — les entreprises répercutant la hausse des prix dans leurs bénéfices."));

corps.push(ESPACE());
corps.push(TAB(
  ["Classe", "PER", "Div.", "Réel M1", "Réel M2", "Espéré"],
  [
    ["Actions européennes", "18,5", "3,07 %", "5,41 %", "5,05 %", "**9,23 %**"],
    ["Actions américaines", "30,0", "1,06 %", "3,33 %", "3,04 %", "**7,19 %**"],
    ["Actions japonaises", "19,1", "3,66 %", "5,24 %", "5,64 %", "**9,44 %**"],
    ["Actions émergentes", "20,8", "2,96 %", "4,81 %", "4,94 %", "**8,40 %**"],
  ], [2700, 1000, 1200, 1400, 1400, 1660]));

corps.push(ESPACE());
corps.push(P("**Les limites, à dire avant qu'on vous les oppose.** Une croissance identique pour toutes les zones pénalise mécaniquement les États-Unis, dont le poids technologique justifierait davantage. Et le PER dépend de la source : avec les PER Yahoo plutôt qu'iShares, les États-Unis remontent à environ 8,1 %. L'écart Europe / États-Unis se réduit alors fortement, mais il ne s'inverse pas."));
corps.push(P("**Le contrôle externe.** Ces chiffres ont été confrontés aux hypothèses de marché long terme de J.P. Morgan Asset Management (LTCMA 2026, hypothèses en euros, au 30/09/2025, inflation supposée 2 %). Même sens, écart inférieur à un point une fois les régimes d'inflation alignés."));

corps.push(H2("3.3 L'or et les matières premières : une hypothèse, et elle est dite"));
corps.push(P("Ni l'un ni l'autre ne verse de flux : il n'existe aucune méthode d'actualisation. On suppose qu'ils conservent leur pouvoir d'achat, soit l'inflation, 4,00 %, avec une fourchette de deux points de part et d'autre. **C'est une hypothèse, pas une estimation**, et elle est étiquetée comme telle dans l'application."));

corps.push(H2("3.4 Le tableau complet"));
corps.push(TAB(
  ["Classe", "Rendement espéré", "Nature du chiffre"],
  [
    ["Actions japonaises", "9,44 %", "Estimé (valorisation)"],
    ["Actions européennes", "9,23 %", "Estimé (valorisation)"],
    ["Actions émergentes", "8,40 %", "Estimé (valorisation)"],
    ["Actions américaines", "7,19 %", "Estimé (valorisation)"],
    ["Obligations indexées", "5,43 %", "Mesuré + inflation énoncé"],
    ["Or", "4,00 %", "Hypothèse"],
    ["États zone euro 2-10 ans", "3,63 %", "Mesuré (courbe BCE)"],
    ["Crédit euro court", "3,39 %", "Mesuré − défauts"],
    ["États AAA 6-24 mois", "3,03 %", "Mesuré (courbe BCE)"],
    ["Monétaire (€STR)", "2,44 %", "Mesuré"],
  ], [3400, 2600, 3360]));

corps.push(ESPACE());
corps.push(P("**La lecture qui commande l'étape 4** : seules les actions et les obligations indexées dépassent le seuil de 4 %. Aucune obligation à taux fixe ne protège contre 4 % d'inflation. Chaque euro placé en obligations ou en or devra donc être compensé par des actions — c'est toute la tension entre l'objectif de 4 % et la limite de 15 %."));

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("4. Étape 3 — Le choix des supports"));

corps.push(H2("4.1 Les actions européennes : 600 titres, 30 retenus"));
corps.push(P("La poche européenne est construite **titre par titre**, pas achetée en indice. C'est le seul endroit du portefeuille où l'on prétend faire mieux que le marché, et c'est assumé : pour les autres zones, on achète l'indice."));

corps.push(TAB(
  ["Étape du tri", "Titres", "Motif"],
  [
    ["Univers de départ", "600", "Grandes capitalisations européennes"],
    ["Exclusions ESG", "− 26", "Armement 20, tabac 4, charbon 2"],
    ["Non investissables", "− 11", "Liquidité ou données insuffisantes"],
    ["Sous 10 Md€", "− 262", "Grandes capitalisations seulement"],
    ["Notés", "300", "Cinq piliers, au sein du secteur"],
    ["**Retenus**", "**30**", "À parts égales"],
  ], [3600, 1800, 3960]));

corps.push(ESPACE());
corps.push(H3("La notation : cinq piliers à poids égaux"));
corps.push(P("Valorisation, Croissance, Dynamique, Qualité, **Résistance**. Le cinquième a été ajouté spécifiquement pour ce mandat : la limite de perte se tient au niveau du portefeuille, mais un panier d'actions qui baisse moins en crise permet d'en détenir davantage pour la même limite. Poids égaux (20 % chacun) parce qu'aucun pilier n'a de raison mesurée d'être privilégié."));

corps.push(P("**Les notes sont calculées au sein de chaque secteur.** Une banque ne se compare pas à un éditeur de logiciels : leurs PER et leurs marges n'ont pas le même sens. Chaque indicateur est orienté pour que « plus haut = mieux », borné pour détecter les données fausses, écrêté aux 5e et 95e percentiles pour qu'un chiffre extrême ne fasse pas la note à lui seul, puis transformé en écart-type au sein du secteur."));

corps.push(CADRE("Deux corrections qui montrent que le tri a été vérifié",
  "**Les sociétés d'investissement cotées** (Investor, Industrivärden, Exor, Sofina, 3i…) arrivaient en tête du classement. Leur bénéfice comptable inclut la réévaluation de leurs participations : PER, rentabilité et croissance n'ont pas le sens qu'ils ont ailleurs. Elles restent dans l'univers mais sortent de la notation.|**Les bornes de plausibilité** ont attrapé des PER multipliés par cent, Yahoo confondant pence et livres sur les valeurs britanniques ; et l'écrêtage a neutralisé une croissance de bénéfices à −91 % chez Sanofi due à des éléments exceptionnels."));

corps.push(P("Résultat : 30 titres, 10 secteurs, 10 pays, à parts égales. Volatilité sur 3 ans de 10,4 % contre 12,8 % pour le STOXX Europe 600 ; perte de 12,8 % en 2022 contre 18,4 % pour l'indice. **Mais en crise il perd bien plus que 15 %** : c'est le dosage avec les obligations et l'or, à l'étape 4, qui tient la limite."));

corps.push(H2("4.2 Les obligations d'État : achetées en direct"));
corps.push(P("Pas de frais de gestion, et la date et le montant de chaque remboursement connus d'avance. Deux échelles."));
corps.push(PUCE("**Les 10 M€ à décaisser** : une échelle AAA (Allemagne, Pays-Bas) en quatre tranches de 2,5 M€ à 6, 12, 18 et 24 mois, aux taux garantis de 2,75 % à 3,22 %. Coût d'achat 9,63 M€ aujourd'hui, soit 78 k€ économisés face au monétaire."));
corps.push(PUCE("**La poche longue** : une échelle 2-3-5-7-10 ans sur toute la zone euro, rendement moyen 3,63 %, sensibilité −4,7 % si les taux montent d'un point. Allonger au-delà de dix ans rapporte peu et expose beaucoup."));

corps.push(H2("4.3 Le crédit : pourquoi il pèse si peu"));
corps.push(P("La prime de crédit n'a presque jamais été aussi basse : elle n'a été inférieure à son niveau actuel que **2 % du temps en quarante ans** (Moody's Baa depuis 1986). Une remontée d'un point coûterait 4,3 % au crédit euro, soit plus d'un an de rendement. Peu à gagner, beaucoup à perdre. Le fonds retenu rapporte 0,24 point de plus qu'un État de même échéance, 0,13 point après défauts. **Sa place ne pouvait être que modeste, et le calcul l'a ramenée à zéro.**"));

corps.push(H2("4.4 Les fonds, et la question de la couverture de change"));
corps.push(P("Pour les classes non investies en direct, des ETF UCITS. Deux points de méthode."));
corps.push(P("**Les exclusions ESG ont été lues dans les méthodologies MSCI, pas déduites des noms de fonds.** Un fonds « ESG Screened » exclut les armes controversées, le tabac et le charbon, mais **pas** l'armement conventionnel — alors que la sélection en direct exclut tout le secteur défense. Un fonds Screened aurait donc contredit la règle appliquée aux titres. Les fonds retenus sont des « Low Carbon SRI Selection », plus stricts que le mandat."));
corps.push(P("**La couverture de change coûte environ 1,70 % par an** au niveau actuel des écarts de taux. C'est ce qui transforme un Trésor américain à 10 ans de 5,01 % en 3,31 % une fois ramené en euros — sous le rendement d'un État de la zone euro. La couverture est donc appliquée aux obligations étrangères, qu'elle rend inintéressantes, et **pas** aux actions, dont elle absorberait une part excessive du rendement espéré."));

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("5. Étape 4 — Le modèle d'allocation"));

corps.push(H2("5.1 Le problème, écrit"));
corps.push(P("On cherche les poids qui **maximisent le rendement espéré** sous une exigence de risque, poids positifs, somme égale à 100 %, bitcoin hors calcul."));
corps.push(PUCE("**Fonction objectif** : le produit des poids par les rendements espérés de l'étape 2. Elle est linéaire."));
corps.push(PUCE("**Contrainte de risque** : le portefeuille, rééquilibré chaque mois, ne doit jamais avoir perdu plus de 15 % depuis son plus haut sur les séries d'octobre 2006 à septembre 2026."));

corps.push(H2("5.2 Pourquoi pas Markowitz"));
corps.push(CADRE("La question sera posée, voici la réponse",
  "La contrainte du client n'est pas une volatilité, c'est une **perte maximale depuis le plus haut**. Ce n'est pas la même chose : une perte maximale est un maximum le long d'un chemin, elle dépend de l'ordre dans lequel les rendements arrivent. Elle ne se déduit pas d'une matrice de covariance, qui ignore l'ordre.|Optimiser une variance puis espérer que la perte maximale suive aurait été un raccourci non vérifié. On optimise donc **directement sur le chemin historique**.|Le prix de ce choix est réel et il est payé explicitement : le calcul apprend le passé par cœur. C'est pourquoi le résultat brut est rejeté et corrigé par des règles (§ 5.4). Black-Litterman a été écarté pour une autre raison : les vues de l'étape 2 sont déjà dans les rendements espérés, les y réinjecter serait les compter deux fois."));

corps.push(H2("5.3 La résolution"));
corps.push(P("La pire baisse n'est pas une fonction lisse des poids : un optimiseur à base de gradient peut s'arrêter sur un mauvais point. On part donc de **seize répartitions tirées au hasard** (loi de Dirichlet, graine fixée à 0, donc reproductible), on résout chacune par SLSQP, et on garde le meilleur résultat qui respecte la limite. Le rééquilibrage mensuel est évalué en matrices pour que l'optimiseur puisse l'appeler des milliers de fois."));

corps.push(H2("5.4 Les règles, une par une, et ce qu'elles coûtent"));
corps.push(P("Le calcul libre est relancé en ajoutant une règle à la fois, chaque ligne gardant les précédentes. C'est le tableau le plus important du dossier : il chiffre le prix de chaque précaution."));

corps.push(TAB(
  ["Règle ajoutée", "Rdt", "Coût", "Répartition obtenue"],
  [
    ["Seule la limite de 15 %", "6,47 %", "—", "Indexées 55, Japon 32, États longs 9"],
    ["+ 10 % sur l'échelle AAA", "6,46 %", "−0,01", "Indexées 58, Japon 32, AAA 10"],
    ["+ clé actions 40/35/10/15", "5,78 %", "−0,68", "Indexées 70, actions 20, AAA 10"],
    ["+ plafonds par ligne", "5,40 %", "−0,38", "États longs 37, actions 32, indexées 15"],
    ["+ marge à 14 %", "**5,31 %**", "−0,09", "États longs 41, actions 30, indexées 15"],
  ], [2900, 1100, 1000, 4360]));

corps.push(ESPACE());
corps.push(H3("Comment lire chaque ligne"));
corps.push(P("**6,47 % — le calcul libre.** Une seule exigence. Il répond 55 % d'indexées et 32 % de Japon. Ce n'est pas une proposition, c'est un **plafond** : rien, sous la règle des 15 %, ne fera mieux."));
corps.push(P("**−0,01 point pour les 10 M€.** Le résultat le plus contre-intuitif, et le meilleur argument client du dossier. Le calcul a payé l'échelle AAA (3,03 %) en vendant les États longs (3,63 %) et le crédit (3,39 %) : il a troqué une obligation médiocre contre une autre. **Sécuriser la liquidité du client ne coûte rien.**"));
corps.push(P("**−0,68 point pour la clé actions. La règle la plus chère.** Le calcul libre mettait 32 % sur le Japon et zéro sur l'Europe, les États-Unis et les émergents. On impose donc une clé géographique fixe — 40 % Europe, 35 % États-Unis, 10 % Japon, 15 % émergents — et le calcul ne décide plus que de la **taille** de la poche actions, pas de sa composition. Ce que ces 0,68 point achètent : aucun pari sur un pays, aucun pari sur une devise."));
corps.push(P("**−0,38 point pour les plafonds.** La ligne précédente mettait 70 % sur un seul support. Plafonds : indexées ≤ 15 %, or ≤ 10 %, matières premières ≤ 5 %, crédit ≤ 20 %. Effet de bord notable : le portefeuille devient plus diversifié **et** plus actions, parce que plafonner les indexées ne laisse que les actions pour tenir le rendement."));
corps.push(P("**−0,09 point pour la marge à 14 %.** La seule règle qui ne vienne pas du client. Avant 2018, plusieurs supports sont mesurés par des remplaçants parfois flatteurs ; viser 14 % laisse un point de jeu pour l'erreur de mesure. C'est l'assurance la moins chère du tableau."));

corps.push(CADRE("La colonne que personne ne regarde",
  "La pire baisse affiche −15,0 % sur les quatre premières lignes. Ce n'est pas une coïncidence : le calcul maximise le rendement, donc il va systématiquement s'écraser contre la limite. **À chaque étape, ce qui l'arrête c'est le risque, jamais les règles.** Les règles ne font que changer la façon dont il dépense un budget de risque constant."));

corps.push(H2("5.5 Le portefeuille retenu"));
corps.push(TAB(
  ["Ligne", "Poids", "Montant", "Rendement espéré"],
  [
    ["États zone euro 2-10 ans", "41 %", "41,3 M€", "3,63 %"],
    ["Actions européennes (30 titres)", "12 %", "12,2 M€", "9,23 %"],
    ["Actions américaines", "11 %", "10,6 M€", "7,19 %"],
    ["Obligations indexées", "15 %", "15,0 M€", "5,43 %"],
    ["États AAA 6-24 mois", "10 %", "10,0 M€", "3,03 %"],
    ["Actions émergentes", "5 %", "4,6 M€", "8,40 %"],
    ["Actions japonaises", "3 %", "3,0 M€", "9,44 %"],
    ["Or", "3 %", "3,3 M€", "4,00 %"],
  ], [3600, 1400, 1800, 2560]));

corps.push(ESPACE());
corps.push(P("**30 % d'actions, 66 % d'obligations, 3 % d'or.** Rendement espéré 5,31 %, pire baisse 14,0 %. Les actions font 30 % du patrimoine mais 48 % du rendement espéré : elles portent l'objectif, les obligations tiennent la limite."));

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("6. Étape 5 — Ce que le backtest prouve, et ce qu'il ne prouve pas"));

corps.push(CADRE("À dire avant qu'on vous le reproche",
  "Les vingt années de données sont **celles qui ont servi à construire le portefeuille**. L'étape 4 a cherché une répartition qui ne perde jamais plus de 14 % sur cette période : qu'elle n'y perde pas plus de 14 % est donc **acquis d'avance** et ne dit rien de la prochaine crise.|Le rejeu sert à mesurer ce que le calcul n'a pas regardé : la **durée** des baisses et la fréquence des mauvaises années."));

corps.push(H2("6.1 Le parcours"));
corps.push(P("100 M€ en octobre 2006 deviennent 239 M€ en septembre 2026, soit **4,47 % par an**, rééquilibrage mensuel. Pire baisse 14,0 % (2008 et 2020)."));

corps.push(H2("6.2 La durée, qui est le vrai enseignement"));
corps.push(TAB(
  ["Mesure", "Valeur"],
  [
    ["Temps passé à plus de 1 % sous le plus haut", "53 %"],
    ["Temps passé à plus de 5 % sous le plus haut", "17 %"],
    ["Temps passé à plus de 10 % sous le plus haut", "4 %"],
    ["Plus longue période sous l'eau (2022)", "32 mois"],
  ], [6400, 2960]));

corps.push(ESPACE());
corps.push(P("**2022 est la crise la plus instructive du lot** : 32 mois sous l'eau pour une baisse pourtant moindre qu'en 2008. La raison est que les obligations ont baissé **avec** les actions, ce qu'un portefeuille équilibré classique ne prévoit pas. C'est le régime que redoute précisément le client."));

corps.push(H2("6.3 À quoi ressemble une mauvaise année"));
corps.push(P("Sur 228 années glissantes, à chaque fin de mois depuis octobre 2007 : VaR 95 % à −6,5 %, CVaR 95 % à −8,5 %, pire année −11,4 %, 18 % des années en perte."));
corps.push(P("**Le point de lecture** : la pire année fait −11,4 % alors que la pire baisse atteint 14 %. L'écart vient des baisses longues — en 2008 comme en 2022, la perte s'est accumulée sur plus d'un an. C'est exactement pour cela que la limite a été mesurée depuis le plus haut et non sur douze mois : une limite annuelle aurait laissé passer ces baisses."));

corps.push(H2("6.4 La variante testée et écartée : viser 4 % au-dessus de l'inflation"));
corps.push(P("Si l'objectif était 4 % **réel**, soit 8 % nominal, il serait hors d'atteinte sous la règle de l'étape 4 : le plafond y est de 6,47 %. En remplaçant le pire cas par une limite en fréquence (dépasser 15 % au plus une année sur vingt), la cible devient atteignable — mais à un prix qui la disqualifie."));

corps.push(TAB(
  ["Contrainte de risque", "Rdt max", "VaR 95 %", "CVaR 95 %", "Pire baisse"],
  [
    ["Pire baisse ≥ −15 % (retenue)", "6,47 %", "−6,9 %", "−8,9 %", "−15,0 %"],
    ["VaR 95 % ≥ −15 %", "8,42 %", "−15,0 %", "**−29,5 %**", "**−51,5 %**"],
    ["CVaR 95 % ≥ −15 %", "7,77 %", "−13,5 %", "−15,0 %", "−32,3 %"],
    ["Aucune", "9,44 %", "−25,2 %", "−27,0 %", "−52,7 %"],
  ], [2900, 1400, 1600, 1700, 1760]));

corps.push(ESPACE());
corps.push(P("**Trois raisons de refuser.** En CVaR — la mesure qui dit **de combien** on dépasse — on plafonne à 7,77 %, sous la cible. En VaR la cible passe, mais la contrainte ne contraint plus rien : les années de dépassement coûtent 29,5 % en moyenne et 51,5 % au pire. Enfin, ces quantiles sont estimés sur des fenêtres qui se chevauchent et ne reposent que sur sept épisodes de baisse distincts en vingt ans."));
corps.push(P("Ces calculs sont conservés hors de l'application ; ils existent pour répondre à la question, pas pour être proposés."));

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("7. Les données : ce qui vient d'où"));

corps.push(TAB(
  ["Source", "Ce qu'elle fournit", "Limite connue"],
  [
    ["BCE — courbe zéro-coupon", "Taux d'État zone euro et AAA, toutes échéances", "Modèle de Svensson, pas des cotations réelles"],
    ["FRED (St. Louis Fed)", "Activité, courbes, primes de crédit, inflation", "Clé gratuite ; séries parfois révisées"],
    ["Yahoo Finance", "Prix, fondamentaux, changes", "Données fondamentales inégales ; pence/livres"],
    ["Fiches iShares / justETF", "PER, dividendes, frais, taille des fonds", "Photo datée, pas une série"],
    ["Moody's (via FRED)", "Pertes sur défauts, primes Baa depuis 1986", "Marché américain, transposé à l'euro"],
    ["Shiller", "Croissance réelle des bénéfices depuis 1900", "S&P 500 uniquement, appliqué à toutes zones"],
    ["J.P. Morgan LTCMA 2026", "Contrôle externe des rendements espérés", "Inflation supposée 2 %, à réaligner"],
  ], [2300, 3400, 3660]));

corps.push(ESPACE());
corps.push(H2("7.1 Les pièges de données qui ont été rencontrés et corrigés"));
corps.push(P("Ils sont listés parce qu'ils produisent des chiffres faux **invisibles** : rien ne signale l'erreur, le résultat a l'air normal."));
corps.push(PUCE("**Devises de cotation.** Un même ETF coté à Francfort et à Londres donne deux performances différentes. Toutes les séries sont ramenées en euros, dividendes réinvestis."));
corps.push(PUCE("**Libellés trompeurs.** L'univers hérité contenait neuf fonds dont le nom ne correspondait pas au produit. Les séries de prix étaient les bonnes — c'est le nom qui était faux, ce qu'aucun contrôle de volatilité ne pouvait détecter."));
corps.push(PUCE("**Fenêtres non comparables.** Comparer deux actifs sur des périodes différentes produit un classement faux. Toutes les comparaisons de ce dossier partent d'octobre 2006, date de la plus courte série disponible."));
corps.push(PUCE("**Remplaçants avant 2018.** Plusieurs supports n'existaient pas sur toute la période et sont représentés par un indice proche. C'est la raison de la marge de prudence à 14 %."));

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("8. Les questions de fond, et comment y répondre"));

corps.push(P("Chaque question ci-dessous a été identifiée comme une attaque plausible. La réponse donnée est celle que les chiffres autorisent, pas celle qui arrange."));

const QA = [
  ["« Vous mettez 32 % sur le Japon parce que le yen a monté en 2008. C'est du surapprentissage. »",
   "**C'est exact, et c'est pour cela qu'on ne l'a pas retenu.** Le calcul libre choisit le Japon pour deux raisons : c'est la classe au rendement espéré le plus élevé (9,44 %, à cause d'un PER de 19,1 et d'un dividende de 3,66 %), et c'est l'action qui a le mieux résisté en 2008 — −49,1 % en euros contre −59,0 % pour l'Europe. La seconde raison ne repose que sur une crise : c'est fragile. La clé actions 40/35/10/15 a donc été imposée précisément pour retirer ce choix au calcul. Elle coûte 0,68 point de rendement annuel, le poste le plus cher du dossier, et on l'a payé. **Le portefeuille retenu ne contient que 3 % de Japon.**"],
  ["« Le Japon a été un mauvais investissement pendant vingt ans. »",
   "**Sur vingt ans oui, sur cinq ans non, et il faut donner les deux chiffres.** En euros, dividendes réinvestis : 3,95 % par an sur vingt ans — c'est la mauvaise réputation, et elle est méritée. Mais 6,40 % par an sur dix ans, 9,02 % sur cinq ans et 17,35 % sur trois ans. Sur les cinq dernières années le Japon fait mieux que l'Europe (8,71 %) et que les émergents (3,72 %), moins bien que les États-Unis (12,54 %). Affirmer qu'il s'est effondré récemment serait factuellement faux."],
  ["« Pourquoi pas une frontière efficiente ? »",
   "Parce que la contrainte du client est une perte maximale depuis le plus haut, pas une volatilité. Une perte maximale dépend de l'ordre d'arrivée des rendements ; une matrice de covariance l'ignore. Optimiser la variance en espérant que la perte suive aurait été un raccourci non vérifié. Voir § 5.2."],
  ["« Votre 5,31 %, c'est avant ou après frais ? »",
   "**Le 5,31 % est brut, et le dossier donne maintenant les deux.** L'objectif du client est un objectif net : ce qui doit battre l'inflation, c'est ce qui lui reste. On retire donc les frais d'instruments (47 k€ par an, 0,05 point) et les frais de mandat (0,40 point), ce qui donne **4,86 % net, soit +0,86 point au-dessus des 4 %**. La marge reste confortable, et elle est maintenant défendable. La fiscalité, hors périmètre, en retirerait encore environ 0,30 point."],
  ["« Vous validez sur les données qui ont servi à optimiser. »",
   "Oui, et le dossier le dit de lui-même en tête de l'étape 5. La tenue de la limite de 14 % est acquise d'avance et ne prouve rien. Ce que le rejeu mesure, c'est ce que l'optimisation n'a pas regardé : la durée des baisses (32 mois en 2022) et la fréquence des mauvaises années (18 %). Les quatre règles de l'étape 4 existent précisément pour limiter le surapprentissage, et leur coût est chiffré ligne à ligne."],
  ["« Votre hypothèse d'inflation à 4 % est le double du consensus. »",
   "Elle n'a pas été corrigée, volontairement : le portefeuille est construit pour tenir **dans le scénario du client**, pas dans le nôtre. Si l'inflation se révèle conforme au consensus à 2 %, le seuil à battre baisse d'autant et la marge s'élargit. Le point de méthode important est que seuil et rendements sont évalués **dans le même régime d'inflation** — comparer un seuil bâti sur 4 % à des rendements bâtis sur 2 % ferait paraître le mandat bien plus difficile qu'il n'est."],
  ["« Le backtest fait 4,47 % pour un objectif de 4 %. C'est très juste. »",
   "**La comparaison n'est pas légitime, et elle jouait contre nous.** Le seuil de 4 % est bâti pour un monde à 4 % d'inflation ; la zone euro a connu **2,18 % par an** sur la fenêtre exacte du rejeu, soit 53,5 % cumulés en vingt ans (FRED, IPCH zone euro). Jugé contre l'inflation réellement constatée, le portefeuille a donc rapporté **+2,29 points de rendement réel par an**. Ce n'est pas une réussite de justesse, c'est un net succès. C'est le piège de régime signalé au § 3.1, et il est désormais corrigé dans l'application."],
  ["« Pourquoi 30 titres en direct plutôt qu'un ETF européen ? »",
   "Trois raisons. Les exclusions du client sont appliquées **littéralement**, ce qu'aucun ETF ne fait exactement — le fonds le plus proche n'exclut pas l'armement conventionnel. Le pilier Résistance permet de détenir plus d'actions pour la même limite de perte. Et il n'y a pas de frais de gestion. Le panier est effectivement moins agité que l'indice : 10,4 % de volatilité contre 12,8 %."],
  ["« Comment garantissez-vous les 15 % ? »",
   "**On ne les garantit pas, et il ne faut pas le prétendre.** La limite tient sur le passé, sur quatre crises datées à l'avance. La prochaine crise peut être différente. Trois choses réduisent ce risque sans l'annuler : la mesure au pire cas plutôt qu'en probabilité, la marge d'un point (viser 14 %), et le refus de la concentration que le calcul libre proposait."],
  ["« Pourquoi pas de crypto, alors que le fils en veut ? »",
   "Parce qu'elle ne rapporte rien d'estimable — aucun flux, donc aucune méthode d'actualisation — et qu'elle n'amortit rien : elle a perdu 72,9 % en 2020 et 73,8 % en 2022, en baissant **avec** les actions. Elle n'a donc sa place ni dans le moteur de performance ni dans l'amortisseur. Elle reste mesurée dans le dossier pour pouvoir montrer pourquoi, ce qui est une réponse plus respectueuse qu'un refus de principe."],
  ["« Pourquoi l'Europe devant les États-Unis ? »",
   "Uniquement par le prix payé : PER de 18,5 contre 30,0. L'action américaine est de meilleure qualité, mais elle se paie presque deux fois plus cher ; à ce prix elle rapportera probablement moins sur dix ans. La limite est assumée : une croissance de bénéfices identique pour toutes les zones pénalise les États-Unis, et avec une autre source de PER l'écart se réduit fortement. Il ne s'inverse pas."],
];

QA.forEach(([q, r]) => {
  corps.push(new Paragraph({ spacing: { before: 240, after: 80 },
    children: [new TextRun({ text: q, bold: true, color: ENCRE, size: 21 })] }));
  corps.push(P(r));
});

corps.push(new Paragraph({ children: [new PageBreak()] }));

// ==========================================================================
corps.push(H1("9. Les faiblesses du dossier, dites franchement"));

corps.push(P("Un dossier qui ne connaît pas ses faiblesses les découvre en séance. Celles-ci sont connues, et trois d'entre elles ne sont pas corrigées à ce jour."));

corps.push(H2("9.1 Le surapprentissage, structurel"));
corps.push(P("L'optimisation et la validation partagent les mêmes vingt années. Les quatre règles et la marge à 14 % le limitent, sans le supprimer. Une validation hors échantillon — optimiser sur 2006-2016 et vérifier sur 2016-2026 — serait la correction naturelle et n'a pas été faite."));

corps.push(H2("9.2 La qualité des séries avant 2018"));
corps.push(P("Plusieurs supports sont représentés par des remplaçants sur la première moitié de la période, et certains flattent la réalité — le comportement des obligations indexées en 2008 notamment. Tout ce qui repose sur 2008 doit donc être présenté avec cette réserve."));

corps.push(H2("9.3 Le seuil net comparé à un rendement brut — corrigé le 21/09/2026"));
corps.push(P("L'objectif de 4 % est net de frais ; les rendements espérés sont bruts. Une version antérieure du dossier faisait le calcul, la suivante l'avait perdu, et la marge annoncée de +1,31 point était donc surévaluée."));
corps.push(P("**Correction appliquée.** L'étape 4 affiche désormais le passage du brut au net, ligne à ligne : 5,31 % bruts, moins 0,05 point de frais d'instruments, moins 0,40 point de frais de mandat, soit **4,86 % nets et +0,86 point au-dessus de l'inflation de l'énoncé**. Le taux de frais de mandat est un paramètre nommé du dossier (`core/ips.py`), pas un chiffre enfoui dans un onglet."));

corps.push(H2("9.4 Le backtest jugé dans le mauvais régime d'inflation — corrigé le 21/09/2026"));
corps.push(P("Le rendement réalisé de 4,47 % était comparé à un seuil de 4 % bâti pour un monde à 4 % d'inflation, alors que la période rejouée en a connu une autre. L'erreur jouait **en défaveur** du portefeuille."));
corps.push(P("**Correction appliquée.** L'inflation zone euro constatée sur la fenêtre exacte du rejeu a été mesurée : **2,18 % par an**, soit 53,5 % cumulés sur vingt ans. Le portefeuille a donc dégagé **+2,29 points de rendement réel par an**. L'étape 5 présente maintenant les trois chiffres ensemble et conclut que l'objectif a été tenu largement, là où elle laissait croire à une réussite de justesse."));
corps.push(P("**Un résultat inattendu au passage** : sur les cinq dernières années, la zone euro a connu 4,31 % d'inflation par an. L'hypothèse de 4 % du client n'est donc pas une crainte disproportionnée — il extrapole ce qu'il vient de vivre. C'est une façon plus juste, et plus respectueuse, de présenter son hypothèse que de la qualifier simplement d'élevée."));

corps.push(H2("9.5 La fréquence des années sous l'objectif — corrigée le 21/09/2026"));
corps.push(P("Le chiffre existait dans l'application mais était enfoui, et comparé au mauvais seuil. Mesuré correctement — contre l'inflation de chaque époque et non contre les 4 % d'un régime qui n'a pas eu lieu — **29 % des années glissantes n'ont pas battu l'inflation**, contre 40,8 % sous le seuil de l'énoncé."));
corps.push(P("**Correction appliquée.** L'étape 5 affiche les deux mesures côte à côte et énonce la conséquence : préserver le pouvoir d'achat est un objectif de moyenne longue, pas une garantie annuelle, et aucun portefeuille tenu à 15 % de perte maximum ne peut promettre le contraire. Ce chiffre est calculable par n'importe qui à partir des données du dossier : mieux vaut le donner que se le faire sortir."));

corps.push(CADRE("Ce qui reste à faire, et qui n'est pas dans l'application",
  "**Le PowerPoint n'a pas été mis à jour.** Il est retouché à la main et fait foi ; le corriger automatiquement l'écraserait. Trois chiffres y sont à reprendre : la slide 27 et la slide 33 annoncent « 5,31 % » et « +1,31 pt au-dessus des 4 % » — lire désormais 4,86 % nets et +0,86 pt ; et la slide 30 affiche « 4,47 % par an » sans le comparer à l'inflation de la période, alors que le bon chiffre à montrer est +2,29 points réels."));

corps.push(H2("9.6 Ce qui a été volontairement laissé de côté"));
corps.push(PUCE("**Fiscalité et transmission** : hors périmètre, assumé. Conséquence directe sur le § 9.3."));
corps.push(PUCE("**Immobilier et actifs non cotés** : absents de l'univers, alors qu'un patrimoine de 100 M€ en comporterait normalement. La liquidité exigée par la limite de perte mesurée en continu les rendait difficiles à intégrer."));
corps.push(PUCE("**Gestion dynamique** : l'allocation est stratégique et rééquilibrée mensuellement, sans vue tactique. Aucun pilier de sur-réaction au cycle n'a été testé."));

corps.push(ESPACE());
corps.push(CADRE("La phrase de clôture, si on vous demande ce qu'il faut retenir",
  "Le mandat est tenu : 5,31 % de rendement espéré contre 4 % à battre, et jamais plus de 14 % de baisse dans les quatre crises des vingt dernières années. Mais la limite de perte tient **sur le passé**, les rendements espérés sont des **moyennes sur dix ans et non des promesses**, et une baisse peut durer plus de deux ans — elle a duré 32 mois en 2022."));

// ==========================================================================
const doc = new Document({
  creator: "Allan Guichard",
  title: "Mandat Lauren — dossier technique",
  description: "Stratégie, modèles, choix et données du mandat Lauren",
  numbering: {
    config: [{
      reference: "puces",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 460, hanging: 230 } } },
      }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 21 } },
      heading1: { run: { font: "Calibri", size: 32, bold: true, color: ENCRE },
        paragraph: { spacing: { before: 360, after: 160 } } },
      heading2: { run: { font: "Calibri", size: 25, bold: true, color: ENCRE },
        paragraph: { spacing: { before: 280, after: 120 } } },
      heading3: { run: { font: "Calibri", size: 22, bold: true, color: GRIS },
        paragraph: { spacing: { before: 200, after: 100 } } },
    },
  },
  sections: [{
    properties: { page: { margin: { top: 1100, bottom: 1100, left: 1040, right: 1040 } } },
    children: corps,
  }],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync("outputs/Mandat_Lauren_dossier_technique.docx", b);
  console.log("-> outputs/Mandat_Lauren_dossier_technique.docx", b.length, "octets");
});
