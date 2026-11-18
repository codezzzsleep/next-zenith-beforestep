import {accepted, clearance, planRoute} from './mission-planner.js?v=judges-demo-20261118-1';

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

export function rehearsalReason(result) {
  if (result.reason==='completed'&&result.passed) return '完成 / 无碰撞';
  if (result.cancelled) return '已取消，未完成';
  if (result.contact?.high) return result.contact.measured?'接触新增实测表面':'碰撞候选高石';
  if (result.contact?.wall) return '碰撞侧壁';
  if (result.contact?.gateBody) return '车身接触矮坎';
  if (result.contact?.tilt>25) return '预演失去平衡';
  if (result.reason==='timeout') return '预演超时，路线未走完';
  if (result.reason==='no_route_with_required_clearance') return '没有满足净空的路线';
  return '预演未完成';
}

export function stopExplanation(reason) {
  return ({no_route_with_required_clearance:'当前观测和假设下没有满足净空的路线，选择停在这里。',
    no_valid_candidate_world:'当前选择没有有效候选组合，尚不能取得辅助出发许可。',
    candidate_world_contact:'这条路在候选世界中发生接触，选择暂缓出发。',
    candidate_world_incomplete:'候选世界的试路没有全部完成，选择暂缓出发。',
    player_chose_to_stop:'你主动停车，保留这次初判；可以回到检查点再试。'})[reason]||'已停稳；本次停车原因未记录。';
}

export function routeInsight(comparison, policy, proof = null) {
  if (!comparison) return '选择形状假设，看它占据通道的哪一部分。';
  if (proof?.policy === policy) {
    if (proof.passed) return `${proof.results.length} 个候选世界完整预演通过；${policy === 'imagination' ? '绿线给所选背面留出空间' : '灰线在这组假设中通过'}，可以按这条路线出发。`;
    const collisions = proof.results.filter(physicalCollision).length;
    return collisions ? `${policy === 'optimistic' ? '灰线' : '这条路线'}在 ${collisions} 个候选世界中预演碰撞；换个走法，再判断。` : `${rehearsalReason(proof.results.find(r=>!r.passed)||{})}；当前路线未获许可，可以换路、补看或停车。`;
  }
  if (!comparison.hypothesisPlan.path) return '所选假设下没有足够宽的绕行路线；先停下，再换组假设。';
  const margin=comparison.exposure?.margin;
  const estimate=Number.isFinite(margin)?`灰线贴近点的投影余量约 ${margin>=0?'+':''}${Math.round(margin*100)} cm（5 cm 栅格）。`:'没有可比较的贴近点。';
  if (margin < 0) return estimate+' 所选背面伸近灰线，金线绕开新增占地；是否会碰撞，交给物理预演判断。';
  const overlap=comparison.visiblePlan.path&&JSON.stringify(comparison.visiblePlan.path)===JSON.stringify(comparison.hypothesisPlan.path);
  return estimate+(overlap?' 两条路线重合。':' 这组假设下两条路线都留出了规划余量。')+' 选好走法，再用完整物理预演核实。';
}

export function runRecap(result, mission) {
  const events=result.decisions?.events||[],initial=result.decisions?.initial;
  const initialText=initial?.detail?.label||'未记录';
  const viewed=[...new Set(events.filter(e=>e.type==='modelViewed'||e.type==='inspectCandidate').map(e=>e.detail.taskId))];
  const models=viewed.length?viewed.join('、'):result.decisions?'未查看候选':result.viewedTasks?.join('、')||'未记录';
  const ids=result.routeSelected?.length?result.routeSelected:result.selected||[];
  const choices=['T1','T2'].map(target=>`${target==='T1'?'A':'B'}·${ids.filter(id=>mission.candidates.some(c=>c.task_id===id&&c.target===target)).join('、')||'未选'}`).join(' / ');
  const changed=events.filter(e=>e.type==='selectionChanged'&&e.sequence>(initial?.sequence??Infinity)).at(-1);
  const change=changed?`初判后选择${changed.detail.policy==='imagination'?'计入背面假设':changed.detail.policy==='optimistic'?'只按眼前所见':'保守停车'}的走法`:initial?'初判后未切换路线依据':'走法调整：未记录';
  const failure={high_rock_contact:'实际接触高石',wall_contact:'实际接触侧壁',gate_body_contact:'车身接触矮坎',lost_balance:'失去平衡',leg_error:'轮腿执行未完成',nonfinite_state:'物理状态无效'};
  const outcome=result.completed?'抵达并停稳':result.outcome==='stopped'?stopExplanation(result.stopReason):failure[result.outcome]||'未抵达';
  const execution=result.assistedMeters===undefined?'执行方式：未记录':`手控 ${(result.manualMeters||0).toFixed(1)} m / 辅助 ${result.assistedMeters.toFixed(1)} m`;
  return `初判：${initialText}；查看：${models}；${change}；执行选组 ${choices}；${result.previewedWorlds||0} 个候选世界完成预演；${execution}，${result.actions||0} 次轮腿动作；实际结局：${outcome}。`;
}
