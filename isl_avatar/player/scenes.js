// Animated teaching pictures, one per lesson chapter (lessons/photosynthesis.json "scene").
//
// Each scene is an SVG drawing (viewBox 600 x 360). A chapter is told in numbered steps
// ("beats"); elements say when they are shown:
//   data-b="3"    shown in step 3 only     data-b="3+"  from step 3 on     data-b="2-3"  steps 2 and 3
//   data-hl="3"   pulses (highlighted) during step 3
// Labels are bilingual: English, then Kannada (draft translation, see the lesson file).

const L = (x, y, en, kn, cls = '', b = '') =>
  `<g class="lbl ${cls}" ${b ? `data-b="${b}"` : ''}><text x="${x}" y="${y}">${en}</text>` +
  (kn ? `<text class="kn" x="${x}" y="${y + 17}">${kn}</text>` : '') + '</g>';

const SKY = '<rect class="sky" width="600" height="360"/>';
const GROUND = (y = 280) => `<rect class="soil" y="${y}" width="600" height="${360 - y}"/>`;
const SUN = (x, y, r = 34, b = '') =>
  `<g class="sun-g" ${b ? `data-b="${b}"` : ''}><circle class="corona" cx="${x}" cy="${y}" r="${r + 14}"/>` +
  `<circle class="sun" cx="${x}" cy="${y}" r="${r}"/></g>`;
const DROP = (x, y, cls = '') => `<path class="drop ${cls}" d="M${x} ${y - 9}C${x + 6} ${y - 1} ${x + 7} ${y + 6} ${x} ${y + 6}C${x - 7} ${y + 6} ${x - 6} ${y - 1} ${x} ${y - 9}Z"/>`;
const MOL = (x, y, txt, cls = 'co2m', r = 13) => `<g class="mol ${cls}"><circle cx="${x}" cy="${y}" r="${r}"/><text x="${x}" y="${y + r * 0.32}" style="font-size:${Math.round(r * 0.78)}px">${txt}</text></g>`;
const STACKS = (pts) => pts.map(([x, y]) => [0, 1, 2, 3].map((k) => `<ellipse class="thylakoid faint" cx="${x}" cy="${y - k * 8}" rx="24" ry="5"/>`).join('')).join('');
const PERSON = (x, y, cls = '') =>
  `<g class="person ${cls}"><circle cx="${x}" cy="${y}" r="16"/><path d="M${x - 20} ${y + 70}C${x - 20} ${y + 30} ${x - 14} ${y + 20} ${x} ${y + 20}C${x + 14} ${y + 20} ${x + 20} ${y + 30} ${x + 20} ${y + 70}Z"/></g>`;

// A potted-style plant standing on the ground line (stem base at x, y).
function plant(x, y, s = 1, extra = '') {
  const P = (d) => d.replace(/(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)/g, (_, a, c) => `${x + a * s} ${y + c * s}`);
  return `<g class="plant">
    <g class="roots" data-hl="2">${['0 0 C-4 22 -20 36 -38 48', '0 0 C6 26 24 38 44 50', '0 0 C0 30 -2 50 0 72']
      .map((d) => `<path d="${P('M' + d)}"/>`).join('')}</g>
    <path class="stem" data-hl="3" d="${P('M0 0 C0 -40 -2 -80 0 -150')}"/>
    <g class="leaves" data-hl="4">
      <path class="leaf" d="${P('M0 -70 C-42 -100 -78 -92 -94 -64 C-60 -46 -24 -50 0 -70Z')}"/>
      <path class="leaf" d="${P('M0 -110 C40 -148 84 -144 100 -118 C68 -92 30 -90 0 -110Z')}"/>
    </g>
    <g class="flower" data-hl="5"><circle cx="${x}" cy="${y - 158 * s}" r="${11 * s}" class="petal"/>
      ${[0, 72, 144, 216, 288].map((a) => `<circle class="petal" cx="${x + Math.cos(a * Math.PI / 180) * 13 * s}" cy="${y - 158 * s + Math.sin(a * Math.PI / 180) * 13 * s}" r="${8 * s}"/>`).join('')}
      <circle class="centre" cx="${x}" cy="${y - 158 * s}" r="${6 * s}"/></g>
    ${extra}</g>`;
}

// A big leaf, centred at (cx, cy).
const BIG_LEAF = (cx, cy, w = 200) => {
  const h = w * 0.42;
  return `<path class="leaf big" d="M${cx - w} ${cy} C${cx - w / 2} ${cy - h * 1.5} ${cx + w / 2} ${cy - h * 1.3} ${cx + w} ${cy} C${cx + w / 2} ${cy + h * 1.3} ${cx - w / 2} ${cy + h * 1.5} ${cx - w} ${cy}Z"/>`;
};
const VEINS = (cx, cy, w = 200, b = '') => `<g class="veins" ${b ? `data-b="${b}"` : ''}>
  <path d="M${cx - w - 30} ${cy} L${cx + w - 10} ${cy}"/>
  ${[-0.6, -0.25, 0.1, 0.45].map((k) => `<path d="M${cx + k * w} ${cy} Q${cx + (k + 0.15) * w} ${cy - 0.3 * w} ${cx + (k + 0.32) * w} ${cy - 0.42 * w}"/><path d="M${cx + k * w} ${cy} Q${cx + (k + 0.15) * w} ${cy + 0.3 * w} ${cx + (k + 0.32) * w} ${cy + 0.42 * w}"/>`).join('')}</g>`;
const MAGNIFIER = (x, y, r, inner, b) => `<g class="magnifier" data-b="${b}">
  <clipPath id="clip-${x}-${y}"><circle cx="${x}" cy="${y}" r="${r}"/></clipPath>
  <circle class="lens-bg" cx="${x}" cy="${y}" r="${r}"/>
  <g clip-path="url(#clip-${x}-${y})">${inner}</g>
  <circle class="lens" cx="${x}" cy="${y}" r="${r}"/>
  <path class="handle" d="M${x + r * 0.72} ${y + r * 0.72} L${x + r * 1.15} ${y + r * 1.15}"/></g>`;
const CELLS = (x0, y0, cols, rows, w, h, chloro = false) => {
  let s = '';
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const x = x0 + c * w + (r % 2 ? w / 2 : 0), y = y0 + r * h;
    s += `<rect class="cell" x="${x}" y="${y}" width="${w - 4}" height="${h - 4}" rx="8"/>`;
    if (chloro) for (let k = 0; k < 4; k++) s += `<ellipse class="chloro-dot" cx="${x + 10 + (k % 2) * (w - 24)}" cy="${y + 10 + Math.floor(k / 2) * (h - 24)}" rx="6" ry="4"/>`;
  }
  return s;
};

export const SCENES = {
  // ---------------------------------------------------------------- introduction
  intro: `${SKY}${GROUND()}${SUN(80, 64, 30, '5')}
    ${plant(300, 280, 1)}
    <g data-b="1-2">${PERSON(110, 196)}${L(70, 132, 'People', 'ಮನುಷ್ಯರು')}</g>
    <g data-b="1-2" class="cow"><ellipse cx="500" cy="236" rx="46" ry="24"/><circle cx="548" cy="220" r="14"/>
      <path d="M470 254v24M490 256v24M512 256v24M530 254v24"/>${L(470, 196, 'Animals', 'ಪ್ರಾಣಿಗಳು')}</g>
    <g data-b="2" class="bowl"><path d="M140 250h60c0 18-14 28-30 28s-30-10-30-28z"/>${L(132, 300, 'eat food', 'ಆಹಾರ ತಿನ್ನುತ್ತಾರೆ')}</g>
    <g data-b="2" class="question"><text x="370" y="110">?</text></g>
    <g data-b="3-4" class="kitchen">${L(400, 150, 'Leaves = kitchen', 'ಎಲೆ = ಅಡುಗೆಮನೆ')}</g>
    <g data-b="4" class="wordsum"><rect x="20" y="16" width="360" height="66" rx="12"/>
      <text x="36" y="44"><tspan class="hot">Photo</tspan> = light   +   <tspan class="hot">synthesis</tspan> = putting together</text>
      <text class="kn" x="36" y="68">ದ್ಯುತಿ = ಬೆಳಕು   +   ಸಂಶ್ಲೇಷಣೆ = ಒಟ್ಟುಗೂಡಿಸುವುದು</text></g>
    <g data-b="5"><g class="rays"><path d="M112 82 L240 180"/><path d="M116 66 L300 140"/></g>
      ${DROP(300, 330, 'rise')}${DROP(300, 330, 'rise d2')}
      ${MOL(540, 120, 'CO₂', 'co2m drift-in')}${MOL(540, 170, 'CO₂', 'co2m drift-in d2')}
      ${L(420, 60, 'Light + Water + CO₂', 'ಬೆಳಕು + ನೀರು + CO₂')}</g>`,

  // ---------------------------------------------------------------- the plant
  plant: `${SKY}${GROUND()}
    ${plant(300, 280, 1.15)}
    ${L(40, 40, 'A plant', 'ಸಸ್ಯ', 'title', '1+')}
    <g data-b="2+" class="callout"><path d="M262 318 L170 318"/>${L(40, 314, 'Roots', 'ಬೇರುಗಳು')}</g>
    <g data-b="3+" class="callout"><path d="M302 200 L420 200"/>${L(426, 196, 'Stem', 'ಕಾಂಡ')}</g>
    <g data-b="3+" class="pipe-water"><path d="M300 280 L300 110"/></g>
    <g data-b="4+" class="callout"><path d="M220 196 L150 170"/>${L(40, 160, 'Leaves', 'ಎಲೆಗಳು')}</g>
    <g data-b="5+" class="callout"><path d="M312 98 L420 70"/>${L(426, 66, 'Flower', 'ಹೂವು')}</g>
    <g data-b="5+" class="seeds"><ellipse cx="480" cy="300" rx="7" ry="4"/><ellipse cx="500" cy="306" rx="7" ry="4"/>
      <path class="sprout" d="M520 300c0-12 4-20 12-24M520 300c-2-8-8-12-14-12"/>${L(470, 340, 'seeds → new plants', '', 'small')}</g>`,

  // ---------------------------------------------------------------- the Sun
  sun: `<rect class="space" width="600" height="360"/>
    ${[[40, 300], [520, 40], [560, 300], [220, 330], [380, 20], [30, 140]].map(([x, y]) => `<circle class="star" cx="${x}" cy="${y}" r="1.8"/>`).join('')}
    ${SUN(140, 170, 80)}
    <g class="flares" data-b="1"><circle class="flare" cx="140" cy="170" r="96"/></g>
    ${L(80, 300, 'The Sun: a star', 'ಸೂರ್ಯ: ಒಂದು ನಕ್ಷತ್ರ', 'title light', '1')}
    <g data-b="2" class="heat">${[0, 1, 2].map((i) => `<path class="wave w${i}" d="M240 ${120 + i * 50} q12 -12 24 0 t24 0 t24 0"/>`).join('')}
      ${L(250, 100, 'light and heat', 'ಬೆಳಕು ಮತ್ತು ಶಾಖ', 'light')}</g>
    <g data-b="3"><path class="trip" d="M230 170 L520 170"/><circle class="photon" cx="230" cy="170" r="6"/>
      <circle class="earth" cx="535" cy="170" r="22"/><path class="land" d="M524 158c8 2 10 10 4 14s-10 8-4 14"/>
      ${L(300, 214, '15 crore km · about 8 minutes', '15 ಕೋಟಿ ಕಿ.ಮೀ · ಸುಮಾರು 8 ನಿಮಿಷ', 'light')}</g>
    <g data-b="4-5"><rect class="sky-panel" x="330" y="40" width="250" height="290" rx="16"/></g>
    <g data-b="4"><g class="rays"><path d="M330 90 L440 160"/><path d="M330 130 L430 190"/><path d="M330 60 L470 150"/></g>
      <path class="leaf big glow" d="M420 190 C450 140 520 130 560 160 C530 210 470 220 420 190Z"/>
      ${[0, 1, 2].map((i) => `<path class="spark s${i}" d="M${480 + i * 22} ${160 + (i % 2) * 18}l4 -10l4 10l-10 -4h12z"/>`).join('')}
      ${L(400, 260, 'the leaf catches energy', 'ಎಲೆ ಶಕ್ತಿಯನ್ನು ಹಿಡಿಯುತ್ತದೆ')}</g>
    <g data-b="5"><rect class="pot" x="470" y="280" width="50" height="40" rx="4"/>
      <path class="stem bend" d="M495 280 C495 240 470 210 440 190"/>
      <path class="leaf" d="M460 220 C440 200 420 204 412 220 C430 232 448 230 460 220Z"/>
      <path class="leaf" d="M440 190 C420 166 398 168 392 184 C410 196 428 198 440 190Z"/>
      <g class="rays"><path d="M330 150 L400 185"/></g>
      ${L(345, 70, 'plants grow towards light', 'ಸಸ್ಯಗಳು ಬೆಳಕಿನ ಕಡೆಗೆ ಬೆಳೆಯುತ್ತವೆ')}</g>`,

  // ---------------------------------------------------------------- soil
  soil: `<rect class="sky" width="600" height="80"/>
    <rect class="layer top" y="80" width="600" height="90"/><rect class="layer sub" y="170" width="600" height="100"/>
    <rect class="layer rock" y="270" width="600" height="90"/>
    ${[[60, 300], [140, 330], [260, 310], [400, 325], [520, 300]].map(([x, y]) => `<ellipse class="stone" cx="${x}" cy="${y}" rx="34" ry="16"/>`).join('')}
    <path class="grass" d="M0 80 ${Array.from({ length: 30 }, (_, i) => `l10 -12 l10 12`).join(' ')}"/>
    <g data-b="1+">${L(16, 120, 'Topsoil', 'ಮೇಲ್ಮಣ್ಣು', 'light')}${L(16, 214, 'Subsoil', 'ಕೆಳಮಣ್ಣು', 'light')}${L(16, 352, 'Rock', 'ಬಂಡೆ', 'light')}</g>
    <g data-b="2-4">${MAGNIFIER(410, 175, 110, `<rect x="300" y="60" width="230" height="230" class="zoom-soil"/>
      ${[[350, 120, 30, 'sand'], [430, 110, 22, 'sand'], [470, 200, 34, 'sand'], [360, 220, 26, 'sand'], [410, 260, 18, 'sand']].map(([x, y, r, c]) => `<circle class="${c}" cx="${x}" cy="${y}" r="${r}"/>`).join('')}
      ${[[400, 160], [445, 150], [385, 185], [420, 215], [455, 245]].map(([x, y]) => `<circle class="clay" cx="${x}" cy="${y}" r="8"/>`).join('')}
      <path class="humus" d="M330 160c12-8 26-6 34 4c-12 6-24 6-34-4z M480 140c10-10 26-8 30 2c-12 4-22 4-30-2z"/>
      <g data-b="4">${[[398, 132], [455, 182], [392, 245], [340, 180]].map(([x, y], i) => i % 2 ? `<circle class="air-pocket" cx="${x}" cy="${y}" r="9"/>` : DROP(x, y, 'still')).join('')}</g>`, '2-4')}
      ${L(300, 312, 'rock bits, sand, clay, humus', 'ಕಲ್ಲು, ಮರಳು, ಜೇಡಿಮಣ್ಣು, ಹ್ಯೂಮಸ್', 'light small', '2')}
      ${L(300, 312, 'spaces hold water and air', 'ಖಾಲಿ ಜಾಗದಲ್ಲಿ ನೀರು, ಗಾಳಿ', 'light small', '4')}</g>
    <g data-b="3" class="worm"><path d="M120 140 c14 -10 28 10 42 0 s28 10 42 0"/>${L(110, 175, 'earthworm', 'ಎರೆಹುಳು', 'light small')}</g>
    <g data-b="5"><path class="stem" d="M300 80 L300 20"/><path class="leaf" d="M300 46 C280 30 262 34 256 46 C272 56 288 54 300 46Z"/>
      <g class="roots grow">${['M300 80 C296 120 270 150 230 190', 'M300 80 C306 130 340 160 380 200', 'M300 80 C300 140 298 190 300 250'].map((d) => `<path d="${d}"/>`).join('')}</g>
      ${[[250, 170], [360, 185], [300, 230], [270, 120]].map(([x, y], i) => `<circle class="mineral m${i}" cx="${x}" cy="${y}" r="5"/>`).join('')}
      ${L(390, 120, 'minerals + water → roots', 'ಖನಿಜ + ನೀರು → ಬೇರು', 'light')}</g>`,

  // ---------------------------------------------------------------- water
  water: `${SKY}${GROUND(260)}
    <g data-b="1+"><g class="cloud"><ellipse cx="140" cy="50" rx="60" ry="24"/><ellipse cx="190" cy="40" rx="44" ry="26"/><ellipse cx="100" cy="56" rx="34" ry="18"/></g>
      ${[90, 120, 150, 180, 210].map((x, i) => `<path class="rain r${i % 3}" d="M${x} 80 l-6 16"/>`).join('')}
      ${[100, 160, 210].map((x, i) => `<g class="soak k${i}">${DROP(x, 270)}</g>`).join('')}
      </g>${L(30, 130, 'rain soaks in', 'ಮಳೆ ನೀರು ಇಂಗುತ್ತದೆ', '', '1')}
    ${plant(330, 260, 1)}
    <g data-b="2">${MAGNIFIER(470, 300, 52, `<rect x="410" y="240" width="120" height="120" class="zoom-soil"/>
      <path class="root-close" d="M420 300 L530 300"/>${[440, 460, 480, 500].map((x) => `<path class="hair" d="M${x} 300 l-6 22M${x} 300 l6 -22"/>`).join('')}
      ${DROP(452, 335, 'into')}${DROP(492, 272, 'into d2')}`, '2')}${L(420, 236, 'root hairs', 'ಬೇರುಕೂದಲು')}</g>
    <g data-b="3-5" class="xylem"><path d="M330 260 L330 112"/></g>
    <g data-b="3">${L(345, 236, 'up the stem, like a straw', 'ಸ್ಟ್ರಾದಂತೆ ಕಾಂಡದ ಮೇಲೆ')}</g>
    <g data-b="4-5" class="leaf-veins"><path d="M330 190 L248 196"/><path d="M330 150 L420 140"/></g>
    <g data-b="4">${L(400, 190, 'veins carry water', 'ನರಗಳು ನೀರು ಒಯ್ಯುತ್ತವೆ')}</g>
    <g data-b="5">${[0, 1, 2].map((i) => `<path class="vapour v${i}" d="M${400 + i * 14} 130 q-8 -12 0 -24 t0 -24"/>`).join('')}
      ${L(360, 40, 'water vapour into the air', 'ನೀರಾವಿ ಗಾಳಿಗೆ')}</g>`,

  // ---------------------------------------------------------------- the leaf
  leaf: `<rect class="sky" width="600" height="360"/>
    <g class="leaf-whole">${BIG_LEAF(260, 190, 200)}<path class="petiole" d="M60 190 L20 200"/>${VEINS(260, 190, 200)}</g>
    <g data-b="1"><g class="rays"><path d="M520 20 L380 110"/><path d="M570 40 L420 140"/><path d="M590 90 L450 170"/></g>
      ${L(420, 330, 'thin, flat and wide', 'ತೆಳು, ಚಪ್ಪಟೆ, ಅಗಲ')}</g>
    <g data-b="2+" class="vein-hl">${VEINS(260, 190, 200)}${L(80, 330, 'veins', 'ನರಗಳು')}</g>
    <g data-b="3">${MAGNIFIER(470, 110, 80, `<rect x="380" y="20" width="180" height="180" class="leaf-under"/>
      ${[[430, 70], [500, 60], [460, 130], [520, 140], [410, 160]].map(([x, y]) => `<g class="stoma"><ellipse cx="${x}" cy="${y}" rx="13" ry="9" class="guard"/><ellipse cx="${x}" cy="${y}" rx="8" ry="2.5" class="pore"/></g>`).join('')}`, '3')}
      ${L(300, 330, 'stomata (under the leaf)', 'ಪತ್ರರಂಧ್ರಗಳು (ಎಲೆಯ ಕೆಳಗೆ)')}</g>
    <g data-b="4-5">${MAGNIFIER(470, 120, 90, `<rect x="370" y="20" width="200" height="200" class="cell-bg"/>${CELLS(370, 28, 4, 5, 50, 40, false)}<g data-b="5">${CELLS(370, 28, 4, 5, 50, 40, true)}</g>`, '4-5')}</g>
    ${L(300, 330, 'tiny cells', 'ಸಣ್ಣ ಜೀವಕೋಶಗಳು', '', '4')}
    ${L(300, 330, 'full of green chlorophyll', 'ಹಸಿರು ಪತ್ರಹರಿತ್ತು ತುಂಬಿದೆ', '', '5')}`,

  // ---------------------------------------------------------------- chlorophyll
  chlorophyll: `<rect class="micro" width="600" height="360"/>
    <g data-b="1-2"><rect class="cell big-cell" x="40" y="40" width="360" height="280" rx="40"/>
      <circle class="nucleus" cx="300" cy="230" r="34"/>
      <g class="chloroplasts" data-hl="2">${[[100, 100], [180, 80], [260, 100], [340, 110], [90, 200], [150, 270], [240, 290], [350, 290], [100, 300]].map(([x, y]) => `<ellipse class="chloroplast" cx="${x}" cy="${y}" rx="26" ry="15"/>`).join('')}</g>
      ${L(420, 80, 'a leaf cell', 'ಎಲೆಯ ಜೀವಕೋಶ', 'light', '1')}
      ${L(420, 80, 'chloroplasts', 'ಹರಿತ್ತಿಲುಗಳು', 'light', '2')}</g>
    <g data-b="3+"><ellipse class="chloroplast huge" cx="200" cy="190" rx="170" ry="100"/>
      ${[[110, 170], [170, 210], [230, 160], [290, 200], [150, 140]].map(([x, y]) => [0, 1, 2, 3].map((k) => `<ellipse class="thylakoid" cx="${x}" cy="${y - k * 8}" rx="24" ry="5"/>`).join('')).join('')}
      </g>${L(370, 60, 'chlorophyll = green colouring', 'ಪತ್ರಹರಿತ್ತು = ಹಸಿರು ಬಣ್ಣ', 'light', '3')}
    <g data-b="4">${SUN(540, 300, 30)}<g class="rays"><path d="M510 290 L340 220"/><path d="M520 270 L360 180"/></g>
      <g class="panel"><rect x="420" y="140" width="120" height="70" rx="4"/>${[0, 1, 2].map((i) => `<path d="M${450 + i * 30} 140 v70"/>`).join('')}<path d="M420 175 h120"/></g>
      ${L(410, 240, 'like a solar panel', 'ಸೌರ ಫಲಕದಂತೆ', 'light')}</g>
    <g data-b="5"><g class="spectrum">${[['#e53935', 0], ['#fb8c00', 1], ['#fdd835', 2], ['#43a047', 3], ['#1e88e5', 4], ['#5e35b1', 5]].map(([c, i]) => `<path stroke="${c}" class="${['red', '', '', 'green', 'blue', 'blue'][i]}" d="M600 ${110 + i * 8} L380 ${170 + i * 4}"/>`).join('')}</g>
      <path class="bounce" d="M380 186 L470 300"/><g class="eye"><ellipse cx="490" cy="320" rx="26" ry="14"/><circle cx="490" cy="320" r="8"/></g>
      ${L(20, 324, 'red + blue taken in, green bounced back', 'ಕೆಂಪು, ನೀಲಿ ಒಳಗೆ · ಹಸಿರು ಹಿಂದಕ್ಕೆ', 'light')}</g>`,

  // ---------------------------------------------------------------- carbon dioxide
  co2: `${SKY}
    <g data-b="1-2"><rect class="air-box" x="30" y="30" width="300" height="220" rx="20"/>
      ${[[70, 70, 'N₂', 'n2'], [140, 100, 'N₂', 'n2'], [230, 70, 'N₂', 'n2'], [290, 150, 'N₂', 'n2'], [90, 200, 'N₂', 'n2'], [180, 210, 'N₂', 'n2'], [110, 140, 'O₂', 'o2m'], [250, 200, 'O₂', 'o2m'], [200, 150, 'CO₂', 'co2m']].map(([x, y, t, c]) => `<g class="float">${MOL(x, y, t, c)}</g>`).join('')}
      ${L(40, 280, 'air: a mix of gases', 'ಗಾಳಿ: ಅನಿಲಗಳ ಮಿಶ್ರಣ', '', '1')}</g>
    <g data-b="2">${PERSON(450, 150)}<g class="breath-out">${MOL(400, 170, 'CO₂')}${MOL(380, 200, 'CO₂', 'co2m d2')}</g>
      ${L(380, 280, 'we breathe out CO₂', 'ನಾವು CO₂ ಹೊರಬಿಡುತ್ತೇವೆ')}</g>
    <g data-b="3" class="model"><circle class="atom o" cx="200" cy="170" r="40"/><circle class="atom c" cx="300" cy="170" r="46"/><circle class="atom o" cx="400" cy="170" r="40"/>
      <path class="bond" d="M240 162h14M240 178h14M346 162h14M346 178h14"/>
      <text class="atom-t" x="200" y="178">O</text><text class="atom-t" x="300" y="178">C</text><text class="atom-t" x="400" y="178">O</text>
      ${L(200, 270, 'one carbon + two oxygens = CO₂', 'ಒಂದು ಇಂಗಾಲ + ಎರಡು ಆಮ್ಲಜನಕ = CO₂')}</g>
    <g data-b="4-5"><path class="leaf big" d="M20 120 C160 40 440 40 580 120 L580 180 L20 180Z"/>
      <rect class="leaf-under" x="20" y="180" width="560" height="40"/>
      ${L(30, 254, 'under the leaf', 'ಎಲೆಯ ಕೆಳಭಾಗ', '', '4')}</g>
    <g data-b="4-5"><g class="stoma big ${''}"><ellipse class="guard l" cx="282" cy="200" rx="22" ry="34"/><ellipse class="guard r" cx="318" cy="200" rx="22" ry="34"/><ellipse class="pore-big" cx="300" cy="200" rx="5" ry="26"/></g></g>
    <g data-b="4">${MOL(300, 320, 'CO₂', 'co2m enter')}${MOL(300, 320, 'CO₂', 'co2m enter d2')}</g>
    <g data-b="5" class="daynight">${SUN(90, 300, 18)}<g class="moon-g"><circle class="moon" cx="510" cy="300" r="18"/></g>
      ${L(150, 296, 'day: open', 'ಹಗಲು: ತೆರೆದಿದೆ')}${L(370, 296, 'night: closed', 'ರಾತ್ರಿ: ಮುಚ್ಚಿದೆ')}${L(210, 50, 'guard cells', 'ಕಾವಲು ಜೀವಕೋಶಗಳು')}</g>`,

  // ---------------------------------------------------------------- making food
  food: `<rect class="micro" width="600" height="360"/>
    <ellipse class="chloroplast huge" cx="300" cy="190" rx="220" ry="130"/>${STACKS([[170, 150], [230, 260], [420, 140], [440, 250], [330, 110]])}
    ${L(230, 340, 'inside a chloroplast', 'ಹರಿತ್ತಿಲಿನ ಒಳಗೆ', 'light small')}
    <g data-b="1"><g class="rays"><path d="M40 30 L200 120"/></g>${MOL(40, 300, 'H₂O', 'h2o', 22)}${MOL(560, 300, 'CO₂', 'co2m', 22)}
      <path class="in-arrow" d="M60 290 L170 230"/><path class="in-arrow" d="M540 290 L430 230"/>
      ${L(20, 24, 'light', 'ಬೆಳಕು', 'light')}${L(20, 350, 'water', 'ನೀರು', 'light small')}${L(500, 350, 'CO₂', '', 'light small')}</g>
    <g data-b="2" class="split"><g class="h-part">${MOL(230, 180, 'H', 'h', 22)}${MOL(260, 205, 'H', 'h', 22)}</g><g class="o-part">${MOL(330, 170, 'O', 'o2m', 22)}</g>
      <path class="zap" d="M290 120 l-10 30 h16 l-12 30"/>${L(180, 270, 'light splits water', 'ಬೆಳಕು ನೀರನ್ನು ಒಡೆಯುತ್ತದೆ', 'light')}</g>
    <g data-b="3" class="join">${MOL(220, 190, 'H', 'h', 22)}<path class="in-arrow" d="M240 190 L270 190"/>
      <polygon class="glucose" points="330,140 372,164 372,212 330,236 288,212 288,164"/><text class="glu-t" x="330" y="194">C₆H₁₂O₆</text>
      ${MOL(440, 190, 'CO₂', 'co2m', 22)}<path class="in-arrow" d="M420 190 L380 190"/>${L(240, 280, 'sugar (glucose)', 'ಸಕ್ಕರೆ (ಗ್ಲೂಕೋಸ್)', 'light')}</g>
    <g data-b="4" class="sugar-flow">${[0, 1, 2, 3].map((i) => `<rect class="cube q${i}" x="290" y="180" width="16" height="16" rx="3"/>`).join('')}
      <path class="vein-out" d="M300 190 L560 190"/>${L(360, 160, 'food goes to every part', 'ಆಹಾರ ಎಲ್ಲಾ ಭಾಗಗಳಿಗೆ', 'light')}</g>
    <g data-b="5" class="equation"><rect x="20" y="20" width="560" height="80" rx="14"/>
      <text x="300" y="56">☀ light + water + CO₂  →  sugar + oxygen</text>
      <text class="kn" x="300" y="84">ಬೆಳಕು + ನೀರು + ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್ → ಸಕ್ಕರೆ + ಆಮ್ಲಜನಕ</text></g>`,

  // ---------------------------------------------------------------- oxygen
  oxygen: `${SKY}${GROUND(290)}
    <g data-b="1"><ellipse class="chloroplast" cx="300" cy="170" rx="160" ry="90"/>${MOL(260, 170, 'H', 'h', 18)}${MOL(290, 200, 'H', 'h', 18)}
      <g class="o-free">${MOL(340, 160, 'O₂', 'o2m', 18)}</g>${L(200, 300, 'oxygen is left over', 'ಆಮ್ಲಜನಕ ಉಳಿಯುತ್ತದೆ')}</g>
    <g data-b="2"><path class="leaf big" d="M20 120 C160 40 440 40 580 120 L580 180 L20 180Z"/><rect class="leaf-under" x="20" y="180" width="560" height="40"/>
      <g class="stoma big"><ellipse class="guard l" cx="282" cy="200" rx="22" ry="34"/><ellipse class="guard r" cx="318" cy="200" rx="22" ry="34"/></g>
      <g class="o2-out">${MOL(300, 210, 'O₂', 'o2m', 18)}</g><g class="o2-out d2">${MOL(300, 210, 'O₂', 'o2m', 18)}</g>
      ${L(200, 300, 'out through the stomata', 'ಪತ್ರರಂಧ್ರಗಳ ಮೂಲಕ ಹೊರಗೆ')}</g>
    <g data-b="3-4">${plant(140, 290, 0.9)}${PERSON(460, 200)}</g>
    <g data-b="3"><g class="to-person">${MOL(220, 140, 'O₂', 'o2m', 18)}</g><g class="to-person d2">${MOL(220, 140, 'O₂', 'o2m', 18)}</g>
      ${L(330, 60, 'we breathe in oxygen', 'ನಾವು ಆಮ್ಲಜನಕ ಉಸಿರಾಡುತ್ತೇವೆ')}</g>
    <g data-b="4"><path class="cycle top" d="M210 120 C280 50 380 50 440 150"/><path class="cycle bottom" d="M440 270 C380 330 260 330 210 250"/>
      ${L(270, 50, 'O₂ →', 'ಆಮ್ಲಜನಕ')}${L(270, 340, '← CO₂', 'ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್')}</g>
    <g data-b="5">${plant(120, 290, 0.8)}<rect class="sea" x="300" y="220" width="300" height="140"/>
      <path class="waves" d="M300 220 q20 -10 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0"/>
      ${[[350, 280], [420, 310], [500, 270], [550, 320]].map(([x, y]) => `<circle class="algae" cx="${x}" cy="${y}" r="6"/>`).join('')}
      <g class="o2-up">${MOL(120, 120, 'O₂', 'o2m', 18)}${MOL(460, 200, 'O₂', 'o2m d2', 18)}</g>
      ${L(250, 40, 'plants on land + tiny plants in the sea', 'ನೆಲದ ಸಸ್ಯ + ಸಮುದ್ರದ ಸೂಕ್ಷ್ಮ ಸಸ್ಯ')}</g>`,

  // ---------------------------------------------------------------- growing
  growth: `${SKY}${GROUND()}
    <g class="growing">${plant(300, 280, 1)}</g>
    <g data-b="1"><rect class="cube" x="330" y="150" width="16" height="16" rx="3"/><path class="zap" d="M360 120 l-10 24 h14 l-10 24"/>
      ${L(380, 140, 'sugar → energy', 'ಸಕ್ಕರೆ → ಶಕ್ತಿ')}</g>
    <g data-b="2-4" class="new-parts"><path class="leaf new" d="M300 236 C270 222 250 228 242 244 C262 254 284 250 300 236Z"/>
      <path class="leaf new" d="M300 160 C330 136 356 140 364 156 C342 172 318 172 300 160Z"/>
      <path class="root-new" d="M300 280 C320 310 350 326 380 340"/></g>
    <g data-b="2">${L(400, 230, 'new leaves, stem, roots', 'ಹೊಸ ಎಲೆ, ಕಾಂಡ, ಬೇರು')}</g>
    <g data-b="3-4" class="stores"><g class="potato"><ellipse cx="90" cy="320" rx="34" ry="22"/></g>
      <g class="rice">${[0, 1, 2, 3, 4].map((i) => `<ellipse cx="${460 + i * 12}" cy="${90 + (i % 2) * 6}" rx="5" ry="9"/>`).join('')}</g>
      <path class="banana" d="M470 170 c30 40 80 40 100 0 c-20 22 -70 22 -100 0z"/>
      ${L(30, 270, 'potato: starch store', 'ಆಲೂಗಡ್ಡೆ: ಪಿಷ್ಟ ಸಂಗ್ರಹ', 'small')}${L(440, 60, 'rice', 'ಅಕ್ಕಿ', 'small')}${L(470, 220, 'banana', 'ಬಾಳೆಹಣ್ಣು', 'small')}</g>
    <g data-b="4">${PERSON(170, 150)}<path class="zap" d="M220 140 l-10 24 h14 l-10 24"/>${L(30, 120, 'we eat it → energy', 'ನಾವು ತಿನ್ನುತ್ತೇವೆ → ಶಕ್ತಿ')}</g>`,

  // ---------------------------------------------------------------- recap
  recap: `${SKY}${GROUND()}${SUN(80, 64, 30)}
    ${plant(300, 280, 1)}
    <g class="rays"><path d="M112 82 L240 180"/><path d="M116 66 L300 140"/></g>
    ${DROP(300, 330, 'rise')}${DROP(300, 330, 'rise d2')}
    ${MOL(540, 140, 'CO₂', 'co2m drift-in')}<g class="o2-up">${MOL(380, 120, 'O₂', 'o2m')}</g>
    <g class="equation small"><rect x="150" y="10" width="440" height="60" rx="12"/>
      <text x="370" y="36">light + water + CO₂  →  sugar + oxygen</text>
      <text class="kn" x="370" y="58">ಬೆಳಕು + ನೀರು + CO₂ → ಸಕ್ಕರೆ + ಆಮ್ಲಜನಕ</text></g>`,
};

SCENES.terms = SCENES.recap;

export function showScene(svg, id) {
  if (svg.dataset.scene === id) return;
  svg.dataset.scene = id;
  svg.innerHTML = SCENES[id] || SCENES.recap;
}

// Show step n of the scene (1-based).
export function setBeat(svg, n) {
  svg.dataset.beat = n;
  for (const el of svg.querySelectorAll('[data-b]')) {
    const spec = el.dataset.b;
    const [a, b] = spec.split('-').map((x) => parseInt(x, 10));
    const last = spec.endsWith('+') ? Infinity : (b || a);
    el.classList.toggle('on', n >= a && n <= last);
  }
  for (const el of svg.querySelectorAll('[data-hl]')) el.classList.toggle('hl', Number(el.dataset.hl) === n);
}

// ---------- example galleries ----------
// A step can show examples instead of the chapter picture (lesson: beat.gallery):
//   {"title": "...", "kn_title": "...", "cards": [{"icon": "tree", "en": "Tree", "kn": "ಮರ", "mark": "yes"|"no", "note": "..."}]}
// Cards appear one after another; "yes"/"no" marks answer "is this a ...?".
import { ICONS } from './icons.js?v=3';

const esc = (t) => String(t ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

export function showGallery(svg, key, g) {
  if (svg.dataset.scene === key) return;
  svg.dataset.scene = key;
  const cards = g.cards || [];
  const perRow = cards.length <= 3 ? cards.length : Math.ceil(cards.length / 2);
  const rows = Math.ceil(cards.length / perRow);
  const top = g.title ? 52 : 12;
  const gap = 12, w = (600 - gap * (perRow + 1)) / perRow, h = (360 - top - gap * (rows + 1)) / rows;
  const hasNote = cards.some((c) => c.note);
  const icon = Math.min(w - 20, h - (hasNote ? 64 : 50));
  let out = `<rect class="gallery-bg" width="600" height="360"/>`;
  if (g.title) out += `<text class="gallery-title" x="300" y="26">${esc(g.title)}</text><text class="gallery-title kn" x="300" y="45">${esc(g.kn_title)}</text>`;
  cards.forEach((c, i) => {
    const x = gap + (i % perRow) * (w + gap), y = top + gap + Math.floor(i / perRow) * (h + gap);
    const ix = x + (w - icon) / 2, iy = y + 8;
    out += `<g class="card ${c.mark ? 'mark-' + c.mark : ''}" style="animation-delay:${0.35 * i}s">
      <rect class="card-bg" x="${x}" y="${y}" width="${w}" height="${h}" rx="12"/>
      <svg x="${ix}" y="${iy}" width="${icon}" height="${icon}" viewBox="0 0 100 100">${ICONS[c.icon] || ''}</svg>
      <text class="card-en" x="${x + w / 2}" y="${iy + icon + 16}">${esc(c.en)}</text>
      <text class="card-kn" x="${x + w / 2}" y="${iy + icon + 32}">${esc(c.kn)}</text>
      ${c.mark ? `<g class="badge"><circle cx="${x + w - 18}" cy="${y + 18}" r="14"/><text x="${x + w - 18}" y="${y + 24}">${c.mark === 'yes' ? '✓' : '✗'}</text></g>` : ''}
      ${c.note ? `<text class="card-note" x="${x + w / 2}" y="${iy + icon + 46}">${esc(c.note)}</text>` : ''}
    </g>`;
  });
  svg.innerHTML = out;
}
