import {accepted, clearance, planRoute} from './mission-planner.js?v=mission-1';

/** Read the same frozen observation and registered footprints as the planner.
 * A projected clearance warning is not a physical collision certificate.
 */
export function compareRoutes(mission, selected, start = mission.start, chosenPlan = null) {
  const {grid, observation_state: observed, known_nogo: forbidden} = mission;
  const candidates = mission.candidates.filter(c => selected.includes(c.task_id) && accepted(c, mission.thresholds));
  const visible = Uint8Array.from(observed, value => value === 1 ? 1 : 0);
  const added = new Uint8Array(observed.length);
  for (const candidate of candidates) {
    for (let i = 0; i < added.length; i++) {
      if (candidate.footprint[i] && !visible[i] && !forbidden[i]) added[i] = 1;
    }
  }
  const validIds = candidates.map(c => c.task_id);
  const visiblePlan = chosenPlan?.policy === 'optimistic' ? chosenPlan : planRoute(mission, validIds, 'optimistic', start);
  const hypothesisPlan = chosenPlan?.policy === 'imagination' ? chosenPlan : planRoute(mission, validIds, 'imagination', start);
  const distances = clearance(added, grid);
  const required = visiblePlan.clearance?.drive ?? grid.r_drive + (mission.control_allowance ?? .07);
  let exposure = null;
  for (let k = 1; k < (visiblePlan.path?.length || 0); k++) {
    const a = visiblePlan.path[k - 1], b = visiblePlan.path[k];
    const steps = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / .025));
    for (let j = 0; j <= steps; j++) {
      const t = j / steps, point = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
      const x = Math.floor((point[0] - grid.x0) / grid.res), y = Math.floor((point[1] - grid.y0) / grid.res);
      if (x < 0 || y < 0 || x >= grid.nx || y >= grid.ny) continue;
      const distance = distances[x * grid.ny + y];
      if (!exposure || distance < exposure.distance) exposure = {point, distance, required, margin: distance - required};
    }
  }
  const targets = ['T1', 'T2'].flatMap(target => {
    const cells = new Set();
    for (const c of candidates.filter(c => c.target === target)) c.footprint.forEach((value, i) => { if (value) cells.add(i); });
    if (!cells.size) return [];
    let x = 0, y = 0;
    for (const i of cells) { x += grid.x0 + (Math.floor(i / grid.ny) + .5) * grid.res; y += grid.y0 + (i % grid.ny + .5) * grid.res; }
    return [{target, point: [x / cells.size, y / cells.size]}];
  });
  return {start: [...start], selected: validIds, visible, added, visiblePlan, hypothesisPlan, exposure, targets};
}

export function physicalCollision(result) {
  return !!(result.contact?.high || result.contact?.wall || result.contact?.gateBody);
}

export function routeInsight(comparison, policy, proof = null) {
  if (!comparison) return '选择形状假设，看它占据通道的哪一部分。';
  if (proof?.policy === policy) {
    if (proof.passed) return `${proof.results.length} 个候选世界完整预演通过；${policy === 'imagination' ? '绿线给所选背面留出空间' : '灰线在这组假设中通过'}，可以按这条路线出发。`;
    const collisions = proof.results.filter(physicalCollision).length;
    return collisions ? `${policy === 'optimistic' ? '灰线' : '这条路线'}在 ${collisions} 个候选世界中预演碰撞；换个走法，再判断。` : '这条路线未完成全部候选世界的预演，先停下，再选走法。';
  }
  if (!comparison.hypothesisPlan.path) return '所选假设下没有足够宽的绕行路线；先停下，再换组假设。';
  if (comparison.exposure?.margin < 0) return '所选背面伸近灰线，规划余量不足；金线绕开新增占地。两条路线是否可行，由物理预演判断。';
  return '这组假设下，两条线均留出了规划余量；选好走法，再用完整物理预演核实。';
}

export function runRecap(result, mission) {
  const ids = result.routeSelected?.length ? result.routeSelected : result.selected;
  const choices = ['T1', 'T2'].map(target => {
    const tasks = ids.filter(id => mission.candidates.some(c => c.task_id === id && c.target === target));
    return `${target === 'T1' ? 'A' : 'B'}·${tasks.join('、') || '未选'}`;
  }).join(' / ');
  const viewed = (result.viewedTargets || []).map(target => target === 'T1' ? 'A' : 'B').join('、');
  const observation = viewed ? `从原观测出发，转看高石 ${viewed} 的模型` : '从高石的有限观测出发';
  const route = result.worlds ? '沿预演通过的路线绕行' : '自行判断并驾驶';
  return `${observation}，选 ${choices}，${result.previewedWorlds || 0} 个世界完成预演；${route}，亲手触发 ${result.actions} 次轮腿动作${result.completed ? '后抵达' : '，本次尚未抵达'}。`;
}
