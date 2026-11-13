// 先见一步 BeforeStep — homepage behaviour.
// Every number and shape drawn here is read from home-assets/data/site.json and
// home-assets/data/exhibit.json, which dev/build_data.py and dev/build_exhibit.py
// assemble from the project's audited evidence files.

const C = {
  night: '#0a0b0c', soil: '#14171a', rule: '#2c3135', rock: '#5f5c56', rockEdge: '#8d897f',
  text: '#ece8e0', muted: '#9c9d99', lamp: '#f2a63b', ghost: '#8fa3b8', crash: '#e5533c',
};
const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (selector, root = document) => root.querySelector(selector);

const [data, exhibit] = await Promise.all(
  ['home-assets/data/site.json', 'home-assets/data/exhibit.json'].map((path) => fetch(path).then((response) => response.json())),
);

/* ---------- drawing helpers ---------- */

function fit(canvas, world) {
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Number(canvas.getAttribute('width'));
  const height = Number(canvas.getAttribute('height'));
  if (!canvas.dataset.sized) {
    canvas.dataset.sized = '1';
    canvas.dataset.w = width;
    canvas.dataset.h = height;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
  }
  const w = Number(canvas.dataset.w);
  const h = Number(canvas.dataset.h);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const scale = Math.min(w / (world.x1 - world.x0), h / (world.y1 - world.y0));
  const ox = (w - scale * (world.x1 - world.x0)) / 2;
  const oy = (h - scale * (world.y1 - world.y0)) / 2;
  const px = (x) => ox + (x - world.x0) * scale;
  const py = (y) => h - oy - (y - world.y0) * scale;
  return { ctx, w, h, scale, px, py };
}

function polygon(view, points) {
  const { ctx, px, py } = view;
  ctx.beginPath();
  points.forEach(([x, y], index) => (index ? ctx.lineTo(px(x), py(y)) : ctx.moveTo(px(x), py(y))));
  ctx.closePath();
}

// What the robot knew after its first look, one 5 cm cell at a time.
const SHADE = ['#262b30', '#262b30', '#000000', '#0d0f11', '#0d0f11'];
function drawKnowledge(view, world) {
  const { ctx, px, py, scale } = view;
  const state = data.look1_state;
  const size = scale * state.res;
  for (let i = 0; i < state.nx; i += 1) {
    const x = state.x0 + state.res * i;
    if (x < world.x0 - 0.05 || x > world.x1 + 0.05) continue;
    for (let j = 0; j < state.ny; j += 1) {
      const y = state.y0 + state.res * j;
      if (y < world.y0 - 0.05 || y > world.y1 + 0.05) continue;
      ctx.fillStyle = SHADE[state.cells.charCodeAt(i * state.ny + j) - 48];
      ctx.fillRect(px(x) - size / 2, py(y) - size / 2, size + 0.7, size + 0.7);
    }
  }
}

let hatchTile;
function hatch(ctx) {
  if (!hatchTile) {
    hatchTile = document.createElement('canvas');
    hatchTile.width = 9;
    hatchTile.height = 9;
    const tile = hatchTile.getContext('2d');
    tile.fillStyle = C.night;
    tile.fillRect(0, 0, 9, 9);
    tile.strokeStyle = '#1f2428';
    tile.beginPath();
    tile.moveTo(0, 9);
    tile.lineTo(9, 0);
    tile.stroke();
  }
  return ctx.createPattern(hatchTile, 'repeat');
}

function drawGround(view, world, labels = true, knowledge = false) {
  const { ctx, w, h, px, py, scale } = view;
  const scene = data.scene;
  ctx.fillStyle = C.soil;
  ctx.fillRect(0, 0, w, h);
  if (knowledge) drawKnowledge(view, world);

  // Rille on the +y side and the boulder pile on the -y side: both impassable.
  const edge = scene.rille_edge.filter(([x]) => x >= world.x0 - 0.5 && x <= world.x1 + 0.5);
  if (edge.length > 1) {
    ctx.beginPath();
    ctx.moveTo(px(edge[0][0]), py(world.y1 + 1));
    edge.forEach(([x, y]) => ctx.lineTo(px(x), py(y)));
    ctx.lineTo(px(edge[edge.length - 1][0]), py(world.y1 + 1));
    ctx.closePath();
    ctx.fillStyle = hatch(ctx);
    ctx.fill();
  }
  ctx.fillStyle = hatch(ctx);
  ctx.fillRect(0, py(scene.wall_y), w, h - py(scene.wall_y));

  scene.rocks.forEach((rock) => {
    polygon(view, rock.polygon);
    ctx.fillStyle = C.rock;
    ctx.fill();
    ctx.strokeStyle = C.rockEdge;
    ctx.lineWidth = 1;
    ctx.stroke();
    if (labels) {
      ctx.fillStyle = C.text;
      ctx.font = `700 ${Math.max(12, scale * 0.24)}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(rock.id, px(rock.x), py(rock.y));
    }
  });

  if (labels) {
    ctx.fillStyle = C.muted;
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText('月溪', px(world.x0) + 14, py(world.y1) + 22);
    ctx.fillText('大石堆', px(world.x0) + 14, h - 12);
    const [gx, gy] = scene.goal;
    ctx.strokeStyle = C.lamp;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(px(gx), py(gy), scale * 0.3, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = C.lamp;
    ctx.textAlign = 'center';
    ctx.fillText('终点', px(gx), py(gy) - scale * 0.42);
  }
}

function drawImagined(view, cells, alpha = 0.5) {
  const { ctx, px, py, scale } = view;
  ctx.fillStyle = C.ghost;
  ctx.globalAlpha = alpha;
  const size = scale * 0.05;
  cells.forEach(([x, y]) => ctx.fillRect(px(x) - size / 2, py(y) - size / 2, size + 0.5, size + 0.5));
  ctx.globalAlpha = 1;
}

function drawRun(view, run, progress = 1) {
  const { ctx, px, py, scale } = view;
  const path = run.traj;
  const last = Math.max(1, Math.round((path.length - 1) * progress));
  ctx.strokeStyle = C.text;
  ctx.lineWidth = 2;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  path.slice(0, last + 1).forEach(([x, y], index) => (index ? ctx.lineTo(px(x), py(y)) : ctx.moveTo(px(x), py(y))));
  ctx.stroke();

  const [x, y] = path[last];
  const [bx, by] = path[Math.max(0, last - 3)];
  const heading = Math.atan2(-(y - by), x - bx);
  const { half_len: halfLen, half_wid: halfWid } = data.scene.envelope;
  ctx.save();
  ctx.translate(px(x), py(y));
  ctx.rotate(heading);
  ctx.fillStyle = 'rgba(236,232,224,.16)';
  ctx.strokeStyle = C.text;
  ctx.lineWidth = 2;
  ctx.fillRect(-halfLen * scale, -halfWid * scale, halfLen * 2 * scale, halfWid * 2 * scale);
  ctx.strokeRect(-halfLen * scale, -halfWid * scale, halfLen * 2 * scale, halfWid * 2 * scale);
  ctx.beginPath();
  ctx.moveTo(halfLen * scale, 0);
  ctx.lineTo(halfLen * scale * 0.45, 0);
  ctx.stroke();
  ctx.restore();

  if (progress < 1) return;
  if (run.result === 'collision' && run.collision) {
    const [cx, cy] = run.collision.pos;
    const r = scale * 0.22;
    ctx.strokeStyle = C.crash;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(px(cx) - r, py(cy) - r); ctx.lineTo(px(cx) + r, py(cy) + r);
    ctx.moveTo(px(cx) + r, py(cy) - r); ctx.lineTo(px(cx) - r, py(cy) + r);
    ctx.stroke();
  }
  if (run.result === 'arrived') {
    const [gx, gy] = data.scene.goal;
    ctx.fillStyle = C.lamp;
    ctx.globalAlpha = 0.28;
    ctx.beginPath();
    ctx.arc(px(gx), py(gy), scale * 0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }
}

/* ---------- hero: flag the side the camera never saw ---------- */

const hero = $('#hero-rock');
const flag = $('#back-flag');
const FRONT_DEG = 15; // orbit angle at which the generated rock shows the photographed face
if (calm) hero.removeAttribute('auto-rotate');
document.querySelectorAll('.hero .turns button').forEach((button) => {
  button.addEventListener('click', () => {
    hero.removeAttribute('auto-rotate');
    hero.cameraOrbit = button.dataset.orbit;
  });
});
hero.addEventListener('camera-change', () => {
  const degrees = ((hero.getCameraOrbit().theta * 180) / Math.PI - FRONT_DEG) % 360;
  const away = Math.abs(((degrees + 540) % 360) - 180);
  flag.hidden = away < 105;
});

/* ---------- why: show where the camera measured nothing ---------- */

$('#dark-note').textContent = `标出来的是地面和石头上测不到距离的地方，占这一眼画面的 ${Math.round(data.dark_fraction_without_sky * 100)}%。天空没有算进去。`;
const darkToggle = $('#dark-toggle');
const darkLayer = $('#dark-layer');
let darkReady = false;
darkToggle.addEventListener('click', async () => {
  const on = darkToggle.getAttribute('aria-pressed') !== 'true';
  darkToggle.setAttribute('aria-pressed', String(on));
  darkToggle.textContent = on ? '收起标记' : '标出相机测不到的地方';
  $('#dark-note').hidden = !on;
  if (on && !darkReady) {
    const mask = new Image();
    mask.src = 'home-assets/img/first-view-dark.png';
    await mask.decode();
    const ctx = darkLayer.getContext('2d');
    ctx.drawImage(mask, 0, 0, darkLayer.width, darkLayer.height);
    const image = ctx.getImageData(0, 0, darkLayer.width, darkLayer.height);
    const pixels = image.data;
    for (let i = 0; i < pixels.length; i += 4) {
      const dark = pixels[i] > 127;
      pixels[i] = 143; pixels[i + 1] = 163; pixels[i + 2] = 184;
      pixels[i + 3] = dark ? 150 : 0;
    }
    ctx.putImageData(image, 0, 0);
    darkReady = true;
  }
  darkLayer.hidden = !on;
});

/* ---------- problem: three ways to drive the same lane ---------- */

const LANE = { x0: 0.5, x1: 11.4, y0: -2.05, y1: 2.25 };
const laneCanvas = $('#lane-map');
const intrusionCm = (data.audit.optimistic_intrusion_m * 100).toFixed(1);
const verdicts = {
  conservative: (run) => `看不见的地方，一律当成石头。看了 ${run.looks} 眼，还是规划不出路线，停下。`,
  optimistic: () => `看不见的地方，一律当成空地。撞上了 B 藏在黑影里的那一截。出发前的计划就已经压进石头 ${intrusionCm} 厘米。`,
  see_dark: (run) => `只多给它一样真实机器人拿不到的东西：黑影里的距离。看了 ${run.looks} 眼，到达。`,
};
let frame = 0;
function showLane(key, animate) {
  cancelAnimationFrame(frame);
  const run = data.runs[key];
  $('#lane-verdict').textContent = verdicts[key](run);
  const paint = (progress) => {
    const view = fit(laneCanvas, LANE);
    drawGround(view, LANE, true, true);
    drawRun(view, run, progress);
  };
  if (!animate || calm) { paint(1); return; }
  const started = performance.now();
  const tick = (now) => {
    const progress = Math.min(1, (now - started) / 2400);
    paint(progress);
    if (progress < 1) frame = requestAnimationFrame(tick);
  };
  frame = requestAnimationFrame(tick);
}
document.querySelectorAll('#problem .tabs button').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('#problem .tabs button').forEach((other) => other.setAttribute('aria-selected', String(other === button)));
    showLane(button.dataset.run, true);
  });
});
showLane('conservative', false);

/* ---------- core: every real Lux3D result, pick one and turn it ---------- */

const studio = $('#studio-rock');
const facts = $('#studio-facts');
const ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
const threshold = 0.7068;
function choose(candidate, button) {
  document.querySelectorAll('.pick').forEach((other) => other.setAttribute('aria-pressed', String(other === button)));
  studio.poster = candidate.poster;
  studio.src = candidate.glb;
  const verdict = candidate.admitted
    ? '<dd class="pass">通过检查，机器人会用它</dd>'
    : `<dd class="fail">被拒：轮廓吻合度低于 ${threshold}</dd>`;
  facts.innerHTML = `
    <dt>Lux3D 任务编号</dt><dd>${candidate.task_id}</dd>
    <dt>轮廓吻合度</dt><dd>${candidate.contour_iou}</dd>
    <dt>尺寸比</dt><dd>${candidate.scale_ratio}</dd>
    <dt>检查结论</dt>${verdict}`;
}
['A', 'B'].forEach((rock) => {
  const shelf = $(`#picks-${rock}`);
  ORDER.forEach((sample, index) => {
    const candidate = data.candidates.find((item) => item.rock === rock && item.sample === sample);
    if (!candidate) {
      const hole = document.createElement('div');
      hole.className = 'pick missing';
      hole.innerHTML = '<div class="hole">服务端失败<br>没有模型</div><span>第 ' + (index + 1) + ' 份</span>';
      shelf.append(hole);
      return;
    }
    const button = document.createElement('button');
    button.type = 'button';
    button.className = candidate.admitted ? 'pick' : 'pick rejected';
    button.setAttribute('aria-pressed', 'false');
    button.innerHTML = `<img src="${candidate.poster}" alt="石头 ${rock} 的第 ${index + 1} 份生成结果" loading="lazy" width="320" height="320">
      <span>第 ${index + 1} 份　${candidate.admitted ? '通过' : '轮廓对不上'}</span>`;
    button.addEventListener('click', () => choose(candidate, button));
    shelf.append(button);
    if (rock === 'A' && sample === 'C1') choose(candidate, button);
  });
});

/* ---------- wall: every real Lux3D call of the experiments, in the order it was made ---------- */

{
  const wall = exhibit.wall;
  const grid = $('#wall-grid');
  const read = $('#wall-read');
  const WORD = {
    p: ['good', '通过检查，机器人可以用它'],
    r: ['', '被检查拒掉。事后强行信了它再跑，车没有撞'],
    c: ['bad', '被检查拒掉。事后强行信了它再跑，车撞了'],
    n: ['', '被检查拒掉。没有做过强行信任的运行'],
    f: ['', 'Lux3D 没有返回模型'],
  };
  const stats = wall.stats;
  $('#w-calls').textContent = stats.calls;
  $('#w-models').textContent = stats.models;
  $('#w-passed').textContent = stats.passed;
  $('#w-rejected').textContent = stats.rejected;
  $('#w-crash').textContent = stats.rejected_would_crash;
  $('#w-failed').textContent = stats.failed;

  const cols = wall.sprite_cols;
  const rows = wall.sprite_rows;
  const tiles = document.createDocumentFragment();
  wall.tiles.forEach(([, state, position], index) => {
    const tile = document.createElement('span');
    tile.className = state;
    tile.dataset.i = index;
    if (position >= 0) {
      tile.style.setProperty('--x', `${((position % cols) / (cols - 1)) * 100}%`);
      tile.style.setProperty('--y', `${(Math.floor(position / cols) / (rows - 1)) * 100}%`);
    }
    tiles.append(tile);
  });
  grid.append(tiles);

  // The sprite is one 370 KB image; fetch it only when the wall is about to be seen.
  const sprite = new URL(wall.sprite, document.baseURI).href;
  new IntersectionObserver((entries, observer) => {
    if (!entries.some((entry) => entry.isIntersecting)) return;
    grid.style.setProperty('--sprite', `url("${sprite}")`);
    grid.classList.add('ready');
    observer.disconnect();
  }, { rootMargin: '900px 0px' }).observe(grid);

  let chosen = null;
  function tell(tile) {
    if (!tile || tile === chosen) return;
    if (chosen) chosen.classList.remove('on');
    chosen = tile;
    tile.classList.add('on');
    const index = Number(tile.dataset.i);
    const [taskId, state, , scene] = wall.tiles[index];
    const [tone, words] = WORD[state];
    read.innerHTML = `<b>第 ${index + 1} 次提交</b><b>任务 ${taskId}</b>${scene ? `<b>场景 ${scene}</b>` : ''}<br><span class="${tone}">${words}</span>`;
  }
  grid.addEventListener('pointerover', (event) => tell(event.target.closest('.wall span')));
  grid.addEventListener('click', (event) => tell(event.target.closest('.wall span')));

  document.querySelectorAll('.wall-filters button').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.wall-filters button').forEach((other) => other.setAttribute('aria-pressed', String(other === button)));
      grid.dataset.show = button.dataset.show;
    });
  });
}

/* ---------- trust: twelve imagined worlds, then the real drive ---------- */

const WORLD = { x0: 1.6, x1: 11.2, y0: -1.75, y1: 1.75 };
const worlds = $('#worlds');
data.rehearsals.forEach((rehearsal) => {
  const figure = document.createElement('figure');
  const canvas = document.createElement('canvas');
  canvas.width = 240;
  canvas.height = 96;
  const caption = document.createElement('figcaption');
  caption.textContent = `${rehearsal.label}　${rehearsal.completed && !rehearsal.collided ? '安全' : '未通过'}`;
  figure.append(canvas, caption);
  worlds.append(figure);
  const view = fit(canvas, WORLD);
  drawGround(view, WORLD, false);
  view.ctx.strokeStyle = C.ghost;
  view.ctx.lineWidth = 1.5;
  view.ctx.beginPath();
  rehearsal.traj.forEach(([x, y], index) => (index ? view.ctx.lineTo(view.px(x), view.py(y)) : view.ctx.moveTo(view.px(x), view.py(y))));
  view.ctx.stroke();
});

{
  const view = fit($('#go-map'), LANE);
  drawGround(view, LANE, true, true);
  drawImagined(view, data.imagined_union, 0.42);
  drawRun(view, data.runs.imagination, 1);
}

/* ---------- reveal: the imagined back against the real one ---------- */

const REVEAL = { x0: 5.75, x1: 8.2, y0: -0.85, y1: 1.3 };
const revealCanvas = $('#reveal-map');
const rockB = data.scene.rocks.find((rock) => rock.id === 'B');
const twin = $('#twin-rock');
const twinOf = Object.fromEntries(exhibit.overlays.anchor.map((overlay) => [overlay.sample, overlay]));
function wireViews(buttons, viewer) {
  buttons.querySelectorAll('button').forEach((button) => {
    button.addEventListener('click', () => { viewer.cameraOrbit = button.dataset.orbit; });
  });
}
wireViews($('#twin-views'), twin);
function showReveal(sample) {
  if (!twin.src.endsWith(twinOf[sample].glb)) twin.src = twinOf[sample].glb;
  const view = fit(revealCanvas, REVEAL);
  const { ctx, w, h, px, py } = view;
  ctx.fillStyle = C.soil;
  ctx.fillRect(0, 0, w, h);

  drawImagined(view, data.footprints_B[sample], 0.62);
  polygon(view, rockB.polygon);
  ctx.fillStyle = 'rgba(242,166,59,.10)';
  ctx.fill();
  ctx.strokeStyle = C.lamp;
  ctx.lineWidth = 2;
  ctx.stroke();

  const row = data.back_error_anchor.find((item) => item.target === 'T2' && item.candidate === sample);
  const imagined = row.predicted_farthest_m;
  const real = row.truth_farthest_m;
  const top = py(REVEAL.y1) + 46;
  const bottom = py(REVEAL.y0) - 30;
  ctx.setLineDash([5, 5]);
  ctx.lineWidth = 1.5;
  [[imagined, C.ghost], [real, C.lamp]].forEach(([x, colour]) => {
    ctx.strokeStyle = colour;
    ctx.beginPath();
    ctx.moveTo(px(x), top);
    ctx.lineTo(px(x), bottom);
    ctx.stroke();
  });
  ctx.setLineDash([]);
  ctx.strokeStyle = C.text;
  ctx.beginPath();
  ctx.moveTo(px(imagined), top + 14);
  ctx.lineTo(px(real), top + 14);
  ctx.stroke();
  ctx.fillStyle = C.text;
  ctx.font = '700 16px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(`背面短了 ${Math.abs(row.back_error_m).toFixed(2)} 米`, (px(imagined) + px(real)) / 2, top);

  ctx.fillStyle = C.muted;
  ctx.font = '13px sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('机器人从这一侧看过来', px(REVEAL.x0) + 14, h - 16);
  ctx.strokeStyle = C.muted;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(px(REVEAL.x0) + 150, h - 21);
  ctx.lineTo(px(REVEAL.x0) + 196, h - 21);
  ctx.lineTo(px(REVEAL.x0) + 190, h - 25);
  ctx.moveTo(px(REVEAL.x0) + 196, h - 21);
  ctx.lineTo(px(REVEAL.x0) + 190, h - 17);
  ctx.stroke();
}
document.querySelectorAll('#reveal .tabs button').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('#reveal .tabs button').forEach((other) => other.setAttribute('aria-selected', String(other === button)));
    showReveal(button.dataset.sample);
  });
});
const shortBy = (sample) => Math.abs(data.back_error_anchor.find((item) => item.target === 'T2' && item.candidate === sample).back_error_m).toFixed(2);
$('#short-a').textContent = shortBy('A2');
$('#short-c').textContent = shortBy('C1');
{
  const metres = (value) => Math.abs(value).toFixed(2);
  const { A2, C1 } = twinOf;
  $('#grid-a').textContent = metres(A2.back_error_grid_m);
  $('#grid-c').textContent = metres(C1.back_error_grid_m);
  $('#vert-a').textContent = metres(A2.back_error_vertices_m);
  $('#vert-c').textContent = metres(C1.back_error_vertices_m);
  $('#vert-gap').textContent = (Math.abs(A2.back_error_vertices_m - A2.back_error_grid_m) * 100).toFixed(1);
  $('#overlay-count').textContent = exhibit.overlays.all_overlays;
}
showReveal('A2');

/* ---------- results ---------- */

const ROWS = [
  ['conservative', '谨慎的车', ''],
  ['optimistic', '大胆的车', ''],
  ['imagination', '会想象的车', 'ours'],
  ['imagination_strict', '收紧规则之后', ''],
  ['see_dark', '黑影里能测距', ''],
];
const WORDS = { arrived: '到达', stuck: '停下', stopped_short: '停下', collision: '碰撞' };
const GLYPH = { arrived: '到', stuck: '停', stopped_short: '停', collision: '撞' };
const decisive = data.known.filter((scene) => scene.classification === 'decisive');
function group(title, scenes) {
  const lines = ROWS.map(([policy, name, tone]) => {
    const cells = scenes.map((scene) => {
      const outcome = scene.runs[policy];
      const result = outcome ? outcome.result : 'missing';
      return `<span class="cell ${result}" title="${WORDS[result] || '未运行'}">${GLYPH[result] || ''}</span>`;
    }).join('');
    return `<div class="line ${tone}"><span>${name}</span><span class="cells">${cells}</span></div>`;
  }).join('');
  return `<div class="group"><h3>${title}</h3>${lines}</div>`;
}
$('#score').innerHTML =
  group(`预先登记的 ${decisive.length} 个场景`, decisive) +
  group(`方法定稿后才第一次跑的 ${data.holdouts.length} 个场景`, data.holdouts);
$('#score').insertAdjacentHTML('afterend',
  '<p class="legend"><span><i class="arrived"></i>到达终点</span><span><i class="stuck"></i>安全停下</span><span><i class="collision"></i>碰撞</span><span>每一格是一个场景</span></p>');

const total = (policy, result) => [data.stats.known_decisive, data.stats.holdout]
  .reduce((sum, table) => sum + (table[policy][result] || 0), 0);
$('#n-arrive').textContent = total('imagination', 'arrived');
$('#n-crash').textContent = total('imagination', 'collision');
$('#n-strict').textContent = total('imagination_strict', 'arrived');
const cf = data.counterfactuals;
const cfRuns = cf.r2.executed + cf.r3.known_frozen.executed + cf.r3.designated_holdout.executed;
const cfCrashes = cf.r2.collisions + cf.r3.known_frozen.collisions + cf.r3.designated_holdout.collisions;
$('#n-cf-total').textContent = cfRuns;
{
  const { known_decisive: known, holdout } = data.stats;
  $('#n-known').textContent = decisive.length;
  $('#n-known-arrive').textContent = known.imagination.arrived;
  $('#n-known-crash').textContent = known.imagination.collision;
  $('#n-hold').textContent = data.holdouts.length;
  $('#n-hold-arrive').textContent = holdout.imagination.arrived;
  $('#n-hold-crash').textContent = holdout.imagination.collision;
  const forced = exhibit.wall.stats;
  if (forced.forced_runs !== cfRuns || forced.forced_run_crashes !== cfCrashes) {
    console.error('forced-trust counts differ between site.json and exhibit.json');
  }
  $('#n-cf-models').textContent = forced.rejected_forced_models;
  $('#n-cf-crash').textContent = forced.rejected_would_crash;
  $('#n-cf-never').textContent = forced.rejected_never_forced;
}

/* ---------- results: the three runs where the imagined back was too short ---------- */

{
  const viewer = $('#crash-rock');
  const tabs = $('#crash-tabs');
  const scenes = Object.fromEntries([...data.known, ...data.holdouts].map((scene) => [scene.scene, scene]));
  const heldOut = new Set(data.holdouts.map((scene) => scene.scene));
  const metres = (value) => Math.abs(value).toFixed(2);
  wireViews($('#crash-views'), viewer);
  function showCrash(item, button) {
    tabs.querySelectorAll('button').forEach((other) => other.setAttribute('aria-selected', String(other === button)));
    viewer.src = item.glb;
    const shorts = item.admitted_for_this_rock.map((sibling) => metres(sibling.back_error_grid_m));
    const same = shorts.every((value) => value === shorts[0]);
    const run = scenes[item.scene].runs.imagination;
    $('#crash-gap').textContent = metres(item.back_error_grid_m);
    $('#crash-text').textContent =
      `${heldOut.has(item.scene) ? '方法定稿后才第一次跑的场景' : '预先登记的场景'} ${item.scene_short}。` +
      `这块石头有 ${shorts.length} 份想象通过了检查，` +
      (same ? `背面都比真实的短 ${shorts[0]} 米。` : `背面分别短了 ${shorts.join('、')} 米，这里放的是伸得最远的那一份。`) +
      `机器人把它们叠在一起定路线，每一个想象世界里的预演都安全。真车开到第 ${run.sim_time_s.toFixed(1)} 秒，碰上了这块石头。`;
  }
  exhibit.overlays.crashes.forEach((item, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-selected', 'false');
    button.textContent = `场景 ${item.scene_short}`;
    button.addEventListener('click', () => showCrash(item, button));
    tabs.append(button);
    if (index === 0) showCrash(item, button);
  });
}
