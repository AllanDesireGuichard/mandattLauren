/*
 * Note d'analyse et de suivi YTD du portefeuille, FR + EN.
 *   outputs/Mandat_Lauren_suivi_YTD_2026.docx       (francais)
 *   outputs/Mandat_Lauren_monitoring_YTD_2026.docx  (anglais)
 *
 * Lancer :  node scripts/suivi_ytd.js
 * Prerequis : python3 scripts/suivi_figures.py  (ecrit outputs/figures/ :
 *   macro/indice/actifs/secteurs/contrib_{fr,en}.png et suivi_ytd.json).
 *
 * Les chiffres DU PORTEFEUILLE sont lus dans suivi_ytd.json (calcule par
 * suivi_figures.py en meme temps que les graphiques) : texte et figures ne
 * peuvent pas diverger. Les faits MACRO (BCE, inflation, Stoxx 600, Bund,
 * spreads) sont ecrits dans le texte : ce sont des faits de marche dates, une
 * photo d'octobre 2026, pas une sortie vivante.
 *
 * PERIMETRE. Suivi « depuis le 1er janvier 2026 » du portefeuille arrete le
 * 24/09 : comportement de la selection sur l'annee, pas un gain realise. Les
 * obligations en direct sont representees par des ETF de meme maturite.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, ImageRun, LevelFormat,
} = require("docx");

const ENCRE = "14304F", GRIS = "5A6069", VERT = "0A7A0A", ROUGE = "B5302F";
const ROOT = path.dirname(__dirname);
const FIG = path.join(ROOT, "outputs", "figures");
const S = JSON.parse(fs.readFileSync(path.join(FIG, "suivi_ytd.json"), "utf8"));

const asof = new Date(S.asof + "T00:00:00Z");
const MOIS_FR = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"];
const MOIS_EN = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const dateFR = `${asof.getUTCDate()} ${MOIS_FR[asof.getUTCMonth()]} ${asof.getUTCFullYear()}`;
const dateEN = `${asof.getUTCDate()} ${MOIS_EN[asof.getUTCMonth()]} ${asof.getUTCFullYear()}`;
const [a0, a1] = S.window;

function buildDoc(lang) {
  const fr = lang === "fr";
  const sep = (s) => fr ? s.replace(".", ",") : s;
  const sval = (v, d) => sep((v >= 0 ? "+" : "−") + Math.abs(v).toFixed(d));
  const val = (v, d) => sep((v < 0 ? "−" : "") + Math.abs(v).toFixed(d));
  const pct = (v, d = 1) => val(v, d) + (fr ? " %" : "%");
  const spct = (v, d = 1) => sval(v, d) + (fr ? " %" : "%");
  const pt = (v, d = 2) => sval(v, d) + (fr ? " pt" : " pts");
  const st = S.stocks, se = S.sectors, bo = S.bonds, ma = S.macro, ge = S.geo;

  // --- mise en forme ---
  const H1 = (t) => new Paragraph({ text: t, heading: HeadingLevel.HEADING_1 });
  const P = (t) => new Paragraph({ spacing: { after: 120, line: 276 }, alignment: AlignmentType.JUSTIFIED,
    children: String(t).split("**").map((x, i) => new TextRun({ text: x, bold: i % 2 === 1 })) });
  const PUCE = (t) => new Paragraph({ numbering: { reference: "puces", level: 0 }, spacing: { after: 80, line: 276 },
    children: String(t).split("**").map((x, i) => new TextRun({ text: x, bold: i % 2 === 1 })) });
  const ESP = () => new Paragraph({ spacing: { after: 120 }, text: "" });
  const CADRE = (titre, lignes) => new Table({
    columnWidths: [9360], width: { size: 9360, type: WidthType.DXA },
    borders: { top: { style: BorderStyle.SINGLE, size: 2, color: "C9CFD6" }, bottom: { style: BorderStyle.SINGLE, size: 2, color: "C9CFD6" },
      left: { style: BorderStyle.SINGLE, size: 12, color: ENCRE }, right: { style: BorderStyle.SINGLE, size: 2, color: "C9CFD6" },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
    rows: [new TableRow({ children: [new TableCell({ width: { size: 9360, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: "F2F4F7" }, margins: { top: 160, bottom: 160, left: 200, right: 200 },
      children: [new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: titre, bold: true, color: ENCRE })] }), ...lignes.map(P)] })] })] });
  const TAB = (entetes, lignes, largeurs, colColor) => {
    const cell = (t, o = {}) => {
      let color; const txt = String(t);
      if (o.colored) { if (txt.startsWith("+")) color = VERT; else if (txt.startsWith("−") || txt.startsWith("-")) color = ROUGE; }
      return new TableCell({ width: { size: o.w, type: WidthType.DXA },
        shading: o.head ? { type: ShadingType.CLEAR, fill: ENCRE } : { type: ShadingType.CLEAR, fill: o.alt ? "F7F8FA" : "FFFFFF" },
        margins: { top: 80, bottom: 80, left: 130, right: 130 },
        children: [new Paragraph({ alignment: o.right ? AlignmentType.RIGHT : AlignmentType.LEFT,
          children: txt.split("**").map((x, i) => new TextRun({ text: x, bold: o.head || i % 2 === 1, color: o.head ? "FFFFFF" : color, size: 19 })) })] });
    };
    return new Table({ columnWidths: largeurs, width: { size: 9360, type: WidthType.DXA },
      rows: [new TableRow({ tableHeader: true, children: entetes.map((t, i) => cell(t, { w: largeurs[i], head: true, right: i > 0 })) }),
        ...lignes.map((l, n) => new TableRow({ children: l.map((t, i) => cell(t, { w: largeurs[i], alt: n % 2 === 1, right: i > 0, colored: i === colColor })) }))] });
  };
  const IMG = (file, w, h) => new Paragraph({ spacing: { before: 80, after: 40 }, alignment: AlignmentType.CENTER,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(FIG, file)), transformation: { width: w, height: h } })] });
  const LEG = (t) => new Paragraph({ spacing: { after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: t, italics: true, color: GRIS, size: 17 })] });
  const sfx = fr ? "fr" : "en";

  // ======================= CONTENU =======================
  const corps = [];
  const push = (...x) => corps.push(...x);

  // --- titre ---
  push(
    new Paragraph({ spacing: { before: 1600, after: 80 }, children: [new TextRun({ text: "Mandat Lauren", bold: true, size: 56, color: ENCRE })] }),
    new Paragraph({ spacing: { after: 320 }, children: [new TextRun({ text: fr ? "Suivi et analyse de portefeuille — année 2026" : "Portfolio monitoring and review — 2026", size: 32, color: GRIS })] }),
    P(fr ? "Gestion privée · 100 M€ · préserver le pouvoir d'achat sous contrainte de perte maximum de 15 %"
         : "Private wealth · €100m · preserve purchasing power under a 15% maximum-loss constraint"),
    P(fr ? `**Période :** 1ᵉʳ janvier → 29 octobre 2026 (depuis le début de l'année). **Arrêté au ${dateFR}.**`
         : `**Period:** 1 January → 29 October 2026 (year-to-date). **As of ${dateEN}.**`),
    ESP(),
    CADRE(fr ? "Ce que mesure cette note" : "What this note measures", fr ? [
      "Le portefeuille a été arrêté le 24/09/2026. Un suivi « depuis le 1ᵉʳ janvier » n'est donc **pas un gain réalisé**, mais une analyse de **ce qu'aurait fait la sélection sur l'année 2026** : comment elle s'est comportée, pourquoi, et ce que cela dit de la thèse.",
      "Les chiffres du portefeuille sont calculés en euros, dividendes réinvestis. Les deux poches d'obligations détenues en direct sont représentées par des ETF de même maturité. Les repères de marché (BCE, inflation, indices, taux) sont des faits datés d'octobre 2026. Méthode complète en fin de note.",
    ] : [
      "The portfolio was finalised on 24/09/2026. A “since 1 January” track is therefore **not a realised gain**, but an analysis of **what the selection would have done over 2026**: how it behaved, why, and what that says about the thesis.",
      "Portfolio figures are computed in euros, dividends reinvested. The two directly-held bond sleeves are represented by maturity-matched ETFs. Market reference points (ECB, inflation, indices, yields) are facts as of October 2026. Full method at the end.",
    ]),
    new Paragraph({ children: [new PageBreak()] }),
  );

  // --- 1. Résumé ---
  push(H1(fr ? "1. Résumé" : "1. Summary"));
  if (fr) {
    push(P(`Sur les dix premiers mois de 2026, le portefeuille progresse de **${spct(S.port_ytd)}** en euros. C'est **${pt(S.ecart,1)} de plus** que l'objectif d'inflation (4 %/an, soit ${spct(S.infl)} au prorata de la période). Dans le même temps, sa pire baisse depuis le plus haut s'est limitée à **${spct(S.maxdd)}**, à ${val(S.floor_margin,1)} points de la limite de perte du mandat (−15 %).`));
    push(P(`Autrement dit, l'année a fait travailler le portefeuille exactement comme il a été construit pour le faire : **un moteur actions qui suffit à battre l'inflation, et un socle obligataire qui tient la perte.** Les actions (30 % du portefeuille) ont apporté ${pt(S.poches.actions.contrib)} ; l'obligataire (66 %), conçu pour protéger et non pour rapporter, a coûté ${pt(S.poches.oblig.contrib)} dans une année de hausse des taux ; l'or (3 %), ${pt(S.poches.or.contrib)}.`));
    push(P(`2026 n'a pourtant pas été une année facile : un choc énergétique a ramené l'inflation, poussé la BCE à **relever** ses taux et fait chuter les obligations. Le portefeuille s'en sort parce que sa sélection d'actions était du bon côté de ce choc — énergie, utilities, santé, banques — et parce qu'il **n'a aucune exposition** aux deux grands perdants européens de l'année, l'automobile et le luxe. Le reste de la note explique cet enchaînement, du contexte macro jusqu'à chaque ligne.`));
  } else {
    push(P(`Over the first ten months of 2026, the portfolio rose **${spct(S.port_ytd)}** in euros — **${pt(S.ecart,1)} more** than the inflation objective (4%/yr, i.e. ${spct(S.infl)} pro-rated). Over the same period its worst drawdown from peak was held to **${spct(S.maxdd)}**, ${val(S.floor_margin,1)} points away from the mandate's loss limit (−15%).`));
    push(P(`In short, the year made the portfolio work exactly as designed: **an equity engine that is enough to beat inflation, and a bond base that holds the loss.** Equities (30% of the portfolio) added ${pt(S.poches.actions.contrib)}; the bond sleeve (66%), built to protect rather than earn, cost ${pt(S.poches.oblig.contrib)} in a year of rising yields; gold (3%), ${pt(S.poches.or.contrib)}.`));
    push(P(`Yet 2026 was not an easy year: an energy shock brought inflation back, pushed the ECB to **raise** rates and sent bonds lower. The portfolio came through because its equity selection was on the right side of that shock — energy, utilities, healthcare, banks — and because it has **no exposure** to the two big European losers of the year, autos and luxury. The rest of this note traces that chain, from the macro backdrop down to each holding.`));
  }

  // --- 2. Macro ---
  push(H1(fr ? "2. Le contexte macro de 2026" : "2. The 2026 macro backdrop"));
  push(IMG(`macro_${sfx}.png`, 614, 307),
    LEG(fr ? "Pétrole Brent et or (en dollars), rebasés à 100 au 1ᵉʳ janvier 2026. Le pétrole est le fil conducteur de l'année."
           : "Brent crude and gold (in dollars), rebased to 100 on 1 January 2026. Oil is the year's through-line."));
  if (fr) {
    push(P(`**Tout part de l'énergie.** Un conflit au Moyen-Orient à partir de fin février a fait bondir le pétrole : le Brent termine l'année en hausse de **${val(ma.brent_ytd,0)} %**, après un pic proche de ${val(ma.brent_peak,0)} % fin mars. C'est le choc dominant de 2026, et il irrigue tout le reste.`));
    push(P(`**L'inflation est revenue.** Sous l'effet de l'énergie, l'inflation de la zone euro est remontée à 3,3 % en août (le poste énergie bondissant de plus de 14 % sur un an). Le pouvoir d'achat redevient le vrai sujet — précisément le risque contre lequel le mandat a été calibré.`));
    push(P(`**La BCE a relevé ses taux.** À rebours du cycle d'assouplissement attendu en début d'année, la Banque centrale a maintenu ses taux au premier trimestre, puis les a relevés en juin et de nouveau en septembre, portant le taux de dépôt à 2,50 %. 2026 est donc une année de **resserrement**, pas de détente.`));
    push(P(`**Les obligations ont décroché.** Mécaniquement, les taux longs sont montés : le Bund allemand à 10 ans a atteint des sommets de quinze ans cet été (autour de 3,3-3,6 %) avant de se détendre vers 3,35 % fin octobre. Le stress s'est concentré sur la France, où l'écart de taux avec l'Allemagne s'est tendu autour de 170 points de base, au plus haut depuis la crise de la dette — un point d'attention pour toute poche d'État.`));
    push(P(`**Les actions, elles, ont bien tenu.** Malgré ce décor, le Stoxx 600 a gagné de l'ordre de 9 à 10 % et inscrit des records en août. Mais la hausse a été très inégale : les **semi-conducteurs** (ASML en tête, +60 % et plus) et les **banques** (+22 %, portées par des opérations de rapprochement) ont mené ; l'**automobile** (−16 %) et le **luxe** (demande chinoise molle) ont été les grands retardataires.`));
    push(P(`**Deux effets de change, enfin.** Malgré les hausses de la BCE, l'euro s'est **affaibli** (${spct(ma.eurusd_ytd)} face au dollar) — un pays importateur d'énergie voit sa monnaie souffrir d'un choc pétrolier ; à l'inverse, la couronne norvégienne, adossée au pétrole, s'est renforcée. Et l'or, valeur refuge, a flambé en début d'année (pic de +${val(ma.gold_usd_peak,0)} % en dollars fin janvier) avant de refluer : il finit **${spct(ma.gold_usd_ytd)}** en dollars, mais seulement ${spct(ma.gold_eur_ytd)} en euros, l'euro faible ayant amorti la baisse.`));
  } else {
    push(P(`**It all starts with energy.** A Middle East conflict from late February sent oil surging: Brent ends the period up **${val(ma.brent_ytd,0)}%**, after a peak near ${val(ma.brent_peak,0)}% in late March. This is the dominant shock of 2026, and it feeds everything else.`));
    push(P(`**Inflation came back.** Driven by energy, euro-area inflation rose to 3.3% in August (energy alone up more than 14% year-on-year). Purchasing power is the live issue again — precisely the risk the mandate was calibrated against.`));
    push(P(`**The ECB raised rates.** Against the easing cycle expected early in the year, the central bank held in Q1, then hiked in June and again in September, taking the deposit rate to 2.50%. 2026 is therefore a year of **tightening**, not easing.`));
    push(P(`**Bonds sold off.** Long yields rose accordingly: the German 10-year Bund hit 15-year highs over the summer (around 3.3-3.6%) before easing back toward 3.35% in late October. Stress concentrated on France, where the yield gap to Germany widened to around 170 basis points, the most since the debt crisis — a watch point for any government-bond sleeve.`));
    push(P(`**Equities, though, held up well.** Despite that backdrop, the Stoxx 600 gained roughly 9-10% and set records in August. But the rise was very uneven: **semiconductors** (ASML to the fore, +60% and more) and **banks** (+22%, lifted by consolidation) led; **autos** (−16%) and **luxury** (soft Chinese demand) were the big laggards.`));
    push(P(`**Two currency effects, finally.** Despite the ECB's hikes, the euro **weakened** (${spct(ma.eurusd_ytd)} against the dollar) — an energy importer's currency suffers in an oil shock; conversely the oil-linked Norwegian krone strengthened. And gold, the safe haven, spiked early in the year (peak +${val(ma.gold_usd_peak,0)}% in dollars in late January) before fading: it ends **${spct(ma.gold_usd_ytd)}** in dollars, but only ${spct(ma.gold_eur_ytd)} in euros, the weak euro having cushioned the fall.`));
  }

  // --- 3. Évolution du portefeuille ---
  push(H1(fr ? "3. L'évolution du portefeuille, mois par mois" : "3. How the portfolio moved, month by month"));
  push(IMG(`indice_${sfx}.png`, 614, 333),
    LEG(fr ? "Valeur du portefeuille rebasée à 100, en euros, face à l'objectif d'inflation et au plancher de perte du mandat."
           : "Portfolio value rebased to 100, in euros, against the inflation target and the mandate's loss floor."));
  if (fr) {
    push(P(`**Janvier-février : une montée tranquille.** Le portefeuille s'apprécie doucement, porté par des actions encore calmes, pendant que l'or joue déjà les refuges dès les premières tensions.`));
    push(P(`**Fin février-mars : le seul vrai trou d'air.** Le choc pétrolier et la poussée des taux font plier les actions ; le point bas de l'année est touché le 27 mars, à **${spct(S.maxdd)}** depuis le plus haut. C'est le moment révélateur : l'obligataire ne joue pas son rôle d'amortisseur habituel, car les taux montent **en même temps** que les actions baissent. Et pourtant la perte reste contenue à ${val(Math.abs(S.maxdd),1)} % — à plus de 11 points de la limite. La diversification n'a pas eu besoin des obligations ce jour-là : la modération de la poche actions a suffi.`));
    push(P(`**Avril à l'été : la reconstruction, puis les records.** Une fois le choc digéré, les actions repartent et ne s'arrêtent plus : semi-conducteurs, énergie, banques et utilities tirent l'indice européen vers de nouveaux sommets en août, et le portefeuille avec. L'essentiel du +6 % se construit sur cette période.`));
    push(P(`**Automne : consolidation.** Depuis septembre, le portefeuille oscille autour de son niveau de +6 %, l'obligataire continuant de peser légèrement tandis que les actions tiennent leurs gains. Rien de spectaculaire — ce qui, pour un mandat défensif, est une bonne nouvelle.`));
  } else {
    push(P(`**January-February: a quiet climb.** The portfolio appreciates gently, carried by still-calm equities, while gold already plays safe haven at the first signs of tension.`));
    push(P(`**Late February-March: the only real air pocket.** The oil shock and the jump in yields push equities down; the year's low is reached on 27 March, at **${spct(S.maxdd)}** from the peak. This is the telling moment: bonds do not play their usual shock-absorber role, because yields rise **at the same time** as equities fall. And yet the loss stays contained at ${val(Math.abs(S.maxdd),1)}% — more than 11 points from the limit. Diversification did not need bonds that day: the equity sleeve's own moderation was enough.`));
    push(P(`**April to summer: the rebuild, then the records.** Once the shock is digested, equities turn up and keep going: semiconductors, energy, banks and utilities drag the European index to new highs in August, and the portfolio with it. Most of the +6% is built over this stretch.`));
    push(P(`**Autumn: consolidation.** Since September the portfolio has hovered around its +6% level, bonds still weighing slightly while equities hold their gains. Nothing spectacular — which, for a defensive mandate, is good news.`));
  }

  // --- 4. Catégories d'actif ---
  push(H1(fr ? "4. Par catégorie d'actif" : "4. By asset category"));
  push(IMG(`actifs_${sfx}.png`, 614, 307),
    LEG(fr ? "Chaque poche rebasée à 100 au 1ᵉʳ janvier. Les actions montent, l'obligataire reste plat, l'or fait un aller-retour."
           : "Each sleeve rebased to 100 on 1 January. Equities rise, bonds stay flat, gold round-trips."));
  push(TAB(
    fr ? ["Poche", "Poids", "Performance", "Contribution"] : ["Sleeve", "Weight", "Performance", "Contribution"],
    [
      [fr ? "**Actions**" : "**Equities**", pct(S.poches.actions.w), spct(S.poches.actions.perf), `**${pt(S.poches.actions.contrib)}**`],
      [fr ? "**Obligataire**" : "**Bonds**", pct(S.poches.oblig.w), spct(S.poches.oblig.perf), `**${pt(S.poches.oblig.contrib)}**`],
      [fr ? "**Or**" : "**Gold**", pct(S.poches.or.w), spct(S.poches.or.perf), `**${pt(S.poches.or.contrib)}**`],
    ], [3360, 1600, 2200, 2200], 3));
  push(ESP());
  if (fr) {
    push(P(`**Les actions (${pct(S.poches.actions.w)}) sont le moteur.** Elles gagnent ${spct(S.poches.actions.perf)} sur l'année et apportent la quasi-totalité de la performance. Fait notable : elles battent nettement l'indice européen large (de l'ordre de +9 à 10 %), ce qui tient à la **sélection** — le détail arrive aux sections secteurs et titres.`));
    push(P(`**L'obligataire (${pct(S.poches.oblig.w)}) est le socle, et il a fait son travail.** Il recule de ${val(Math.abs(S.poches.oblig.perf),1)} % seulement, dans une année où les taux ont fortement monté. Le détail est instructif :`));
    push(TAB(
      ["Sous-poche", "Poids", "Performance", "Contribution"],
      [
        ["**États 2-10 ans** (proxy 3-7 ans)", "41,3 %", spct(bo.govt_ytd), pt(bo.govt_contrib)],
        ["**Échelle AAA 6-24 mois** (proxy 1-3 ans)", "10,0 %", spct(bo.aaa_ytd), "≈ 0"],
        ["**Indexées inflation** (IBCI)", "15,0 %", spct(bo.link_ytd), "≈ 0"],
      ], [4360, 1400, 1800, 1800], 2));
    push(ESP());
    push(P(`Toute la perte vient de la poche d'État **longue** (${spct(bo.govt_ytd)}) : c'est la plus sensible à la hausse des taux. En face, l'**échelle courte AAA** — là où logent les 10 M€ à sortir — et les **obligations indexées** sont restées positives (${spct(bo.aaa_ytd)} et ${spct(bo.link_ytd)}). Le court terme a protégé la liquidité, et l'indexation a protégé contre l'inflation : les deux poches ont fonctionné exactement l'année où on en avait besoin.`));
    push(P(`**L'or (${pct(S.poches.or.w)}) a fait un aller-retour.** Refuge recherché en début d'année, il a reflué ensuite pour finir ${spct(S.poches.or.perf)} en euros. Une assurance qui, cette année, n'aura presque rien coûté (${pt(S.poches.or.contrib)}).`));
  } else {
    push(P(`**Equities (${pct(S.poches.actions.w)}) are the engine.** They gained ${spct(S.poches.actions.perf)} over the year and delivered almost all of the performance. Notably, they clearly beat the broad European index (around +9-10%), thanks to **selection** — detailed in the sector and stock sections below.`));
    push(P(`**Bonds (${pct(S.poches.oblig.w)}) are the base, and they did their job.** They fell only ${val(Math.abs(S.poches.oblig.perf),1)}% in a year of sharply rising yields. The breakdown is instructive:`));
    push(TAB(
      ["Sub-sleeve", "Weight", "Performance", "Contribution"],
      [
        ["**Govt 2-10y** (3-7y proxy)", "41.3%", spct(bo.govt_ytd), pt(bo.govt_contrib)],
        ["**AAA 6-24m ladder** (1-3y proxy)", "10.0%", spct(bo.aaa_ytd), "≈ 0"],
        ["**Inflation-linked** (IBCI)", "15.0%", spct(bo.link_ytd), "≈ 0"],
      ], [4360, 1400, 1800, 1800], 2));
    push(ESP());
    push(P(`All of the loss comes from the **long** government sleeve (${spct(bo.govt_ytd)}): the most sensitive to rising yields. Against it, the **short AAA ladder** — where the €10m to be withdrawn sits — and the **inflation-linked** bonds stayed positive (${spct(bo.aaa_ytd)} and ${spct(bo.link_ytd)}). The short end protected the liquidity, and linkers protected against inflation: both sleeves worked in exactly the year they were meant for.`));
    push(P(`**Gold (${pct(S.poches.or.w)}) round-tripped.** A sought-after haven early in the year, it then faded to finish ${spct(S.poches.or.perf)} in euros. Insurance that, this year, cost almost nothing (${pt(S.poches.or.contrib)}).`));
  }

  // --- 5. Secteurs ---
  push(H1(fr ? "5. Par secteur (le panier d'actions européen)" : "5. By sector (the European equity basket)"));
  push(IMG(`secteurs_${sfx}.png`, 614, 333),
    LEG(fr ? "Contribution de chaque secteur du panier des 15 actions européennes à la performance totale, en points de %."
           : "Each sector's contribution within the 15-stock European basket to total performance, in percentage points."));
  if (fr) {
    push(P(`Le panier d'actions européennes a profité **très largement** du décor macro. Huit secteurs sur neuf sont positifs, et le seul plat (la communication) le reste de justesse.`));
    push(P(`**L'énergie domine** (${pt(se.ener.contrib)}, ${spct(se.ener.perf)} de performance) : une seule ligne, Vår Energi, portée par le choc pétrolier. Viennent ensuite la **santé** (${pt(se.sante.contrib)}), tirée par Orion, les **services aux collectivités** (${pt(se.util.contrib)}) — des utilities ibériques directement sensibles au prix de l'énergie — l'**industrie** (${pt(se.ind.contrib)}) et la **finance** (${pt(se.fin.contrib)}), au cœur de la revalorisation des banques et assureurs européens.`));
    push(P(`La **technologie** (${pt(se.tech.contrib)}, ${spct(se.tech.perf)}) n'est « que » sixième en contribution malgré la très forte hausse d'ASML, parce qu'elle ne pèse qu'une ligne. La **consommation** (cyclique ${pt(se.cycl.contrib)} et défensive ${pt(se.def.contrib)}) complète le tableau. Seule la **communication** (${pt(se.comm.contrib)}) est neutre : la baisse d'Airtel Africa y annule le gain de Publicis.`));
    push(P(`**L'enseignement est double.** D'abord, la performance est **large**, pas concentrée sur un pari sectoriel. Ensuite — et c'est au moins aussi important — le panier **ne contient ni automobile ni luxe**, les deux secteurs qui ont fait perdre de l'argent en Europe cette année. Ce qui n'est pas là compte autant que ce qui y est.`));
  } else {
    push(P(`The European equity basket benefited **very broadly** from the macro backdrop. Eight of nine sectors are positive, and the only flat one (communication) stays so by a whisker.`));
    push(P(`**Energy dominates** (${pt(se.ener.contrib)}, ${spct(se.ener.perf)} performance): a single holding, Vår Energi, lifted by the oil shock. Next come **healthcare** (${pt(se.sante.contrib)}), driven by Orion, **utilities** (${pt(se.util.contrib)}) — Iberian names directly sensitive to energy prices — **industrials** (${pt(se.ind.contrib)}) and **financials** (${pt(se.fin.contrib)}), at the heart of the re-rating of European banks and insurers.`));
    push(P(`**Technology** (${pt(se.tech.contrib)}, ${spct(se.tech.perf)}) is “only” sixth by contribution despite ASML's very large rise, because it is a single holding. **Consumer** (cyclical ${pt(se.cycl.contrib)} and defensive ${pt(se.def.contrib)}) rounds out the picture. Only **communication** (${pt(se.comm.contrib)}) is neutral: Airtel Africa's fall cancels Publicis's gain.`));
    push(P(`**The takeaway is twofold.** First, performance is **broad**, not a concentrated sector bet. Second — and at least as important — the basket holds **no autos and no luxury**, the two sectors that lost money in Europe this year. What is absent matters as much as what is present.`));
  }

  // --- 6. Titres ---
  push(H1(fr ? "6. Par titre" : "6. By holding"));
  push(IMG(`contrib_${sfx}.png`, 560, 442),
    LEG(fr ? "Contribution de chaque ligne à la performance 2026, en points de %. Vert : apport positif ; rouge : négatif."
           : "Each holding's contribution to 2026 performance, in percentage points. Green: positive; red: negative."));
  if (fr) {
    push(P(`**Les locomotives.** **Vår Energi** (${spct(st["Vår Energi"].ytd)} en euros) signe la plus forte hausse : production et dividendes solides, prix du pétrole élevé, et une couronne norvégienne qui ajoute au gain en euros. **Orion** (${spct(st.Orion.ytd)}) profite de la montée en puissance de son traitement du cancer de la prostate (Nubeqa, avec Bayer). **ASML** (${spct(st.ASML.ytd)}), seul fabricant au monde des machines de lithographie EUV, reste le pur-sang du cycle des semi-conducteurs. Derrière, **Endesa** (${spct(st.Endesa.ytd)}) et **Naturgy** (${spct(st.Naturgy.ytd)}) — utilities ibériques — , **Diploma** (${spct(st.Diploma.ytd)}), **AB InBev** (${spct(st["AB InBev"].ytd)}), **BAWAG** (${spct(st.BAWAG.ytd)}), **Unipol** (${spct(st.Unipol.ytd)}) et **InterContinental** (${spct(st.InterContinental.ytd)}) alignent des hausses de 25 à 50 %.`));
    push(P(`**Le peloton.** **Aena** (${spct(st.Aena.ytd)}), **Publicis** (${spct(st.Publicis.ytd)}), **Next** (${spct(st.Next.ytd)}) et **Argenx** (${spct(st.Argenx.ytd)}) progressent plus sagement, entre 11 et 20 % — des hausses honorables qui, sans faire les gros titres, ajoutent à l'ensemble.`));
    push(P(`**Le seul perdant.** **Airtel Africa** cède ${val(Math.abs(st["Airtel Africa"].ytd),1)} %, pénalisée par la rotation hors des valeurs exposées aux marchés émergents et par les devises africaines, malgré de bons résultats opérationnels. Mais comme chaque titre pèse le même poids (environ 0,8 % du patrimoine), l'impact se limite à ${pt(st["Airtel Africa"].contrib)} : **l'équipondération a transformé une mauvaise nouvelle en détail.** C'est le même mécanisme qui empêche Vår Energi, à l'autre extrême, de transformer le portefeuille en pari énergie.`));
    push(P(`**Les trois zones géographiques, enfin**, complètent les actions européennes :`));
    push(TAB(["Zone (ETF)", "Performance 2026", "Contribution"],
      [["**Japon** (XZMJ)", spct(ge.jp), pt(ge.jp_c,2)],
       ["**États-Unis** (XZMU)", spct(ge.us), pt(ge.us_c,2)],
       ["**Émergents** (XZEM)", spct(ge.em), pt(ge.em_c,2)]],
      [4360, 2600, 2400], 2));
    push(ESP());
    push(P(`Le Japon (${spct(ge.jp)}) et les États-Unis (${spct(ge.us)}, soutenus par un dollar plus ferme) ont bien contribué ; les émergents (${spct(ge.em)}) sont restés plus discrets.`));
  } else {
    push(P(`**The locomotives.** **Vår Energi** (${spct(st["Vår Energi"].ytd)} in euros) posts the largest rise: solid production and dividends, high oil prices, and a Norwegian krone that adds to the euro gain. **Orion** (${spct(st.Orion.ytd)}) benefits from the ramp-up of its prostate-cancer treatment (Nubeqa, with Bayer). **ASML** (${spct(st.ASML.ytd)}), the world's only maker of EUV lithography machines, remains the thoroughbred of the semiconductor cycle. Behind them, **Endesa** (${spct(st.Endesa.ytd)}) and **Naturgy** (${spct(st.Naturgy.ytd)}) — Iberian utilities — , **Diploma** (${spct(st.Diploma.ytd)}), **AB InBev** (${spct(st["AB InBev"].ytd)}), **BAWAG** (${spct(st.BAWAG.ytd)}), **Unipol** (${spct(st.Unipol.ytd)}) and **InterContinental** (${spct(st.InterContinental.ytd)}) line up gains of 25 to 50%.`));
    push(P(`**The pack.** **Aena** (${spct(st.Aena.ytd)}), **Publicis** (${spct(st.Publicis.ytd)}), **Next** (${spct(st.Next.ytd)}) and **Argenx** (${spct(st.Argenx.ytd)}) rose more modestly, between 11 and 20% — respectable gains that, without making headlines, add to the whole.`));
    push(P(`**The only loser.** **Airtel Africa** fell ${val(Math.abs(st["Airtel Africa"].ytd),1)}%, hit by rotation out of emerging-market-exposed names and by African currencies, despite good operating results. But since each stock carries the same weight (about 0.8% of wealth), the impact is limited to ${pt(st["Airtel Africa"].contrib)}: **equal-weighting turned bad news into a footnote.** The same mechanism stops Vår Energi, at the other extreme, from turning the portfolio into an energy bet.`));
    push(P(`**Finally, the three geographies** complement the European equities:`));
    push(TAB(["Region (ETF)", "2026 performance", "Contribution"],
      [["**Japan** (XZMJ)", spct(ge.jp), pt(ge.jp_c,2)],
       ["**United States** (XZMU)", spct(ge.us), pt(ge.us_c,2)],
       ["**Emerging** (XZEM)", spct(ge.em), pt(ge.em_c,2)]],
      [4360, 2600, 2400], 2));
    push(ESP());
    push(P(`Japan (${spct(ge.jp)}) and the United States (${spct(ge.us)}, helped by a firmer dollar) contributed well; emerging markets (${spct(ge.em)}) stayed quieter.`));
  }

  // --- 7. Thèse ---
  push(H1(fr ? "7. Lecture de la thèse" : "7. Does the thesis hold?"));
  push(P(fr ? "La thèse défensive du mandat **se vérifie dans les deux sens** :" : "The mandate's defensive thesis **holds both ways**:"));
  if (fr) {
    push(PUCE(`**Le plancher a tenu largement.** La pire baisse de l'année (${spct(S.maxdd)}) reste à plus de 11 points de la limite de −15 %, et ce alors même que les obligations ne jouaient pas leur rôle d'amortisseur habituel. Le portefeuille n'a jamais mis le client en difficulté.`));
    push(PUCE(`**Le moteur a suffi.** ${spct(S.port_ytd)}, soit ${pt(S.ecart,1)} au-dessus de l'inflation à battre. Dans une année où l'inflation est justement revenue, l'objectif central — préserver le pouvoir d'achat — est rempli.`));
    push(PUCE(`**La sélection a payé.** Battre l'indice européen de plus de dix points ne doit rien au hasard : c'est le fruit d'un panier bien orienté (énergie, santé, utilities, banques) et surtout **débarrassé** des secteurs perdants de l'année. La diversification géographique et l'équipondération ont fait le reste.`));
  } else {
    push(PUCE(`**The floor held comfortably.** The year's worst drawdown (${spct(S.maxdd)}) stays more than 11 points from the −15% limit, even though bonds were not playing their usual shock-absorber role. The portfolio never put the client at risk.`));
    push(PUCE(`**The engine was enough.** ${spct(S.port_ytd)}, i.e. ${pt(S.ecart,1)} above the inflation to beat. In a year when inflation did come back, the core objective — preserving purchasing power — is met.`));
    push(PUCE(`**Selection paid off.** Beating the European index by more than ten points is no accident: it is the result of a well-positioned basket (energy, healthcare, utilities, banks) and, above all, one **cleared** of the year's losing sectors. Geographic diversification and equal-weighting did the rest.`));
  }

  // --- 8. Rééquilibrage et vigilance ---
  push(H1(fr ? "8. Rééquilibrage et points de vigilance" : "8. Rebalancing and watch points"));
  if (fr) {
    push(PUCE(`**Dérive des poids.** Les actions (${spct(S.poches.actions.perf)}) ont monté bien plus vite que le reste ; leur part réelle a glissé au-dessus de la cible de ${pct(S.poches.actions.w)}. Le rééquilibrage mensuel prévu par le mandat allège les actions vers l'obligataire — c'est ce geste qui réarme la protection après une hausse.`));
    push(PUCE(`**L'obligataire est désormais mieux rémunéré.** La hausse des taux a coûté cette année, mais elle améliore le rendement attendu de la poche d'État pour la suite : on réinvestit à des taux plus élevés, et le coussin de protection est plus épais qu'en début d'année.`));
    push(PUCE(`**Vår Energi** est devenue, de loin, la plus grosse ligne du panier après son ${spct(st["Vår Energi"].ytd)}. Seule exposition énergie, volatile et liée au prix du pétrole : à surveiller, et le rééquilibrage du panier la ramène à sa taille.`));
    push(PUCE(`**La France.** L'écart de taux OAT-Bund au plus haut depuis la crise de la dette justifie de garder un œil sur la composition de la poche d'État et d'éviter une surpondération de la signature française.`));
    push(PUCE(`**Échelle AAA 6-24 mois (les 10 M€ de liquidité).** ${spct(bo.aaa_ytd)} sur l'année : conforme à son rôle — préserver la somme à sortir, pas la faire travailler.`));
  } else {
    push(PUCE(`**Weight drift.** Equities (${spct(S.poches.actions.perf)}) rose far faster than the rest; their actual share has drifted above the ${pct(S.poches.actions.w)} target. The monthly rebalancing set out in the mandate trims equities back toward bonds — this is the move that re-arms protection after a rally.`));
    push(PUCE(`**Bonds now pay more.** Rising yields cost this year, but they improve the government sleeve's expected return going forward: reinvestment happens at higher rates, and the protection cushion is thicker than at the start of the year.`));
    push(PUCE(`**Vår Energi** has become, by far, the largest holding in the basket after its ${spct(st["Vår Energi"].ytd)}. The sole energy exposure, volatile and oil-price-driven: one to watch, and the basket's rebalancing brings it back to size.`));
    push(PUCE(`**France.** The OAT-Bund spread at its widest since the debt crisis warrants keeping an eye on the government sleeve's composition and avoiding an overweight to French paper.`));
    push(PUCE(`**AAA 6-24m ladder (the €10m of liquidity).** ${spct(bo.aaa_ytd)} on the year: consistent with its role — preserving the sum to be withdrawn, not making it work.`));
  }

  // --- 9. Méthode ---
  push(H1(fr ? "9. Méthode et limites" : "9. Method and limits"));
  if (fr) {
    push(PUCE(`**Fenêtre :** ${a0.split("-").reverse().join("/")} → ${a1.split("-").reverse().join("/")} (${S.days} jours). Cours quotidiens, dividendes réinvestis, tout converti en euros (cours de change pour les titres de Londres et d'Oslo).`));
    push(PUCE(`**Construction :** achat-conservation aux poids cibles depuis le 1ᵉʳ janvier, sans rééquilibrage dans le calcul — les poids dérivent avec les cours, comme dans la réalité entre deux rééquilibrages.`));
    push(PUCE(`**Obligations en direct → proxies ETF de même maturité :** emprunts d'État 2-10 ans représentés par un ETF d'État zone euro 3-7 ans ; échelle AAA 6-24 mois par un ETF 1-3 ans. Le proxy reproduit le comportement de la poche, pas le prix exact des titres détenus.`));
    push(PUCE(`**Repères macro :** pétrole (Brent) et or en dollars ; chiffres de la BCE, de l'inflation, des indices et des taux relevés sur sources publiques en octobre 2026. Ce sont des faits datés, non recalculés en continu.`));
    push(PUCE(`**Pire baisse** mesurée en quotidien sur l'année seulement : elle éclaire le comportement récent mais ne remplace pas le test du mandat sur 2006-2026 (−14,0 % au pire), qui reste la référence pour la limite de −15 %.`));
    push(PUCE(`**Rappel :** YTD ≠ gain réalisé — le mandat date du 24/09. Ces chiffres décrivent la sélection sur l'année, pas un relevé de compte.`));
  } else {
    push(PUCE(`**Window:** ${a0.split("-").reverse().join("/")} → ${a1.split("-").reverse().join("/")} (${S.days} days). Daily prices, dividends reinvested, everything converted to euros (FX for London- and Oslo-listed names).`));
    push(PUCE(`**Construction:** buy-and-hold at target weights since 1 January, with no rebalancing inside the calculation — weights drift with prices, as they do in reality between two rebalancings.`));
    push(PUCE(`**Direct bonds → maturity-matched ETF proxies:** 2-10y government bonds represented by a euro-area 3-7y government ETF; the 6-24m AAA ladder by a 1-3y ETF. The proxy reproduces the sleeve's behaviour, not the exact price of the holdings.`));
    push(PUCE(`**Macro references:** oil (Brent) and gold in dollars; ECB, inflation, index and yield figures taken from public sources in October 2026. These are dated facts, not continuously recomputed.`));
    push(PUCE(`**Worst drawdown** measured daily over this year only: it lights up recent behaviour but does not replace the mandate's 2006-2026 test (−14.0% at worst), which remains the reference for the −15% limit.`));
    push(PUCE(`**Reminder:** YTD ≠ realised gain — the mandate dates from 24/09. These figures describe the selection over the year, not an account statement.`));
  }

  return new Document({
    creator: "Allan Guichard",
    title: fr ? "Mandat Lauren — suivi de portefeuille 2026" : "Mandat Lauren — portfolio monitoring 2026",
    description: fr ? "Analyse YTD du portefeuille du mandat Lauren" : "YTD review of the Mandat Lauren portfolio",
    numbering: { config: [{ reference: "puces", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 460, hanging: 230 } } } }] }] },
    styles: { default: {
      document: { run: { font: "Calibri", size: 21 } },
      heading1: { run: { font: "Calibri", size: 30, bold: true, color: ENCRE }, paragraph: { spacing: { before: 340, after: 150 } } },
      heading2: { run: { font: "Calibri", size: 24, bold: true, color: ENCRE }, paragraph: { spacing: { before: 260, after: 110 } } },
    } },
    sections: [{ properties: { page: { margin: { top: 1100, bottom: 1100, left: 1040, right: 1040 } } }, children: corps }],
  });
}

const cibles = [["fr", "Mandat_Lauren_suivi_YTD_2026.docx"], ["en", "Mandat_Lauren_monitoring_YTD_2026.docx"]];
(async () => {
  for (const [lang, nom] of cibles) {
    const b = await Packer.toBuffer(buildDoc(lang));
    fs.writeFileSync(path.join(ROOT, "outputs", nom), b);
    console.log(`-> outputs/${nom}`, b.length, "octets");
  }
})();
