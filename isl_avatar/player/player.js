// Photosynthesis lesson player.
//
// The lesson follows a fixed structure (lessons/photosynthesis.json): introduction, the big
// idea, six animated steps, key words, recap. Each section has a diagram scene, a caption with
// the important words highlighted, and an ISL slot.
//
// Safety and language rules
// - A section's ISL is ONE recording authored by a signer (the ISLRTC explanation today, an
//   interpreter's recording later) or nothing. While a step has no interpreter recording the
//   page says so; the avatar never strings dictionary signs together to fake a sentence.
// - Key words can be watched one at a time, only when the student taps them.
// - Only motion copied from real ISLRTC recordings that passed every technical check is played.
// - Until an interpreter verifies a sign, the page says "Draft".
// - Students never see the recorded videos; only ?review=1 shows them, for the interpreter.

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { showScene, setBeat, showGallery } from './scenes.js?v=5';
import { ICONS } from './icons.js?v=3';

const ROOT = '../';                       // registry paths are relative to the project root
// Always the current bake (the browser would otherwise keep an old copy without new signs).
const AVATAR_URL = ROOT + 'avatar/avatar.glb?t=' + Date.now();
const LESSON_URL = 'lessons/photosynthesis.json';
const IDLE_CLIP = 'idle';                 // a real signer's neutral standing pose

const $ = (id) => document.getElementById(id);
const REVIEW = new URLSearchParams(location.search).get('review') === '1';
if (REVIEW) { $('review-banner').hidden = false; document.body.classList.add('review'); }

// ---------- 3D stage ----------

const canvas = $('avatar');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
const controls = new OrbitControls(camera, canvas);
controls.enablePan = false;

// Soft, even, front-weighted light: faces and hands must read clearly (facial grammar, handshapes).
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a86a0, 2.0));
const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(1, 2.5, 2.5);
scene.add(key);
const fill = new THREE.DirectionalLight(0xffffff, 1.0);
fill.position.set(-1.5, 1.5, 3);
scene.add(fill);
// Rim light from behind and above: a bright edge on fingers and arms so they separate from
// the dark T-shirt when the hands are in front of the body.
const rim = new THREE.DirectionalLight(0xfff4e8, 2.6);
rim.position.set(-1.2, 2.2, -2.5);
scene.add(rim);
const rim2 = new THREE.DirectionalLight(0xe8f0ff, 1.6);
rim2.position.set(1.4, 1.6, -2.2);
scene.add(rim2);

let mixer = null;
let clips = new Map();
let current = null;
let timing = {};                          // sign_id -> {start, end} seconds (clip_timing.json)
const clock = new THREE.Clock();
const SIGN_FADE = 0.28;                   // seconds, idle <-> sign, eased in and out

function resize() {
  const { clientWidth: w, clientHeight: h } = canvas;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  frameView();
}
window.addEventListener('resize', resize);
new ResizeObserver(() => resize()).observe(canvas);     // the stage follows the picture's height

// Crossfade with a smoothstep curve (three.js's own crossfade is linear: a visible start/stop).
let fading = null;
const smoothstep = (x) => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };

function updateFade(dt) {
  if (!fading) return;
  fading.t += dt;
  const w = smoothstep(fading.t / fading.duration);
  fading.to.setEffectiveWeight(w);
  if (fading.from) fading.from.setEffectiveWeight(1 - w);
  if (fading.t >= fading.duration) {
    if (fading.from && fading.from !== fading.to) fading.from.stop();
    fading = null;
  }
}

// ---------- voice (for hearing teachers only) ----------
// The lesson is for Deaf students: everything is in ISL signs, captions and pictures. A spoken
// voice (tools/make_narration.py) can be switched on for a hearing teacher; it is off by default.
// No lip-sync: removed 13 Nov 2026 (school feedback). Mouth shapes driven by a voice were not
// accurate and replaced the ISLRTC signer's own ISL mouth movements; the avatar keeps the signer's face.
const narrations = {};           // lang -> index.json
let narration = { audio: null };

async function loadNarrations() {
  for (const lang of ['kn', 'en']) {
    try {
      const r = await fetch(`audio/${lang}/index.json`, { cache: 'no-store' });
      if (r.ok) narrations[lang] = await r.json();
    } catch { /* not generated */ }
  }
  const select = $('narration');
  const names = { kn: 'ಕನ್ನಡ (Kannada)', en: 'English' };
  for (const lang of Object.keys(narrations)) {
    select.append(Object.assign(document.createElement('option'), { value: lang, textContent: names[lang] || lang }));
  }
  select.value = '';                                   // off by default
  const note = $('narration-note');
  if (lesson?.narration?.translation_status) {
    note.hidden = false;
    note.textContent = 'Kannada text: ' + lesson.narration.translation_status;
  }
}

function stopNarration() {
  if (narration.audio) narration.audio.pause();
  narration = { audio: null };
}

// Starts this section's narration; resolves with its length in ms (0 if none).
async function startNarration(id) {
  stopNarration();
  const lang = $('narration').value;
  const entry = lang && narrations[lang]?.sections[id];
  if (!entry) return 0;
  const audio = new Audio(`audio/${lang}/${entry.audio}`);
  audio.playbackRate = speed();
  audio.preservesPitch = true;
  narration = { audio };
  try { await audio.play(); } catch { narration = { audio: null }; return 0; }
  return (entry.duration * 1000) / speed();
}

function loop() {
  requestAnimationFrame(loop);
  const dt = clock.getDelta() * speed();
  if (mixer) {
    mixer.update(dt);
    updateFade(dt);
    // A sign stops at the end of its movement (the rest frames after it are skipped) and the
    // avatar eases back to idle.
    if (current && current.userData?.end !== undefined && current.time >= current.userData.end && !fading) playIdle();
  }
  controls.update();
  renderer.render(scene, camera);
}

let model = null;
async function loadAvatar() {
  try {
    const gltf = await new GLTFLoader().loadAsync(AVATAR_URL);
    model = gltf.scene;
    scene.add(model);
    mixer = new THREE.AnimationMixer(model);
    clips = new Map(gltf.animations.map((c) => [c.name, c]));
    playIdle();
    mixer.update(0);
    frameView();
  } catch (err) {
    console.warn('No avatar model:', err.message);
    $('no-model').hidden = false;
  }
}

function bonePosition(suffix) {
  let found = null;
  model.traverse((o) => { if (!found && o.isBone && o.name.endsWith(suffix)) found = o; });
  return found ? found.getWorldPosition(new THREE.Vector3()) : null;
}

// Framing measured on the ISLRTC videos (median over the signs): shoulders at 48% of the picture
// height from the top, hips at the bottom edge (99%). So the picture is (shoulder - hip) / 0.51
// tall, from just above the head down to the hips, which makes the hands as large as in the
// dictionary videos. Signing space: at least 1.6 shoulder widths each side of the middle.
// "Hands close-up" is tighter but keeps the whole face (facial grammar).
const ISLRTC = { shoulder: 0.48, hip: 0.99 };

function frameView() {
  if (!model) return;
  model.updateMatrixWorld(true);
  model.traverse((o) => { if (o.isSkinnedMesh) o.skeleton.update(); });
  const head = new THREE.Box3().setFromObject(model).max.y;
  const ls = bonePosition('LeftArm'), rs = bonePosition('RightArm');
  const lh = bonePosition('LeftUpLeg'), rh = bonePosition('RightUpLeg');
  if (!ls || !rs || !lh || !rh) return;
  const shoulder = (ls.y + rs.y) / 2, hip = (lh.y + rh.y) / 2;
  const shoulderWidth = ls.distanceTo(rs);
  const close = $('closeup').checked;
  let view, centreY;
  if (close) {
    const top = head + 0.04 * (head - hip), bottom = shoulder - 0.5 * (shoulder - hip);
    view = top - bottom;
    centreY = (top + bottom) / 2;
  } else {
    view = (shoulder - hip) / (ISLRTC.hip - ISLRTC.shoulder);
    centreY = shoulder - (0.5 - ISLRTC.shoulder) * view;          // shoulder sits 48% from the top
  }
  view = Math.max(view, (3.2 * shoulderWidth) / camera.aspect);
  const centre = new THREE.Vector3((ls.x + rs.x) / 2, centreY, (ls.z + rs.z) / 2);
  const distance = view / 2 / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  controls.target.copy(centre);
  camera.position.set(centre.x, centre.y, centre.z + distance);
  camera.near = distance / 50;
  camera.far = distance * 20;
  camera.updateProjectionMatrix();
  // For checking the framing: the shoulder width on screen as a fraction of the picture height
  // (ISLRTC videos: about 0.36).
  const a = ls.clone().project(camera), b = rs.clone().project(camera);
  window.ISL_FRAME = { shoulderWidthOfHeight: Math.abs(a.x - b.x) / 2 * camera.aspect };
}

function play(name, { once }) {
  if (!mixer || !clips.has(name)) return false;
  const action = mixer.clipAction(clips.get(name));
  const span = once ? timing[name] : undefined;
  action.reset();
  action.setLoop(once ? THREE.LoopOnce : THREE.LoopRepeat);
  action.clampWhenFinished = once;
  action.time = span ? span.start : 0;
  action.userData = span ? { end: span.end } : {};
  action.play();
  if (current && current !== action) {
    action.setEffectiveWeight(0);
    fading = { from: current, to: action, t: 0, duration: SIGN_FADE };
  } else {
    action.setEffectiveWeight(1);
  }
  current = action;
  return true;
}

function playIdle() {
  if (current && current.getClip().name === IDLE_CLIP) return;
  if (!play(IDLE_CLIP, { once: false }) && current) {
    current.stop();
    current = null;
  }
}

// Seconds the sign's movement lasts (without the skipped rest frames), at 1x.
function signSeconds(id) {
  const span = timing[id];
  return span ? span.end - span.start : clips.get(id).duration;
}

// ---------- signs ----------

const bySign = new Map();       // sign_id -> registry entry

// Real ISLRTC motion that passed extraction QC and retargeting. Not yet interpreter-verified = draft.
function canPlay(id) {
  const st = bySign.get(id)?.stages;
  return Boolean(id && clips.has(id) && st && st.motion_extraction_passed && st.retargeting_passed);
}

function isDraft(id) {
  return bySign.get(id)?.status !== 'VERIFIED';
}

function showReference(id) {
  if (!REVIEW) return;
  const sign = bySign.get(id);
  const video = $('ref-video');
  if (sign?.review_reference_video) {
    video.src = ROOT + sign.review_reference_video;
    $('ref-credit').textContent = `${sign.english_term}: ${sign.source.attribution}`;
    $('reference').hidden = false;
  }
}

const termName = (id) => (bySign.get(id)?.english_term || id).replace(/ \((Sign 2|Academic)\)$/, '');

// ---------- lesson ----------
// Each chapter (lessons/photosynthesis.json) is about one idea: the Sun, soil, water, the leaf,
// chlorophyll, carbon dioxide, oxygen ... It is played like a short teaching video:
//   1. the idea's ISLRTC sign, once, as a single word (shown with the word on screen);
//   2. the ISL explanation, if a real recording exists (never assembled from dictionary signs);
//   3. numbered steps: each step changes the animated picture (scenes.js), shows its caption in
//      English and Kannada, and shows word cards (word, meaning, picture). The step's main word is
//      signed by the avatar, on its own, with its card lit up; words without a checked ISLRTC
//      sign are shown as picture cards. (Voice narration only if a hearing teacher turns it on.)

let lesson = null;
let index = 0;                  // current section
let beat = 1;                   // current step in the section (1-based)
let run = 0;                    // bumping it cancels whatever is playing
let lastSign = null;            // for "Replay sign"

const speed = () => Number($('speed').value) || 1;
const wait = (ms, token) => new Promise((done) => setTimeout(() => done(token === run), ms));
const section = () => lesson.sections[index];
const beatsOf = (s) => s.beats?.length || 1;

// Caption text with the section's key words highlighted (no HTML from the lesson is trusted).
function setCaption(text, emphasis = []) {
  const el = $('lesson-caption');
  el.replaceChildren();
  const words = [...emphasis].sort((a, b) => b.length - a.length).map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  if (!words.length) { el.textContent = text; return; }
  const re = new RegExp(`\\b(${words.join('|')})\\b`, 'gi');
  let last = 0;
  for (const m of text.matchAll(re)) {
    el.append(text.slice(last, m.index));
    const mark = document.createElement('mark');
    mark.textContent = m[0];
    el.append(mark);
    last = m.index + m[0].length;
  }
  el.append(text.slice(last));
}

function renderNav() {
  const nav = $('section-nav');
  nav.replaceChildren(...lesson.sections.map((s, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = s.heading;
    if (s.kn_heading) b.title = s.kn_heading;
    if (i === index) b.setAttribute('aria-current', 'step');
    b.addEventListener('click', () => { stop(); index = i; beat = 1; render(); });
    return b;
  }));
}

function renderConcept(s, activeSign) {
  const box = $('concept');
  const c = s.concept;
  box.hidden = !c;
  if (!c) return;
  $('concept-term').textContent = c.term;
  $('concept-kn').textContent = c.kn || '';
  const btn = $('concept-sign');
  const ok = c.sign && canPlay(c.sign);
  btn.hidden = !ok;
  btn.classList.toggle('now', ok && activeSign === c.sign);
  btn.onclick = ok ? () => playOne(c.sign) : null;
  // Sign status and reasons are for the team (review mode); students just see the button or not.
  const why = $('concept-why');
  why.hidden = !REVIEW;
  why.textContent = ok
    ? (isDraft(c.sign) ? 'ISLRTC sign · draft, not yet checked by an interpreter' : 'ISLRTC sign · checked by an interpreter')
    : 'No checked ISL sign yet: ' + (c.why || 'no quality-checked recording.');
}

function islStatus(s) {
  const el = $('isl-status');
  el.hidden = !s.isl;
  if (!s.isl) return;
  if (!REVIEW) {                         // students: only a short line when a real ISL explanation plays
    el.hidden = !(s.isl.status === 'available' && canPlay(s.isl.sign));
    el.className = 'isl-status available';
    el.textContent = 'ISL explanation by ISLRTC (Indian Sign Language Research and Training Centre)';
    return;
  }
  if (s.isl.status === 'available' && canPlay(s.isl.sign)) {
    el.className = 'isl-status available';
    el.textContent = `ISL explanation by the ${s.isl.author}` + (s.isl.note ? ` (${s.isl.note})` : '') +
      (isDraft(s.isl.sign) ? '. Draft: not yet checked by an interpreter.' : '. Checked by an interpreter.');
  } else {
    el.className = 'isl-status awaiting';
    el.textContent = 'The ISL explanation of these steps is coming: an ISL interpreter will record it. ' +
      'Until then, watch the picture, read the captions and tap the signs.';
    if (REVIEW) el.textContent += ' [Team: what to record is in INTERPRETER_RECORDING_SHEET.md' +
      (s.isl.note ? '; ' + s.isl.note : '') + ']';
  }
}

// Words of the current step (or chapter): picture, word in English and Kannada, meaning, and
// the ISL sign when a checked ISLRTC recording exists (played on its own, one word at a time).
const wordsOf = (s) => s.beats?.[beat - 1]?.words || s.words || [];
const mainWord = (s) => wordsOf(s).find((w) => canPlay(lesson.glossary?.[w]?.sign));

function renderWords(s, activeSign) {
  const list = $('key-terms-list');
  list.replaceChildren();
  const words = wordsOf(s).filter((w) => lesson.glossary?.[w]);
  for (const id of words) {
    const g = lesson.glossary[id];
    const signed = canPlay(g.sign);
    const card = document.createElement('div');
    card.className = 'word-card' + (signed ? ' signed' : '') + (signed && g.sign === activeSign ? ' now' : '');
    card.innerHTML = `<svg viewBox="0 0 100 100" aria-hidden="true">${ICONS[g.icon] || ''}</svg>`;
    const text = document.createElement('div');
    text.className = 'word-text';
    for (const [cls, t, lang] of [['w-en', g.en], ['w-kn', g.kn, 'kn'], ['w-mean', g.meaning], ['w-mean-kn', g.meaning_kn, 'kn']]) {
      const el = document.createElement('span');
      el.className = cls;
      el.textContent = t;
      if (lang) el.lang = lang;
      text.append(el);
    }
    card.append(text);
    if (signed) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = '✋ Sign';
      b.setAttribute('aria-label', `Watch the ISL sign for ${g.en}`);
      b.addEventListener('click', () => playOne(g.sign));
      card.append(b);
    } else {
      const tag = document.createElement('small');
      tag.className = 'w-nosign';
      tag.textContent = 'no ISL sign yet';
      if (REVIEW) card.append(tag);
    }
    list.append(card);
  }
  list.classList.toggle('all', s.kind === 'key_terms');
  $('key-terms').hidden = !words.length;
  $('key-terms-label').textContent = s.kind === 'key_terms'
    ? 'All words · ✋ = watch the ISL sign'
    : 'Words';
}

function renderSteps(s) {
  const el = $('steps');
  const n = s.beats?.length || 0;
  el.hidden = n < 2;
  el.replaceChildren(...Array.from({ length: n }, (_, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = i + 1;
    b.setAttribute('aria-label', `Step ${i + 1}`);
    if (i + 1 === beat) b.setAttribute('aria-current', 'step');
    if (i + 1 < beat) b.className = 'done';
    b.addEventListener('click', () => { stop(); beat = i + 1; render(); });
    return b;
  }));
}

function render(activeSign = null) {
  const s = section();
  renderNav();
  const svg = $('diagram');
  const step = s.beats?.[beat - 1];
  if (step?.gallery) showGallery(svg, `${s.id}.${beat}`, step.gallery);   // examples
  else {
    showScene(svg, s.scene || 'recap');
    // The picture's own step number: example (gallery) steps do not count.
    setBeat(svg, s.beats ? s.beats.slice(0, beat).filter((b) => !b.gallery).length : 99);
  }
  $('lesson-part').textContent = `${s.heading}${s.kn_heading ? ' · ' + s.kn_heading : ''}`;
  setCaption(step ? step.text : s.caption, s.emphasis);
  const kn = $('lesson-caption-kn');
  const knText = step ? step.kn : (s.kn ? [s.kn.caption, ...(s.kn.points || [])].join(' ') : '');
  kn.textContent = knText;
  kn.hidden = !knText;
  const points = $('recap-points');
  points.replaceChildren(...(s.points || []).map((p) => Object.assign(document.createElement('li'), { textContent: p })));
  points.hidden = !s.points;
  renderConcept(s, activeSign);
  renderSteps(s);
  islStatus(s);
  renderWords(s, activeSign);
  $('lesson-prev').disabled = index === 0 && beat === 1;
  $('lesson-next').disabled = index === lesson.sections.length - 1 && beat >= beatsOf(s);
  $('replay').disabled = !lastSign;
}

async function performSign(id, token) {
  if (!canPlay(id)) return 0;               // no quality-checked ISLRTC motion: skip, never fake
  lastSign = id;
  render(id);
  showReference(id);
  play(id, { once: true });
  const ms = ((signSeconds(id) + SIGN_FADE) * 1000) / speed() + 200;
  if (!(await wait(ms, token))) return null;
  render();
  playIdle();
  return ms;
}

// One vocabulary sign, on request.
async function playOne(id) {
  const token = ++run;
  setPlaying(false);
  stopNarration();
  await performSign(id, token);
}

// Reading time for a caption: about 3.5 words a second at 1x, at least 4 seconds.
const readingMs = (text) => Math.max(4000, (text.split(/\s+/).length / 3.5) * 1000) / speed();

async function playSection(s, token, fromBeat) {
  if (fromBeat === 1) {
    // 1. The idea's sign, as one word.
    if (s.concept?.sign && canPlay(s.concept.sign)) {
      if ((await performSign(s.concept.sign, token)) === null) return false;
      if (!(await wait(500, token))) return false;
    }
    // 2. A real ISL explanation, when there is one (and it is not the same clip just shown).
    if (s.isl?.status === 'available' && s.isl.sign !== s.concept?.sign) {
      if ((await performSign(s.isl.sign, token)) === null) return false;
    }
  }
  if (!s.beats) {
    render();
    const spoken = await startNarration(s.id);
    if (token !== run) return false;
    const text = s.caption + ' ' + (s.points || []).join(' ');
    return wait(Math.max(readingMs(text), spoken + 400), token);
  }
  // 3. The steps.
  for (beat = fromBeat; beat <= s.beats.length; beat++) {
    render();
    const spoken = await startNarration(`${s.id}.${beat}`);
    if (token !== run) return false;
    // The step's main word in ISL, on its own (skipped when it is the sign just shown for the chapter).
    let signed = 0;
    const w = mainWord(s);
    const sign = w && lesson.glossary[w].sign;
    if (sign && !(beat === 1 && sign === s.concept?.sign)) {
      if (!(await wait(600, token))) return false;           // first the picture and caption
      signed = await performSign(sign, token);
      if (signed === null) return false;
      signed += 600;
    }
    if (!(await wait(Math.max(readingMs(s.beats[beat - 1].text) - signed, spoken + 700 - signed, 1500), token))) return false;
  }
  beat = s.beats.length;
  return true;
}

async function playFrom(start, fromBeat = 1) {
  const token = ++run;
  setPlaying(true);
  for (index = start; index < lesson.sections.length; index++) {
    if (!(await playSection(section(), token, index === start ? fromBeat : 1))) return;
    if (index < lesson.sections.length - 1) beat = 1;
  }
  index = lesson.sections.length - 1;
  render();
  setPlaying(false);
}

function setPlaying(on) {
  $('lesson-play').textContent = on ? '■ Stop' : '▶ Play';
  $('lesson-play').dataset.playing = on ? '1' : '';
}

function stop() {
  run++;
  setPlaying(false);
  stopNarration();
  playIdle();
}

function step(dir) {
  stop();
  const s = section();
  if (dir > 0) {
    if (beat < beatsOf(s)) beat++;
    else if (index < lesson.sections.length - 1) { index++; beat = 1; }
  } else if (beat > 1) beat--;
  else if (index > 0) { index--; beat = beatsOf(section()); }
  render();
}

$('lesson-play').addEventListener('click', () => {
  if ($('lesson-play').dataset.playing) return stop();
  const atEnd = index >= lesson.sections.length - 1 && beat >= beatsOf(section());
  playFrom(atEnd ? 0 : index, atEnd ? 1 : beat);
  if (atEnd) beat = 1;
});
$('lesson-prev').addEventListener('click', () => step(-1));
$('lesson-next').addEventListener('click', () => step(1));
$('replay').addEventListener('click', () => lastSign && playOne(lastSign));
$('captions').addEventListener('change', () => {
  $('lesson-caption').classList.toggle('off', !$('captions').checked);
  $('lesson-caption-kn').classList.toggle('off', !$('captions').checked);
});
$('narration').addEventListener('change', stopNarration);
$('closeup').addEventListener('change', frameView);
window.addEventListener('keydown', (e) => {
  if (e.target.closest('input, select, textarea')) return;
  if (e.key === 'ArrowRight') $('lesson-next').click();
  else if (e.key === 'ArrowLeft') $('lesson-prev').click();
  else if (e.key === ' ') { e.preventDefault(); $('lesson-play').click(); }
});

// ---------- start ----------

async function main() {
  resize();
  loop();
  await loadAvatar();
  try {
    const registry = await (await fetch('registry.json', { cache: 'no-store' })).json();
    registry.signs.forEach((s) => bySign.set(s.sign_id, s));
    lesson = await (await fetch(LESSON_URL, { cache: 'no-store' })).json();
    try { timing = await (await fetch('clip_timing.json', { cache: 'no-store' })).json(); } catch { timing = {}; }
  } catch {
    $('lesson-caption').textContent = 'Lesson data not found: run tools/check_registry.py';
    return;
  }
  $('lesson-title').textContent = lesson.title;
  $('lesson-note').textContent = lesson.language_rule;
  const used = lesson.sections.flatMap((s) => [s.isl?.sign, s.concept?.sign, ...(s.key_terms || []), ...(s.terms || []).map((x) => x.sign)])
    .concat(Object.values(lesson.glossary || {}).map((g) => g.sign))
    .filter(canPlay);
  $('draft-note').hidden = !used.some(isDraft);
  await loadNarrations();
  index = 0;
  beat = 1;
  render();
}

main();
