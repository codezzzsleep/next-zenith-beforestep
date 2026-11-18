const $ = id => document.getElementById(id);

/** Teaches the observation -> local world -> prediction -> action sequence.
 * It controls presentation and existing pause commands, never robot poses.
 */
export class MissionStory {
  constructor({post, stopInput, activate, refresh, setPerception}) {
    Object.assign(this, {post, stopInput, activate, refresh, setPerception});
    this.ready = false;
    this.reset(true);
    $('begin-mission').onclick = () => this.begin();
    $('story-activate').onclick = () => this.activate();
  }
  reset(intro = false) {
    this.intro = intro; this.started = !intro; this.imagination = false;
    this.usedDrive = false; this.usedBrake = false; this.context = null;
    this.setPerception(true);
    $('mission-intro').hidden = !intro;
    $('story-coach').hidden = intro;
  }
  becomeReady() {
    this.ready = true;
    if (this.intro) this.post({type: 'pause', value: true});
    this.render();
  }
  begin() {
    if (!this.ready || !this.intro) return;
    this.stopInput(); this.intro = false; this.started = true;
    $('mission-intro').hidden = true;
    this.post({type: 'pause', value: false});
    $('world').focus(); this.refresh();
  }
  input(key) {
    if (['w', 'ArrowUp'].includes(key)) this.usedDrive = true;
    if (key === ' ') this.usedBrake = true;
  }
  openImagination() { this.imagination = true; }
  restore(state) {
    this.intro = false; this.started = true;
    this.imagination = !!state?.showcase?.completed;
    $('mission-intro').hidden = true;
  }
  update(context) { this.context = context; this.render(); }
  render() {
    const context = this.context, s = context?.state;
    const execute = !this.intro && !!s?.showcase.completed;
    this.fullWorld = execute;
    this.setPerception(!execute);
    document.body.classList.toggle('perception-mode', !execute);
    document.documentElement.dataset.storyPhase = this.intro ? 'mission-goal' : !s ? 'preparing' : s.phase==='complete'?'goal-reached':s.phase==='failed'?'failed':execute ? 'exploring' : context.busy?'forecasting':context.cert?.passed?'prediction-ready':this.imagination ? 'spatial-imagination' : 'observation-only';
    $('begin-mission').disabled = !this.ready;
    $('begin-mission').textContent = this.ready ? '进入机器人视野 · 开始探索' : '准备机器人…';
    $('mission-intro').hidden = !this.intro;
    $('story-coach').hidden = this.intro || !s || ['complete','failed'].includes(s.phase);
    $('pause').disabled = this.intro || !this.ready || s?.showcase.stage === 'braking';
    $('gameplay-open').disabled = this.intro || !this.ready || s?.showcase.stage === 'braking';
    $('help').disabled = this.intro;
    for (const b of document.querySelectorAll('button[data-view]')) b.disabled = this.intro || !execute && b.dataset.view !== '1';
    $('pip').disabled = this.intro || !execute;
    $('inset-label').hidden = !execute || !$('pip').getAttribute('aria-pressed')?.includes('true');
    $('perception-label').hidden = execute;
    $('perception-label').textContent = this.imagination ? '二维观测仍在眼前 · 三维空间假设在脑内' : '二维轮廓观测 · 尚未启用空间想象';
    $('unknown-key').lastChild.textContent = execute ? '空间假设留在脑中 · 当前月面实际执行' : ' 轮廓可见，后方占地未知 · 感知展示示意';
    for (const b of document.querySelectorAll('.guide-target')) b.classList.remove('guide-target');
    if (!s || this.intro) return;
    const modelSeen = !!s.showcase.viewedTask && context.selected.includes(s.showcase.viewedTask);
    const passed = !!context.cert?.passed && s.proof?.usable;
    const step = ['complete','failed'].includes(s.phase) ? s.phase==='complete'?4:execute?3:this.imagination?2:0 : execute?3:context.busy||modelSeen?2:this.imagination?1:0;
    const route=$('mission-route');
    route.querySelectorAll('li').forEach((node,index)=>{node.classList.toggle('done',index<step);node.classList.toggle('current',index===step);node.setAttribute('aria-current',index===step?'step':'false');});
    route.style.setProperty('--journey-progress',`${Math.min(100,step*25)}%`);
    route.setAttribute('aria-label','观测 → 局部空间想象 → 预测 → 探索');
    if(['complete','failed'].includes(s.phase)){
      $('objective').textContent=s.phase==='complete'?'空间预测支持探索，目标已抵达。':'行动未完成，回到局部世界再判断。';
      $('hint').textContent=s.phase==='complete'?'二维观测 → 空间想象 → 预测 → 实际探索。':'查看实际失败位置，换走法或假设，再预测一次。';
      return;
    }
    let title, copy, key, target;
    $('story-activate').hidden = true;
    $('story-controls').textContent = `${this.usedDrive ? '✓' : '①'} W / ↑ 前进 · ${this.usedBrake ? '✓' : '②'} 空格刹车 · E 观察 · Q 空间想象`;
    if (!execute) {
      if (s.showcase.stage === 'braking') {
        title = '到达观测点，先停稳'; copy = '眼前只有表面轮廓。背后占多少地、哪侧能通过，还没有足够信息判断。'; key = '等待轮子停稳';
      } else if (!s.showcase.active) {
        title = '你的目标：带 M20 抵达信标'; copy = '先按 W 前进，试一次空格刹车，再继续靠近高石。现在还没有补足未见空间的模型。'; key = !this.usedDrive ? '先按 W 或 ↑ 前进' : !this.usedBrake ? '松开前进键，按空格刹车停稳' : '操作已学会，继续前进到观测点'; target = 'world';
      } else if (!this.imagination) {
        title = '只见轮廓，还不能判断通道'; copy = '这是缺少空间想象模块时的感知示意：你看见了石头，却不知道背面如何延伸。让 Lux3D 预测局部空间，再决定下一步。'; key = '按 Q · 启用前额叶空间想象'; target = 'think'; $('story-activate').hidden = false;
      } else if (context.busy === 'route') {
        title = '在局部世界里，预测行动后果'; copy = `所选形状进入真实碰撞预演，已完成 ${context.results.length} / ${context.worlds} 个候选世界。机器人先在脑中走，当前月面机器人保持停稳。`; key = '观察路线是否能通过';
      } else if (passed) {
        title = '预测完成，可以开始探索'; copy = `${context.cert.results.length} 个候选世界都走通了。沿所选假设验证的路线出发，实际环境再检验这次判断。`; key = '按预测路线出发 · 随时用 WASD 接管'; target = 'execute';
      } else if (modelSeen) {
        title = '空间想象要用来做判断'; copy = '完整候选已经放进通道。对照它的占地和两条走法，再预测这条路线是否能通过。'; key = '点「预测这条路线」'; target = 'preview';
      } else {
        title = '前额叶 · 预测未见的局部空间'; copy = 'Lux3D 提出了可能的完整形状。转到背面，并看它放进通道后占了多少空间；这就是机器人新增的空间想象。'; key = '拖动模型，或点「看背面预测」'; target = 'model-back';
      }
      $('objective').textContent = title;
      $('hint').textContent = !s.showcase.active ? '仅观测 → 空间想象 → 预测路线 → 探索抵达' : key;
      $('think').disabled = this.intro || !s.showcase.active;
      $('manual-continue').disabled = !modelSeen || !passed || !!context.busy || !s.stable;
    } else if (s.phase === 'crossing') {
      title = '空间判断之后，轮腿执行'; copy = '高石已绕过，门槛是可见地形。跟随高亮动作，亲手完成抬、迈、落；身体执行前面做出的行动判断。'; key = $('leg-hint').textContent; target = 'leg-actions';
    } else if (s.x >= context.mission.dock[0] - .18 && s.phase !== 'finish-drive') {
      title = '通行预测已完成，准备跨越'; copy = '停稳、对正门槛。可先做跨越预演，再按高亮按钮让四条腿依次抬、迈、落。'; key = '停稳 · 观察门槛 · 亲手迈腿'; target = 'gate-preview';
    } else if (s.phase === 'finish-drive') {
      title = '最后一步：抵达青绿色信标'; copy = '空间想象形成假设，预演支持判断，机器人执行探索。回到轮行，向前驶入目标圈并停稳。'; key = '回到轮行 → W 前进 → 空格停稳'; target = 'wheel-mode';
    } else {
      title = '沿空间预测，探索高石后方'; copy = '局部模型已经支持了路线判断。脑内假设继续随行，按方向键随时接管；新走法需要停稳后重新预测。'; key = 'WASD 驾驶 · Q 回到局部世界 · V 切视角';
    }
    $('story-title').textContent = title;
    $('story-copy').textContent = copy;
    $('story-key').textContent = key;
    if(execute){$('objective').textContent=title;$('hint').textContent=key;}
    if (target) $(target)?.classList.add('guide-target');
  }
  fail() { $('mission-intro').hidden = true; $('story-coach').hidden = true; }
  snapshot() { return {intro: this.intro, started: this.started, imagination: this.imagination, fullWorld: !!this.fullWorld, usedDrive: this.usedDrive, usedBrake: this.usedBrake, phase: document.documentElement.dataset.storyPhase}; }
}
