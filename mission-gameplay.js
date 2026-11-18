import {MissionRun, MODE_NAMES, chapterFor, nextObjective, readRecords, saveRecord, bestRecord} from './mission-run.js?v=judges-demo-20261118-1';
import {runRecap} from './mission-insight.js?v=judges-demo-20261118-1';
import {accepted} from './mission-planner.js?v=judges-demo-20261118-1';

const $ = id => document.getElementById(id);
const BILIBILI = 'https://b23.tv/4CAPaLu';
const formatTime = seconds => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;

/** Small game layer over the existing worker: objectives, deliberate replay and
 * personal records. It never writes a robot pose or awards a route certificate.
 */
export class MissionGameplay {
  constructor({post, restart, retry, selected, stopInput, setObjective}) {
    this.post = post;
    this.restart = restart;
    this.retry = retry;
    this.getSelected = selected;
    this.stopInput = stopInput;
    this.setObjective = setObjective;
    this.initialMode = new URL(location.href).searchParams.get('mode') === 'challenge' ? 'challenge' : 'explore';
    this.run = new MissionRun(this.initialMode);
    this.mission = null;
    this.state = null;
    this.hudBottom = 175;
    try { this.storage = localStorage; } catch { this.storage = null; }
    this.records = readRecords(this.storage);
    this.recordStatus = '个人纪录只保存在这台设备上。';
    this.pauseBeforePanel = false;
    this.panelOpen = false;
    this.bind();
    new ResizeObserver(() => this.measureHud()).observe(document.querySelector('.hud-left'));
  }

  bind() {
    $('gameplay-open').onclick = () => this.togglePanel(!this.panelOpen);
    $('gameplay-close').onclick = () => this.togglePanel(false);
    for (const button of document.querySelectorAll('[data-game-mode]')) button.onclick = () => {
      this.closePanel(false);
      this.restart({mode: button.dataset.gameMode});
    };
    $('checkpoint-retry').onclick = $('result-checkpoint').onclick = () => {
      this.closePanel(false);
      this.retry();
    };
    $('new-hypotheses').onclick = $('result-hypotheses').onclick = () => {
      this.closePanel(false);
      this.restart({mode: this.run.mode, newHypotheses: true});
    };
    $('result-challenge').onclick = () => this.restart({mode: 'challenge'});
    $('copy-game-result').onclick = () => this.copyResult();
  }

  setMission(mission, selected) {
    this.mission = mission;
    this.run.selectionChanged(selected);
    $('gameplay-open').disabled = false;
    this.renderRecords();
  }

  measureHud() {
    const stage = $('main').getBoundingClientRect();
    this.hudBottom = document.querySelector('.hud-left').getBoundingClientRect().bottom - stage.top;
    $('main').style.setProperty('--mission-hud-bottom', `${Math.ceil(this.hudBottom + 9)}px`);
  }

  togglePanel(open) {
    if (!this.mission || this.state?.showcase.stage === 'braking') return;
    if (open) {
      this.stopInput();
      this.pauseBeforePanel = !!this.state?.paused;
      this.post({type: 'pause', value: true});
    } else if (this.panelOpen) this.post({type: 'pause', value: this.pauseBeforePanel});
    this.panelOpen = open;
    $('gameplay-panel').hidden = !open;
    $('gameplay-open').setAttribute('aria-expanded', String(open));
    if (open) $('gameplay-close').focus();
  }

  closePanel(resume = true) {
    if (resume) this.togglePanel(false);
    else {
      this.panelOpen = false;
      $('gameplay-panel').hidden = true;
      $('gameplay-open').setAttribute('aria-expanded', 'false');
    }
  }

  selectionChanged(selected) { this.run.selectionChanged(selected); }

  modelViewed(candidate) {
    if (!candidate || !accepted(candidate, this.mission.thresholds)) return;
    const already = this.run.viewedTargets.has(candidate.target);
    this.run.modelViewed(candidate);
    if (!already && this.run.viewedTargets.has(candidate.target)) this.toast(
      this.run.viewedTargets.size === 2 ? '获得勘察印记 · 两面勘察' : '高石 A 的完整形状已转看',
    );
  }

  onState(state) {
    if (!this.mission) return;
    this.state = state;
    this.run.update(state, this.mission);
    this.renderProgress();
    this.renderCheckpoint();
    if (!state.gameMode) return;
    document.documentElement.dataset.gameMode = state.gameMode;
  }

  onEvent(message) {
    this.run.event(message);
    if (message.type === 'resetDone') {
      this.run.selectionChanged(this.getSelected());
      $('result').hidden = true;
      this.recordStatus = '个人纪录只保存在这台设备上。';
    }
    if (message.type === 'checkpointSaved') this.toast(`检查点已保存 · ${message.checkpoint.label}`);
    if (message.type === 'checkpointRestored') {
      this.run.chapter = this.state ? chapterFor(this.state, this.mission) : 0;
      this.toast(`回到${message.checkpoint.label} · 换个走法继续`);
    }
    if (message.type === 'crossed') this.toast('四腿接力完成 · 最后一小段！');
    if (['missionComplete','missionFailed','missionStopped'].includes(message.type)) {
      const record = this.run.record();
      if (record) {
        const result = saveRecord(this.storage, record);
        this.records = result.records;
        this.recordStatus = result.saved ? '本次成绩已存入这台设备的个人纪录。' : '当前成绩可查看；此浏览器暂未保存个人纪录。';
      }
      this.renderResult();
      this.renderRecords();
    }
  }

  renderProgress() {
    if (!this.state || !this.mission) return;
    const state = this.state;
    const chapter = state.phase === 'failed' ? this.run.chapter : chapterFor(state, this.mission);
    const objective = nextObjective(state, this.mission);
    if(!this.storyMode){$('objective').textContent = objective.title;
      $('hint').textContent = state.phase === 'failed' && state.gameMode === 'challenge' ? '全程挑战从头再来；也可以切换探索练习。' : objective.hint;}
    $('game-mode-label').textContent = MODE_NAMES[this.run.mode];
    $('game-action-time').textContent = formatTime(this.run.actionSeconds);
    if(!this.storyMode)$('mission-route').querySelectorAll('li').forEach((node, index) => {
      node.classList.toggle('done', index < chapter);
      node.classList.toggle('current', index === chapter);
      node.setAttribute('aria-current', index === chapter ? 'step' : 'false');
    });
    for (const button of document.querySelectorAll('[data-game-mode]')) button.setAttribute('aria-pressed', String(button.dataset.gameMode === this.run.mode));
    const progress = chapter === 2 ? 2 + Math.min(this.state.actionCount / 12, .98) : chapter;
    if(!this.storyMode){$('mission-route').setAttribute('aria-label', `任务进度：已完成 ${Math.min(chapter, 4)} / 4 站`);
      $('mission-route').style.setProperty('--journey-progress', `${Math.min(100, progress * 25)}%`);}
    $('gameplay-open').disabled = state.showcase?.stage === 'braking';
    const target = chapter === 0 ? [this.mission.start[0] + .55, this.mission.start[1]] : chapter === 1 || chapter === 2 ? this.mission.dock : null;
    this.setObjective?.(state.legs || state.phase === 'failed' ? null : target);
    this.measureHud();
  }

  renderCheckpoint() {
    const checkpoint = this.state?.checkpoint;
    const available = this.run.mode === 'explore' && !!checkpoint;
    $('checkpoint-retry').disabled = !available;
    $('result-checkpoint').hidden = !available || this.run.completed;
    $('checkpoint-retry').textContent = checkpoint && available ? `回到${checkpoint.label}` : '回到检查点';
    $('result-checkpoint').textContent = checkpoint && available ? `从${checkpoint.label}继续` : '从检查点继续';
    $('checkpoint-note').textContent = this.run.mode === 'challenge' ? '全程挑战：从起点一次完成，重新开始会重置本轮成绩。' : checkpoint ? `${checkpoint.label}已保存。恢复后需要重新验证要用的路线。` : '驶到高石观察点并停稳后，保存第一个检查点。';
  }

  renderResult() {
    const result = this.run.result || this.run.summary();
    $('run-score').textContent = String(result.score);
    $('run-score-label').textContent = result.completed ? '局内成绩 / 100' : '本次已获得的积分';
    $('run-result-mode').textContent = MODE_NAMES[result.mode] + (result.checkpointUses ? ` · 检查点继续 ${result.checkpointUses} 次` : '');
    $('run-result-time').textContent = formatTime(result.actionSeconds);
    $('run-result-worlds').textContent = String(result.previewedWorlds);
    $('run-result-actions').textContent = `${result.actions} / 12`;
    $('run-result-tilt').textContent = `${result.maxTilt.toFixed(1)}°`;
    $('run-recap').textContent = runRecap(result, this.mission);
    const badges = $('run-badges');
    badges.replaceChildren();
    for (const badge of result.badges) {
      const node = document.createElement('span');
      node.className = 'run-badge' + (badge.earned ? ' earned' : '');
      node.textContent = (badge.earned ? '✦ ' : '○ ') + badge.name;
      node.title = badge.note;
      node.setAttribute('aria-label', `${badge.name}：${badge.earned ? '已获得' : '未获得'}，${badge.note}`);
      badges.append(node);
    }
    $('game-record-status').textContent = this.run.completed ? this.recordStatus : '这次实际结局已保留；停下与接触不计为抵达。';
    $('result-challenge').hidden = this.run.mode === 'challenge';
    $('copy-game-result').hidden = !result.completed;
    this.renderCheckpoint();
  }

  renderRecords() {
    const container = $('personal-records');
    container.replaceChildren();
    for (const mode of Object.keys(MODE_NAMES)) {
      const best = bestRecord(this.records, mode);
      const row = document.createElement('div');
      const name = document.createElement('strong');
      const value = document.createElement('span');
      name.textContent = MODE_NAMES[mode];
      value.textContent = best ? `${best.score} 分 · 行动 ${formatTime(best.actionSeconds)}` : '完成一轮后，留下你的第一条纪录';
      row.append(name, value);
      container.append(row);
    }
  }

  toast(text) {
    $('achievement-toast').textContent = text;
    $('achievement-toast').hidden = false;
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => { $('achievement-toast').hidden = true; }, 4000);
  }

  async copyResult() {
    const result = this.run.summary();
    if (!result.completed) return;
    const badges = result.badges.filter(b => b.earned).map(b => b.name).join(' / ');
    const text = `先见一步 · ${MODE_NAMES[result.mode]}\n局内成绩 ${result.score}/100 · 行动仿真 ${formatTime(result.actionSeconds)}\n${badges}\nMuJoCo 仿真游玩成绩，与原研究实验分开。\n来开机器狗：https://codezzzsleep.github.io/next-zenith-beforestep/play.html\nB站主宣传片：${BILIBILI}`;
    try {
      await navigator.clipboard.writeText(text);
      $('copy-game-result').textContent = '成绩已复制';
    } catch {
      $('copy-game-result').textContent = '复制未完成 · 可手动保存成绩';
    }
  }

  snapshot() { return {...this.run.summary(), chapter: this.run.chapter, recordCount: this.records.length}; }
}
