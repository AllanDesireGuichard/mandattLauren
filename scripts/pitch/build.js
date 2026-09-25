// Pitch oral du mandat Lauren : un fil principal court, le détail en annexes.
// Le speech client est dans les notes de chaque slide.
// Lit data.json (PYTHONPATH=. python3 scripts/pitch/extraire.py), puis :
//   cd scripts/pitch && npm install && npm run build
// Sortie : outputs/Mandat_Lauren_pitch_genere.pptx. Depuis la bascule du
// 2026-09-21, ce générateur est la source du deck de référence : on régénère
// puis on recopie sur Mandat_Lauren_pitch.pptx. L'écriture directe reste
// refusée, pour qu'une retouche faite à la main ne soit jamais écrasée sans
// qu'on l'ait vue : comparer les deux fichiers avant de recopier.
const pptxgen = require("pptxgenjs");
const D = require("./data.json");
const OUT = process.argv[2] || "Mandat_Lauren_pitch_genere.pptx";
if (/Mandat_Lauren_pitch\.pptx$/.test(OUT)) throw new Error("refus : Mandat_Lauren_pitch.pptx est la version retouchée à la main");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "Mandat Lauren — proposition de gestion";
pres.author = "Allan Guichard";

// ---------------------------------------------------------------- style
const INK = "14304F", TEXT = "1F2937", MUTED = "6B7280", CARD = "F2F5F9",
  GRID = "E3E6EA", GOLD = "C98A1B", WHITE = "FFFFFF", NEG = "C2410C";
const FAM = { act: "2A78D6", eta: "EB6834", idx: "1BAF7A", or: "EDA100" };
const HF = "Cambria", BF = "Calibri";
const W = 13.333, M = 0.6;

const fr = (v, d = 1) => {
  const s = Math.abs(v).toFixed(d).replace(".", ",");
  const [a, b] = s.split(",");
  const g = a.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return (v < 0 ? "−" : "") + g + (b !== undefined ? "," + b : "");
};
const pct = (v, d = 1) => fr(v, d) + " %";
const sgn = (v, d = 1) => (v > 0 ? "+" : "") + pct(v, d);
const me = (v, d = 1) => fr(v / 1e6, d) + " M€";

const SECTIONS = ["Paramètres", "Macro", "Lignes", "Allocation", "Backtests"];
let slideNo = 0;

function base(step, title, opts = {}) {
  const s = pres.addSlide();
  slideNo++;
  s.background = { color: WHITE };
  if (step) {
    // motif : pastille numérotée + fil des 5 étapes
    s.addShape(pres.shapes.OVAL, { x: M, y: 0.42, w: 0.52, h: 0.52, fill: { color: INK }, line: { color: INK } });
    s.addText(String(step), { x: M, y: 0.42, w: 0.52, h: 0.52, align: "center", valign: "middle", fontFace: HF, fontSize: 18, bold: true, color: WHITE, margin: 0, isTextBox: true });
    SECTIONS.forEach((n, i) => {
      const on = i + 1 === step;
      s.addShape(pres.shapes.OVAL, { x: 9.55 + i * 0.66, y: 0.52, w: 0.14, h: 0.14, fill: { color: on ? GOLD : GRID }, line: { color: on ? GOLD : GRID } });
      s.addText(n, { x: 9.3 + i * 0.66, y: 0.68, w: 0.64, h: 0.22, fontSize: 7.5, color: on ? INK : MUTED, bold: on, align: "center", fontFace: BF, margin: 0, isTextBox: true });
    });
  }
  s.addText(title, { x: step ? 1.3 : M, y: 0.32, w: step ? 7.9 : W - 2 * M, h: 0.75, fontFace: HF, fontSize: opts.titleSize || 26, bold: true, color: INK, valign: "middle", margin: 0, isTextBox: true });
  if (opts.kicker) s.addText(opts.kicker, { x: step ? 1.3 : M, y: 1.05, w: W - 2 * M - (step ? 0.7 : 0), h: 0.4, fontFace: BF, fontSize: 14, color: MUTED, italic: true, margin: 0, isTextBox: true });
  s.addText(String(slideNo), { x: W - M - 0.5, y: 7.02, w: 0.5, h: 0.3, fontSize: 9, color: MUTED, align: "right", fontFace: BF, margin: 0, isTextBox: true });
  if (opts.source) s.addText(opts.source, { x: M, y: 7.02, w: W - 2 * M - 0.7, h: 0.3, fontSize: 8.5, color: MUTED, fontFace: BF, margin: 0, isTextBox: true });
  return s;
}

function dark(title, sub, opts = {}) {
  const s = pres.addSlide();
  slideNo++;
  s.background = { color: INK };
  if (opts.num) {
    s.addText(opts.num, { x: M, y: 1.6, w: 3, h: 1.6, fontFace: HF, fontSize: 110, bold: true, color: GOLD, margin: 0, isTextBox: true });
  }
  s.addText(title, { x: M, y: opts.num ? 3.25 : 2.3, w: W - 2 * M, h: 1.1, fontFace: HF, fontSize: 40, bold: true, color: WHITE, margin: 0, isTextBox: true });
  if (sub) s.addText(sub, { x: M, y: opts.num ? 4.35 : 3.4, w: 9.5, h: 1.2, fontFace: BF, fontSize: 18, color: "CADCFC", margin: 0, valign: "top", isTextBox: true });
  return s;
}

function stat(s, x, y, w, value, label, color = INK, size = 34) {
  s.addText(value, { x, y, w, h: 0.7, fontFace: HF, fontSize: size, bold: true, color, margin: 0, valign: "bottom", isTextBox: true });
  s.addText(label, { x, y: y + 0.72, w, h: 0.62, fontFace: BF, fontSize: 12, color: MUTED, margin: 0, valign: "top", isTextBox: true });
}

function card(s, x, y, w, h, fill = CARD) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 });
}

function para(s, x, y, w, h, runs, size = 14, opts = {}) {
  s.addText(runs, { x, y, w, h, fontFace: BF, fontSize: size, color: TEXT, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true, ...opts });
}

// texte riche : "**gras** normal" -> runs
function rich(str, extra = {}) {
  const out = [];
  str.split(/(\*\*[^*]+\*\*)/).forEach((p) => {
    if (!p) return;
    if (p.startsWith("**")) out.push({ text: p.slice(2, -2), options: { bold: true, color: INK, ...extra } });
    else out.push({ text: p, options: { ...extra } });
  });
  return out;
}
function bullets(items, extra = {}) {
  const out = [];
  items.forEach((it, i) => {
    const r = rich(it, extra);
    r[0].options = { ...r[0].options, bullet: { indent: 16 } };
    if (i < items.length - 1) r[r.length - 1].options = { ...r[r.length - 1].options, breakLine: true };
    out.push(...r);
  });
  return out;
}

function table(s, rows, x, y, w, colW, opts = {}) {
  const fs = opts.fontSize || 12;
  const data = rows.map((r, i) => r.map((c, j) => {
    const cell = typeof c === "object" && c !== null && c.text !== undefined ? c : { text: String(c) };
    const o = { fontFace: BF, fontSize: fs, color: TEXT, valign: "middle", margin: [3, 6, 3, 6], ...(cell.options || {}) };
    if (i === 0) Object.assign(o, { bold: true, color: WHITE, fill: { color: INK } });
    else if (opts.zebra !== false && i % 2 === 0 && !(cell.options && cell.options.fill)) o.fill = { color: CARD };
    if (j > 0 && opts.alignRight) o.align = "right";
    if (opts.bold1 && j === 0 && i > 0) o.bold = true;
    return { text: cell.text, options: o };
  }));
  s.addTable(data, { x, y, w, colW, border: { type: "solid", pt: 0.5, color: GRID }, rowH: opts.rowH || 0.32, autoPage: false });
}

function callout(s, x, y, w, h, text, fill = INK, size = 15) {
  card(s, x, y, w, h, fill);
  s.addText(rich(text, { color: fill === INK ? WHITE : TEXT }).map((r) => (fill === INK && r.options.bold ? { ...r, options: { ...r.options, color: "F5C969" } } : r)),
    { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: h - 0.3, fontFace: BF, fontSize: size, valign: "middle", margin: 0, isTextBox: true });
}

const chartBase = (title) => ({
  showTitle: !!title, title, titleFontFace: BF, titleFontSize: 13, titleColor: INK,
  catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: BF, valAxisLabelFontFace: BF,
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  valGridLine: { color: GRID, size: 0.5 }, catGridLine: { style: "none" },
  catAxisLineShow: false, valAxisLineShow: false,
  dataLabelFontFace: BF, dataLabelFontSize: 10, dataLabelColor: TEXT,
});
const FMT_PCT = '0.0" %";-0.0" %";;';

// ---------------------------------------------------------------- données utiles
const T = D.taux, S = D.scenarios, R4 = S.r4_marge, LIB = S.libre, BT = D.bt, W4 = D.retenu;
const act = ["actions_europe", "usa", "japon", "emergents"];
const partAct = act.reduce((a, k) => a + W4[k], 0);
const oblig = W4.etats_courts + W4.etats_longs + W4.indexees;
const rdtCls = Object.fromEntries(D.entrees.map(([k, , r]) => [k, r]));
const contrib = Object.keys(W4).reduce((a, k) => a + W4[k] * (rdtCls[k] || 0), 0);
const contribAct = act.reduce((a, k) => a + W4[k] * rdtCls[k], 0);
const ep08 = BT.episodes[0], ep20 = BT.episodes.find((e) => e[0].endsWith("2020")), ep22 = BT.episodes.find((e) => e[0].endsWith("2021"));
const RC = Object.fromEntries(D.rendements.map(([k, lib, c, b, h, n, j]) => [k, { lib, c, b, h, n, j }]));

// ================================================================ 1. Titre
{
  const s = dark("Mandat Lauren", "Préserver le pouvoir d'achat de 100 M€ sans jamais perdre plus de 15 %\n\nProposition de gestion — de l'analyse macro au portefeuille ligne à ligne");
  s.addText("Allan Guichard · septembre 2026", { x: M, y: 6.6, w: 8, h: 0.4, fontSize: 14, color: "CADCFC", fontFace: BF, margin: 0, isTextBox: true });
  s.addNotes("Bonjour. Je vais vous présenter la proposition de gestion que nous avons construite pour M. Lauren. En une phrase : faire en sorte que ses 100 millions gardent leur pouvoir d'achat face à une inflation de 4 %, sans qu'il voie jamais son patrimoine baisser de plus de 15 %. Je vais vous montrer comment on y arrive, étape par étape, et pourquoi chaque choix a été fait.");
}

// ================================================================ 2. Le cas
{
  const s = base(0, "Le cas : M. Lauren, 60 ans, vient de céder sa startup");
  card(s, M, 1.45, 6.1, 5.2);
  para(s, M + 0.3, 1.65, 5.5, 4.9, bullets([
    "**100 M€** en cash, une feuille blanche",
    "**10 M€** à décaisser dans les deux ans",
    "Protéger le reste contre une **inflation de 4 %**",
    "Ne **jamais perdre plus de 15 %**",
    "Exclure **tabac, armement, charbon**",
    "Le fils veut de la **crypto**, le père hésite",
    "Inquiet sur **l'Europe comme sur les États-Unis**",
  ]), 19, { paraSpaceAfter: 16 });
  s.addText("Le cœur du problème", { x: 7.2, y: 1.5, w: 5.5, h: 0.4, fontFace: HF, fontSize: 18, bold: true, color: INK, margin: 0, isTextBox: true });
  stat(s, 7.2, 2.05, 2.6, "≥ 4 %", "par an, pour ne pas s'appauvrir", FAM.idx, 44);
  stat(s, 10.0, 2.05, 2.7, "≤ 15 %", "de baisse, jamais", NEG, 44);
  callout(s, 7.2, 4.0, 5.53, 2.6, "Viser 4 % impose de prendre du risque ; limiter la perte à 15 % en interdit trop. **Tout l'exercice : trouver un portefeuille qui tient les deux à la fois.**", INK, 16);
  s.addNotes("Le client : 60 ans, il vient de vendre sa société, il a 100 millions en cash. Il a construit sa fortune en prenant beaucoup de risque ; aujourd'hui il veut la garder. Deux exigences qui tirent en sens inverse : rapporter au moins 4 % par an, sinon l'inflation l'appauvrit, et ne jamais perdre plus de 15 %. Plus on vise de rendement, plus on prend de risque. Toute la présentation répond à une question : existe-t-il un portefeuille qui tienne les deux ? La fiscalité et la transmission font partie du cas mais sont hors du périmètre de cet exercice.");
}

// ================================================================ 3. Démarche
{
  const s = base(0, "Notre démarche : cinq étapes, chacune nourrit la suivante", { kicker: "Le processus d'un fonds multi-actifs : du plus général au plus détaillé, puis vérification sur le passé" });
  const steps = [
    ["1", "Paramètres", "Que demande le client ?", "Contraintes et hypothèses"],
    ["2", "Macro", "Où en est l'économie ?", "Un rendement espéré par classe"],
    ["3", "Ligne à ligne", "Dans quoi investir ?", "Un support par classe"],
    ["4", "Allocation", "Combien sur chacun ?", "Le portefeuille en M€"],
    ["5", "Backtests", "Aurait-il tenu ?", "Durée des baisses, mauvaise année"],
  ];
  const cw = 2.2, gap = 0.26;
  steps.forEach(([n, t, q, o], i) => {
    const x = M + i * (cw + gap);
    card(s, x, 2.2, cw, 3.7);
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: 2.4, w: 0.62, h: 0.62, fill: { color: INK }, line: { color: INK } });
    s.addText(n, { x: x + 0.2, y: 2.4, w: 0.62, h: 0.62, align: "center", valign: "middle", fontFace: HF, fontSize: 22, bold: true, color: WHITE, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.2, y: 3.2, w: cw - 0.4, h: 0.45, fontFace: HF, fontSize: 18, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(q, { x: x + 0.2, y: 3.7, w: cw - 0.4, h: 0.9, fontFace: BF, fontSize: 14, italic: true, color: TEXT, margin: 0, valign: "top", isTextBox: true });
    s.addText("→ " + o, { x: x + 0.2, y: 4.9, w: cw - 0.4, h: 1.2, fontFace: BF, fontSize: 13, color: GOLD, bold: true, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("Nous avons suivi le processus d'un fonds multi-actifs institutionnel, en cinq étapes. On part de ce que demande le client, puis de l'état de l'économie, on descend jusqu'au choix de chaque titre, on décide des proportions, et on vérifie le résultat sur vingt ans d'histoire. Chaque étape utilise ce que la précédente a produit : aucun chiffre n'apparaît avant l'étape qui le calcule. Tout est disponible dans une application en ligne, que je pourrai ouvrir si vous voulez creuser un point.");
}

// ================================================================ SECTION 1
dark("Paramètres d'entrée", "Ce que dit l'énoncé, ce qu'il révèle du client, et ce qu'il laisse ouvert", { num: "1" })
  .addNotes("Première étape : comprendre la demande avant de chercher des réponses. Cette étape ne calcule rien.");

{
  const s = base(1, "Ce que chaque ligne de l'énoncé veut dire");
  const items = [
    ["10 M€ sous deux ans", "Un décaissement quasi certain : cet argent ne doit pas être exposé au risque."],
    ["Inflation de 4 %", "L'objectif n'est pas de s'enrichir mais de ne pas s'appauvrir : 4 % est le seuil à battre."],
    ["Jamais −15 %", "La limite de risque. C'est elle qui fixe la part d'actifs risqués, donc le rendement possible."],
    ["Tabac, armement, charbon", "Des convictions qui réduisent l'univers d'entreprises ; États et or ne sont pas concernés."],
    ["Crypto", "Une question familiale autant que financière : une petite poche, ou rien."],
    ["Inquiet Europe et États-Unis", "Pas de zone refuge : vraie diversification, et des actifs indépendants de toute économie, comme l'or."],
  ];
  items.forEach(([t, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.15, y = 1.5 + row * 1.75;
    card(s, x, y, 5.95, 1.55);
    s.addText(t, { x: x + 0.25, y: y + 0.15, w: 5.5, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(d, { x: x + 0.25, y: y + 0.6, w: 5.5, h: 0.85, fontFace: BF, fontSize: 13.5, color: TEXT, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("Chaque ligne de l'énoncé a une traduction concrète. Les 10 millions à décaisser ne doivent pas être exposés au risque. L'inflation de 4 %, c'est le seuil à battre : en dessous, le client s'appauvrit. La limite de 15 % fixe la part d'actifs risqués qu'on peut se permettre. Les exclusions touchent les entreprises, pas les États ni l'or. Et l'inquiétude sur l'Europe et les États-Unis plaide pour une vraie diversification. Portrait qui s'en dégage : un entrepreneur qui ne cherche plus à faire fortune mais à la garder, et qui attend qu'on lui explique pourquoi, pas seulement quoi.");
}

{
  const s = base(1, "Questions ouvertes et hypothèses de travail", { kicker: "Des questions à poser à M. Lauren ; faute de réponse, on retient la lecture la plus exigeante" });
  table(s, [
    ["Question laissée ouverte", "Hypothèse retenue"],
    ["Les 15 % : mesurés comment ?", "Depuis le plus haut jamais atteint, sur les 100 M€ ensemble, en euros"],
    ["« Jamais » : sur quelles crises ?", "Tenir au pire cas historique : 2008, 2011, 2020, 2022"],
    ["Les 10 M€ : quand ?", "Quatre versements de 2,5 M€, dans 6, 12, 18 et 24 mois"],
    ["L'inflation à 4 % : prévision ou prudence ?", "Une donnée du problème : le seuil à battre"],
    ["La crypto : combien ?", "Aucune (elle ne rapporte rien et baisse avec les actions, étape 4)"],
    ["Quels supports ?", "Particulier français : fonds européens (UCITS) uniquement"],
  ], M, 1.65, W - 2 * M, [5.0, W - 2 * M - 5.0], { fontSize: 14, rowH: 0.62, bold1: true });
  s.addNotes("L'énoncé laisse plusieurs questions ouvertes, qu'il faudrait poser au client. Faute de réponse, nous avons retenu à chaque fois la lecture la plus exigeante. La plus importante : les 15 %, on les mesure depuis le plus haut jamais atteint, sans limite de durée. C'est ce que le client ressentira : l'écart entre ce qu'il a eu et ce qu'il a. Pour les 10 millions, faute de calendrier, on suppose quatre versements égaux sur deux ans. Pour la crypto, on montrera à l'étape 4 pourquoi nous n'en mettons pas.");
}

// ================================================================ SECTION 2
dark("Macro top-down", "Ce que le marché paie aujourd'hui, où en est le cycle, et ce qu'on peut attendre de chaque classe d'actifs", { num: "2" })
  .addNotes("Deuxième étape : l'analyse macro. On part de ce que le marché paie, de l'état de l'économie, pour en tirer un rendement espéré par classe d'actifs.");

{
  const s = base(2, "Aucune obligation classique ne bat 4 %", { kicker: "Ce que rapportent aujourd'hui les placements de taux, ramenés en euros", source: `Relevé du 18/09/2026 · BCE, FRED, fiches iShares · * rendement avant défauts, un plafond · couverture de change ≈ ${pct(T.cout_couv, 2)} par an` });
  const rows = T.synthese.slice().sort((a, b) => a[1] - b[1]);
  const labels = rows.map((r) => r[0]);
  s.addChart(pres.charts.BAR, [
    { name: "Sous le seuil", labels, values: rows.map((r) => (r[1] <= 4 ? r[1] : 0)) },
    { name: "Au-dessus", labels, values: rows.map((r) => (r[1] > 4 ? r[1] : 0)) },
  ], { ...chartBase("Rendement annuel en euros, seuil de l'énoncé : 4 %"), x: M, y: 1.5, w: 7.6, h: 5.4, barDir: "bar", barGrouping: "stacked", chartColors: ["9CA3AF", FAM.idx], showValue: true, dataLabelFormatCode: FMT_PCT, dataLabelPosition: "inEnd", dataLabelColor: WHITE, valAxisMaxVal: 7, valAxisLabelFormatCode: '0" %"', showLegend: true, legendPos: "b", legendFontSize: 10, barGapWidthPct: 45 });
  para(s, 8.5, 1.6, 4.25, 3.3, bullets([
    `**Monétaire ${pct(T.estr, 2)}** : sans risque, mais le pouvoir d'achat recule`,
    `**États zone euro ${pct(T.etat_euro, 2)}** : sous le seuil`,
    `**Trésor US ${pct(T.us10, 2)}**… mais ${pct(T.us10 - T.cout_couv, 2)} une fois le change couvert`,
    `**Indexées ≈ ${pct(T.idx_reel + 4, 2)}** : les seules qui suivent l'inflation par construction`,
  ]), 14, { paraSpaceAfter: 9 });
  callout(s, 8.5, 5.0, 4.25, 1.8, "Pour le reste de l'objectif, il faudra des actifs dont le rendement n'est **pas fixé d'avance** : actions, actifs réels.", INK, 14);
  s.addNotes(`Premier constat, et il est net : aucune obligation classique ne protège contre 4 % d'inflation. Le monétaire rapporte ${pct(T.estr, 2)}, les emprunts d'État de la zone euro ${pct(T.etat_euro, 2)}. Les taux américains paraissent plus élevés, mais un client qui vit en euros doit couvrir le change, et cette couverture coûte environ ${pct(T.cout_couv, 1)} par an : le supplément disparaît. Les seules obligations au-dessus du seuil de façon certaine sont les indexées sur l'inflation. Le haut rendement affiche plus, mais c'est un rendement avant défauts. Conclusion : pour atteindre 4 %, il faudra des actions et des actifs réels. Question technique possible : pourquoi le taux à l'achat suffit ? Parce que pour une obligation gardée jusqu'à l'échéance, c'est exactement ce qu'elle rapportera, sans aucune prévision.`);
}

{
  const s = base(2, "Le cycle : un choc d'inflation venu de l'énergie", { kicker: "Des banques centrales qui resserrent : le scénario que redoute le client", source: "FRED, BCE, Eurostat, FMI, OCDE · relevé du 18/09/2026 · « avant » : six mois plus tôt (un an pour la croissance)" });
  const c = D.cycle;
  const arrow = (d, s2 = 0.1) => (d[0] - d[1] > s2 ? "↗" : d[1] - d[0] > s2 ? "↘" : "→");
  const cell = (d, dec = 1) => `${pct(d[0], dec)} ${arrow(d)}  (avant ${pct(d[1], dec)})`;
  const lines = [["Croissance (PIB sur un an)", "pib", 1], ["Chômage", "chomage", 1], ["Inflation totale", "inflation", 1], ["Inflation hors énergie et alim.", "inflation_sj", 1], ["Taux de la banque centrale", "banque_centrale", 2], ["Taux à 2 ans", "taux_2a", 2], ["Taux à 10 ans", "taux_10a", 2]];
  table(s, [["", "États-Unis", "Zone euro"], ...lines.map(([n, k, d]) => [n, cell(c.us[k], d), cell(c.ea[k], d)])], M, 1.6, 7.9, [3.0, 2.45, 2.45], { fontSize: 12.5, rowH: 0.52, bold1: true });
  para(s, 8.85, 1.6, 3.9, 3.0, bullets([
    `**Inflation totale en hausse** (${pct(c.ea.inflation[1])} → ${pct(c.ea.inflation[0])} en zone euro), **sous-jacente stable** : c'est l'énergie`,
    `**BCE** déjà remontée à ${pct(c.ea.banque_centrale[0], 2)} ; le **2 ans** annonce d'autres hausses`,
    `**Émergents** : ${pct(c.em.croiss26)} de croissance, mais la Chine ralentit quand l'Inde accélère`,
  ]), 13.5, { paraSpaceAfter: 9 });
  callout(s, 8.85, 4.85, 3.9, 1.95, "À surveiller : si l'inflation **hors énergie** se met à monter, le choc s'installe.", INK, 14);
  s.addNotes("Deuxième lecture : le cycle. On lit une chaîne : l'activité fait l'emploi, l'emploi et l'énergie font l'inflation, l'inflation décide de la banque centrale, qui entraîne les taux. Aujourd'hui, des deux côtés de l'Atlantique, l'inflation totale remonte alors que l'inflation hors énergie ne bouge pas : c'est un choc énergétique. La BCE a déjà remonté son taux, le marché en attend d'autres, et aux États-Unis le taux à 2 ans annonce des hausses de la Fed. C'est précisément le scénario que redoute M. Lauren. Ce contexte pèse sur les obligations à taux fixe, et favorise les indexées et les actifs réels.");
}

{
  const s = base(2, "Le crédit n'a presque jamais été aussi mal payé", { kicker: "La prime de crédit : ce qu'une entreprise paie de plus qu'un État", source: "FRED : Moody's Baa (depuis 1986), ICE BofA US High Yield (depuis 2010) · moyennes trimestrielles" });
  const h = D.credit.histo;
  const idx = h.dates.map((d, i) => i).filter((i) => h.baa[i] !== null);
  s.addChart(pres.charts.LINE, [
    { name: "Entreprises notées Baa (US)", labels: idx.map((i) => h.dates[i]), values: idx.map((i) => h.baa[i]) },
    { name: "Haut rendement (US)", labels: idx.map((i) => h.dates[i]), values: idx.map((i) => (h.hy[i] === null ? "" : h.hy[i])) },
  ], { ...chartBase("Primes de crédit, en points au-dessus de l'État"), x: M, y: 1.5, w: 7.7, h: 5.35, chartColors: [FAM.act, FAM.eta], lineSize: 2, lineDataSymbol: "none", valAxisLabelFormatCode: '0" %"', catAxisLabelFrequency: 20, showLegend: true, legendPos: "b", legendFontSize: 10 });
  stat(s, 8.7, 1.6, 4, `${D.credit.baa_rang} % du temps`, "la prime a été plus basse qu'aujourd'hui, en 40 ans", FAM.eta, 32);
  stat(s, 8.7, 3.0, 4, `−${pct(D.credit.duration_ig)}`, "pour le crédit euro si la prime remonte d'un point : plus d'un an de rendement", NEG, 32);
  callout(s, 8.7, 4.6, 4.05, 2.2, "Peu à gagner, beaucoup à perdre. **Le crédit ne mérite pas d'être surpondéré** : qualité et durées courtes.", INK, 14);
  s.addNotes(`Troisième lecture : le crédit, c'est-à-dire prêter aux entreprises. L'écart entre ce que paie une entreprise et ce que paie un État s'appelle la prime de crédit. Sur quarante ans, elle n'a été plus basse qu'aujourd'hui que ${D.credit.baa_rang} % du temps. Une prime basse n'annonce pas une crise, mais elle laisse très peu de marge : si elle remonte simplement d'un point, le crédit européen perd environ ${pct(D.credit.duration_ig)}, plus d'une année de rendement. En 2008, elle a été multipliée par quatre. Risque asymétrique : on reste sur des entreprises bien notées et des durées courtes.`);
}

{
  const s = base(2, "Les marchés confirment : l'énergie mène", { kicker: "Performance sur 12 mois, en euros — ce qu'aurait vécu le client", source: "ETF cotés à Francfort en euros, dividendes réinvestis · relevé du 18/09/2026" });
  const mk = D.marches;
  const zone = mk.filter((m) => m[1] === "zone").sort((a, b) => a[3] - b[3]);
  const sect = mk.filter((m) => m[1] !== "zone").sort((a, b) => a[3] - b[3]);
  const mkChart = (rows, x, w, title, hide = false) => s.addChart(pres.charts.BAR, [
    { name: "Hausse", labels: rows.map((r) => r[0]), values: rows.map((r) => (r[3] >= 0 ? r[3] : 0)) },
    { name: "Baisse", labels: rows.map((r) => r[0]), values: rows.map((r) => (r[3] < 0 ? r[3] : 0)) },
  ], { ...chartBase(title), x, y: 1.5, w, h: 5.4, barDir: "bar", barGrouping: "stacked", chartColors: [FAM.act, FAM.eta], showValue: true, dataLabelFormatCode: '+0" %";−0" %";;', dataLabelPosition: "inBase", dataLabelColor: WHITE, dataLabelFontSize: 9, valAxisLabelFormatCode: '0" %"', showLegend: false, catAxisLabelFontSize: 10, barGapWidthPct: 40, catAxisLabelPos: "low", valAxisHidden: hide });
  mkChart(zone, M, 5.2, "Par zone");
  mkChart(sect, 5.9, 4.1, "Par secteur, et l'or", true);
  const p = (n) => mk.find((m) => m[0] === n)[3];
  para(s, 10.2, 1.6, 2.55, 5.2, bullets([
    `**Énergie ${sgn(p("Énergie"), 0)}** : l'inflation vient de là`,
    `**Consommation ${sgn(p("Consommation discrétionnaire"), 0)}** : des ménages que l'énergie pénalise`,
    `**Chine ${sgn(p("Chine"), 0)}, Inde ${sgn(p("Inde"), 0)}** : les émergents se regardent pays par pays`,
    "La dynamique dit **ce qui monte**, pas ce qui est bon marché",
  ]), 12.5, { paraSpaceAfter: 9 });
  s.addNotes("Quatrième lecture : les marchés, qui montrent en temps réel où va l'argent. L'énergie mène très largement, ce qui confirme que l'inflation vient de là, et la consommation recule. Les émergents ont monté, mais pas la Chine ni l'Inde : il faut les regarder pays par pays. Attention cependant : la dynamique dit ce qui monte, pas ce qui est bon marché. Un marché qui a pris 30 % est aussi devenu plus cher. C'est l'objet de la slide suivante.");
}

{
  const s = base(2, "Ce qu'on peut attendre de chaque classe d'actifs", { kicker: "Rendement annuel espéré sur dix ans, en euros, dans le monde de l'énoncé (4 % d'inflation)", source: "Obligations : taux lus sur le marché · actions : 1/PER et dividende + croissance des bénéfices · or, matières premières : hypothèse · contrôle J.P. Morgan" });
  const keys = ["cash", "govt_bonds_eur", "credit_ig_eur", "gold", "inflation_linked", "us", "equity_emerging", "infrastructure", "europe", "japon"];
  const rows = keys.map((k) => [RC[k].lib.replace("dont ", "Actions "), RC[k].c]);
  s.addChart(pres.charts.BAR, [
    { name: "Sous 4 %", labels: rows.map((r) => r[0]), values: rows.map((r) => (r[1] <= 4 ? r[1] : 0)) },
    { name: "Au-dessus de 4 %", labels: rows.map((r) => r[0]), values: rows.map((r) => (r[1] > 4 ? r[1] : 0)) },
  ], { ...chartBase(""), x: M, y: 1.55, w: 7.8, h: 5.35, barDir: "bar", barGrouping: "stacked", chartColors: ["9CA3AF", FAM.act], showValue: true, dataLabelFormatCode: '0.0" %";;;', dataLabelPosition: "inEnd", dataLabelColor: WHITE, valAxisMaxVal: 10, valAxisLabelFormatCode: '0" %"', showLegend: false, barGapWidthPct: 40, catAxisLabelFontSize: 11 });
  stat(s, 8.75, 1.6, 2, pct(RC.europe.c), "Actions européennes", FAM.act, 30);
  stat(s, 10.8, 1.6, 2, pct(RC.us.c), "Actions américaines", FAM.act, 30);
  para(s, 8.75, 3.1, 4, 1.7, bullets([
    "**Actions et indexées** dépassent nettement 4 %",
    "Obligations à taux fixe **au niveau ou en dessous**",
    "L'Europe et le Japon devant les États-Unis : **moins chers**",
  ]), 13.5, { paraSpaceAfter: 7 });
  callout(s, 8.75, 5.05, 4, 1.8, "Préserver le pouvoir d'achat impose **des actifs de croissance**. Jusqu'où ? C'est la limite de 15 % qui le dira.", INK, 13.5);
  s.addNotes(`L'aboutissement de l'étape 2 : un rendement espéré par classe d'actifs, sur dix ans, en euros, à 4 % d'inflation. Pour les obligations, on lit simplement le taux du marché : ce sont les chiffres les plus solides. Pour les actions, on estime ce que rapportent les bénéfices achetés aujourd'hui. Résultat : seules les actions et les obligations indexées dépassent nettement le seuil. Préserver le pouvoir d'achat impose donc une part importante d'actions ; la limite de 15 % dira jusqu'où aller. Vous remarquerez que l'Europe est attendue au-dessus des États-Unis : j'y reviens sur la slide suivante.`);
}

{
  const s = base(2, "Europe devant États-Unis : le prix payé", { kicker: "Deux estimations du rendement au-delà de l'inflation, moyennées, puis + 4 % d'inflation", source: `Croissance réelle des bénéfices : ${pct(D.croissance)} par an (S&P 500 depuis 1900, Shiller), la même pour toutes les zones · PER iShares` });
  const e = D.eu_us.europe, u = D.eu_us.us;
  table(s, [
    ["", "Europe", "États-Unis"],
    ["PER (années de bénéfices payées)", fr(e.per_ishares), fr(u.per_ishares)],
    ["① Rendement des bénéfices (1 / PER)", pct(e.m1_reel, 2), pct(u.m1_reel, 2)],
    ["② Dividende + croissance des bénéfices", `${pct(e.dividende, 2)} + ${pct(D.croissance)}`, `${pct(u.dividende, 2)} + ${pct(D.croissance)}`],
    ["Moyenne + 4 % d'inflation", { text: pct(RC.europe.c, 2), options: { bold: true, color: INK } }, { text: pct(RC.us.c, 2), options: { bold: true, color: INK } }],
    ["Repère J.P. Morgan (inflation 2 %)", pct(RC.europe.j), pct(RC.us.j)],
  ], M, 1.65, 7.6, [3.8, 1.9, 1.9], { fontSize: 14, rowH: 0.62, bold1: true, alignRight: true });
  callout(s, 8.6, 1.65, 4.15, 2.3, "« L'action américaine est de meilleure qualité, mais **on la paie presque deux fois plus cher**. À ce prix, elle rapportera probablement moins sur dix ans. »", INK, 14.5);
  card(s, 8.6, 4.2, 4.15, 2.6);
  s.addText("Limites, assumées", { x: 8.85, y: 4.3, w: 3.7, h: 0.4, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 8.85, 4.75, 3.7, 2.0, bullets([
    "Même croissance pour tous : **pénalise les US** (tech)",
    `PER Yahoo ${fr(u.per_yahoo)} au lieu de ${fr(u.per_ishares)} : US ≈ ${pct(RC.us.h)}`,
    "J.P. Morgan : même sens, écart **bien plus faible**",
  ]), 12.5, { paraSpaceAfter: 6 });
  s.addNotes(`Question fréquente : pourquoi l'Europe rapporterait-elle plus que les États-Unis ? Uniquement à cause du prix. À un PER de ${fr(u.per_ishares, 0)}, on paie trente ans de bénéfices pour une action américaine, contre ${fr(e.per_ishares, 1)} en Europe : on achète ${pct(u.m1_reel)} de bénéfices par an d'un côté, ${pct(e.m1_reel)} de l'autre. Le dividende européen est aussi trois fois plus élevé. Limites que j'assume : on applique la même croissance des bénéfices partout, ce qui pénalise les États-Unis dont la tech croît plus vite ; et J.P. Morgan va dans le même sens mais avec un écart de 0,3 point seulement. Conséquence limitée : la répartition entre zones est fixée à l'avance, elle ne dépend pas de cet écart.`);
}

// ================================================================ SECTION 3
dark("Analyse ligne à ligne", "Avec quoi investir : des titres en direct pour les actions européennes et les États, les meilleurs fonds pour le reste", { num: "3" })
  .addNotes("Troisième étape : choisir les supports. Des actions européennes et des obligations d'État en direct, et les meilleurs fonds pour les autres classes.");

{
  const E = D.entonnoir;
  const s = base(3, `De 600 valeurs européennes à ${E.final} titres`, { kicker: "Point de départ : le STOXX Europe 600 · on ne garde que les grandes capitalisations (10 Md€ et plus)" });
  const steps = [[`${E.n}`, "valeurs du STOXX 600"], [`− ${E.excl}`, "exclues : tabac, armement, charbon"], [`− ${E.inv}`, "sociétés d'investissement, non notables"], [`− ${E.petites}`, "trop petites (< 10 Md€)"], [`${E.notees}`, "notées sur cinq piliers"], [`− ${E.vue}`, "écartées par notre vue sectorielle"], [`${E.sel}`, "présélectionnées"], [`${E.final}`, "retenues sur les attentes des analystes"]];
  steps.forEach(([n, l], i) => {
    const w = 11.9 - i * 1.18, x = (W - w) / 2, y = 1.52 + i * 0.63;
    const fill = i === steps.length - 1 ? GOLD : i === 0 ? INK : "3B5A80";
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.55, fill: { color: fill }, line: { color: fill }, rectRadius: 0.06 });
    s.addText([{ text: n + "  ", options: { bold: true, fontSize: 17, fontFace: HF } }, { text: l, options: { fontSize: 12.5 } }], { x, y, w, h: 0.55, align: "center", valign: "middle", color: WHITE, fontFace: BF, margin: 0, isTextBox: true });
  });
  s.addNotes(`Pour les actions européennes, on part des 600 plus grandes valeurs d'Europe. On retire d'abord les ${E.excl} sociétés touchées par les exclusions du client : ${E.excl_motifs.armement} dans l'armement, ${E.excl_motifs.tabac} dans le tabac, ${E.excl_motifs.charbon} dans le charbon, au seuil de 5 % du chiffre d'affaires. On écarte les sociétés d'investissement, que la notation ne sait pas mesurer, et les sociétés de moins de 10 milliards, moins suivies et moins liquides. Il en reste ${E.notees}, que l'on note. Deux étages ensuite : notre vue sectorielle en écarte ${E.vue}, la note en retient ${E.sel}, et les attentes des analystes resserrent ces ${E.sel} en ${E.final}. Deux questions différentes, dans cet ordre : ce que les sociétés SONT, puis où elles VONT.`);
}

{
  const s = base(3, "Cinq piliers, face à son propre secteur", { kicker: "Une banque est comparée aux banques, un laboratoire aux laboratoires" });
  const P = [["Valorisation", "Est-elle bon marché ?"], ["Croissance", "Ses résultats progressent-ils ?"], ["Dynamique", "Le marché la soutient-il ?"], ["Qualité", "Est-elle solide et rentable ?"], ["Résistance", "Tient-elle bon quand le marché chute ?"]];
  P.forEach(([t, q], i) => {
    const y = 1.6 + i * 0.98;
    s.addShape(pres.shapes.OVAL, { x: M, y: y + 0.08, w: 0.6, h: 0.6, fill: { color: i === 4 ? GOLD : INK }, line: { color: i === 4 ? GOLD : INK } });
    s.addText(String(i + 1), { x: M, y: y + 0.08, w: 0.6, h: 0.6, align: "center", valign: "middle", color: WHITE, bold: true, fontFace: HF, fontSize: 18, margin: 0, isTextBox: true });
    s.addText(t, { x: M + 0.8, y, w: 3.5, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(q, { x: M + 0.8, y: y + 0.4, w: 4.2, h: 0.4, fontFace: BF, fontSize: 13.5, color: TEXT, italic: true, margin: 0, isTextBox: true });
  });
  card(s, 6.3, 1.6, 6.43, 2.35);
  s.addText("Pourquoi « Résistance » ?", { x: 6.55, y: 1.72, w: 6, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 6.55, 2.15, 5.95, 1.7, rich("Plus la poche d'actions baisse modérément en crise, plus on peut en détenir sous la limite de 15 %. On note donc aussi **la volatilité, les pertes de 2020 et 2022, et le bêta**."), 13.5);
  card(s, 6.3, 4.15, 6.43, 2.65);
  s.addText("Garde-fous de diversification", { x: 6.55, y: 4.27, w: 6, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 6.55, 4.72, 5.95, 2.0, bullets(["**4 titres** au plus par secteur, **6** par pays", `Volatilité plafonnée **dans son métier** : ${fr(D.vol_plafond.univers, 1)} % pour tous, jusqu'à ${fr(D.vol_plafond.max, 1)} % là où l'agitation est structurelle`, "Données aberrantes écartées (un PER de 1 042…)"]), 12.5, { paraSpaceAfter: 6 });
  // Le corollaire de « face à son propre secteur » : la note est aveugle aux
  // secteurs, donc la macro de l'étape 2 ne descend pas jusqu'ici. Dit sur la
  // slide parce qu'un jury le demande, et que le deck l'annonçait nulle part.
  para(s, M, 6.42, 5.5, 0.55, rich("**La note ne dit donc rien d'un secteur**, seulement d'une société face à ses concurrentes : la vue macro agit à l'étape 4, pas ici."), 12);
  s.addNotes("Chaque société reçoit une note sur cinq piliers à poids égaux, toujours comparée aux sociétés de son propre secteur : c'est ce qui permet de comparer une banque, dont le PER est naturellement bas, à un éditeur de logiciels. Le cinquième pilier, la résistance, est propre à ce mandat : plus la poche d'actions baisse modérément en crise, plus on peut en détenir sous la limite de 15 %. Détail technique si on me le demande : chaque indicateur est mesuré en écarts-types par rapport à la moyenne du secteur, après avoir écarté les données aberrantes. SUR LE PLAFOND DE VOLATILITÉ, il est mesuré DANS le métier et non sur tout l'univers, et c'est une correction du 25 septembre : un plafond unique ne dit pas « ce titre est agité pour son métier », il dit « ce métier est agité », et il interdisait le métier. La technologie disparaissait entièrement de la sélection alors qu'elle pèse 7,4 % de l'indice — ASML sortait pour moins d'un point de volatilité, alors que sa note passait le seuil. Elle est aujourd'hui la première des quinze sur les attentes des analystes. SI ON ME DEMANDE OÙ EST LA VUE SECTORIELLE : elle existe, mais elle n'est pas dans la note — elle a sa propre slide. La note, elle, est aveugle aux secteurs par construction : comparer chaque société à son propre secteur la fait dire qu'une banque est meilleure que les autres banques, jamais s'il faut détenir des banques. Les secteurs de la sélection sont donc un résultat, pas une décision, et notre vue sectorielle agit à côté, en écartant des métiers, pas en pondérant. SI ON ME DEMANDE OÙ AGIT LA MACRO : sur la répartition entre classes d'actifs, et par un seul canal — elle fixe les rendements espérés, et c'est le calcul de l'étape 4 qui les convertit en poids. Elle tranche combien d'actions au total et combien d'indexées ; elle ne tranche ni la zone, figée par la clé 40/35/10/15, ni le secteur. Attention à une formulation que j'ai corrigée : le crédit à zéro n'est PAS une décision macro, c'est une mesure de marché de l'étape 3 — 3,39 % défauts déduits contre 3,63 % pour les emprunts d'État. Tirer EN PLUS des paris sectoriels de la macro reviendrait à miser deux fois sur le même diagnostic. Un portefeuille, un pari.");
}

{
  // Ajoutée le 2026-09-25. Une décision discrétionnaire doit avoir sa slide :
  // elle ne peut pas vivre dans une note de bas de page ni dans un coefficient.
  const V = D.vue;
  const s = base(3, "Notre vue sectorielle, et ce qu'elle coûte", { kicker: `Quatre métiers que nous nous interdisons · décision de gestion, pas contrainte du client · depuis le ${V.depuis.split("-").reverse().join("/")}` });
  const rows = [["Métier écarté", "Pourquoi", "Ce que disent nos données"],
    ...V.industries.map(([i, these, don]) => [i, these, don])];
  table(s, rows, M, 1.5, W - 2 * M, [2.2, 5.3, 5.0], { fontSize: 9, rowH: 0.3 });
  card(s, M, 5.55, W - 2 * M, 1.25);
  s.addText("Ce que la décision coûte", { x: M + 0.25, y: 5.67, w: 6, h: 0.35, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M + 0.25, 6.05, W - 2 * M - 0.5, 0.65, rich(`**${V.titres} sociétés notées** sortent de l'univers. La meilleure d'entre elles, ${V.meilleur}, était notée **${fr(V.meilleure_note, 2)}** : elle était la dernière des présélectionnés. La sélection finale et le risque du panier sont **inchangés** — la vue ne coûte qu'un titre, et le dernier.`), 12.5);
  s.addNotes(`Une précision de méthode, et j'insiste dessus parce qu'elle sépare deux choses que l'on confond souvent. Les exclusions tabac, armement et charbon sont des contraintes du client : elles sont subies, non négociables, et leur respect se constate. Ce que vous voyez ici est l'inverse : c'est notre décision de gérant, assumée et révisable, et c'est à nous de la défendre. D'où une slide séparée. POURQUOI UNE EXCLUSION ET NON UN MALUS DANS LA NOTE, si on me le demande : parce que le signe d'un malus n'est pas déterminé. Dire que les gérants sous-pondèrent l'automobile justifie aussi bien de la vendre, si le consensus a raison, que de l'acheter, puisqu'elle est devenue bon marché parce qu'elle est détestée. Nos cinq piliers disent d'ailleurs exactement ces deux choses à la fois : sur les constructeurs, la Dynamique sort à moins 0,58 quand la Valorisation sort à plus 0,62, et la note finale ressort à la médiane de l'univers. La note ne rate donc pas la difficulté du secteur — le momentum médian des constructeurs est à moins 15,9 % quand l'univers est à plus 15,5 % — elle juge qu'elle est DÉJÀ PAYÉE par le prix. Retrancher un malus reviendrait à casser cette compensation sans le dire. Une exclusion déclarée, elle, est datée, motivée, et son coût se mesure. DERNIER POINT, et je le dis avant qu'on me le demande : la colonne de droite dit ce que NOS données pensent de chaque thèse, y compris quand elles la contredisent. Sur la chimie de spécialité, elles la contredisent — quinze titres, milieu de classement. La vue y anticipe une dégradation que les chiffres n'enregistrent pas encore, et c'est aussi le seul cas qui nous coûte un titre. C'est écrit dans le tableau plutôt que caché.`);
}


{
  // Deuxième étage, ajouté au deck le 2026-09-25 : il existait dans
  // l'application depuis le 24 septembre, le deck n'en disait rien.
  const A = D.avenir;
  const s = base(3, `Deuxième étage : où vont-elles ?`, { kicker: `Les ${D.entonnoir.sel} présélectionnés resserrés en ${D.entonnoir.final} · ce que le consensus des analystes ATTEND, relevé du ${A.releve.split("-").reverse().join("/")}`, source: "Objectifs de cours et estimations de bénéfice · Yahoo Finance" });
  s.addText("Deux mesures qui classent", { x: M, y: 1.5, w: 6, h: 0.38, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M, 1.92, 5.9, 1.75, bullets([
    "**La révision** : de combien le bénéfice attendu a bougé en 90 jours. Le SENS dans lequel le consensus se déplace, qui vaut mieux que son niveau",
    "**Le solde des révisions** : la part des analystes qui relèvent, moins ceux qui abaissent",
  ]), 12.5, { paraSpaceAfter: 7 });
  s.addText("Deux mesures qui éliminent", { x: M, y: 3.8, w: 6, h: 0.38, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M, 4.22, 5.9, 1.75, bullets([
    `**Le potentiel** (cours face à l'objectif). Écarte un titre **seulement** s'il cote au-dessus de sa cible ET que les bénéfices ne suivent pas`,
    `**La dispersion** des estimations : au-delà de ${fr(A.plafond_dispersion, 0)} %, l'avenir de la société est jugé illisible`,
  ]), 12.5, { paraSpaceAfter: 7 });
  card(s, 6.85, 1.5, W - M - 6.85, 2.5);
  s.addText("Les garde-fous, et pourquoi ces seuils", { x: 7.1, y: 1.62, w: 5.5, h: 0.38, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 7.1, 2.05, W - M - 7.35, 1.85, bullets([
    `Bénéfice attendu coupé de plus de **${fr(-A.revision_min, 0)} %** : écarté. Seuil **absolu** et non en percentile — un percentile écarte toujours 10 % des titres, même quand aucun ne va mal`,
    `Solde ignoré en dessous de **${A.revisions_min} révisions** : sur une seule, il ne peut valoir que −100 ou +100`,
    `Au plus **${A.max_secteur} titres par secteur** et **${A.max_pays} par pays** : sur 15 lignes, les plafonds du premier étage laisseraient 6 espagnols faire 40 % du panier`,
  ]), 11.5, { paraSpaceAfter: 5 });
  card(s, 6.85, 4.2, W - M - 6.85, 1.77);
  s.addText(`Écartés par les garde-fous`, { x: 7.1, y: 4.32, w: 5.5, h: 0.38, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 7.1, 4.75, W - M - 7.35, 1.1, rich(D.ecartes.map(([n, , m]) => `**${n.split(/[ ,]/)[0]}** — ${m.toLowerCase()}`).join("  ·  ")), 11);
  para(s, M, 6.25, W - 2 * M, 0.6, rich("**Pourquoi pas l'avis « acheter / conserver / vendre »** : le biais acheteur est structurel, et l'objectif de cours monte mécaniquement quand un titre baisse. Il manquait en plus sur 6 des 30, dont des sociétés suivies par 14 analystes. Affiché, jamais noté."), 12);
  s.addNotes(`Le premier étage mesure ce que les sociétés SONT : tout y est constaté, sur le passé et le présent. Ce deuxième étage pose la question d'après — où vont-elles ? C'est une décision de méthode que je revendique : trente lignes, pour du stock picking, c'est beaucoup, et surtout c'est un portefeuille qu'on n'a pas vraiment choisi. QUATRE INDICATEURS, et deux usages distincts. Deux classent : la révision du bénéfice attendu sur 90 jours, et le solde des révisions du mois. Deux éliminent seulement : le potentiel et la dispersion. Pourquoi cette séparation ? Parce que la valeur exacte d'un potentiel n'est pas un signal — l'objectif de cours bouge plus lentement que le cours, donc un fort potentiel signale souvent une chute récente plutôt qu'un bon dossier. Et la dispersion est structurellement sectorielle : une pétrolière dépend d'un prix que personne ne prévoit, donc la noter reviendrait à noter le secteur. TROIS SEUILS QUE J'AI DÛ CORRIGER, et je préfère les dire : le solde était d'abord rapporté au nombre d'analystes, un champ incohérent chez Yahoo, ce qui plaçait argenx première pour cette seule raison ; sans plancher de qualité, la sélection raclait le fond dès qu'un secteur se vidait, et retenait Norsk Hydro avec une révision de moins 17 % ; et sur une ou deux révisions le solde ne peut valoir que moins 100 ou plus 100, ce qui faisait sortir Airtel à moins 100 pour UN analyste. Les trois sont corrigés, et c'est écrit dans le code. DERNIER POINT si on me le demande : le garde-fou du potentiel est CONDITIONNEL. Il excluait d'abord tout titre cotant au-dessus de sa cible, ce qui contredisait mon propre argument. Mesuré : les huit titres concernés avaient TOUS un bénéfice révisé à la hausse. La règle ne sanctionnait pas la cherté, elle sanctionnait la bonne dynamique.`);
}

{
  const Q = D.quinze;
  const s = base(3, `Les ${D.entonnoir.final} titres retenus`, { kicker: `À parts égales · ${Object.keys(D.secteurs).length} secteurs et ${Object.keys(D.pays).length} pays · note = le constaté, avenir = l'attendu`, source: "Composition iShares STOXX Europe 600 · Yahoo Finance, septembre 2026" });
  const name = (n) => n.replace(/,?\s+(plc|p\.l\.c\.|s\.a\.|s\.p\.a\.|sa|ag|se|n\.v\.|asa|ab|\(publ\)|holdings?|société anonyme|aktiengesellschaft|group|limited|oyj|a\/s)\.?$/i, "").replace(/,?\s+(plc|s\.a\.|ag|se|sa|n\.v\.)\.?$/i, "");
  const rows = [["#", "Société", "Secteur", "Pays", "Note", "Avenir", "Bénéfice attendu, 90 j"],
    ...Q.map((r, i) => [String(i + 1), name(r[0]).slice(0, 26), r[1], r[2], (r[3] >= 0 ? "+" : "") + fr(r[3], 2), (r[4] >= 0 ? "+" : "") + fr(r[4], 2), (r[5] >= 0 ? "+" : "") + fr(r[5], 1) + " %"])];
  // 16 lignes × 0,31 = 4,96 sous un tableau posé à 1,50 : il finit à 6,46,
  // ce qui laisse la note au-dessus de la ligne de source (7,02).
  table(s, rows, M, 1.5, W - 2 * M, [0.4, 3.0, 2.6, 1.5, 0.95, 0.95, 2.73], { fontSize: 10, rowH: 0.31, alignRight: false });
  para(s, M, 6.56, W - 2 * M, 0.4, rich(`**Le resserrement coûte du risque, et je l'assume** : volatilité ${fr(D.panier.panier.vol_3a, 2)} % contre ${fr(D.panier.trente.vol_3a, 2)} % à trente — chercher l'avenir coûte de la protection, parce que les défensives cotent souvent au-dessus de leur objectif.`), 11.5);
  s.addNotes(`Voici le portefeuille d'actions européennes : ${D.entonnoir.final} lignes à parts égales, ${Object.keys(D.secteurs).length} secteurs et ${Object.keys(D.pays).length} pays. Deux colonnes de note, et c'est tout le propos : « Note » est le premier étage, ce que la société EST ; « Avenir » est le second, où elle VA. Un titre doit passer les deux. ASML est le cas le plus parlant : son bénéfice attendu a été relevé de 24 % en trois mois, le meilleur dossier des trente sur l'avenir — et elle a failli ne jamais entrer dans l'univers, parce que le plafond de volatilité était mesuré sur tout le marché au lieu de l'être sur son métier. SUR LE SURCROÎT DE RISQUE, et il faut le dire avant qu'on me le demande : passer de trente à quinze lignes fait monter la volatilité du panier d'environ 1,3 point. La cause est identifiée : le garde-fou du potentiel frappe les défensives, qui cotent souvent au-dessus de leur objectif quand elles sont chères. Chercher l'avenir coûte de la protection. L'échelle réelle, en revanche, est petite : la poche d'actions européennes vaut 12,2 % du portefeuille, donc l'écart pèse environ 0,16 point au niveau du patrimoine. La limite de moins 15 % n'est pas approchée.`);
}

{
  const P = D.panier;
  const s = base(3, "Le panier résiste mieux que l'indice", { kicker: `Les ${D.entonnoir.final} titres à parts égales, en euros, face aux ${D.entonnoir.sel} présélectionnés et au STOXX Europe 600` });
  const items = [["Volatilité sur 3 ans", P.panier.vol_3a, P.trente.vol_3a, P.indice.vol_3a], ["Pire baisse en 2020", P.panier.dd_2020, P.trente.dd_2020, P.indice.dd_2020], ["Pire baisse en 2022", P.panier.dd_2022, P.trente.dd_2022, P.indice.dd_2022]];
  items.forEach(([l, a, b, c], i) => {
    const x = M + i * 4.1;
    card(s, x, 1.7, 3.85, 2.85);
    s.addText(l, { x: x + 0.25, y: 1.82, w: 3.4, h: 0.4, fontFace: BF, fontSize: 14, color: MUTED, margin: 0, isTextBox: true });
    s.addText(pct(a), { x: x + 0.25, y: 2.24, w: 3.4, h: 0.85, fontFace: HF, fontSize: 38, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText(`les ${D.entonnoir.sel} : ` + pct(b), { x: x + 0.25, y: 3.14, w: 3.4, h: 0.38, fontFace: BF, fontSize: 13.5, color: TEXT, margin: 0, isTextBox: true });
    s.addText("indice : " + pct(c), { x: x + 0.25, y: 3.52, w: 3.4, h: 0.38, fontFace: BF, fontSize: 13.5, color: MUTED, margin: 0, isTextBox: true });
  });
  callout(s, M, 4.9, W - 2 * M, 1.6, "Moins agité que l'indice, nettement mieux tenu en 2022, un peu plus exposé en 2020 que les trente — le prix du resserrement. Mais en crise, un panier d'actions perd **bien plus que 15 %** : c'est le dosage avec les obligations et l'or, à l'étape 4, qui tiendra la limite.", INK, 14.5);
  s.addNotes(`On vérifie que la sélection tient mieux en crise que l'indice. C'est le cas en 2022 : ${pct(P.panier.dd_2022)} contre ${pct(P.indice.dd_2022)}. En 2020, les deux ont baissé d'environ un tiers. La colonne du milieu est la mesure honnête du resserrement : passer de ${D.entonnoir.sel} à ${D.entonnoir.final} lignes coûte de la volatilité, ${pct(P.panier.vol_3a, 2)} contre ${pct(P.trente.vol_3a, 2)}, et un peu de 2020. Rapporté au patrimoine, où la poche vaut 12,2 %, cela pèse environ 0,16 point. Message important : un panier d'actions reste un panier d'actions. La limite de 15 % ne se tiendra pas par le choix des titres, mais par le dosage entre actions, obligations et or, à l'étape 4. Précaution d'honnêteté : les titres sont choisis avec les données d'aujourd'hui, donc leur performance passée est flatteuse par construction ; seul leur comportement en crise est informatif.`);
}

{
  const SV = D.souverains;
  const s = base(3, "Les emprunts d'État, achetés en direct", { kicker: "Pas de frais de gestion, et la date et le montant de chaque remboursement connus d'avance", source: "Courbes zéro-coupon de la BCE (modèle de Svensson) au 18/09/2026" });
  s.addText("Les 10 M€ à décaisser : une échelle AAA", { x: M, y: 1.6, w: 6, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: INK, margin: 0, isTextBox: true });
  ["6 mois", "12 mois", "18 mois", "24 mois"].forEach((l, i) => {
    const x = M + i * 1.5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.15, w: 1.35, h: 1.25, fill: { color: FAM.eta }, line: { color: FAM.eta }, rectRadius: 0.06 });
    s.addText([{ text: "2,5 M€", options: { bold: true, fontSize: 17, breakLine: true } }, { text: l, options: { fontSize: 12, breakLine: true } }, { text: pct(SV.taux[i], 2), options: { fontSize: 11 } }], { x, y: 2.15, w: 1.35, h: 1.25, align: "center", valign: "middle", color: WHITE, fontFace: BF, margin: 0, isTextBox: true });
  });
  stat(s, M, 3.7, 2.9, me(SV.cout, 2), "à investir aujourd'hui, à taux garantis (Allemagne, Pays-Bas…)", INK, 28);
  stat(s, M + 3.0, 3.7, 2.9, fr((SV.cout_mon - SV.cout) / 1e3, 0) + " k€", "économisés face au monétaire", FAM.idx, 28);
  card(s, 6.85, 1.6, 5.88, 3.45);
  s.addText("La poche longue : une échelle 2-3-5-7-10 ans", { x: 7.1, y: 1.75, w: 5.4, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: INK, margin: 0, isTextBox: true });
  stat(s, 7.1, 2.25, 2.6, pct(SV.rdt_long, 2), "de rendement moyen, toute la zone euro", INK, 30);
  stat(s, 9.9, 2.25, 2.6, pct(SV.choc_long), "si les taux montent d'un point", NEG, 30);
  para(s, 7.1, 3.85, 5.4, 1.1, rich("Allonger au-delà de 10 ans rapporte peu et **multiplie la perte** en cas de hausse des taux : avec une inflation qui remonte, on n'allonge pas."), 13);
  callout(s, M, 5.35, W - 2 * M, 1.4, "AAA pour l'argent attendu **à date fixe** ; toute la zone euro, diversifiée, pour la poche longue (tous « investment grade », près d'un demi-point de plus à 10 ans).", INK, 14.5);
  s.addNotes(`Pour la partie la plus sûre, pas besoin de fonds : on achète directement des obligations d'État. Les 10 millions à décaisser sont placés en quatre obligations allemandes ou néerlandaises qui arrivent à échéance aux dates des versements : il faut investir ${me(SV.cout, 2)} aujourd'hui, à taux garantis, et on économise environ ${fr((SV.cout_mon - SV.cout) / 1e3, 0)} milliers d'euros par rapport au monétaire. Pour le reste de la poche obligataire, une échelle de 2 à 10 ans sur toute la zone euro, qui rapporte ${pct(SV.rdt_long, 2)} et perdrait environ ${pct(-SV.choc_long)} si les taux montaient d'un point. On n'allonge pas au-delà : cela rapporte peu et multiplie le risque, dans un contexte où l'inflation remonte.`);
}

{
  const s = base(3, "Les autres classes : les meilleurs fonds", { kicker: "Exclusions conformes au mandat  →  taille d'au moins 1 Md€  →  frais les plus bas", source: "justETF, Yahoo, méthodologies MSCI lues le 18/09/2026 · « Screened » écarté : il n'exclut pas l'armement conventionnel" });
  // La colonne « Exclusions » est la PREMIÈRE des trois règles de sélection et
  // n'était affichée nulle part : le deck annonçait la conformité en
  // sous-titre sans jamais la montrer fonds par fonds. « Sans objet » veut
  // dire qu'il n'y a aucune action d'entreprise à filtrer (États, or,
  // contrats à terme), pas que rien n'a été vérifié.
  if (D.fonds_non_conformes.length) throw new Error("fonds retenus non conformes aux exclusions : " + D.fonds_non_conformes.join(", "));
  const EX = { conforme: "Conforme", "sans objet": "Sans objet" };
  const rows = [["Classe", "Fonds retenu", "Exclusions", "Frais / an", "Taille"]];
  D.fonds.forEach(([cl, t, nom, fr_, tl, ex]) => rows.push([cl, `${t} · ${nom.replace(" UCITS ETF", "").replace(" EUR (Acc)", "").replace(" 1C", "")}`, EX[ex] || ex, pct(fr_, 2), fr(tl / 1000, 1) + " Md€"]));
  const cf = D.credit_fonds;
  rows.push(["Crédit euro bien noté, court", `${cf.ticker} · ${cf.nom.replace(" UCITS ETF EUR (Dist)", "")}`, "Conforme", pct(cf.frais, 2), fr(cf.taille / 1000, 1) + " Md€"]);
  table(s, rows, M, 1.6, 8.3, [2.4, 3.1, 1.0, 0.9, 0.9], { fontSize: 11.5, rowH: 0.48, bold1: true });
  para(s, 9.2, 1.6, 3.55, 5.2, bullets([
    "**Aucun fonds non conforme retenu** : *sans objet* = ni action ni entreprise à filtrer (États, or, contrats à terme)",
    "**États-Unis et Japon séparés**, plutôt qu'un fonds Monde qui recompterait l'Europe",
    `**Émergents** : le seul fonds conforme s'écarte du marché (${sgn(D.xzem_ecart, 1)} par an sur 7 ans) — écart annoncé au client`,
    "**Infrastructure retirée** : aucun fonds à la fois assez gros et conforme",
    "**Pas de fonds Bitcoin** : la décision est de ne pas en détenir",
  ]), 12, { paraSpaceAfter: 7 });
  s.addNotes("Pour les autres classes, on passe par des fonds cotés, choisis selon une règle simple : d'abord des exclusions conformes au mandat, puis une taille d'au moins un milliard, pour ne jamais peser plus de 1 % d'un fonds, et enfin les frais les plus bas. Point de vigilance : un filtre ESG dit « Screened » n'exclut pas l'armement conventionnel, alors que nous l'avons exclu des actions en direct ; nous avons donc lu les méthodologies d'indices et retenu des indices plus stricts. Conséquence pour les émergents : le seul fonds conforme s'éloigne nettement du marché, écart que nous annoncerons au client. L'infrastructure a été retirée : aucun fonds n'était à la fois assez gros et conforme. Enfin, en revérifiant l'univers de départ, nous avons trouvé neuf fonds mal libellés, dont un fonds d'actions américaines présenté comme de la dette émergente.");
}


// ================================================================ SECTION 4
dark("Allocation", "Combien placer sur chaque support pour rapporter au moins 4 % sans jamais perdre plus de 15 %", { num: "4" })
  .addNotes("Quatrième étape, le cœur de l'exercice : combien placer sur chaque support.");

{
  const PR = D.panier_rdt;
  const s = base(4, "Seules les actions et les indexées dépassent 4 %", { kicker: "Rendement espéré de chaque support : étape 2, corrigé de ce que l'étape 3 a appris", source: `Actions européennes : ${pct(PR.central, 2)}, mesuré sur les ${PR.n} titres retenus — 1/PER ${pct(PR.m1_reel, 2)}, dividende ${pct(PR.dividende, 2)} + croissance ${pct(PR.croissance, 2)}, plus ${pct(PR.inflation, 0)} d'inflation` });
  const nm = { actions_europe: "Actions Europe", usa: "Actions États-Unis", japon: "Actions Japon", emergents: "Actions émergentes", etats_courts: "Échelle AAA (10 M€)", etats_longs: "États 2-10 ans", credit_court: "Crédit court", indexees: "Indexées", or: "Or", matieres: "Matières premières" };
  const rows = D.entrees.slice().sort((a, b) => a[2] - b[2]);
  s.addChart(pres.charts.BAR, [
    { name: "Sous 4 %", labels: rows.map((r) => nm[r[0]]), values: rows.map((r) => (r[2] <= 4 ? r[2] : 0)) },
    { name: "Au-dessus", labels: rows.map((r) => nm[r[0]]), values: rows.map((r) => (r[2] > 4 ? r[2] : 0)) },
  ], { ...chartBase("Rendement espéré par an"), x: M, y: 1.55, w: 7.4, h: 5.35, barDir: "bar", barGrouping: "stacked", chartColors: ["9CA3AF", FAM.act], showValue: true, dataLabelFormatCode: '0.00" %";;;', dataLabelPosition: "inEnd", dataLabelColor: WHITE, valAxisMaxVal: 10, valAxisLabelFormatCode: '0" %"', showLegend: false, barGapWidthPct: 40 });
  card(s, 8.3, 1.6, 4.43, 2.9);
  s.addText("La règle de perte", { x: 8.55, y: 1.72, w: 4, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 8.55, 2.15, 4.0, 2.3, bullets(["Mesurée **depuis le plus haut**", "Sur **les 100 M€** ensemble", "Jamais au-delà de 15 % dans **2008, 2011, 2020, 2022**", "**Pas de crypto**"]), 13.5, { paraSpaceAfter: 6 });
  callout(s, 8.3, 4.75, 4.43, 1.25, "Chaque euro placé en obligations ou en or devra être **compensé par des actions** : c'est la tension entre 4 % et 15 %.", INK, 14);
  // Le seul rendement espéré qui ne vient pas de l'indice de sa classe.
  para(s, 8.3, 6.15, 4.43, 0.8, rich(`**Actions Europe : ${pct(PR.central, 2)} mesuré sur les ${PR.n} titres retenus**, pas sur l'indice — même méthode, appliquée au panier qu'on achète.`), 12);
  s.addNotes("Le calcul a besoin de trois ingrédients. La règle : la perte se mesure depuis le plus haut, sur les 100 millions, et ne doit jamais dépasser 15 % dans les quatre crises de référence. Les rendements espérés : seules les actions et les obligations indexées dépassent 4 %. Tout le reste rapporte moins : chaque euro placé en obligations devra être compensé par des actions. Et le troisième ingrédient, c'est le comportement de chaque support en crise, sur vingt ans. Or la plupart des fonds datent de 2018 : avant, on utilise un remplaçant qui suit le même marché, et pour les États une obligation recalculée sur la courbe de la BCE.");
}

{
  const s = base(4, "En crise, qui amortit ? Ça dépend de la crise", { kicker: "Variation de chaque support pendant que les actions baissaient, du sommet au creux", source: "Séries quotidiennes en euros depuis octobre 2006 · vrai support dès qu'il existe, remplaçant avant · crises datées à l'avance" });
  const P = D.pendant;
  const rows = [["poche_actions", "Poche actions (40/35/10/15)"], ["etats_longs", "États zone euro 2-10 ans"], ["indexees", "Obligations indexées"], ["or", "Or"], ["matieres", "Matières premières"], ["crypto", "Bitcoin"]];
  const crises = Object.keys(D.crises_lib);
  const cellc = (v) => (v === null ? { text: "—" } : { text: sgn(v, 0), options: { bold: true, color: v >= 0 ? "0F7A55" : NEG } });
  table(s, [["", ...crises.map((c) => `${c} · ${D.crises_lib[c]}`)], ...rows.map(([k, n]) => [n, ...crises.map((c) => cellc(P[k][c]))])], M, 1.6, 8.2, [2.8, 1.35, 1.35, 1.35, 1.35], { fontSize: 12.5, rowH: 0.62, bold1: true, alignRight: true });
  const pa = D.pertes.poche_actions["2008"];
  stat(s, 9.2, 1.6, 3.55, "≤ " + pct(15 / -pa * 100, 0), `d'actions au plus sans amortisseur (15 ÷ ${fr(-pa, 0)})`, INK, 34);
  para(s, 9.2, 3.2, 3.55, 3.6, bullets(["**Récession** (2008, 2011) : les États montent", "**Inflation** (2022) : tout baisse ensemble", "**L'or** tient dans les quatre crises", "Matières premières et bitcoin : **aucun amortisseur**"]), 13.5, { paraSpaceAfter: 9 });
  s.addNotes(`Deuxième ingrédient : le comportement en crise. Les actions perdent jusqu'à ${pct(-pa, 0)} en 2008. Sans amortisseur, on ne pourrait donc pas en détenir plus de ${pct(15 / -pa * 100, 0)}. Pour aller au-delà, il faut des supports qui montent quand les actions baissent. En 2008, sur la fenêtre de crise, les emprunts d'État gagnent ${pct(D.perf_crises.etats_longs['2008'])} et l'or ${pct(D.perf_crises.or['2008'])} : ils amortissent. Mais en 2022, crise d'inflation, les obligations baissent avec les actions : plus d'amortisseur. C'est le régime décrit à l'étape 2. L'or est le seul qui tienne partout. Parce que ce lien change d'une crise à l'autre, le calcul ne s'appuie pas sur une corrélation moyenne : il fait traverser à chaque portefeuille les vingt années, jour après jour.`);
}

{
  const s = base(4, "Le calcul libre apprend le passé par cœur", { kicker: "La répartition qui rapporte le plus, avec une seule exigence : jamais plus de 15 % de baisse sur 2006-2026" });
  const L = LIB.poids;
  const lab = { japon: "Actions Japon", indexees: "Obligations indexées", etats_longs: "États 2-10 ans", credit_court: "Crédit court", etats_courts: "Échelle AAA" };
  const ks = Object.keys(lab).filter((k) => L[k] > 0.005).sort((a, b) => L[a] - L[b]);
  s.addChart(pres.charts.BAR, [{ name: "Poids", labels: ks.map((k) => lab[k]), values: ks.map((k) => L[k] * 100) }],
    { ...chartBase("Le portefeuille du calcul libre"), x: M, y: 1.6, w: 6.3, h: 3.6, barDir: "bar", chartColors: [FAM.act], showValue: true, dataLabelFormatCode: '0" %"', dataLabelPosition: "outEnd", valAxisHidden: true, valGridLine: { style: "none" }, showLegend: false, barGapWidthPct: 35 });
  stat(s, M + 0.2, 5.45, 2.8, pct(LIB.rdt, 2), "de rendement espéré, sur le papier", FAM.idx, 34);
  stat(s, M + 3.3, 5.45, 2.8, pct(LIB.pire), "de pire baisse : la limite tout juste", INK, 34);
  card(s, 7.3, 1.6, 5.43, 5.2);
  s.addText("Pourquoi c'est inutilisable", { x: 7.55, y: 1.72, w: 5, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  const mj = S.moins_japon, ju = S.japon_egal_usa;
  para(s, 7.55, 2.2, 5.0, 4.5, bullets([
    `**87 % sur deux supports** : si l'un se comporte autrement qu'en 2006-2026, rien ne compense`,
    `Le Japon n'est pas gardé pour son rendement : ramené à ${pct(mj.variante.rendement, 2)}, il reste à ${pct(mj.poids.japon * 100, 0)}. Il l'est pour sa **tenue en crise** (le yen refuge)`,
    "Les indexées : leur 2008 est **flatté par le remplaçant**",
    `Les 10 M€ ignorés : **${pct(L.etats_courts * 100, 0)}** seulement en AAA`,
    "L'Europe à zéro, alors que c'est la poche **construite titre par titre**",
  ]), 14.5, { paraSpaceAfter: 12 });
  s.addNotes(`On laisse d'abord le calcul seul, avec une seule exigence : jamais plus de 15 % de baisse sur les vingt ans. Il propose 55 % d'obligations indexées et 32 % d'actions japonaises, pour ${pct(LIB.rdt, 2)} sur le papier. Ce n'est pas une proposition : c'est pour montrer ce que fait un optimiseur livré à lui-même. On a vérifié pourquoi il choisit le Japon : pas pour son rendement, car même en le baissant il le garde ; c'est parce que le Japon, grâce au yen, a bien tenu dans ces quatre crises précises. Rien ne garantit que le yen jouera ce rôle la prochaine fois : en 2022, il a perdu 8 % contre l'euro. Le calcul a appris le passé par cœur. D'où des règles.`);
}

{
  const s = base(4, "Quatre règles, chacune chiffrée", { kicker: "On ajoute les règles une à une ; chaque ligne garde les précédentes" });
  const ord = ["libre", "r1_aaa", "r2_cle", "r3_plafonds", "r4_marge"];
  const regle = { libre: "Calcul libre (limite de 15 % seule)", r1_aaa: "+ Au moins 10 % sur l'échelle AAA", r2_cle: "+ Actions 40 / 35 / 10 / 15", r3_plafonds: "+ Plafonds (indexées 15 %, or 10 %…)", r4_marge: "+ Marge : pire baisse visée 14 %" };
  const why = { libre: "—", r1_aaa: "Les 10 M€ à décaisser", r2_cle: "Pas de pari sur le yen", r3_plafonds: "Pas de concentration", r4_marge: "Remplaçants flatteurs" };
  let prev = null;
  const rows = [["Règle", "Pourquoi", "Rendement", "Coût"]];
  ord.forEach((n) => { rows.push([regle[n], why[n], pct(S[n].rdt, 2), prev === null ? "—" : fr(S[n].rdt - prev, 2) + " pt"]); prev = S[n].rdt; });
  table(s, rows, M, 1.6, 7.0, [3.15, 1.95, 1.0, 0.9], { fontSize: 12, rowH: 0.55, bold1: true });
  const fams = { "Actions": act, "Emprunts d'État": ["etats_courts", "etats_longs"], "Indexées": ["indexees"], "Or et autres": ["or", "credit_court", "matieres"] };
  const labels = ["Libre", "+ AAA", "+ clé", "+ plafonds", "+ marge"];
  s.addChart(pres.charts.BAR, Object.entries(fams).map(([f, ks]) => ({ name: f, labels, values: ord.map((n) => ks.reduce((a, k) => a + (S[n].poids[k] || 0), 0) * 100) })),
    { ...chartBase("La répartition, règle après règle"), x: 7.85, y: 1.5, w: 4.9, h: 4.1, barDir: "bar", barGrouping: "percentStacked", chartColors: [FAM.act, FAM.eta, FAM.idx, FAM.or], showValue: true, dataLabelFormatCode: '[<4]"";0" %"', dataLabelPosition: "ctr", dataLabelColor: WHITE, dataLabelFontSize: 9, valAxisHidden: true, valGridLine: { style: "none" }, catAxisOrientation: "maxMin", showLegend: true, legendPos: "b", legendFontSize: 10, barGapWidthPct: 35 });
  callout(s, M, 5.0, 7.0, 1.8, `La plus chère : **la clé des actions** (${fr(S.r2_cle.rdt - S.r1_aaa.rdt, 2)} pt). Coût total des règles : **${fr(R4.rdt - LIB.rdt, 2)} pt** — le prix pour ne pas miser sur un passé appris par cœur.`, INK, 14);
  // Ce paragraphe dit ce que le calcul REFUSE de prendre — c'est là que
  // l'or a sa place : son plafond de 10 % n'est pas saturé, et la question
  // « pourquoi si peu d'or ? » se pose à chaque soutenance.
  para(s, 7.85, 5.68, 4.9, 1.25, rich(`Crédit et matières premières restent **à zéro** : le crédit rapporte moins que les États, les matières premières baissent avec les actions. **L'or s'arrête à ${pct(W4.or * 100, 1)}** alors que son plafond est à ${pct(D.plafonds.or, 0)} : personne ne l'a fixé à ce niveau, c'est tout ce que le calcul en veut.`), 11);
  s.addNotes(`On reprend le calcul et on ajoute les règles une par une, en chiffrant ce que chacune coûte. Réserver les 10 millions en AAA ne coûte presque rien. Imposer la répartition des actions, Europe 40, États-Unis 35, Japon 10, émergents 15, est la règle la plus chère : ${fr(S.r2_cle.rdt - S.r1_aaa.rdt, 2)} point, c'est le prix du renoncement au pari sur le yen. Les plafonds évitent la concentration ; résultat intéressant, les actions remontent, parce que les États à 2-10 ans amortissaient mieux 2020 que les indexées. Enfin une marge : viser 14 % au lieu de 15, parce que certains remplaçants flattent 2008. Au total, les règles coûtent ${fr(LIB.rdt - R4.rdt, 2)} point de rendement espéré : c'est le prix d'un portefeuille robuste. SI ON ME DEMANDE POURQUOI SI PEU D'OR : parce que personne n'a choisi ce chiffre. Le plafond autorise ${pct(D.plafonds.or, 0)} et le calcul n'en prend que ${pct(W4.or * 100, 1)} — le plafond n'est pas la contrainte qui mord. L'or a le plus faible rendement espéré du modèle, ${pct(rdtCls.or, 2)}, à peine au-dessus des ${pct(rdtCls.etats_longs, 2)} des emprunts d'État à 2-10 ans. On ne le détient donc pas pour ce qu'il rapporte mais pour sa tenue en crise. Les chiffres exacts, en euros et sur les fenêtres de crise du dossier : ${pct(D.perf_crises.or['2008'])} en 2008, ${pct(D.perf_crises.or['2011'])} en 2011, ${pct(D.perf_crises.or['2020'])} en 2020, ${pct(D.perf_crises.or['2022'])} en 2022 — c'est LE SEUL SUPPORT du portefeuille à finir positif sur les quatre, quand la poche d'actions perd ${pct(-D.perf_crises.poche_actions['2008'])} en 2008 et les emprunts d'État ${pct(-D.perf_crises.etats_longs['2022'])} en 2022. Si on me montre la table des pires baisses, où l'or affiche moins 25,7 % en 2008 : les deux sont vrais et ne mesurent pas la même chose — il a bien reculé de 25,7 % À L'INTÉRIEUR de la fenêtre avant de la finir en hausse. Le calcul en achète juste ce qu'il faut pour laisser la poche actions atteindre ${pct(partAct * 100, 1)} sous la limite ; au-delà, chaque euro d'or supplémentaire coûte du rendement sans acheter assez de protection. Et c'est stable : huit tirages aléatoires différents donnent tous ${pct(W4.or * 100, 1)}.`);
}

{
  const s = base(4, "Le portefeuille retenu", { kicker: "Rééquilibré chaque mois · les actions portent l'objectif, les obligations tiennent la limite" });
  const fams = [["Actions", partAct, FAM.act], ["Emprunts d'État", W4.etats_courts + W4.etats_longs, FAM.eta], ["Obligations indexées", W4.indexees, FAM.idx], ["Or", W4.or, FAM.or]];
  s.addChart(pres.charts.DOUGHNUT, [{ name: "Familles", labels: fams.map((f) => f[0]), values: fams.map((f) => f[1] * 100) }],
    { x: M, y: 1.5, w: 5.2, h: 5.35, holeSize: 55, chartColors: fams.map((f) => f[2]), showValue: false, showPercent: true, dataLabelColor: WHITE, dataLabelFontSize: 13, dataLabelFontBold: true, showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: BF, dataBorder: { pt: 2, color: WHITE } });
  stat(s, 6.3, 1.6, 3.1, pct(D.net, 2), "de rendement espéré NET de frais", FAM.idx, 40);
  stat(s, 9.6, 1.6, 3.1, "+" + fr(D.net - D.seuil, 2) + " pt", "au-dessus des 4 % d'inflation", INK, 40);
  stat(s, 6.3, 3.2, 3.1, pct(R4.pire), "de pire baisse depuis le plus haut (2008 et 2020)", NEG, 40);
  stat(s, 9.6, 3.2, 3.1, pct(contribAct / contrib * 100, 0), `du rendement vient des actions, qui ne font que ${pct(partAct * 100, 0)} du patrimoine`, FAM.act, 40);
  callout(s, 6.3, 4.95, 6.43, 1.85, `Les deux exigences du client sont tenues : **${pct(D.net, 2)} nets espérés** contre 4 % à battre, et **jamais plus de 14 % de baisse** dans les crises des vingt dernières années.`, INK, 15);
  s.addNotes(`Voici le portefeuille retenu : environ ${pct(partAct * 100, 0)} d'actions, ${pct((W4.etats_courts + W4.etats_longs) * 100, 0)} d'emprunts d'État, 15 % d'obligations indexées et ${pct(W4.or * 100, 0)} d'or. Un point de méthode important : le rendement brut est de ${pct(R4.rdt, 2)}, mais l'objectif du client est un objectif NET — ce qui doit battre l'inflation, c'est ce qui lui reste. On retire donc les frais des fonds, ${fr(D.frais_inst, 2)} point, et nos frais de mandat, ${fr(D.frais_mandat, 2)} point : il reste ${pct(D.net, 2)} nets, soit ${fr(D.net - D.seuil, 2)} point au-dessus de l'inflation de l'énoncé. Si on me demande la fiscalité : elle est hors périmètre de cet exercice et retirerait encore environ 0,30 point. Pire baisse sur vingt ans : ${pct(-R4.pire)}. Les actions ne font que 30 % du patrimoine mais apportent près de la moitié du rendement ; les obligations tiennent la limite de perte. Le petit ${pct(W4.or * 100, 1)} d'or n'est pas un arrondi de confort : c'est un résidu de calcul, détaillé à la slide précédente.`);
}

{
  const s = base(4, "Le portefeuille en millions d'euros", { kicker: "100 M€, support par support", source: `Frais des fonds : ${fr(D.frais_total / 1e3, 0)} k€ par an (${pct(D.frais_inst, 2)} du patrimoine) · frais de mandat ${pct(D.frais_mandat, 2)} · aucune ligne ne dépasse 1 % de son fonds` });
  const nm = { actions_europe: "Actions européennes", usa: "Actions américaines", japon: "Actions japonaises", emergents: "Actions émergentes", etats_courts: "Échelle AAA, 6 à 24 mois", etats_longs: "Échelle zone euro, 2 à 10 ans", indexees: "Obligations indexées", or: "Or" };
  const sup = { actions_europe: `${D.entonnoir.final} titres en direct`, etats_courts: "4 obligations en direct", etats_longs: "5 obligations en direct" };
  const fc = { actions_europe: FAM.act, usa: FAM.act, japon: FAM.act, emergents: FAM.act, etats_courts: FAM.eta, etats_longs: FAM.eta, indexees: FAM.idx, or: FAM.or };
  const rows = [["Ligne", "Support", "Montant", "Poids", "Rendement espéré"]];
  D.retenu_lignes.forEach(([k, , s_, w, r]) => rows.push([{ text: [{ text: "■  ", options: { color: fc[k] } }, { text: nm[k], options: { color: TEXT } }] }, sup[k] || s_, me(w * 1e8), pct(w * 100), pct(r, 2)]));
  rows.push([{ text: "Total", options: { bold: true } }, "", { text: "100,0 M€", options: { bold: true } }, "100 %", { text: pct(R4.rdt, 2), options: { bold: true } }]);
  table(s, rows, M, 1.55, 8.3, [3.0, 2.2, 1.05, 0.8, 1.25], { fontSize: 13, rowH: 0.47, alignRight: true });
  // pastilles de couleur des familles
  const par = W4.actions_europe * 1e8 / D.entonnoir.final;
  para(s, 9.25, 1.6, 3.5, 5.2, bullets([
    `**${D.entonnoir.final} actions européennes** à ${me(par, 2)} chacune`,
    `**Échelle AAA** : ${me(W4.etats_courts * 1e8)} investis, qui rendront les 10 M€ avec une petite réserve`,
    `**Échelle 2-10 ans** : 5 × ${me(W4.etats_longs * 1e8 / 5, 2)}`,
    "**Fonds** : XZMU, XZMJ, XZEM, IBCI, Xetra-Gold",
    `Réalisé 2006-2026 : **${pct(D.realise, 2)} par an** (dix ans de taux négatifs inclus)`,
    `Rendement espéré **net de frais : ${pct(D.net, 2)}**`,
  ]), 13, { paraSpaceAfter: 9 });
  s.addNotes(`Concrètement, en millions d'euros. Environ 12 millions sur les ${D.entonnoir.final} actions européennes, à ${me(par, 0)} chacune ; 10 millions sur l'échelle AAA, qui rendront un peu plus que les 10 millions à décaisser ; 41 millions sur l'échelle d'emprunts d'État de 2 à 10 ans ; 15 millions en obligations indexées ; le reste en fonds d'actions américaines, japonaises et émergentes, et 3 millions en or — la seule ligne détenue pour sa tenue en crise et non pour son rendement. Les frais des fonds représentent environ 47 000 euros par an. Sur 2006-2026, ce portefeuille aurait rapporté 4,5 % par an ; ce n'est pas comparable au rendement espéré, parce que le passé comptait dix ans de taux négatifs alors que l'avenir part de taux autour de 3 %.`);
}

// ================================================================ SECTION 5
dark("Backtests", "Le portefeuille rejoué de 2006 à aujourd'hui : combien de temps sous l'eau, et à quoi ressemble une mauvaise année", { num: "5" })
  .addNotes("Dernière étape : rejouer le portefeuille sur vingt ans.");

{
  const s = base(5, `100 M€ en 2006 : ${fr(BT.final, 0)} M€ aujourd'hui`, { kicker: "Le portefeuille retenu, rééquilibré chaque mois, d'octobre 2006 à septembre 2026", source: `Séries de l'étape 4 · la limite de −14 % a été imposée sur ces mêmes données : sa tenue est acquise d'avance · inflation zone euro constatée : FRED, IPCH, ${pct(D.inflation.cumul, 1)} cumulés sur la période` });
  const ser = BT.serie;
  s.addChart(pres.charts.LINE, [{ name: "Valeur (M€)", labels: ser.dates.map((d) => d.slice(0, 4)), values: ser.valeur }],
    { ...chartBase("Valeur du portefeuille, en M€"), x: M, y: 1.55, w: 8.3, h: 5.3, chartColors: [FAM.act], lineSize: 2, lineDataSymbol: "none", catAxisLabelFrequency: 24, valAxisMinVal: 80, valAxisLabelFormatCode: "0", showLegend: false });
  stat(s, 9.2, 1.7, 3.5, pct(BT.cagr, 2), "par an sur vingt ans", FAM.idx, 38);
  stat(s, 9.2, 3.1, 3.5, "+" + fr(BT.reel, 2) + " pt", `par an AU-DELÀ de l'inflation, qui a fait ${pct(D.inflation.annuel, 2)} sur la période`, FAM.act, 38);
  stat(s, 9.2, 4.6, 3.5, pct(BT.pire), "de pire baisse (2008 et 2020)", NEG, 38);
  callout(s, 9.2, 6.0, 3.53, 0.85, "Ce rejeu ne **prouve pas** la limite.", INK, 13.5);
  s.addNotes(`100 millions investis en octobre 2006 en vaudraient ${fr(BT.final, 0)} aujourd'hui, soit ${pct(BT.cagr, 2)} par an. Ce chiffre-là, il ne faut pas le comparer aux 4 % de l'énoncé : ces 4 % décrivent un monde à 4 % d'inflation, or la zone euro en a connu ${pct(D.inflation.annuel, 2)} par an sur cette période, ${pct(D.inflation.cumul, 1)} cumulés. Jugé contre l'inflation réellement constatée, le portefeuille a donc dégagé ${fr(BT.reel, 2)} point de rendement réel par an. L'objectif du client a été tenu, et largement. Je dois être honnête en revanche sur ce que ce rejeu prouve : rien sur la limite de perte, puisqu'on a construit le portefeuille pour qu'il ne perde jamais plus de 14 % sur ces mêmes données. Ce que le rejeu apporte, c'est ce que le calcul n'a pas regardé : combien de temps le client reste sous son plus haut, et à quoi ressemble une mauvaise année.`);
}

{
  const s = base(5, "La plus longue baisse n'est pas la plus profonde", { kicker: "Chaque baisse de plus de 5 % depuis le plus haut" });
  const ser = BT.serie;
  s.addChart(pres.charts.AREA, [{ name: "Écart au plus haut", labels: ser.dates.map((d) => d.slice(0, 4)), values: ser.dd }],
    { ...chartBase("Écart au plus haut (%), limite du mandat −15 %"), x: M, y: 1.5, w: 6.4, h: 3.0, chartColors: [FAM.act], chartColorsOpacity: 35, catAxisLabelFrequency: 36, valAxisMinVal: -16, valAxisMaxVal: 0, valAxisLabelFormatCode: '0" %"', showLegend: false });
  const mo = (x) => (x === null ? "—" : fr(x, 0) + " mois");
  const rows = [["Plus haut", "Point bas", "Baisse", "Retour", "Sous l'eau"], ...BT.episodes.map((e) => [e[0], e[1], pct(e[2]), e[4] || "pas encore", mo(e[5])])];
  table(s, rows, 7.3, 1.55, 5.43, [1.05, 1.05, 1.0, 1.15, 1.18], { fontSize: 11.5, rowH: 0.4, alignRight: true });
  stat(s, M, 4.8, 2.9, pct(BT.sous, 0), "du temps à plus de 1 % sous son plus haut", INK, 32);
  stat(s, M + 3.1, 4.8, 2.9, pct(BT.s5, 0), "à plus de 5 %", FAM.eta, 32);
  stat(s, M + 6.2, 4.8, 2.9, pct(BT.s10, 0), "à plus de 10 %", NEG, 32);
  para(s, 9.9, 4.8, 2.83, 2.0, rich(`**2022 : ${mo(ep22[5])} sous l'eau**, pour une baisse moindre que 2008 : les obligations ont baissé avec les actions.`), 12.5);
  s.addNotes(`Les deux baisses les plus profondes, 2008 et 2020, font la même taille, 14 %, mais pas la même durée : ${mo(ep20[5])} pour se remettre du krach de 2020, ${mo(ep08[5])} pour 2008. La plus longue, c'est 2022 : ${mo(ep22[5])} sous le plus haut, parce que les obligations, qui font les deux tiers du portefeuille, ont baissé avec les actions puis ont mis deux ans à se reconstituer. Pour le client, cela veut dire : la moitié du temps, son patrimoine est un peu sous son meilleur niveau ; une fois sur six, à plus de 5 % ; les pertes proches de la limite sont rares et brèves. C'est ce qu'il faut lui dire avant, pas après.`);
}

{
  const s = base(5, "À quoi ressemble une mauvaise année", { kicker: `Résultat sur douze mois glissants, à chaque fin de mois depuis octobre 2007 (${BT.n} années glissantes)`, source: "VaR : perte dépassée une année sur vingt · CVaR : perte moyenne de ces années-là · chiffres descriptifs, pas une prévision" });
  const hst = BT.hist;
  s.addChart(pres.charts.BAR, [{ name: "Fins de mois", labels: hst.map((h) => String(h[0])), values: hst.map((h) => h[1]) }],
    { ...chartBase("Nombre de fins de mois, par rendement sur un an (%)"), x: M, y: 1.55, w: 7.6, h: 5.3, barDir: "col", chartColors: [FAM.act], barGapWidthPct: 15, showLegend: false, catAxisLabelFrequency: 2, valAxisLabelFormatCode: "0" });
  stat(s, 8.6, 1.6, 2.0, pct(BT.var95[0]), "VaR 95 % à un an", FAM.eta, 30);
  stat(s, 10.7, 1.6, 2.0, pct(BT.var95[1]), "CVaR 95 %", NEG, 30);
  stat(s, 8.6, 3.0, 2.0, pct(BT.rmin), "pire année", NEG, 30);
  stat(s, 10.7, 3.0, 2.0, pct(BT.sous_infl, 0), "des années n'ont pas battu l'inflation", INK, 30);
  callout(s, 8.6, 4.55, 4.13, 2.25, `Sur un an, jamais plus de **${pct(-BT.rmin)}** de perte, alors que la pire baisse atteint **14 %** : les baisses s'étalent sur plus d'un an. Et préserver le pouvoir d'achat est **un objectif de moyenne longue, pas une garantie annuelle.**`, INK, 13.5);
  s.addNotes(`Deuxième question : une mauvaise année. Une année sur vingt, le portefeuille a perdu plus de ${pct(-BT.var95[0])} ; ces années-là, ${pct(-BT.var95[1])} en moyenne. La pire année : ${pct(BT.rmin)}. Remarquez l'écart avec la pire baisse de 14 % : les baisses s'accumulent sur plus d'un an, en 2008 comme en 2022. C'est pour cela que nous avons mesuré la limite depuis le plus haut : une limite sur un an aurait laissé passer ces baisses. Un chiffre que je préfère donner moi-même plutôt qu'on me le sorte : ${pct(BT.sous_infl, 0)} des années glissantes n'ont pas battu l'inflation de leur époque. C'est normal, et c'est important à dire : préserver le pouvoir d'achat est un objectif de moyenne longue, aucun portefeuille tenu à 15 % de perte maximum ne peut le garantir chaque année. Précaution enfin : vingt ans ne contiennent qu'une vingtaine d'années indépendantes ; ces chiffres reposent sur une poignée d'épisodes.`);
}

// ================================================================ Clôture
{
  const s = dark("Notre proposition", null);
  const items = [[pct(D.net, 2), "de rendement espéré net de frais"], [pct(R4.pire), "de pire baisse sur vingt ans"], [pct(partAct * 100, 0), `d'actions, dont ${D.entonnoir.final} titres en direct`], ["10 M€", "sécurisés en AAA, à taux garantis"]];
  items.forEach(([v, l], i) => {
    const x = M + i * 3.1;
    s.addText(v, { x, y: 3.5, w: 2.95, h: 0.9, fontFace: HF, fontSize: 40, bold: true, color: "F5C969", margin: 0, isTextBox: true });
    s.addText(l, { x, y: 4.45, w: 2.8, h: 0.8, fontFace: BF, fontSize: 15, color: WHITE, margin: 0, valign: "top", isTextBox: true });
  });
  s.addText("Un portefeuille diversifié, sans pari sur une zone, qui préserve le pouvoir d'achat en respectant la limite de perte dans toutes les crises récentes.", { x: M, y: 5.7, w: W - 2 * M, h: 0.9, fontFace: BF, fontSize: 17, italic: true, color: "CADCFC", margin: 0, isTextBox: true });
  s.addNotes(`Pour conclure. Nous proposons à M. Lauren un portefeuille qui rapporte ${pct(D.net, 2)} espérés par an NETS de tous frais, soit ${fr(D.net - D.seuil, 2)} point au-dessus des 4 % d'inflation, et qui n'aurait jamais perdu plus de 14 % dans les crises des vingt dernières années. Environ 30 % d'actions réparties sur quatre zones, sans pari sur l'une d'elles ; une large poche d'emprunts d'État et d'indexées ; un peu d'or. Les 10 millions dont il a besoin sont sécurisés, à taux garantis.`);
}

{
  const s = base(0, "Ce que le client doit savoir, et ce que nous lui demanderons", { source: "Toute la démarche, avec les chiffres et leurs sources, est consultable dans l'application : mandat-lauren.streamlit.app" });
  card(s, M, 1.4, 6.0, 5.4);
  s.addText("Les limites, dites franchement", { x: M + 0.25, y: 1.55, w: 5.5, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M + 0.25, 2.05, 5.5, 4.6, bullets([
    "La limite de 15 % tient **sur le passé** ; la prochaine crise peut être différente",
    "Avant 2018, plusieurs supports sont mesurés par des **remplaçants**, parfois flatteurs",
    "Les rendements espérés sont des **moyennes sur dix ans**, pas des promesses",
    "Une baisse peut durer **plus de deux ans** (2022)",
  ]), 17, { paraSpaceAfter: 18 });
  card(s, 6.83, 1.4, 5.9, 5.4);
  s.addText("Les questions pour M. Lauren", { x: 7.08, y: 1.55, w: 5.4, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 7.08, 2.05, 5.4, 4.6, bullets([
    "Les **dates** exactes des 10 M€",
    "Les 15 % : une limite **absolue**, ou acceptable si très rare ?",
    "La **crypto** : un placement, ou un geste envers son fils ?",
    "Souhaite-t-il être traité en **client professionnel** (univers plus large) ?",
  ]), 17, { paraSpaceAfter: 18 });
  s.addNotes("Deux choses pour terminer. D'abord les limites, que nous dirions franchement au client : la limite de perte tient sur les crises passées, pas forcément sur la prochaine ; certaines mesures anciennes reposent sur des remplaçants ; les rendements espérés sont des moyennes, pas des promesses ; et une baisse peut durer plus de deux ans. Ensuite, les questions que nous lui poserions, car nos hypothèses de travail devront être confirmées. Merci ; je suis à votre disposition pour vos questions, et je peux ouvrir l'application pour montrer n'importe quel détail.");
}

// ================================================================ Annexes
{
  const s = base(0, "Annexe A — Comment on estime le rendement d'une action", { kicker: "Pour les questions techniques" });
  card(s, M, 1.55, 6.0, 1.9);
  s.addText("① Par les bénéfices", { x: M + 0.25, y: 1.7, w: 5.5, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M + 0.25, 2.15, 5.5, 1.7, rich("Rendement réel ≈ **1 / PER**. À un PER de 20, on achète 5 % de bénéfices par an ; sur longue période, c'est une bonne estimation du rendement au-delà de l'inflation."), 13.5);
  card(s, 6.83, 1.55, 5.9, 1.9);
  s.addText("② Par le dividende et la croissance", { x: 7.08, y: 1.7, w: 5.4, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 7.08, 2.15, 5.4, 1.7, rich(`Rendement réel ≈ **dividende + croissance réelle des bénéfices** (${pct(D.croissance)} par an, S&P 500 depuis 1900).`), 13.5);
  callout(s, M, 3.75, W - 2 * M, 1.1, "Rendement espéré = **moyenne de ① et ②  + 4 % d'inflation** (les entreprises répercutent la hausse des prix dans leurs bénéfices).", INK, 15);
  para(s, M, 5.1, W - 2 * M, 1.6, bullets([
    "**Fourchette** : écart entre sources de PER (iShares / Yahoo) et entre périodes de mesure de la croissance",
    "**Contrôle** : à moins d'un point des hypothèses J.P. Morgan une fois leur inflation (2 %) corrigée",
  ]), 15, { paraSpaceAfter: 10 });
  s.addNotes("Annexe, pour les questions techniques sur la méthode d'estimation du rendement des actions.");
}

{
  const s = base(0, "Annexe B — Données, remplaçants et contrôles", { kicker: "Pour les questions techniques" });
  table(s, [
    ["Sujet", "Ce qu'on a fait", "Limite"],
    ["Historique 2006-2018", "Vrai support dès qu'il existe, fonds plus ancien sur le même indice avant, converti en euros", "Indexées : remplaçant classique en 2008 (flatteur)"],
    ["Emprunts d'État", "Obligations recalculées chaque jour sur la courbe BCE (Svensson) depuis 2006", "Aucune"],
    ["Crédit avant 2016", "Prime reconstituée depuis les écarts US (sensibilité mesurée sur le vrai fonds)", "Lien faible : ligne la moins bien mesurée"],
    ["Optimisation", "Pire baisse mesurée sur le chemin réel, rééquilibrage mensuel, 16 départs", "Apprend le passé : d'où les règles"],
    ["Libellés des fonds", "Nom Yahoo et nom justETF (par ISIN) doivent concorder", "Neuf erreurs trouvées et corrigées"],
    ["Prix aberrants", "Allers-retours isolés retirés ; baisses de crédit sur cours du vendredi", "—"],
  ], M, 1.6, W - 2 * M, [2.4, 5.8, 3.93], { fontSize: 12.5, rowH: 0.7, bold1: true });
  s.addNotes("Annexe sur les données : comment l'historique a été reconstitué, et les contrôles appliqués.");
}
{
  // Annexe C — la notation des actions, racontée avant d'être formulée.
  // Reprise de docs/modeles/04 : on dit ce que le chiffre VEUT DIRE, et on
  // ne pose une formule que là où elle apprend quelque chose (1/PER).
  const s = base(0, `Annexe C — Comment 600 actions deviennent ${D.entonnoir.final}`, { kicker: "Pour les questions techniques" });
  callout(s, M, 1.5, W - 2 * M, 0.95, "Le problème : on veut mélanger un PER, une marge, une volatilité et une croissance. **Trois obstacles — les unités diffèrent, les sens s'opposent, et le niveau « normal » dépend du secteur.**", INK, 14.5);

  const E = [
    ["① Tout mettre dans le même sens", "On remplace chaque indicateur par une version où **plus haut = mieux**. Le PER devient **1 / PER**, soit le rendement des bénéfices : à un PER de 20 on achète 5 % par an. Ce n'est pas cosmétique — passer d'un PER de 10 à 20 coûte 5 points de rendement, de 30 à 40 seulement 0,8. Sur le PER brut, les deux écarts valent « 10 »."],
    ["② Comparer chacune à son secteur", "On remplace la valeur par **de combien elle s'écarte de la moyenne de son secteur**, mesuré en nombre d'écarts-types. Une action à +1 est meilleure que 84 % de ses pairs, à 0 elle est dans la moyenne. Tout devient comparable, donc moyennable."],
    ["③ Puis seulement, la moyenne", "Cinq piliers à poids égaux — valorisation, croissance, dynamique, qualité, résistance. Aucun n'a de raison **mesurée** d'être privilégié : les pondérer demanderait d'estimer des primes de facteur, ce qui est un autre métier."],
  ];
  E.forEach(([t, txt], i) => {
    const x = M + i * 4.25;
    card(s, x, 2.65, 4.0, 2.6);
    s.addText(t, { x: x + 0.22, y: 2.8, w: 3.56, h: 0.6, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
    para(s, x + 0.22, 3.42, 3.56, 1.7, rich(txt), 12.8);
  });

  callout(s, M, 5.5, W - 2 * M, 1.1, "**Pourquoi « de son secteur » et pas « du marché entier »** : sinon les banques et l'énergie, structurellement bon marché, rafleraient toutes les bonnes notes de valorisation. On construirait **un pari sectoriel déguisé en sélection de titres**.", CARD, 14);
  s.addNotes("Annexe technique sur la notation. Le point à retenir si on me pose la question : ce n'est pas un modèle à facteurs. On n'explique pas un rendement, on classe des titres les uns par rapport aux autres — c'est du stock screening, et ça ne prétend pas prédire. Les trois étapes règlent trois problèmes concrets : mettre tous les indicateurs dans le sens « plus haut = mieux », les ramener sur une échelle commune en les comparant à leur propre secteur, et seulement alors en faire une moyenne. Le choix du secteur plutôt que du marché entier est le plus important : sans lui, on sélectionnerait des secteurs en croyant sélectionner des sociétés. Deux détails si on creuse : les données aberrantes sont supprimées et non corrigées — Yahoo confond les pence et les livres sur certaines valeurs de Londres, ce qui donnait des PER multipliés par cent — et pour les banques on retire l'endettement, le flux de trésorerie et la marge, parce que la dette d'une banque est sa matière première, pas un fardeau.");
}

{
  // Annexe D — Svensson. Consigne d'Allan : raconter ce que ça veut dire
  // AVANT toute formule. Il n'y en a donc aucune sur cette slide.
  const s = base(0, "Annexe D — La courbe des taux, en six nombres", { kicker: "Pour les questions techniques · modèle de Svensson, publié chaque jour par la BCE" });
  callout(s, M, 1.5, W - 2 * M, 0.95, "Le problème : les obligations qui existent ont des échéances **en désordre**. Une à 4 ans et 2 mois, une à 7 ans et 9 mois, rien à 6 ans. Si j'ai besoin du taux à 6 ans, personne ne me le donne.", INK, 14.5);

  card(s, M, 2.65, 6.0, 2.5);
  s.addText("Deux façons de combler les trous", { x: M + 0.25, y: 2.8, w: 5.5, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M + 0.25, 3.28, 5.5, 1.75, bullets([
    "**Relier les points.** Simple, mais on recopie le bruit : une obligation mal cotée ce jour-là crée une bosse qui n'existe pas",
    "**Décrire la forme** par quelques nombres, en acceptant de ne pas passer exactement par chaque point. C'est Svensson",
  ]), 12.5, { paraSpaceAfter: 8 });

  card(s, 6.83, 2.65, 5.9, 2.5);
  s.addText("Une courbe a toujours la même allure", { x: 7.08, y: 2.8, w: 5.4, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 7.08, 3.28, 5.4, 1.75, bullets([
    "**Un niveau** : globalement haute ou basse",
    "**Une pente** : le court rapporte moins que le long (normal), ou l'inverse (signal de récession)",
    "**Une ou deux bosses** : banques centrales sur le court, assureurs sur le très long",
  ]), 12.5, { paraSpaceAfter: 6 });

  card(s, M, 5.35, 6.0, 1.5);
  s.addText("Les six nombres", { x: M + 0.25, y: 5.45, w: 5.5, h: 0.35, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M + 0.25, 5.82, 5.5, 0.95, rich("**Quatre boutons de taille, deux boutons de position.** Le niveau, la pente, la taille des deux bosses — et où chaque bosse se situe. C'est tout."), 13);

  callout(s, 6.83, 5.35, 5.9, 1.5, "**L'analogie.** Décrire un visage : lister la couleur de chaque pixel, ou dire « ovale, yeux écartés, nez droit ». La seconde description est plus courte, **résiste au bruit**, et permet de dessiner ce qu'on n'a pas vu.", CARD, 13);
  s.addNotes("Annexe technique sur la courbe des taux. Si on me demande d'où viennent les taux que j'utilise pour valoriser les obligations : ils viennent de la courbe zéro-coupon publiée chaque jour par la Banque centrale européenne, calculée avec le modèle de Svensson. L'idée tient en une phrase : plutôt que de relier les points entre les obligations qui existent — ce qui recopie le bruit de cotation — on décrit la forme de la courbe par six nombres. Une courbe de taux a toujours la même allure : un niveau, une pente, une ou deux bosses. Quatre boutons règlent les tailles, deux règlent les positions. C'est comme décrire un visage : on peut lister chaque pixel, ou dire « ovale, yeux écartés, nez droit ». La seconde description est plus robuste, et surtout elle permet de donner le taux à six ans même si aucune obligation ne tombe exactement à six ans. Deux lectures immédiates pour un gérant : le niveau seul donne le très long terme, et le niveau plus la pente donnent le taux au jour le jour.");
}
{
  // Annexe E — pourquoi pas Markowitz. C'est LA question d'un jury de
  // finance, et elle n'était traitée nulle part dans le deck. Reprise de
  // docs/modeles/05 : l'expérience du paquet de cartes, qui se fait en
  // séance et ne demande aucune formule.
  const s = base(0, "Annexe E — Pourquoi pas Markowitz", { kicker: "Pour les questions techniques · la question qui sera posée" });
  callout(s, M, 1.5, W - 2 * M, 0.95, "M. Lauren n'a pas dit « je veux une volatilité de 6 % ». Il a dit **« je ne veux jamais perdre plus de 15 % »**. Ce sont deux objets différents, et le second ne se déduit pas du premier.", INK, 14.5);

  card(s, M, 2.65, 6.0, 2.6);
  s.addText("L'expérience du paquet de cartes", { x: M + 0.25, y: 2.8, w: 5.5, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M + 0.25, 3.28, 5.5, 1.8, bullets([
    "Prends les rendements mensuels du portefeuille sur vingt ans, et **mélange les mois au hasard**",
    "**La volatilité ne bouge pas d'un iota** : elle ne regarde que la dispersion des rendements",
    "**La pire baisse change du tout au tout** : mauvais mois groupés, on creuse 40 % ; éparpillés, jamais plus de 10 %",
  ]), 12.5, { paraSpaceAfter: 7 });

  card(s, 6.83, 2.65, 5.9, 2.6);
  s.addText("Ce qu'on en tire", { x: 7.08, y: 2.8, w: 5.4, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 7.08, 3.28, 5.4, 1.8, rich("**La volatilité ignore l'ordre. La pire baisse ne dépend que de l'ordre.**\n\nIl n'existe donc aucune formule reliant la matrice de covariance à la perte maximale — sauf en supposant les rendements indépendants et gaussiens, ce qui est faux précisément dans les crises, c'est-à-dire là où ça compte.\n\nOn mesure donc directement sur le chemin : chaque répartition candidate est rejouée jour par jour, rééquilibrée chaque mois."), 12.5);

  callout(s, M, 5.45, 6.0, 1.4, "**Le prix, et il est assumé.** La contrainte est évaluée sur **une seule trajectoire**, celle qui a eu lieu. C'est du surapprentissage au sens plein — d'où le résultat brut rejeté, puis les règles chiffrées une par une.", CARD, 12.5);
  callout(s, 6.83, 5.45, 5.9, 1.4, "**Et Black-Litterman ?** Écarté pour une autre raison : les opinions sont **déjà** dans les rendements espérés, qui viennent des valorisations. Les réinjecter reviendrait à les compter deux fois.", CARD, 12.5);
  s.addNotes("Annexe technique, et c'est la question qu'on me posera en premier. La théorie classique dit : matrice de covariance, minimisation de la variance, frontière efficiente. Je ne l'ai pas fait, pour une raison simple : la contrainte du client n'est pas une volatilité. Il n'a pas demandé une volatilité de six pour cent, il a demandé de ne jamais perdre plus de quinze. L'expérience qui tranche tient en une phrase : prenez les rendements mensuels, mélangez les mois comme un paquet de cartes. La volatilité est identique — elle ne regarde que la dispersion. La pire baisse, elle, change complètement : si les mauvais mois se suivent vous creusez quarante pour cent, s'ils sont éparpillés vous ne descendez jamais sous dix. La volatilité ignore l'ordre, le drawdown ne dépend que de l'ordre. Il n'y a donc pas de formule qui relie la covariance à la perte maximale, sauf sous hypothèse d'indépendance et de normalité — hypothèse fausse exactement dans les crises. Optimiser la variance en espérant que la perte suive aurait été un raccourci non vérifié. Je dois dire le prix de mon choix : la contrainte est mesurée sur une seule trajectoire, celle qui a eu lieu, donc c'est du surapprentissage. C'est précisément pour ça que le résultat brut du calcul libre est rejeté et que j'ajoute des règles dont je chiffre le coût une par une. Sur Black-Litterman enfin : écarté parce que mes opinions sont déjà dans les rendements espérés, qui sortent des valorisations. Dire que l'Europe est moins chère donc rapportera plus, c'est déjà l'opinion. La réinjecter serait la compter deux fois.");
}

{
  // Annexe F — duration, sensibilité, convexité, portage et glissement.
  // Le deck cite des chiffres de sensibilité sans jamais les définir.
  const s = base(0, "Annexe F — Ce que « duration » veut dire", { kicker: "Pour les questions techniques · d'où viennent les chiffres de sensibilité du dossier" });
  const SVA = D.souverains, CR = D.credit, CFA = D.credit_fonds;

  const B = [
    ["La duration", `**Le délai moyen de récupération de mon argent.** Une obligation à 10 ans ne me rend pas tout dans 10 ans : elle verse des coupons avant. Avec de gros coupons, sa duration tombe vers 8 ans. Un zéro-coupon à 10 ans a une duration de 10 ans pile, puisque tout arrive à la fin.`],
    ["La sensibilité", `La duration, corrigée d'un petit facteur, et sa lecture est directe : **si tous les taux montent d'un point, le prix baisse d'environ autant de pour cent.** L'intuition : si je détiens du 3 % et que le marché paie 4 %, personne ne veut du mien à son prix — il baisse jusqu'à redevenir compétitif.`],
    ["La convexité", `La relation taux-prix n'est pas une droite, elle est courbée **dans le bon sens pour le détenteur** : quand les taux montent on perd un peu moins que prévu, quand ils baissent on gagne un peu plus. Positive pour toute obligation classique — c'est un actif gratuit.`],
  ];
  B.forEach(([t, txt], i) => {
    const x = M + i * 4.25;
    card(s, x, 1.5, 4.0, 2.4);
    s.addText(t, { x: x + 0.22, y: 1.62, w: 3.56, h: 0.4, fontFace: HF, fontSize: 15.5, bold: true, color: INK, margin: 0, isTextBox: true });
    para(s, x + 0.22, 2.08, 3.56, 1.7, rich(txt), 12.8);
  });

  callout(s, M, 4.1, W - 2 * M, 1.0, `**Ce que fait le code, et c'est mieux que l'approximation.** Au lieu d'estimer la perte par « sensibilité plus convexité », il **revalorise réellement** l'obligation avec la courbe décalée d'un point. Exact au lieu d'approché : l'échelle 2-10 ans perd **${pct(-SVA.choc_long)}**, le fonds de crédit (durée ${fr(CFA.duree)} an) bien moins.`, INK, 13.5);

  card(s, M, 5.35, W - 2 * M, 1.4);
  s.addText("D'où vient le rendement d'une année, si la courbe ne bouge pas", { x: M + 0.25, y: 5.48, w: 8, h: 0.35, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, M + 0.25, 5.88, 11.6, 0.8, rich("**Le portage** : j'encaisse le coupon, c'est évident. **Le glissement** : mon obligation à 10 ans devient une obligation à 9 ans, et sur une courbe montante le taux à 9 ans est plus bas — donc elle est valorisée plus cher. J'ai gagné sans que rien ne bouge, juste parce que le temps a passé."), 12.8);
  s.addNotes(`Annexe technique sur les mesures obligataires, pour les chiffres de sensibilité cités dans le dossier. La duration, c'est le délai moyen de récupération de l'argent : une obligation à dix ans verse des coupons avant l'échéance, donc elle me rend mon argent en moyenne plus tôt que dans dix ans. La sensibilité, c'est la duration corrigée d'un petit facteur, et elle se lit directement : si les taux montent d'un point, le prix baisse d'à peu près autant de pour cent. C'est de là que vient le chiffre du dossier — l'échelle deux-dix ans perdrait ${pct(-SVA.choc_long)} si les taux montaient d'un point. L'intuition est simple : si je détiens du trois pour cent et que le marché se met à payer quatre, personne ne veut du mien à son prix actuel, donc il baisse jusqu'à redevenir compétitif. La convexité est la bonne nouvelle : la relation n'est pas une droite mais une courbe, et elle est courbée en faveur du détenteur — on perd un peu moins que prévu quand les taux montent, on gagne un peu plus quand ils baissent. Un détail de méthode si on me le demande : je ne passe pas par l'approximation sensibilité plus convexité, je revalorise réellement l'obligation avec la courbe décalée d'un point, ce qui est exact plutôt qu'approché et évite de décrocher sur les longues maturités. Enfin, si la courbe ne bouge pas d'un an sur l'autre, je gagne quand même par deux canaux : le portage, c'est-à-dire le coupon, et le glissement — mon obligation à dix ans devient une neuf ans, valorisée avec un taux plus bas sur une courbe montante, donc son prix monte tout seul.`);
}

{
  // Annexes G, H, I — ajoutées le 2026-09-25. Elles portaient le registre
  // explicatif de l'application, qu'Allan a voulue factuelle : « tout ce qui
  // est explicatif tu peux me l'enlever et faire en sorte que ça soit dans
  // le deck dans les annexes ». G complète E, qui dit pourquoi PAS Markowitz
  // sans jamais dire ce que le calcul fait à la place.
  const s = base(0, "Annexe G — Comment le calcul cherche sa réponse", { kicker: "Pour les questions techniques · complète l'annexe E, qui dit pourquoi pas Markowitz" });
  callout(s, M, 1.5, W - 2 * M, 0.9, "**La question, en une phrase** : parmi tous les partages possibles des 100 M€, lequel rapporte le plus sans jamais avoir perdu plus que la limite ?", INK, 14.5);

  const T = [["Ce qu'on maximise", "Le rendement espéré du portefeuille : la moyenne des rendements de chaque support, pondérée par son poids"],
             ["Ce qu'on s'interdit", `Pour CHAQUE partage essayé, on rejoue les vingt ans : 100 M€ placés selon ces poids en octobre 2006, **remis à ces mêmes poids chaque mois**, valeur suivie semaine après semaine. La plus forte baisse depuis un sommet doit rester sous ${pct(D.limites.visee, 0)}`],
             ["Ce qui borne les poids", `Positifs, somme de 100 %, plancher de ${pct(D.limites.min_aaa, 0)} en AAA, clé actions 40/35/10/15, et les plafonds par support`]];
  let y = 2.6;
  T.forEach(([t, d]) => {
    card(s, M, y, W - 2 * M, 1.0);
    s.addText(t, { x: M + 0.25, y: y + 0.12, w: 3.0, h: 0.75, fontFace: HF, fontSize: 14, bold: true, color: INK, valign: "middle", margin: 0, isTextBox: true });
    para(s, M + 3.3, y + 0.12, W - 2 * M - 3.6, 0.78, rich(d), 12);
    y += 1.12;
  });
  callout(s, M, 6.0, W - 2 * M, 0.85, "**Pas de formule, donc on cherche.** La pire baisse est un minimum sur vingt ans de dates : déplacer un poids d'un dixième de point fait basculer la date qui la donne, et la contrainte saute au lieu de varier. Un solveur sous contraintes est relancé depuis **seize départs**, on garde le meilleur résultat admissible.", CARD, 12.5);
  s.addNotes("Annexe technique, la suite de l'annexe E. E dit pourquoi je n'ai pas fait de Markowitz ; celle-ci dit ce que je fais à la place. On maximise le rendement espéré du portefeuille, c'est-à-dire la moyenne des rendements de chaque support pondérée par son poids. On s'interdit de perdre plus que la limite, et c'est le point important : pour chaque partage essayé, le programme rejoue vingt ans d'histoire — il place cent millions selon ces poids en octobre 2006, les remet à ces mêmes poids chaque mois, suit la valeur semaine après semaine, et mesure la plus forte baisse depuis un sommet. Enfin les poids sont bornés : positifs, somme de cent pour cent, dix pour cent au moins sur l'échelle AAA pour les dix millions à décaisser, la clé actions, et les plafonds. Pourquoi aucune formule ne donne la réponse : la variance de Markowitz est lisse et convexe, elle a une solution fermée. La pire baisse est un minimum sur vingt ans de dates, et déplacer un poids d'un dixième de point peut faire basculer la date qui la donne — deux mille huit devient deux mille vingt, et la contrainte saute d'un coup au lieu de varier doucement. Aucune dérivée fiable. On cherche donc, avec un solveur sous contraintes relancé depuis seize points de départ, et on garde le meilleur résultat admissible. QUATRE PRÉCAUTIONS, si on me demande pourquoi seize et pas un. Premièrement les départs sont admissibles par construction : un tirage au hasard ignore les plafonds, il pose en moyenne quatorze pour cent par support quand les matières premières plafonnent à cinq, et trois tirages sur deux cents seulement respectaient les bornes. Deuxièmement il existe un point de repli certain, un portefeuille très obligataire dont on sait qu'il tient la limite — et le repli naturel, tout en États deux-dix ans, est lui-même inadmissible puisque cent pour cent de ce support perd quinze virgule trois pour cent ; le repli est donc sur l'échelle AAA, qui perd sept virgule un. Troisièmement seize départs, parce qu'avant correction un seul sur seize aboutissait et trois graines sur huit ne trouvaient rien : le résultat tenait à un départ heureux. Quatrièmement on vérifie la limite pour de bon, parce que le solveur l'accepte à cinq pour dix mille près, ce qui laissait passer un portefeuille à moins quatorze virgule zéro cinq pour une limite de moins quatorze. Huit tirages indépendants donnent le même portefeuille : c'est ce qui permet de dire que le résultat n'est pas un accident de départ.");
}

{
  const s = base(0, `Annexe H — Pourquoi seulement ${pct(W4.or * 100, 1)} d'or`, { kicker: "Pour les questions techniques · un poids que personne n'a choisi" });
  callout(s, M, 1.5, W - 2 * M, 0.9, `**Personne n'a choisi ce chiffre : c'est un résidu de calcul.** Le plafond autorise ${pct(D.plafonds.or, 0)} et le calcul n'en prend que ${pct(W4.or * 100, 1)} — **le plafond n'est donc pas la contrainte qui mord.**`, INK, 14.5);

  const P = D.perf_crises;
  const rows = [["Crise", "L'or", "La poche d'actions", "Emprunts d'État"],
    ...Object.keys(P.or).map((k) => [k, pct(P.or[k]), pct(P.poche_actions[k]), pct(P.etats_longs[k])])];
  table(s, rows, M, 2.6, 6.2, [1.4, 1.6, 1.7, 1.5], { fontSize: 11, rowH: 0.34, alignRight: true });
  para(s, M, 4.65, 6.2, 0.75, rich("Performance **sur** la fenêtre de crise, en euros. L'or est **le seul support du portefeuille à finir positif sur les quatre**."), 11.5);

  card(s, 6.95, 2.6, W - M - 6.95, 2.8);
  s.addText("Ce que le calcul arbitre", { x: 7.2, y: 2.72, w: 5.4, h: 0.38, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 7.2, 3.15, W - M - 7.45, 2.1, rich(`L'or a le **rendement espéré le plus faible du modèle**, ${pct(rdtCls.or, 2)}, à peine au-dessus des ${pct(rdtCls.etats_longs, 2)} des emprunts d'État à 2-10 ans.\n\nOn ne le détient donc pas pour ce qu'il rapporte mais pour sa tenue en crise : c'est de la protection **achetée avec du rendement**. Le calcul en prend juste ce qu'il faut pour que la poche d'actions atteigne ${pct(partAct * 100, 2)} sous la limite. Au-delà, chaque euro d'or coûte du rendement sans acheter assez de protection pour financer une action de plus.`), 12);
  callout(s, M, 5.6, W - 2 * M, 1.1, `**Attention à ne pas confondre avec la table des pires baisses**, où l'or affiche −25,7 % en 2008 : les deux sont vrais et ne mesurent pas la même chose. Il a bien reculé de 25,7 % **à l'intérieur** de la fenêtre avant de la finir en hausse. Résultat stable sur huit tirages.`, CARD, 12.5);
  s.addNotes(`Annexe technique sur l'or, et c'est une question qui revient systématiquement. La réponse tient en une phrase : personne n'a choisi ce chiffre. Le plafond autorise ${pct(D.plafonds.or, 0)} et le calcul n'en prend que ${pct(W4.or * 100, 1)}, ce qui veut dire que le plafond n'est pas la contrainte qui mord — si on le relevait, rien ne bougerait. L'or a le rendement espéré le plus faible du modèle, ${pct(rdtCls.or, 2)}, à peine au-dessus des emprunts d'État à deux-dix ans. On ne le détient donc pas pour ce qu'il rapporte mais pour sa tenue en crise, et le tableau de gauche le montre : sur les quatre fenêtres de crise du dossier, en euros, l'or est le seul support du portefeuille à finir positif, quand la poche d'actions perd trente-neuf pour cent en deux mille huit et les emprunts d'État huit pour cent en deux mille vingt-deux. C'est de la protection achetée avec du rendement, et le calcul en prend exactement ce qu'il faut pour que la poche d'actions puisse atteindre trente pour cent sous la limite de perte ; au-delà, chaque euro d'or supplémentaire coûte du rendement sans acheter assez de protection pour financer une action de plus. Si on me montre la table des pires baisses, où l'or affiche moins vingt-cinq virgule sept en deux mille huit : les deux chiffres sont vrais et ne mesurent pas la même chose. Il a reculé de vingt-cinq pour cent à l'intérieur de la fenêtre, avant de la finir en hausse. Et le résultat est stable : huit tirages aléatoires différents donnent tous le même poids.`);
}

{
  const s = base(0, "Annexe I — Où agit la lecture macro, et où elle n'agit pas", { kicker: "Pour les questions techniques · un portefeuille, un pari" });
  callout(s, M, 1.5, W - 2 * M, 0.9, "**La lecture macro ne choisit aucun poids.** Elle fixe les rendements espérés de chaque classe, et c'est le calcul de l'étape 4 qui les convertit en poids sous la limite de perte.", INK, 14.5);

  const R = [["Combien d'actions au total", "OUI", "Par les rendements espérés des quatre zones"],
             ["Quelle zone d'actions", "NON", "La clé 40 / 35 / 10 / 15 est fixée d'avance, pour que la vue de zone ne devienne pas un pari"],
             ["Quels secteurs", "NON", "La note de l'étape 3 compare chaque société à son propre secteur : elle est aveugle aux secteurs par construction"],
             ["Combien d'indexées", "OUI", `L'inflation de l'énoncé les porte à ${pct(rdtCls.indexees, 2)}, le meilleur rendement obligataire : le calcul sature leur plafond de 15 %`],
             ["Combien de crédit", "NON", `Zéro, mais par une mesure de MARCHÉ de l'étape 3 : ${pct(rdtCls.credit_court, 2)} défauts déduits, sous les ${pct(rdtCls.etats_longs, 2)} des États`]];
  table(s, [["Décision", "La macro tranche ?", "Par quel canal"], ...R], M, 2.6, W - 2 * M, [3.2, 1.9, 7.0], { fontSize: 10.5, rowH: 0.52 });
  callout(s, M, 6.0, W - 2 * M, 0.9, `**Et la contrainte qui commande n'est pas macro.** Sur dix bornes, deux mordent — le plancher de ${pct(D.limites.min_aaa, 0)} en AAA et le plafond de ${pct(D.plafonds.indexees, 0)} sur les indexées. Ce qui borne vraiment le portefeuille, c'est la **limite de perte**, atteinte à ${pct(R4.pire, 2)}.`, CARD, 12.5);
  s.addNotes(`Annexe technique sur le lien entre l'étape 2 et l'étape 4, parce que le dossier annonce que chaque étape nourrit la suivante et qu'il faut pouvoir dire par quel canal. La lecture macro ne choisit aucun poids : elle fixe les rendements espérés de chaque classe, et c'est le calcul qui les convertit en poids sous la limite de perte. La distinction n'est pas cosmétique, elle explique pourquoi une erreur de diagnostic macro ne déforme pas le portefeuille dans les mêmes proportions. Ce qu'elle tranche : combien d'actions au total, par les rendements espérés des quatre zones ; et combien d'obligations indexées, puisque l'inflation de l'énoncé les porte au meilleur rendement obligataire du tableau et que le calcul sature leur plafond de quinze pour cent. Ce qu'elle ne tranche pas : la zone d'actions, figée par la clé quarante trente-cinq dix quinze précisément pour que la vue de zone ne devienne pas un pari ; et le secteur, puisque la note de l'étape trois compare chaque société à son propre secteur et se trouve aveugle aux secteurs par construction. UNE FORMULATION QUE J'AI CORRIGÉE, si elle figure encore quelque part : le crédit à zéro n'est PAS une décision macro. C'est une mesure de marché de l'étape trois — trois virgule trente-neuf pour cent défauts déduits, contre trois virgule soixante-trois pour les emprunts d'État. Enfin, la contrainte qui commande tout le reste n'est pas macro non plus : sur dix bornes du problème, deux seulement mordent, le plancher AAA et le plafond des indexées. L'or s'arrête à trois virgule trois pour cent pour un plafond de dix. Ce qui borne vraiment le portefeuille, c'est la limite de perte, atteinte exactement à la valeur visée.`);
}

{
  const s = base(0, `Annexe J — Les ${D.entonnoir.sel} présélectionnés, un par un`, { kicker: "Pour les questions techniques · premier étage : ce que les sociétés SONT · note = écart à la moyenne du secteur (+1 = nettement meilleure)", source: "Composition iShares STOXX Europe 600 · données Yahoo Finance relevées en septembre 2026" });
  const t = D.trente;
  const name = (n) => n.replace(/,?\s+(plc|p\.l\.c\.|s\.a\.|s\.p\.a\.|sa|ag|se|n\.v\.|asa|ab|\(publ\)|holdings?|société anonyme|aktiengesellschaft|group|limited|oyj|a\/s)\.?$/i, "").replace(/,?\s+(plc|s\.a\.|ag|se|sa|n\.v\.)\.?$/i, "");
  const half = (a) => [["#", "Société", "Secteur", "Pays", "Note"], ...a.map((r, i) => [String(r.i + 1), name(r[0]).slice(0, 30), r[1], r[2], "+" + fr(r[3], 2)])];
  const rows = t.map((r, i) => Object.assign([...r], { i }));
  const cw = [0.35, 2.35, 1.75, 1.0, 0.6];
  table(s, half(rows.slice(0, 15)), M, 1.55, 6.05, cw, { fontSize: 9.5, rowH: 0.305 });
  table(s, half(rows.slice(15)), 6.68, 1.55, 6.05, cw, { fontSize: 9.5, rowH: 0.305 });
  s.addNotes(`Voici les ${D.entonnoir.sel} titres que la notation retient : ils couvrent ${Object.keys(D.secteurs30).length} secteurs sur 11. Ce n'est PAS encore le portefeuille — c'est le premier étage, celui du constaté : bilan, marges, valorisation, comportement en crise. Tout y est mesuré sur le passé et le présent. Le deuxième étage, dans le corps de la présentation, pose la question d'après, celle de l'avenir, et resserre ces ${D.entonnoir.sel} en ${D.entonnoir.final}. La sélection ne ressemble pas à l'indice, et c'est voulu : la note ignore la taille des sociétés, elle ne regarde que leurs qualités face à leurs concurrentes. Cette liste est en annexe : l'entonnoir suffit dans le corps de la présentation, et la seule liste qui compte est celle des ${D.entonnoir.final} retenus.`);
}

{
  // Matrices de corrélation. Échelle divergente du référentiel dataviz :
  // pôle froid / gris neutre / pôle chaud, bornée à ±80 pour que le gris
  // tombe exactement sur zéro. Diagonale retirée : elle vaut 100 partout,
  // n'apprend rien et écraserait l'échelle.
  const s = base(0, "Annexe K — Les supports bougent-ils ensemble ?", { kicker: "Pour les questions techniques · corrélation des variations hebdomadaires : 100 = ils font la même chose, 0 = indépendants, négatif = l'un monte quand l'autre baisse", source: "Séries quotidiennes en euros, octobre 2006 - septembre 2026 · crises : les quatre fenêtres datées · bitcoin écarté (cotations depuis 2014 seulement)" });
  const C = D.corr;
  const LONG = { poche_actions: "Poche actions", etats_courts: "Échelle AAA", etats_longs: "États 2-10 ans", credit_court: "Crédit court", indexees: "Obligations indexées", or: "Or", matieres: "Matières premières" };
  const COURT = { poche_actions: "Act.", etats_courts: "AAA", etats_longs: "2-10", credit_court: "Créd.", indexees: "Idx.", or: "Or", matieres: "Mat." };
  const RAMPE = ["2a78d6", "6097de", "90b5e4", "c0d2e9", "f0efec", "f3cfc0", "f3af95", "f18d68", "eb6834"];
  const BORNE = 80;

  const teinte = (v) => {
    const t = Math.min(1, Math.max(0, (v + BORNE) / (2 * BORNE))) * (RAMPE.length - 1);
    const i = Math.min(RAMPE.length - 2, Math.floor(t)), f = t - i;
    const mix = (a, b) => Math.round(parseInt(a, 16) + (parseInt(b, 16) - parseInt(a, 16)) * f).toString(16).padStart(2, "0");
    const A = RAMPE[i], B = RAMPE[i + 1];
    return mix(A.slice(0, 2), B.slice(0, 2)) + mix(A.slice(2, 4), B.slice(2, 4)) + mix(A.slice(4, 6), B.slice(4, 6));
  };

  const matrice = (m, x, titre, sous) => {
    s.addText([{ text: titre, options: { bold: true, color: INK } }, { text: "   " + sous, options: { color: MUTED, fontSize: 11 } }],
      { x, y: 1.52, w: 5.9, h: 0.3, fontFace: BF, fontSize: 13.5, margin: 0, isTextBox: true });
    const entete = ["", ...C.ordre.map((k) => COURT[k])];
    const corps = C.ordre.map((k, i) => [LONG[k], ...C.ordre.map((_, j) => (
      i === j ? { text: "", options: { fill: { color: WHITE } } }
              : { text: fr(m[i][j], 0), options: { fill: { color: teinte(m[i][j]) }, color: TEXT } }))]);
    table(s, [entete, ...corps], x, 1.85, 5.9, [1.7, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6],
      { fontSize: 10.5, rowH: 0.4, bold1: true, alignRight: true, zebra: false });
  };
  matrice(C.hors, M, "Hors crise", `${C.semaines.hors_crise} semaines`);
  matrice(C.crise, M + 6.23, "En crise", `${C.semaines.en_crise} semaines`);

  const ix = (k) => C.ordre.indexOf(k);
  const a = ix("poche_actions");
  const cor = (v) => (v > 0 ? "+" : "") + fr(v, 0);
  const av = (k) => cor(C.hors[a][ix(k)]), ap = (k) => cor(C.crise[a][ix(k)]);
  const ent = (i, j) => cor(C[i][ix(j[0])][ix(j[1])]);
  card(s, M, 5.32, W - 2 * M, 1.55);
  para(s, M + 0.25, 5.45, 5.75, 1.35, bullets([
    `**L'échelle AAA** passe de ${av("etats_courts")} à ${ap("etats_courts")} face aux actions, **l'or** de ${av("or")} à ${ap("or")} : les deux amortisseurs se déclenchent au bon moment`,
    `**Les matières premières** restent à ${ap("matieres")} : elles diversifient peu, d'où leur place réduite`,
  ]), 13, { paraSpaceAfter: 7 });
  para(s, M + 6.35, 5.45, 5.5, 1.35, bullets([
    `**Le revers** : entre eux, crédit court et indexées passent de ${ent("hors", ["credit_court", "indexees"])} à ${ent("crise", ["credit_court", "indexees"])}, États courts et longs de ${ent("hors", ["etats_courts", "etats_longs"])} à ${ent("crise", ["etats_courts", "etats_longs"])}`,
    "Le coussin **se resserre sur lui-même** : d'où le refus de le concentrer sur une seule maturité",
  ]), 13, { paraSpaceAfter: 7 });

  s.addNotes(`Un mot sur la corrélation, parce que la question vient toujours. À gauche, les semaines ordinaires ; à droite, les seules semaines de crise. Deux chiffres comptent. L'échelle AAA était à ${av("etats_courts")} face aux actions en temps normal : indépendante. En crise elle passe à ${ap("etats_courts")} : elle monte quand les actions chutent. L'or fait le même chemin, de ${av("or")} à ${ap("or")}. Voilà pourquoi on garde de l'or malgré un rendement espéré de 4 % seulement : on ne l'achète pas pour son rendement, on l'achète pour ce qu'il fait ce jour-là. À l'inverse, les matières premières restent à ${ap("matieres")} : elles diversifient peu, et c'est pour ça qu'elles ont une place réduite. Et je veux être honnête sur le revers, parce qu'on me le demanderait sinon : la poche défensive, elle, se resserre. Crédit court et indexées passent de ${ent("hors", ["credit_court", "indexees"])} à ${ent("crise", ["credit_court", "indexees"])} entre eux. Autrement dit les amortisseurs deviennent un seul pari au moment où on compte sur eux. C'est exactement la raison pour laquelle on ne met pas tout le défensif sur la même maturité, et pourquoi le calcul ne travaille pas sur une corrélation moyenne, mais fait traverser au portefeuille les vingt années jour après jour.`);
}

{
  const cf = D.credit_fonds;
  const s = base(0, "Annexe L — Le crédit court, et pourquoi il finit à zéro", { kicker: `Pour les questions techniques · fonds retenu : ${cf.ticker}, obligations d'entreprises bien notées, durée ${fr(cf.duree)} an`, source: "Fiches iShares · courbe BCE (État de même échéance) · pertes sur défauts : Moody's" });
  stat(s, M, 1.8, 3.8, "+0,24 pt", "de plus qu'un État de même échéance (0,13 pt après défauts)", FAM.eta, 44);
  stat(s, 4.75, 1.8, 3.8, `${pct(cf.dd2020)}`, `en 2020, contre ${pct(cf.etat2020)} pour l'État de même durée`, NEG, 44);
  stat(s, 8.9, 1.8, 3.8, "3,39 %", "rendement retenu pour l'étape 4, défauts déduits", INK, 44);
  const rr = [["Haut rendement euro", RC.hy_euro.c], ["Crédit court retenu", 3.39], ["États zone euro 2-10 ans", D.souverains.rdt_long], ["Crédit, indice toutes durées", RC.credit_ig_eur.c]];
  s.addChart(pres.charts.BAR, [{ name: "Rendement", labels: rr.map((r) => r[0]), values: rr.map((r) => r[1]) }],
    { ...chartBase("Rendement espéré, défauts déduits"), x: M, y: 3.75, w: 7.2, h: 3.1, barDir: "bar", chartColors: [FAM.eta], showValue: true, dataLabelFormatCode: '0.00" %"', dataLabelPosition: "outEnd", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMinVal: 0, valAxisMaxVal: 5, showLegend: false, barGapWidthPct: 40, catAxisOrientation: "maxMin" });
  callout(s, 8.2, 3.9, 4.53, 2.9, "Le haut rendement rapporte, défauts déduits, **moins que les États**. Le crédit court, **moins que l'échelle d'États 2-10 ans** : sa place sera au mieux modeste.", INK, 15);
  s.addNotes("Le crédit mérite une slide, parce que le résultat est contre-intuitif. Le haut rendement, une fois les défauts déduits, rapporte moins que les États : écarté. Le crédit bien noté court ne rapporte que 0,24 point de plus qu'un État de même échéance, et il a perdu trois fois plus en 2020. Défauts déduits, il rapporte 3,39 %, moins que notre échelle d'emprunts d'État. On le garde dans l'univers, mais on verra à l'étape 4 que le calcul lui donne zéro, à raison.");
}


pres.writeFile({ fileName: OUT }).then((f) => console.log("écrit :", f, "·", slideNo, "slides"));
