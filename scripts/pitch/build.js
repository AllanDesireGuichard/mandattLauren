// Pitch oral du mandat Lauren — 36 slides, speech client dans les notes.
// Lit data.json (PYTHONPATH=. python3 scripts/pitch/extraire.py), puis :
//   cd scripts/pitch && npm install && npm run build
// Sortie : outputs/Mandat_Lauren_pitch_genere.pptx. Ne jamais écrire sur
// Mandat_Lauren_pitch.pptx : c'est la version retouchée à la main par Allan.
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
  const s = base(3, "De 600 valeurs européennes à 30 titres", { kicker: "Point de départ : le STOXX Europe 600 · on ne garde que les grandes capitalisations (10 Md€ et plus)" });
  const E = D.entonnoir;
  const steps = [[`${E.n}`, "valeurs du STOXX 600"], [`− ${E.excl}`, "exclues : tabac, armement, charbon"], [`− ${E.inv}`, "sociétés d'investissement, non notables"], [`− ${E.petites}`, "trop petites (< 10 Md€)"], [`${E.notees}`, "notées sur cinq piliers"], [`${E.sel}`, "retenues"]];
  steps.forEach(([n, l], i) => {
    const w = 11.6 - i * 1.55, x = (W - w) / 2, y = 1.6 + i * 0.8;
    const fill = i === steps.length - 1 ? GOLD : i === 0 ? INK : "3B5A80";
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.68, fill: { color: fill }, line: { color: fill }, rectRadius: 0.06 });
    s.addText([{ text: n + "  ", options: { bold: true, fontSize: 20, fontFace: HF } }, { text: l, options: { fontSize: 14 } }], { x, y, w, h: 0.68, align: "center", valign: "middle", color: WHITE, fontFace: BF, margin: 0, isTextBox: true });
  });
  s.addNotes(`Pour les actions européennes, on part des 600 plus grandes valeurs d'Europe. On retire d'abord les ${E.excl} sociétés touchées par les exclusions du client : ${E.excl_motifs.armement} dans l'armement, ${E.excl_motifs.tabac} dans le tabac, ${E.excl_motifs.charbon} dans le charbon, au seuil de 5 % du chiffre d'affaires. On écarte les sociétés d'investissement, que la notation ne sait pas mesurer, et les sociétés de moins de 10 milliards, moins suivies et moins liquides. Il en reste ${E.notees}, que l'on note ; on en retient 30.`);
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
  para(s, 6.55, 4.72, 5.95, 2.0, bullets(["**4 titres** au plus par secteur, **6** par pays", "Aucun titre parmi les **10 % les plus volatils**", "Données aberrantes écartées (un PER de 1 042…)"]), 13.5, { paraSpaceAfter: 7 });
  s.addNotes("Chaque société reçoit une note sur cinq piliers à poids égaux, toujours comparée aux sociétés de son propre secteur : c'est ce qui permet de comparer une banque, dont le PER est naturellement bas, à un éditeur de logiciels. Le cinquième pilier, la résistance, est propre à ce mandat : plus la poche d'actions baisse modérément en crise, plus on peut en détenir sous la limite de 15 %. Enfin, des plafonds par secteur et par pays évitent qu'un seul thème ne prenne toute la place. Détail technique si on me le demande : chaque indicateur est mesuré en écarts-types par rapport à la moyenne du secteur, après avoir écarté les données aberrantes.");
}

{
  const s = base(3, "Les 30 titres retenus", { kicker: "À parts égales · note = écart à la moyenne du secteur (+1 = nettement meilleure)", source: "Composition iShares STOXX Europe 600 · données Yahoo Finance relevées en septembre 2026" });
  const t = D.trente;
  const name = (n) => n.replace(/,?\s+(plc|p\.l\.c\.|s\.a\.|s\.p\.a\.|sa|ag|se|n\.v\.|asa|ab|\(publ\)|holdings?|société anonyme|aktiengesellschaft|group|limited|oyj|a\/s)\.?$/i, "").replace(/,?\s+(plc|s\.a\.|ag|se|sa|n\.v\.)\.?$/i, "");
  const half = (a) => [["#", "Société", "Secteur", "Pays", "Note"], ...a.map((r, i) => [String(r.i + 1), name(r[0]).slice(0, 30), r[1], r[2], "+" + fr(r[3], 2)])];
  const rows = t.map((r, i) => Object.assign([...r], { i }));
  const cw = [0.35, 2.35, 1.75, 1.0, 0.6];
  table(s, half(rows.slice(0, 15)), M, 1.55, 6.05, cw, { fontSize: 9.5, rowH: 0.305 });
  table(s, half(rows.slice(15)), 6.68, 1.55, 6.05, cw, { fontSize: 9.5, rowH: 0.305 });
  s.addNotes(`Voici les 30 titres retenus, investis à parts égales. Ils couvrent ${Object.keys(D.secteurs).length} secteurs sur 11 et ${Object.keys(D.pays).length} pays. La sélection ne ressemble pas à l'indice, et c'est voulu : la note ignore la taille des sociétés, elle ne regarde que leurs qualités face à leurs concurrentes. Je peux ouvrir la fiche de n'importe quel titre dans l'application.`);
}

{
  const P = D.panier;
  const s = base(3, "Le panier résiste mieux que l'indice", { kicker: "Les 30 titres à parts égales, en euros, face au STOXX Europe 600" });
  const items = [["Volatilité sur 3 ans", P.panier.vol_3a, P.indice.vol_3a], ["Pire baisse en 2020", P.panier.dd_2020, P.indice.dd_2020], ["Pire baisse en 2022", P.panier.dd_2022, P.indice.dd_2022]];
  items.forEach(([l, a, b], i) => {
    const x = M + i * 4.1;
    card(s, x, 1.7, 3.85, 2.6);
    s.addText(l, { x: x + 0.25, y: 1.85, w: 3.4, h: 0.4, fontFace: BF, fontSize: 14, color: MUTED, margin: 0, isTextBox: true });
    s.addText(pct(a), { x: x + 0.25, y: 2.3, w: 3.4, h: 0.9, fontFace: HF, fontSize: 40, bold: true, color: INK, margin: 0, isTextBox: true });
    s.addText("indice : " + pct(b), { x: x + 0.25, y: 3.3, w: 3.4, h: 0.4, fontFace: BF, fontSize: 15, color: TEXT, margin: 0, isTextBox: true });
  });
  callout(s, M, 4.7, W - 2 * M, 1.7, "Moins agité au quotidien, nettement mieux tenu en 2022, à égalité en 2020. Mais en crise, il perd **bien plus que 15 %** : c'est le dosage avec les obligations et l'or, à l'étape 4, qui tiendra la limite.", INK, 15.5);
  s.addNotes(`On vérifie que la sélection tient mieux en crise que l'indice. C'est le cas en 2022 : ${pct(P.panier.dd_2022)} contre ${pct(P.indice.dd_2022)}. En 2020, les deux ont baissé d'environ un tiers. Message important : un panier d'actions reste un panier d'actions. La limite de 15 % ne se tiendra pas par le choix des titres, mais par le dosage entre actions, obligations et or, à l'étape 4. Précaution d'honnêteté : les titres sont choisis avec les données d'aujourd'hui, donc leur performance passée est flatteuse par construction ; seul leur comportement en crise est informatif.`);
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
  const rows = [["Classe", "Fonds retenu", "Frais / an", "Taille"]];
  D.fonds.filter((f) => f[1] !== "IB1T").forEach(([cl, t, nom, fr_, tl]) => rows.push([cl, `${t} · ${nom.replace(" UCITS ETF", "").replace(" EUR (Acc)", "").replace(" 1C", "")}`, pct(fr_, 2), fr(tl / 1000, 1) + " Md€"]));
  const cf = D.credit_fonds;
  rows.push(["Crédit euro bien noté, court", `${cf.ticker} · ${cf.nom.replace(" UCITS ETF EUR (Dist)", "")}`, pct(cf.frais, 2), fr(cf.taille / 1000, 1) + " Md€"]);
  table(s, rows, M, 1.6, 8.3, [2.6, 3.9, 0.9, 0.9], { fontSize: 11.5, rowH: 0.48, bold1: true });
  para(s, 9.2, 1.6, 3.55, 5.2, bullets([
    "**États-Unis et Japon séparés**, plutôt qu'un fonds Monde qui recompterait l'Europe",
    `**Émergents** : le seul fonds conforme s'écarte du marché (${sgn(D.xzem_ecart, 1)} par an sur 7 ans) — écart annoncé au client`,
    "**Infrastructure retirée** : aucun fonds à la fois assez gros et conforme",
    "**Neuf libellés faux** corrigés dans l'univers de départ",
  ]), 12.5, { paraSpaceAfter: 9 });
  s.addNotes("Pour les autres classes, on passe par des fonds cotés, choisis selon une règle simple : d'abord des exclusions conformes au mandat, puis une taille d'au moins un milliard, pour ne jamais peser plus de 1 % d'un fonds, et enfin les frais les plus bas. Point de vigilance : un filtre ESG dit « Screened » n'exclut pas l'armement conventionnel, alors que nous l'avons exclu des actions en direct ; nous avons donc lu les méthodologies d'indices et retenu des indices plus stricts. Conséquence pour les émergents : le seul fonds conforme s'éloigne nettement du marché, écart que nous annoncerons au client. L'infrastructure a été retirée : aucun fonds n'était à la fois assez gros et conforme. Enfin, en revérifiant l'univers de départ, nous avons trouvé neuf fonds mal libellés, dont un fonds d'actions américaines présenté comme de la dette émergente.");
}

{
  const cf = D.credit_fonds;
  const s = base(3, "Le crédit court rapporte à peine plus que l'État", { kicker: `Fonds retenu : ${cf.ticker}, obligations d'entreprises bien notées, durée ${fr(cf.duree)} an`, source: "Fiches iShares · courbe BCE (État de même échéance) · pertes sur défauts : Moody's" });
  stat(s, M, 1.8, 3.8, "+0,24 pt", "de plus qu'un État de même échéance (0,13 pt après défauts)", FAM.eta, 44);
  stat(s, 4.75, 1.8, 3.8, `${pct(cf.dd2020)}`, `en 2020, contre ${pct(cf.etat2020)} pour l'État de même durée`, NEG, 44);
  stat(s, 8.9, 1.8, 3.8, "3,39 %", "rendement retenu pour l'étape 4, défauts déduits", INK, 44);
  const rr = [["Haut rendement euro", RC.hy_euro.c], ["Crédit court retenu", 3.39], ["États zone euro 2-10 ans", D.souverains.rdt_long], ["Crédit, indice toutes durées", RC.credit_ig_eur.c]];
  s.addChart(pres.charts.BAR, [{ name: "Rendement", labels: rr.map((r) => r[0]), values: rr.map((r) => r[1]) }],
    { ...chartBase("Rendement espéré, défauts déduits"), x: M, y: 3.75, w: 7.2, h: 3.1, barDir: "bar", chartColors: [FAM.eta], showValue: true, dataLabelFormatCode: '0.00" %"', dataLabelPosition: "outEnd", valAxisHidden: true, valGridLine: { style: "none" }, valAxisMinVal: 0, valAxisMaxVal: 5, showLegend: false, barGapWidthPct: 40, catAxisOrientation: "maxMin" });
  callout(s, 8.2, 3.9, 4.53, 2.9, "Le haut rendement rapporte, défauts déduits, **moins que les États**. Le crédit court, **moins que l'échelle d'États 2-10 ans** : sa place sera au mieux modeste.", INK, 15);
  s.addNotes("Le crédit mérite une slide, parce que le résultat est contre-intuitif. Le haut rendement, une fois les défauts déduits, rapporte moins que les États : écarté. Le crédit bien noté court ne rapporte que 0,24 point de plus qu'un État de même échéance, et il a perdu trois fois plus en 2020. Défauts déduits, il rapporte 3,39 %, moins que notre échelle d'emprunts d'État. On le garde dans l'univers, mais on verra à l'étape 4 que le calcul lui donne zéro, à raison.");
}

// ================================================================ SECTION 4
dark("Allocation", "Combien placer sur chaque support pour rapporter au moins 4 % sans jamais perdre plus de 15 %", { num: "4" })
  .addNotes("Quatrième étape, le cœur de l'exercice : combien placer sur chaque support.");

{
  const s = base(4, "Seules les actions et les indexées dépassent 4 %", { kicker: "Rendement espéré de chaque support : étape 2, corrigé de ce que l'étape 3 a appris", source: "Actions européennes : rendement de l'indice (le panier n'est pas supposé battre son marché)" });
  const nm = { actions_europe: "Actions Europe", usa: "Actions États-Unis", japon: "Actions Japon", emergents: "Actions émergentes", etats_courts: "Échelle AAA (10 M€)", etats_longs: "États 2-10 ans", credit_court: "Crédit court", indexees: "Indexées", or: "Or", matieres: "Matières premières" };
  const rows = D.entrees.slice().sort((a, b) => a[2] - b[2]);
  s.addChart(pres.charts.BAR, [
    { name: "Sous 4 %", labels: rows.map((r) => nm[r[0]]), values: rows.map((r) => (r[2] <= 4 ? r[2] : 0)) },
    { name: "Au-dessus", labels: rows.map((r) => nm[r[0]]), values: rows.map((r) => (r[2] > 4 ? r[2] : 0)) },
  ], { ...chartBase("Rendement espéré par an"), x: M, y: 1.55, w: 7.4, h: 5.35, barDir: "bar", barGrouping: "stacked", chartColors: ["9CA3AF", FAM.act], showValue: true, dataLabelFormatCode: '0.00" %";;;', dataLabelPosition: "inEnd", dataLabelColor: WHITE, valAxisMaxVal: 10, valAxisLabelFormatCode: '0" %"', showLegend: false, barGapWidthPct: 40 });
  card(s, 8.3, 1.6, 4.43, 2.9);
  s.addText("La règle de perte", { x: 8.55, y: 1.72, w: 4, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  para(s, 8.55, 2.15, 4.0, 2.3, bullets(["Mesurée **depuis le plus haut**", "Sur **les 100 M€** ensemble", "Jamais au-delà de 15 % dans **2008, 2011, 2020, 2022**", "**Pas de crypto**"]), 13.5, { paraSpaceAfter: 6 });
  callout(s, 8.3, 4.75, 4.43, 2.05, "Chaque euro placé en obligations ou en or devra être **compensé par des actions** : c'est la tension entre 4 % et 15 %.", INK, 14);
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
  s.addNotes(`Deuxième ingrédient : le comportement en crise. Les actions perdent jusqu'à ${pct(-pa, 0)} en 2008. Sans amortisseur, on ne pourrait donc pas en détenir plus de ${pct(15 / -pa * 100, 0)}. Pour aller au-delà, il faut des supports qui montent quand les actions baissent. En 2008, les emprunts d'État gagnent 14 % et l'or 39 % : ils amortissent. Mais en 2022, crise d'inflation, les obligations baissent avec les actions : plus d'amortisseur. C'est le régime décrit à l'étape 2. L'or est le seul qui tienne partout. Parce que ce lien change d'une crise à l'autre, le calcul ne s'appuie pas sur une corrélation moyenne : il fait traverser à chaque portefeuille les vingt années, jour après jour.`);
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
  para(s, 7.85, 5.75, 4.9, 1.1, rich("Crédit et matières premières restent **à zéro** : le crédit rapporte moins que les États, les matières premières baissent avec les actions."), 11.5);
  s.addNotes(`On reprend le calcul et on ajoute les règles une par une, en chiffrant ce que chacune coûte. Réserver les 10 millions en AAA ne coûte presque rien. Imposer la répartition des actions, Europe 40, États-Unis 35, Japon 10, émergents 15, est la règle la plus chère : ${fr(S.r2_cle.rdt - S.r1_aaa.rdt, 2)} point, c'est le prix du renoncement au pari sur le yen. Les plafonds évitent la concentration ; résultat intéressant, les actions remontent, parce que les États à 2-10 ans amortissaient mieux 2020 que les indexées. Enfin une marge : viser 14 % au lieu de 15, parce que certains remplaçants flattent 2008. Au total, les règles coûtent ${fr(LIB.rdt - R4.rdt, 2)} point de rendement espéré : c'est le prix d'un portefeuille robuste.`);
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
  s.addNotes(`Voici le portefeuille retenu : environ ${pct(partAct * 100, 0)} d'actions, ${pct((W4.etats_courts + W4.etats_longs) * 100, 0)} d'emprunts d'État, 15 % d'obligations indexées et ${pct(W4.or * 100, 0)} d'or. Un point de méthode important : le rendement brut est de ${pct(R4.rdt, 2)}, mais l'objectif du client est un objectif NET — ce qui doit battre l'inflation, c'est ce qui lui reste. On retire donc les frais des fonds, ${fr(D.frais_inst, 2)} point, et nos frais de mandat, ${fr(D.frais_mandat, 2)} point : il reste ${pct(D.net, 2)} nets, soit ${fr(D.net - D.seuil, 2)} point au-dessus de l'inflation de l'énoncé. Si on me demande la fiscalité : elle est hors périmètre de cet exercice et retirerait encore environ 0,30 point. Pire baisse sur vingt ans : ${pct(-R4.pire)}. Les actions ne font que 30 % du patrimoine mais apportent près de la moitié du rendement ; les obligations tiennent la limite de perte.`);
}

{
  const s = base(4, "Le portefeuille en millions d'euros", { kicker: "100 M€, support par support", source: `Frais des fonds : ${fr(D.frais_total / 1e3, 0)} k€ par an (${pct(D.frais_inst, 2)} du patrimoine) · frais de mandat ${pct(D.frais_mandat, 2)} · aucune ligne ne dépasse 1 % de son fonds` });
  const nm = { actions_europe: "Actions européennes", usa: "Actions américaines", japon: "Actions japonaises", emergents: "Actions émergentes", etats_courts: "Échelle AAA, 6 à 24 mois", etats_longs: "Échelle zone euro, 2 à 10 ans", indexees: "Obligations indexées", or: "Or" };
  const sup = { actions_europe: "30 titres en direct", etats_courts: "4 obligations en direct", etats_longs: "5 obligations en direct" };
  const fc = { actions_europe: FAM.act, usa: FAM.act, japon: FAM.act, emergents: FAM.act, etats_courts: FAM.eta, etats_longs: FAM.eta, indexees: FAM.idx, or: FAM.or };
  const rows = [["Ligne", "Support", "Montant", "Poids", "Rendement espéré"]];
  D.retenu_lignes.forEach(([k, , s_, w, r]) => rows.push([{ text: [{ text: "■  ", options: { color: fc[k] } }, { text: nm[k], options: { color: TEXT } }] }, sup[k] || s_, me(w * 1e8), pct(w * 100), pct(r, 2)]));
  rows.push([{ text: "Total", options: { bold: true } }, "", { text: "100,0 M€", options: { bold: true } }, "100 %", { text: pct(R4.rdt, 2), options: { bold: true } }]);
  table(s, rows, M, 1.55, 8.3, [3.0, 2.2, 1.05, 0.8, 1.25], { fontSize: 13, rowH: 0.47, alignRight: true });
  // pastilles de couleur des familles
  const par = W4.actions_europe * 1e8 / 30;
  para(s, 9.25, 1.6, 3.5, 5.2, bullets([
    `**30 actions européennes** à ${me(par, 2)} chacune`,
    `**Échelle AAA** : ${me(W4.etats_courts * 1e8)} investis, qui rendront les 10 M€ avec une petite réserve`,
    `**Échelle 2-10 ans** : 5 × ${me(W4.etats_longs * 1e8 / 5, 2)}`,
    "**Fonds** : XZMU, XZMJ, XZEM, IBCI, Xetra-Gold",
    `Réalisé 2006-2026 : **${pct(D.realise, 2)} par an** (dix ans de taux négatifs inclus)`,
    `Rendement espéré **net de frais : ${pct(D.net, 2)}**`,
  ]), 13, { paraSpaceAfter: 9 });
  s.addNotes("Concrètement, en millions d'euros. Environ 12 millions sur les 30 actions européennes, à 400 000 euros chacune ; 10 millions sur l'échelle AAA, qui rendront un peu plus que les 10 millions à décaisser ; 41 millions sur l'échelle d'emprunts d'État de 2 à 10 ans ; 15 millions en obligations indexées ; le reste en fonds d'actions américaines, japonaises et émergentes, et 3 millions en or. Les frais des fonds représentent environ 47 000 euros par an. Sur 2006-2026, ce portefeuille aurait rapporté 4,5 % par an ; ce n'est pas comparable au rendement espéré, parce que le passé comptait dix ans de taux négatifs alors que l'avenir part de taux autour de 3 %.");
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
  const items = [[pct(D.net, 2), "de rendement espéré net de frais"], [pct(R4.pire), "de pire baisse sur vingt ans"], [pct(partAct * 100, 0), "d'actions, dont 30 titres en direct"], ["10 M€", "sécurisés en AAA, à taux garantis"]];
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

pres.writeFile({ fileName: OUT }).then((f) => console.log("écrit :", f, "·", slideNo, "slides"));
