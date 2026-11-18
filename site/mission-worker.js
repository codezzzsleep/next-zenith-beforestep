import {MissionShowcase} from './mission-showcase.js?v=judges-demo-20261118-1';
import loadMujoco from './vendor/mujoco/mujoco.js';
import {inflateGzip,unpackTar,installAssets} from './robot-physics.js?v=mission-1';
import {MissionWorld,RouteFollower,clamp} from './mission-world.js?v=judges-demo-20261118-1';
import {planRoute,modelWorlds,accepted} from './mission-planner.js?v=judges-demo-20261118-1';
import {rehearseRoute,rehearseCrossing} from './mission-rehearsal.js?v=judges-demo-20261118-1';
import {usableProof,progressOnPath,wrapAngle} from './mission-session.js?v=judges-demo-20261118-1';
import {completeWorldProof} from './mission-session.js?v=judges-demo-20261118-1';
import {SessionObservation,DecisionJournal} from './mission-observation.js?v=judges-demo-20261118-1';
import {CURRENT_CAMERA} from './mission-camera.js?v=judges-demo-20261118-1';
let showcase=new MissionShowcase(),showcaseStill=0;
let gameMode='explore',checkpointRestarts=0;
const checkpoints=new Map();
let mj,mission,live,phase='explore',paused=false,input={v:0,w:0,brake:true},follower=null;
let token=0,revision=0,selected=[],policy='imagination',proof=null,gateProof=null,scan=null,held=0,actions=0,lastSensor=0,routeSession=false,lastLiveFrame=0,sensorVerticalFov=45,sensorYaw=0;
let knowledge=null,journal=new DecisionJournal(),rehearsing=false,lastBlock=null,stopReason=null,holdSeconds=0,judgmentReadyAt=0;
const yieldFrame=()=>new Promise(r=>setTimeout(r,8));
const stable=()=>live.state().speed<.025&&Math.abs(live.data.qvel[5])<.08;
function reject(reason){event('commandRejected',{reason});postMessage({type:'commandRejected',reason});}
function event(type,detail={}){const entry=journal.record(type,detail,live?.state());postMessage({type:'decisionEvent',event:entry});}
function invalidate(reason){cancel();revision++;proof=gateProof=null;routeSession=false;follower=null;lastBlock=null;event('permissionInvalidated',{reason,observationVersion:knowledge?.version||0});}
function startManual(){
  if(!showcase.release('manual',selected)){reject('先留下你的判断：能过、绕开，还是拿不准。');return false;}
  cancel();follower=null;paused=false;input={v:0,w:0,brake:true};event('executionMode',{mode:'manual'});postMessage({type:'manualStarted'});return true;
}
function packet(w,channel,requestId){postMessage({type:'world',channel,requestId,model:w.packet()});}
function checkpointSummary(){
  const saved=[...checkpoints.values()].at(-1);
  return saved?{id:saved.id,label:saved.label}:null;
}
function saveCheckpoint(id,label){
  if(gameMode!=='explore'||!showcase.enabled||checkpoints.has(id)||!stable()||live.legControl)return;
  const state=live.state();
  if(state.tilt>8||live.bodyContact())return;
  checkpoints.set(id,{id,label,physical:live.physicalState(),elapsed:live.elapsed,steps:live.steps,
    phase,actions,showcase:{...showcase.state()},selected:[...selected],policy,knowledge:knowledge.snapshot(),journal:journal.snapshot()});
  postMessage({type:'checkpointSaved',checkpoint:checkpointSummary()});
}
function frame(w=live,channel='live',requestId){
  if(!w)return;const data=w.renderData(),s=w.state();
  postMessage({type:'state',channel,requestId,state:{...s,phase,paused:channel==='live'?paused||rehearsing:false,automatic:!!follower,revision,selected:[...selected],policy,observationVersion:knowledge?.version||0,measuredCells:knowledge?.cells.size||0,sensor:{yaw:sensorYaw,verticalFov:sensorVerticalFov},initialJudgment:journal.initial?.detail.choice||null,judgmentReady:performance.now()>=judgmentReadyAt,actionCount:actions,stable:stable(),gameMode,checkpoint:checkpointSummary(),checkpointRestarts,showcase:showcase.state(),scan:scan?{...scan,points:undefined}:null,proof:proof?{passed:proof.passed,requestId:proof.requestId,usable:!live.legControl&&usableProof(proof,live.state(),revision,knowledge.version),routeSession,revision:proof.revision,observationVersion:proof.observationVersion,worlds:proof.results.length,path:proof.plan.path,length:proof.plan.length,anchor:proof.anchor}:null,gateProof:gateProof?{passed:gateProof.passed,requestId:gateProof.requestId,usable:!live.legControl&&usableProof(gateProof,live.state(),revision,knowledge.version)}:null},data},Object.values(data).map(x=>x.buffer));
}
function cancel(){token++;rehearsing=false;postMessage({type:'dreamClosed'});}
function newLive(initial=null,clock=null){live?.destroy();live=new MissionWorld(mj,mission,'truth.xml',initial);if(clock){live.elapsed=clock.elapsed;live.steps=clock.steps;}live.sensorVerticalFov=sensorVerticalFov;live.sensorYaw=sensorYaw;packet(live,'live');frame();}
function restoreCheckpoint(id){
  if(gameMode!=='explore'){reject('全程挑战需要从头完成。切换探索练习后，可使用检查点。');return;}
  const saved=id?checkpoints.get(id):[...checkpoints.values()].at(-1);
  if(!saved){reject('还没有保存的检查点，先驶到高石观察点。');return;}
  cancel();revision++;proof=gateProof=scan=null;follower=null;routeSession=false;held=0;lastSensor=0;lastLiveFrame=0;
  actions=saved.actions;phase=saved.phase;paused=!!saved.showcase.active&&!saved.showcase.initialJudgment;input={v:0,w:0,brake:true};showcaseStill=0;checkpointRestarts++;selected=[...saved.selected];policy=saved.policy||'imagination';knowledge=new SessionObservation(mission,saved.knowledge);journal=new DecisionJournal(saved.journal);lastBlock=stopReason=null;holdSeconds=0;judgmentReadyAt=performance.now()+3000;
  showcase=new MissionShowcase(true,mission.start[0]+.55);Object.assign(showcase,saved.showcase);
  // Only this explicit reset uses a worker-owned saved physical state. No
  // client-supplied pose is accepted, and every old rehearsal is invalidated.
  newLive(saved.physical,saved);event('checkpointRestored',{id:saved.id,observationVersion:knowledge.version});postMessage({type:'checkpointRestored',checkpoint:{id:saved.id,label:saved.label},gameMode,checkpointRestarts,selected,policy,knowledge:knowledge.snapshot(),journal:journal.snapshot()});
  postMessage({type:'observation',...live.observeRocks()});
  if(showcase.active)postMessage({type:'showcasePrompt'});
  setTimeout(()=>frame(),3005);
}
async function previewRoute(message){
  const requestId=message.requestId;
  if(!showcase.canContinue(selected)){reject('先留下你对石缝的判断，再选择是否试路。');return;}
  if(!stable()||live.legControl){reject('先松开驾驶、停稳，再在脑中试路。');return;}
  cancel();proof=null;routeSession=false;follower=null;const key=token,anchor=live.state(),snapshot=live.physicalState(),planning=knowledge.planningMission(),plan=planRoute(planning,selected,policy,[anchor.x,anchor.y]),worlds=modelWorlds(mission,selected),proofRevision=revision,observationVersion=knowledge.version,surfaces=[...knowledge.cells.values()].map(c=>({...c}));
  if(!plan.path||!worlds.length){lastBlock=plan.path?'no_valid_candidate_world':'no_route_with_required_clearance';event('previewBlocked',{reason:lastBlock,selected,policy,observationVersion});postMessage({type:'previewBlocked',requestId,reason:lastBlock,message:plan.path?'至少为每块石头选一份通过核对的候选。':'当前观测和选择下没有满足净空的路线。可以换条路、补看或停在这里。'});frame();return;}
  rehearsing=true;event('previewStarted',{requestId,selected,policy,observationVersion,worlds:worlds.length,path:plan.path});postMessage({type:'plan',plan,worlds,revision,observationVersion,requestId});frame();const results=[];
  for(let i=0;i<worlds.length;i++){
    if(key!==token)return;const dream=new MissionWorld(mj,mission,worlds[i].file,snapshot,surfaces);packet(dream,'dream',requestId);postMessage({type:'previewProgress',requestId,index:i,total:worlds.length,tasks:worlds[i].tasks});
    let result;try{result=await rehearseRoute(dream,plan.path,{onFrame:()=>{if(key===token)frame(dream,'dream',requestId);},cancelled:()=>key!==token,yieldFrame});}finally{dream.destroy();}
    if(key!==token||result.cancelled)return;results.push({...result,tasks:worlds[i].tasks});event('previewWorldFinished',{requestId,index:i,total:worlds.length,result:results.at(-1)});postMessage({type:'previewResult',requestId,index:i,result:results.at(-1)});
  }
  rehearsing=false;proof={passed:results.length===worlds.length&&results.every(r=>r.passed&&r.reason==='completed'),revision:proofRevision,observationVersion,expectedWorlds:worlds.map(w=>[...w.tasks]),selected:[...selected],policy,results,plan,anchor,requestId};lastBlock=proof.passed?null:results.some(r=>r.contact)?'candidate_world_contact':'candidate_world_incomplete';event('previewFinished',{requestId,passed:proof.passed,completed:results.filter(r=>r.passed).length,worlds:worlds.length,results,observationVersion});postMessage({type:'previewDone',...proof,current:usableProof(proof,live.state(),revision,knowledge.version)});frame();
}
async function previewGate(message){
  const requestId=message.requestId;
  if(showcase.enabled&&!showcase.completed){reject('先到高石观察点留下判断，再驾驶到矮坎。');return;}
  if(follower||!stable()||live.legControl){reject('等路线完成对正、停稳后，才能试跨门槛。');return;}scan=live.observeGate();
  if(!scan.valid){reject('相机还没看清门槛；请靠近、对正，再按“观察”。');return;}
  cancel();gateProof=null;follower=null;rehearsing=true;const key=token,anchor=live.state(),observationVersion=knowledge.version,dream=new MissionWorld(mj,mission,'truth.xml',live.physicalState());dream.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};packet(dream,'dream',requestId);postMessage({type:'gatePreviewStart',requestId});event('gatePreviewStarted',{requestId,observationVersion});frame();
  let result;try{result=await rehearseCrossing(dream,{onFrame:()=>{if(key===token)frame(dream,'dream',requestId);},cancelled:()=>key!==token,yieldFrame});}finally{dream.destroy();}
  if(key!==token||result.cancelled)return;rehearsing=false;gateProof={...result,revision,observationVersion,anchor,requestId};event('gatePreviewFinished',{requestId,result});postMessage({type:'gatePreviewDone',requestId,result});frame();
}
function startCross(assisted){
  if(showcase.enabled&&!showcase.completed){reject('先留下初判、驶到矮坎，再切换轮腿。');return;}
  if(follower){reject('正在沿路线停稳并对正矮坎，请等自动驾驶完成或先接管刹车。');return;}
  if(live.legControl){reject('先把当前腿落稳、回到轮行，再开始门槛跨越。');return;}
  if(!stable()){reject('轮子还在动。先刹车停稳，再抬腿。');return;}
  scan=live.observeGate();if(!scan.valid){reject('门槛不在相机可见范围；靠近并对正再试。');return;}
  if(assisted&&!usableProof(gateProof,live.state(),revision,knowledge.version)){reject('当前位置还没有通过跨越预演。可以重新试路，或选择直接尝试。');return;}
  live.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};
  if(!live.legAction('cross')){live.legControl?.destroy();live.legControl=null;reject('请让车头朝向门槛，靠近中线，并停在门槛前至少 40 cm。');return;}
  cancel();phase='crossing';follower=null;paused=false;input={v:0,w:0,brake:true};event('crossStarted',{assisted});postMessage({type:'crossStart',assisted});frame();
}
function tick(){
  if(!live||paused||rehearsing||['failed','complete','stopped'].includes(phase))return;
  for(let i=0;i<10;i++){
    let command=input;if(follower)command=follower.command(live);
    const s=live.state();if(!live.legControl&&showcase.trigger(s.x)){cancel();proof=gateProof=null;follower=null;routeSession=false;input={v:0,w:0,brake:true};postMessage({type:'showcaseBraking'});}
    if(showcase.locked)command={v:0,w:0,brake:true};
    if(!live.legControl&&s.goalDistance<.35)command={v:0,w:0,brake:true};live.step(command.v,command.w,command.brake);
    if(showcase.locked&&showcase.stage==='braking')showcaseStill=stable()&&live.state().speed<.008?showcaseStill+live.timestep:0;
    if(live.steps%10===0){const s=live.state(),c=live.contacts();if(c.high||c.wall||c.gateBody||s.tilt>30||!s.finite||s.legs?.error){paused=true;follower=null;phase='failed';cancel();const reasonCode=s.legs?.error?'leg_error':!s.finite?'nonfinite_state':s.tilt>30?'lost_balance':c.high?'high_rock_contact':c.wall?'wall_contact':'gate_body_contact';event('missionFailed',{reasonCode,contact:c});postMessage({type:'missionFailed',state:s,reasonCode,contact:c,reason:s.legs?.error||({high_rock_contact:'实际执行接触高石。',wall_contact:'实际执行接触侧壁。',gate_body_contact:'车身触到矮坎。',lost_balance:'车身失去平衡。',nonfinite_state:'物理状态无效。'}[reasonCode])});break;}}
    if(phase==='holding'){
      holdSeconds=stable()&&live.state().speed<.008?holdSeconds+live.timestep:0;
      if(holdSeconds>.45){phase='stopped';paused=true;event('missionStopped',{reason:stopReason});postMessage({type:'missionStopped',state:live.state(),reason:stopReason,journal:journal.snapshot()});break;}
    }
    if(follower?.done){follower=null;input={v:0,w:0,brake:true};phase='gate';scan=live.observeGate();postMessage({type:'gateObserved',scan:{...scan,points:scan.points.length}});}
    if(phase==='explore'&&!follower&&live.state().x>mission.dock[0]-.1)phase='gate';
    if(phase==='crossing'&&live.legControl?.mode==='complete'){phase='finish-drive';postMessage({type:'crossed'});}
    const now=live.state(),over=live.anchors().every(p=>p[0]-.086>mission.gate.far);
    held=now.goalDistance<.35&&now.speed<.035&&over&&!live.legControl?held+live.timestep:0;
    if(held>.35){phase='complete';paused=true;cancel();event('missionComplete',{actions,goalDistance:now.goalDistance});postMessage({type:'missionComplete',state:now,actions,modelWorlds:proof?.results.length||0,journal:journal.snapshot()});break;}
  }
  if(showcase.locked&&showcase.stage==='braking'&&showcaseStill>.45&&showcase.stopped()){saveCheckpoint('observation','高石观察点');paused=true;judgmentReadyAt=performance.now()+3000;event('firstLook',{camera:'current',observationVersion:knowledge.version});postMessage({type:'showcasePrompt',readyAfterMs:3000});setTimeout(()=>frame(),3005);}
  if(gameMode==='explore'&&!checkpoints.has('threshold')&&phase==='gate'&&!follower&&!live.legControl&&live.state().x<mission.gate.near-.4&&Math.abs(live.state().y)<.12&&Math.abs(live.state().yaw)<.08&&live.observeGate().valid)saveCheckpoint('threshold','门槛整备点');
  if(gameMode==='explore'&&!checkpoints.has('finish')&&phase==='finish-drive'&&!live.legControl&&live.anchors().every(p=>p[0]-.086>mission.gate.far))saveCheckpoint('finish','门槛后');
  if(live.elapsed-lastSensor>.35){lastSensor=live.elapsed;postMessage({type:'observation',...live.observeRocks()});}
  if(showcase.locked||paused||['complete','failed','stopped'].includes(phase)||live.elapsed-lastLiveFrame>=.05){lastLiveFrame=live.elapsed;frame();}
}
onmessage=async({data:m})=>{
  try{
    if(m.type==='init'){
      mission=m.mission;knowledge=new SessionObservation(mission);journal=new DecisionJournal();gameMode=m.gameMode==='challenge'?'challenge':'explore';checkpoints.clear();checkpointRestarts=0;showcase=new MissionShowcase(m.showcase===true,mission.start[0]+.55);sensorVerticalFov=clamp(m.sensorVerticalFov||45,15,120);const [wasm,bundle]=await Promise.all([inflateGzip(m.wasm),inflateGzip(m.bundle)]);mj=await loadMujoco({wasmBinary:wasm});installAssets(mj,unpackTar(bundle));newLive();postMessage({type:'ready',engine:mj.mj_versionString()});postMessage({type:'observationLayer',knowledge:knowledge.snapshot()});postMessage({type:'observation',...live.observeRocks()});setInterval(tick,20);
    }else if(m.type==='reset'){gameMode=m.gameMode===undefined?gameMode:m.gameMode==='challenge'?'challenge':'explore';checkpoints.clear();checkpointRestarts=0;revision++;knowledge=new SessionObservation(mission);journal=new DecisionJournal();lastBlock=stopReason=null;holdSeconds=judgmentReadyAt=0;showcase=new MissionShowcase(showcase.enabled,mission.start[0]+.55);showcaseStill=0;sensorYaw=0;cancel();proof=gateProof=scan=null;routeSession=false;follower=null;held=actions=lastSensor=lastLiveFrame=0;phase='explore';paused=false;input={v:0,w:0,brake:true};newLive();postMessage({type:'resetDone',gameMode});postMessage({type:'observationLayer',knowledge:knowledge.snapshot()});postMessage({type:'observation',...live.observeRocks()});}
    else if(m.type==='retryCheckpoint')restoreCheckpoint(m.checkpointId);
    else if(m.type==='selection'){
      invalidate('selection_or_route_changed');selected=[...new Set(m.selected)].filter(id=>mission.candidates.some(c=>c.task_id===id&&accepted(c,mission.thresholds)));policy=['optimistic','imagination','conservative'].includes(m.policy)?m.policy:'imagination';showcase.selectionChanged(selected);event('selectionChanged',{selected,policy});frame();
    }else if(m.type==='preview')await previewRoute(m);
    else if(m.type==='cancel'){invalidate('cancelled');frame();}
    else if(m.type==='initialJudgment'){
      if(performance.now()<judgmentReadyAt||!stable()||!showcase.judge(m.choice)||!journal.judge(m.choice,live.state())){reject('先看清石缝，再留下这局的第一个判断。');return;}
      postMessage({type:'initialJudgmentRecorded',choice:m.choice,journal:journal.snapshot()});frame();
    }
    else if(m.type==='modelViewed'){const c=mission.candidates.find(c=>c.task_id===m.taskId);if(c&&m.rotated===true){if(selected.includes(c.task_id))showcase.view(c.task_id,selected);event('modelViewed',{taskId:c.task_id,target:c.target,input:c.input,admitted:accepted(c,mission.thresholds)});postMessage({type:'showcaseModelReady'});}frame();}
    else if(m.type==='inspectModel'){const c=mission.candidates.find(c=>c.task_id===m.taskId);if(c)event('inspectCandidate',{taskId:c.task_id,target:c.target,input:c.input,admitted:accepted(c,mission.thresholds)});}
    else if(m.type==='imaginationOpened')event('imaginationOpened',{selected});
    else if(m.type==='manualContinue'){startManual();frame();}
    else if(m.type==='execute'){
      if(!showcase.canContinue(selected)){reject('先留下你对石缝的判断。');return;}
      if(live.legControl||!completeWorldProof(proof)||!usableProof(proof,live.state(),revision,knowledge.version)){reject('当前起点、观测和选择尚未全部预演通过；需要重新试路。');return;}
      showcase.release('assisted',selected);follower=new RouteFollower(proof.plan.path);routeSession=true;paused=false;input={v:0,w:0,brake:true};event('executionMode',{mode:'assisted',requestId:proof.requestId,selected,policy,observationVersion:knowledge.version});postMessage({type:'routeStarted',requestId:proof.requestId,revision:proof.revision,worlds:proof.results.length});frame();
    }else if(m.type==='follow'){
      if(live.legControl||!completeWorldProof(proof)||proof.revision!==revision||proof.observationVersion!==knowledge.version||!routeSession){reject('先执行一条在当前位置预演通过的路线。');return;}
      const progress=progressOnPath(live.state(),proof.plan.path);
      if(progress.distance>.09){reject('你已离开预演路线，旧结果无法验证新走法。停稳后重新试路。');return;}
      const s=live.state(),a=proof.plan.path[progress.index-1],b=proof.plan.path[progress.index],atTurn=Math.min(Math.hypot(s.x-a[0],s.y-a[1]),Math.hypot(s.x-b[0],s.y-b[1]))<.065;
      if(!stable()||!atTurn&&Math.abs(wrapAngle(s.yaw-Math.atan2(b[1]-a[1],b[0]-a[0])))>.08){reject('先停稳并沿原路线方向；偏离走向后，需要重新试路。');return;}
      follower=new RouteFollower(proof.plan.path);follower.index=progress.index;if(!atTurn){follower.phase='drive';follower.origin=a;}paused=false;frame();
    }else if(m.type==='input'){
      const moving=Math.abs(m.v||0)+Math.abs(m.w||0)>.005;
      if(showcase.locked&&(!moving||!showcase.canContinue(selected)||!startManual())){input={v:0,w:0,brake:true};frame();return;}
      if(live.legControl||['failed','complete','stopped','holding'].includes(phase))return;
      if(moving&&proof&&!routeSession)invalidate('pose_moved_before_departure');
      if(rehearsing&&moving)invalidate('manual_takeover_during_preview');
      const wasAutomatic=!!follower;input={v:clamp(m.v,-.36,.36),w:clamp(m.w,-.8,.8),brake:!!m.brake};if(moving||input.brake)follower=null;if(wasAutomatic&&!follower)event('executionMode',{mode:'manual',takeover:true});frame();
    }else if(m.type==='pause'){if(showcase.stage==='braking'&&m.value){reject('机器人正在用轮子停稳，请稍等。');return;}paused=!!m.value;input={v:0,w:0,brake:true};frame();}
    else if(m.type==='sensorLens'){const verticalFov=clamp(m.verticalFov,15,120),yaw=clamp(m.yaw||0,-.8,.8);if(Math.abs(verticalFov-sensorVerticalFov)>1e-6||Math.abs(yaw-sensorYaw)>1e-6)event('cameraLens',{yaw,verticalFov,offset:CURRENT_CAMERA.offset});sensorVerticalFov=verticalFov;sensorYaw=yaw;live.sensorVerticalFov=sensorVerticalFov;live.sensorYaw=sensorYaw;postMessage({type:'observation',...live.observeRocks()});}
    else if(m.type==='observe'){
      if(showcase.locked&&!showcase.canContinue(selected)){reject('先留下初判，再选择补看。');return;}
      if(!stable()){reject('停稳再观察，才能把新信息放回同一个局部空间。');return;}
      scan=live.observeGate();const rocks=live.observeRocks(),result=knowledge.ingest(rocks);
      if(result.changed){invalidate('new_effective_observation');event('observationChanged',{...result,camera:rocks.camera,cameraYaw:sensorYaw,verticalFov:sensorVerticalFov});}
      else event('observationUnchanged',result);
      postMessage({type:'observed',rocks,observation:result,knowledge:knowledge.snapshot(),scan:{...scan,points:scan.points.length}});frame();
    }
    else if(m.type==='hold'){
      if(!showcase.canContinue(selected)||live.legControl){reject('先留下初判，或先把抬起的腿落稳。');return;}
      stopReason=lastBlock||'player_chose_to_stop';invalidate('player_stop');showcase.release('hold',selected);phase='holding';paused=false;holdSeconds=0;input={v:0,w:0,brake:true};event('holdRequested',{reason:stopReason});frame();
    }
    else if(m.type==='exportRun')postMessage({type:'runJournal',journal:journal.snapshot(),knowledge:knowledge.snapshot(),selected,policy,state:live.state(),phase});
    else if(m.type==='gatePreview')await previewGate(m);
    else if(m.type==='cross')startCross(!!m.assisted);
    else if(m.type==='legAction'&&!paused){
      if(showcase.enabled&&!showcase.completed){reject('先留下初判并恢复驾驶，再到矮坎试轮腿。');return;}
      if((m.action==='lift'||!live.legControl)&&!stable()){reject('先刹车停稳，再抬腿。');return;}
      if(phase!=='crossing'){follower=null;routeSession=false;input={v:0,w:0,brake:true};cancel();}const ok=live.legAction(m.action);if(ok){actions++;event('legAction',{action:m.action,count:actions,leg:live.legControl?.selected});}else reject('先完成当前腿的动作，落地后再继续。');postMessage({type:'legCommand',ok,action:m.action});frame();
    }else if(m.type==='legSelect'){if(showcase.enabled&&!showcase.completed){reject('先留下初判并恢复手控，再试轮腿。');return;}if(!live.legControl&&!stable()){reject('先停稳再选腿。');return;}if(phase!=='crossing'){follower=null;routeSession=false;input={v:0,w:0,brake:true};cancel();}live.selectLeg(m.index);frame();}
    else if(m.type==='wheelMode'){if(!live.resumeWheels())reject('把抬起的腿放稳，再回轮行。');input={v:0,w:0,brake:true};frame();}
    else if(m.type==='pose'&&!live.legControl){if(m.value!==live.poseName)invalidate('robot_pose_changed');live.setPose(m.value);frame();}
  }catch(error){paused=true;postMessage({type:'error',message:error.message||String(error)});}
};
