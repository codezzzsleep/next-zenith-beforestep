import {accepted} from './mission-planner.js?v=mission-1';

export const GAME_VERSION = 'playability-1';
export const RECORD_KEY = 'beforestep.playability.records.v1';
export const MODE_NAMES = Object.freeze({explore: '探索练习', challenge: '全程挑战'});
export const CHAPTERS = Object.freeze(['看见另一面', '绕过高石', '四腿接力', '稳稳到达']);
const LEG_NAMES = ['右前', '左前', '右后', '左后'];
const ACTION_NAMES = {lift: '抬起', advance: '前移', land: '落地'};
const ACTION_KEYS = {lift: 'J', advance: 'K', land: 'L'};
const finite = value => Number.isFinite(value) && value >= 0;

export function chapterFor(state, mission) {
  if (state.phase === 'complete') return 4;
  if (state.phase === 'finish-drive' || state.legs?.mode === 'complete') return 3;
  if (state.phase === 'crossing' || state.showcase?.completed && state.x >= mission.dock[0] - .18) return 2;
  return state.showcase?.completed ? 1 : 0;
}

export function nextObjective(state, mission) {
  if (state.phase === 'failed') return {title: '换个走法，再试一次。', hint: '探索练习可以从已保存的检查点继续。'};
  const chapter = chapterFor(state, mission);
  if (chapter === 4) return {title: '月面任务，完成！', hint: '看看本次获得的勘察印记，换组真实模型再挑战。'};
  if (chapter === 0) {
    if (state.showcase?.stage === 'braking') return {title: '第一站 · 停稳，看高石。', hint: '轮子正在制动；完整形状马上进入脑内。'};
    if (state.showcase?.active) return {
      title: '第一站 · 看见另一面。',
      hint: state.showcase.viewedTask ? '选脑内试路，或带着 3D 参考亲自开。' : '拖动模型或点“转看另一面”，让假设在脑中转一转。',
    };
    return {title: '第一站 · 驶向高石。', hint: 'WASD / 摇杆前进，到观察点看 Lux3D 的完整形状。'};
  }
  if (chapter === 1) return {
    title: '第二站 · 绕过两块高石。',
    hint: state.automatic ? '正在沿已试过的路线行驶；方向键 / 摇杆随时接管。' : 'Q 展开模型与试路；开到前方门槛整备点。',
  };
  if (chapter === 2) {
    const waiting = state.legs?.waiting;
    if (waiting) return {
      title: `第三站 · ${LEG_NAMES[waiting.leg]}腿${ACTION_NAMES[waiting.action]}。`,
      hint: `按 ${ACTION_KEYS[waiting.action]} 或下方高亮按钮 · ${Math.min(12, state.actionCount)} / 12 个主要动作`,
    };
    if (state.legs) return {title: '第三站 · 四腿接力。', hint: '支撑与重心调整中；下一动作就绪后由你触发。'};
    return {title: '第三站 · 轮子不够，用腿。', hint: '停稳、对正。先试轮行，或点“直接尝试迈腿”。'};
  }
  return {
    title: '最后一站 · 稳稳到达。',
    hint: state.legs ? '四腿已经过线，点“回到轮行”，再向目标圈前进。' : '驶入青绿色目标圈，停稳即可完成。',
  };
}

/** Facts are collected from the live worker and deliberate model interactions.
 * Game scores are separate from the frozen research and from the judges' scores.
 */
export class MissionRun {
  constructor(mode = 'explore') { this.reset(mode); }

  reset(mode = this.mode) {
    this.mode = mode === 'challenge' ? 'challenge' : 'explore';
    this.last = null;
    this.actionSeconds = 0;
    this.manualMeters = 0;
    this.maxTilt = 0;
    this.chapter = 0;
    this.actions = 0;
    this.checkpointUses = 0;
    this.viewedTargets = new Set();
    this.viewedTasks = new Set();
    this.pendingProof = null;
    this.usedProof = null;
    this.crossed = false;
    this.completed = false;
    this.ended = false;
    this.saved = false;
    this.selected = [];
    this.result = null;
  }

  selectionChanged(selected) {
    this.selected = [...selected];
    this.pendingProof = null;
  }

  modelViewed(candidate) {
    if (!candidate || !this.selected.includes(candidate.task_id)) return;
    this.viewedTargets.add(candidate.target);
    this.viewedTasks.add(candidate.task_id);
  }

  update(state, mission) {
    if (state.gameMode && state.gameMode !== this.mode) this.reset(state.gameMode);
    if (!this.ended && this.last && state.elapsed >= this.last.elapsed) {
      const dt = state.elapsed - this.last.elapsed;
      if (!state.paused && (state.speed > .018 || state.automatic || state.legs?.busy)) this.actionSeconds += dt;
      const distance = Math.hypot(state.x - this.last.x, state.y - this.last.y);
      if (!state.paused && !state.automatic && !state.legs && state.speed > .018 && distance < .5) this.manualMeters += distance;
    }
    if (!this.ended) this.maxTilt = Math.max(this.maxTilt, state.tilt || 0);
    this.actions = state.actionCount || 0;
    if (state.phase !== 'failed') this.chapter = Math.max(this.chapter, chapterFor(state, mission));
    this.last = {x: state.x, y: state.y, elapsed: state.elapsed};
  }

  event(message) {
    if (message.type === 'previewDone') this.pendingProof = message.passed ? {
      requestId: message.requestId,
      revision: message.revision,
      worlds: message.results.length,
      selected: [...message.selected],
    } : null;
    if (message.type === 'dreamClosed') this.pendingProof = null;
    if (message.type === 'routeStarted' && this.pendingProof &&
        message.requestId === this.pendingProof.requestId && message.revision === this.pendingProof.revision) {
      this.usedProof = {...this.pendingProof};
    }
    if (message.type === 'crossed') this.crossed = true;
    if (message.type === 'checkpointRestored') {
      this.checkpointUses++;
      this.last = null;
      this.pendingProof = null;
      this.ended = false;
      this.completed = false;
      this.result = null;
      this.saved = false;
    }
    if (message.type === 'resetDone') this.reset(message.gameMode || this.mode);
    if (message.type === 'missionComplete' || message.type === 'missionFailed') {
      this.completed = message.type === 'missionComplete' && message.state?.goalDistance < .35;
      this.ended = true;
      if (this.completed) { this.actions = message.actions; this.chapter = 4; }
      this.result = this.summary();
    }
  }

  summary() {
    const relayed = this.completed && this.crossed && this.actions >= 12;
    const informed = this.viewedTargets.has('T1') && this.viewedTargets.has('T2');
    const steady = this.completed && this.maxTilt <= 8;
    const usedModels = !!this.usedProof;
    const score = (this.completed ? 40 : 0) + (relayed ? 20 : 0) +
      (usedModels ? 20 : 0) + (informed ? 10 : 0) + (steady ? 10 : 0);
    const badges = [
      {id: 'beforestep', name: '先见一步', earned: this.completed && usedModels, note: '实际试路后沿认证路线出发'},
      {id: 'relay', name: '四腿接力', earned: relayed, note: '亲手完成四腿的 12 个主要动作'},
      {id: 'observer', name: '两面勘察', earned: informed, note: '转看高石 A 和 B 的已有原模型'},
      {id: 'steady', name: '稳稳到达', earned: steady, note: '抵达，且本轮最大车身倾角不超过 8°'},
      {id: 'pilot', name: '亲手领航', earned: this.completed && this.manualMeters >= 1, note: '实际手控行驶至少 1 m 并抵达'},
      {id: 'challenge', name: '一气呵成', earned: this.completed && this.mode === 'challenge' && !this.checkpointUses, note: '从头完成全程挑战'},
    ];
    return {
      version: GAME_VERSION, mode: this.mode, completed: this.completed, score,
      actionSeconds: Math.round(this.actionSeconds * 10) / 10,
      manualMeters: Math.round(this.manualMeters * 100) / 100,
      maxTilt: Math.round(this.maxTilt * 10) / 10,
      actions: this.actions, checkpointUses: this.checkpointUses,
      worlds: this.usedProof?.worlds || 0,
      selected: [...this.selected].sort((a, b) => a - b), badges,
    };
  }

  record(now = Date.now()) {
    if (!this.completed || this.saved) return null;
    this.saved = true;
    return {...this.summary(), createdAt: now};
  }
}

function validRecord(record) {
  return record && record.version === GAME_VERSION && record.completed === true &&
    Object.hasOwn(MODE_NAMES, record.mode) && finite(record.score) && record.score <= 100 &&
    finite(record.actionSeconds) && finite(record.checkpointUses) &&
    (record.mode !== 'challenge' || record.checkpointUses === 0) &&
    Array.isArray(record.selected) && record.selected.every(Number.isFinite);
}

export function readRecords(storage) {
  try {
    const records = JSON.parse(storage.getItem(RECORD_KEY) || '[]');
    return Array.isArray(records) ? records.filter(validRecord).slice(-40) : [];
  } catch { return []; }
}

export function saveRecord(storage, record) {
  if (!validRecord(record)) return {saved: false, records: readRecords(storage)};
  const records = [...readRecords(storage), record].slice(-40);
  try { storage.setItem(RECORD_KEY, JSON.stringify(records)); return {saved: true, records}; }
  catch { return {saved: false, records}; }
}

export function bestRecord(records, mode) {
  return records.filter(record => validRecord(record) && record.mode === mode)
    .sort((a, b) => b.score - a.score || a.actionSeconds - b.actionSeconds)[0] || null;
}

/** Only cycles archived admitted hypotheses; it does not change the scene. */
export function nextHypotheses(mission, selected) {
  const first = mission.candidates.filter(c => c.target === 'T1' && accepted(c, mission.thresholds));
  const second = mission.candidates.filter(c => c.target === 'T2' && accepted(c, mission.thresholds));
  const index = first.findIndex(c => selected.includes(c.task_id));
  const next = first[(index + 1) % first.length];
  return next ? [next.task_id, ...second.slice(0, 2).map(c => c.task_id)] : [...selected];
}
