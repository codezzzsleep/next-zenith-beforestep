const $ = id => document.getElementById(id);
const judgments={pass:'我觉得能过',detour:'我想绕开',unsure:'我拿不准'};

/** Guides choices; physics, knowledge and permissions remain worker-owned. */
export class MissionStory {
  constructor({post,stopInput,activate,refresh,setPerception}) {
    Object.assign(this,{post,stopInput,activate,refresh,setPerception});this.ready=false;this.reset(true);
    $('begin-mission').onclick=()=>this.begin();
    for(const b of document.querySelectorAll('[data-judgment]'))b.onclick=()=>{this.stopInput();this.post({type:'initialJudgment',choice:b.dataset.judgment});};
    $('decision-imagine').onclick=()=>this.activate();
    $('decision-manual').onclick=()=>{this.stopInput();this.post({type:'manualContinue'});};
    $('decision-observe').onclick=()=>$('observe').click();
    $('decision-hold').onclick=$('brain-hold').onclick=()=>{this.stopInput();this.post({type:'hold'});};
  }
  reset(intro=false){this.intro=intro;this.started=!intro;this.imagination=false;this.usedDrive=false;this.usedBrake=false;this.context=null;this.setPerception(false);$('mission-intro').hidden=!intro;$('story-coach').hidden=true;}
  becomeReady(){this.ready=true;if(this.intro)this.post({type:'pause',value:true});this.render();}
  begin(){if(!this.ready||!this.intro)return;this.stopInput();this.intro=false;this.started=true;$('mission-intro').hidden=true;this.post({type:'pause',value:false});$('world').focus();this.refresh();}
  input(key){if(['w','ArrowUp'].includes(key))this.usedDrive=true;if(key===' ')this.usedBrake=true;}
  openImagination(){this.imagination=true;}
  restore(){this.intro=false;this.started=true;this.imagination=false;$('mission-intro').hidden=true;}
  update(context){this.context=context;this.render();}
  render(){
    const c=this.context,s=c?.state,judging=!!s?.showcase.active&&!s.initialJudgment&&s.showcase.stage!=='braking';
    this.fullWorld=true;this.setPerception(false);document.body.classList.remove('perception-mode');
    $('begin-mission').disabled=!this.ready;$('begin-mission').textContent=this.ready?'开始探索':'准备机器人…';$('mission-intro').hidden=!this.intro;$('story-coach').hidden=true;
    $('judgment-panel').hidden=this.intro||!judging;$('judgment-actions').hidden=!s?.judgmentReady;$('gap-reticle').hidden=this.intro||!judging;
    $('first-visible').hidden=this.intro||!judging;
    $('decision-tools').hidden=this.intro||!s?.initialJudgment||c.brainOpen||s.showcase.completed||['complete','failed','stopped'].includes(s.phase);
    $('pause').disabled=this.intro||!this.ready||s?.showcase.stage==='braking'||!!c?.busy||judging;
    $('gameplay-open').disabled=this.intro||!this.ready||s?.showcase.stage==='braking';$('help').disabled=this.intro;
    for(const b of document.querySelectorAll('button[data-view]'))b.disabled=this.intro||!this.ready;
    $('pip').disabled=this.intro||!this.ready;$('inset-label').hidden=this.intro||$('pip').getAttribute('aria-pressed')!=='true';
    $('perception-label').hidden=this.intro||!judging;$('perception-label').textContent='当前相机 · 石缝往里仍未知';$('unknown-key').hidden=true;
    if(!s)return;
    $('think').disabled=this.intro||!s.initialJudgment||['complete','failed','stopped'].includes(s.phase);
    $('observe').disabled=this.intro||judging||!!c.busy;
    $('manual-continue').disabled=this.intro||!s.initialJudgment||['complete','failed','stopped'].includes(s.phase);$('manual-continue').hidden=false;
    let title='穿过石缝，跨过矮坎，在青色信标里停稳。',hint='WASD / 方向键驾驶 · 空格刹车',phase='approach';
    if(this.intro)phase='mission-goal';
    else if(s.phase==='complete'){title='已在信标里停稳。';hint='回顾初判、空间假设、试路与实际结局。';phase='goal-reached';}
    else if(s.phase==='failed'){title='这次执行没有完成。';hint='查看实际原因；可回检查点换一种判断。';phase='failed';}
    else if(s.phase==='stopped'){title='我决定停在这里。';hint='主动停车也保留本局判断；可以回检查点再试。';phase='stopped';}
    else if(s.showcase.stage==='braking'){title='高石观察点 · 轮子正在刹停';hint='先用这一眼判断石缝。';phase='braking';}
    else if(judging){title='这里够我过去吗？';hint=s.judgmentReady?'留下你的初判，再选择下一步。':'先静静看三秒。';phase='first-look';}
    else if(c.busy){title=c.busy==='gate'?'先在脑内试跨矮坎。':'先在候选空间里试路。';hint=c.busy==='route'?`${c.results.length} / ${c.worlds} 个世界完成 · 现场 M20 停在原处`:'现场机器人停稳，独立预演跨越。';phase='rehearsing';}
    else if(c.brainOpen){title='让空间想象参与这次判断。';hint=c.cert?.passed&&s.proof?.usable?'本局组合全部通过，可以按这条路出发。':'切换假设，看看它占到哪里，再选路线试路。';phase=c.cert?.passed&&s.proof?.usable?'permission-ready':'imagination';}
    else if(s.phase==='crossing'){title='矮坎已看清 · 轮腿接力';hint=$('leg-hint').textContent;phase='leg-execution';}
    else if(s.phase==='finish-drive'){title='最后一步 · 在青色信标里停稳';hint=s.legs?'回到轮行，再向信标开。':'前进到信标内，刹车停稳。';phase='finish-drive';}
    else if(s.phase==='gate'){title='矮坎已看清 · 选腿、抬、迈、落';hint='停稳后可直接迈腿，也可以先试跨。';phase='visible-gate';}
    else if(s.showcase.completed){title=s.automatic?'按通过预演的路线穿过石缝。':'你正在自己驾驶。';hint=s.automatic?'方向键随时接管 · V 切视角':'V 切视角 · E 补看 · Q 空间想象';phase='driving';}
    else if(s.initialJudgment){title='你的初判：'+judgments[s.initialJudgment];hint='可以自己开、让 Lux3D 想一想、补看或停车。';phase='choice-made';}
    $('objective').textContent=title;$('hint').textContent=hint;document.documentElement.dataset.storyPhase=phase;
    const step=s.phase==='complete'?4:s.showcase.completed?3:c.busy||c.cert?2:this.imagination?1:0;
    $('mission-route').querySelectorAll('li').forEach((node,i)=>{node.classList.toggle('done',i<step);node.classList.toggle('current',i===step);});$('mission-route').style.setProperty('--journey-progress',Math.min(100,step*25)+'%');
  }
  fail(){$('mission-intro').hidden=true;$('story-coach').hidden=true;}
  snapshot(){return {intro:this.intro,started:this.started,imagination:this.imagination,fullWorld:true,usedDrive:this.usedDrive,usedBrake:this.usedBrake,phase:document.documentElement.dataset.storyPhase};}
}
