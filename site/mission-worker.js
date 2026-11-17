import {MissionShowcase} from './mission-showcase.js?v=showcase-1';
import loadMujoco from './vendor/mujoco/mujoco.js';
import {inflateGzip,unpackTar,installAssets} from './robot-physics.js?v=mission-1';
import {MissionWorld,RouteFollower,clamp} from './mission-world.js?v=m20-visual-1';
import {planRoute,modelWorlds,accepted} from './mission-planner.js?v=mission-1';
import {rehearseRoute,rehearseCrossing} from './mission-rehearsal.js?v=immersive-1';
import {usableProof,progressOnPath,wrapAngle} from './mission-session.js?v=immersive-1';
let showcase=new MissionShowcase(),showcaseStill=0;
let gameMode='explore',checkpointRestarts=0;
const checkpoints=new Map();
let mj,mission,live,phase='explore',paused=false,input={v:0,w:0,brake:true},follower=null;
let token=0,revision=0,selected=[],policy='imagination',proof=null,gateProof=null,scan=null,held=0,actions=0,lastSensor=0,routeSession=false,lastLiveFrame=0,sensorVerticalFov=45;
const yieldFrame=()=>new Promise(r=>setTimeout(r,8));
const stable=()=>live.state().speed<.025&&Math.abs(live.data.qvel[5])<.08;
function reject(reason){postMessage({type:'commandRejected',reason});}
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
    phase,actions,showcase:{...showcase.state()},selected:[...selected]});
  postMessage({type:'checkpointSaved',checkpoint:checkpointSummary()});
}
function frame(w=live,channel='live',requestId){
  if(!w)return;const data=w.renderData(),s=w.state();
  postMessage({type:'state',channel,requestId,state:{...s,phase,paused,automatic:!!follower,revision,actionCount:actions,stable:stable(),gameMode,checkpoint:checkpointSummary(),checkpointRestarts,showcase:showcase.state(),scan:scan?{...scan,points:undefined}:null,proof:proof?{passed:proof.passed,requestId:proof.requestId,usable:!live.legControl&&usableProof(proof,live.state(),revision),routeSession,revision:proof.revision,worlds:proof.results.length,path:proof.plan.path,length:proof.plan.length,anchor:proof.anchor}:null,gateProof:gateProof?{passed:gateProof.passed,requestId:gateProof.requestId,usable:!live.legControl&&usableProof(gateProof,live.state(),revision)}:null},data},Object.values(data).map(x=>x.buffer));
}
function cancel(){token++;postMessage({type:'dreamClosed'});}
function newLive(initial=null,clock=null){live?.destroy();live=new MissionWorld(mj,mission,'truth.xml',initial);if(clock){live.elapsed=clock.elapsed;live.steps=clock.steps;}live.sensorVerticalFov=sensorVerticalFov;packet(live,'live');frame();}
function restoreCheckpoint(id){
  if(gameMode!=='explore'){reject('全程挑战需要从头完成。切换探索练习后，可使用检查点。');return;}
  const saved=id?checkpoints.get(id):[...checkpoints.values()].at(-1);
  if(!saved){reject('还没有保存的检查点，先驶到高石观察点。');return;}
  cancel();revision++;proof=gateProof=scan=null;follower=null;routeSession=false;held=0;lastSensor=0;lastLiveFrame=0;
  actions=saved.actions;phase=saved.phase;paused=false;input={v:0,w:0,brake:true};showcaseStill=0;checkpointRestarts++;
  showcase=new MissionShowcase(true,mission.start[0]+.55);Object.assign(showcase,saved.showcase);
  // Only this explicit reset uses a worker-owned saved physical state. No
  // client-supplied pose is accepted, and every old rehearsal is invalidated.
  newLive(saved.physical,saved);postMessage({type:'checkpointRestored',checkpoint:{id:saved.id,label:saved.label},gameMode,checkpointRestarts});
  postMessage({type:'observation',...live.observeRocks()});
  if(showcase.active)postMessage({type:'showcasePrompt'});
}
async function previewRoute(message){
  const requestId=message.requestId;
  if(!showcase.canContinue(selected)){reject('先转动已有的完整3D模型，看看另一面，再在脑中试路。');return;}
  if(!stable()||live.legControl){reject('先松开驾驶、停稳，再在脑中试路。');return;}
  cancel();proof=null;routeSession=false;follower=null;const key=token,anchor=live.state(),snapshot=live.physicalState(),plan=planRoute(mission,selected,policy,[anchor.x,anchor.y]),worlds=modelWorlds(mission,selected);
  if(!plan.path||!worlds.length){reject(plan.path?'每块高石至少选一份可信候选。':'当前位置没有满足净空的参考路线，可以自行尝试或后退观察。');return;}
  postMessage({type:'plan',plan,worlds,revision,requestId});const results=[];
  for(let i=0;i<worlds.length;i++){
    if(key!==token)return;const dream=new MissionWorld(mj,mission,worlds[i].file,snapshot);packet(dream,'dream',requestId);postMessage({type:'previewProgress',requestId,index:i,total:worlds.length,tasks:worlds[i].tasks});
    let result;try{result=await rehearseRoute(dream,plan.path,{onFrame:()=>{if(key===token)frame(dream,'dream',requestId);},cancelled:()=>key!==token,yieldFrame});}finally{dream.destroy();}
    if(key!==token||result.cancelled)return;results.push({...result,tasks:worlds[i].tasks});postMessage({type:'previewResult',requestId,index:i,result:results.at(-1)});
  }
  proof={passed:results.every(r=>r.passed),revision,selected:[...selected],policy,results,plan,anchor,requestId};postMessage({type:'previewDone',...proof,current:usableProof(proof,live.state(),revision)});frame();
}
async function previewGate(message){
  const requestId=message.requestId;
  if(showcase.enabled&&!showcase.completed){reject('先驾驶到高石观察点，看看 Lux3D 的完整形状，再探索门槛。');return;}
  if(!stable()||live.legControl){reject('停稳后，才能试跨门槛。');return;}scan=live.observeGate();
  if(!scan.valid){reject('相机还没看清门槛；请靠近、对正，再按“观察”。');return;}
  cancel();gateProof=null;follower=null;const key=token,anchor=live.state(),dream=new MissionWorld(mj,mission,'truth.xml',live.physicalState());dream.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};packet(dream,'dream',requestId);postMessage({type:'gatePreviewStart',requestId});
  let result;try{result=await rehearseCrossing(dream,{onFrame:()=>{if(key===token)frame(dream,'dream',requestId);},cancelled:()=>key!==token,yieldFrame});}finally{dream.destroy();}
  if(key!==token||result.cancelled)return;gateProof={...result,revision,anchor,requestId};postMessage({type:'gatePreviewDone',requestId,result});frame();
}
function startCross(assisted){
  if(showcase.enabled&&!showcase.completed){reject('先完成高石的3D观察，再继续探索。');return;}
  if(live.legControl){reject('先把当前腿落稳、回到轮行，再开始门槛跨越。');return;}
  if(!stable()){reject('轮子还在动。先刹车停稳，再抬腿。');return;}
  scan=live.observeGate();if(!scan.valid){reject('门槛不在相机可见范围；靠近并对正再试。');return;}
  if(assisted&&!usableProof(gateProof,live.state(),revision)){reject('当前位置还没有通过跨越预演。可以重新试路，或选择直接尝试。');return;}
  live.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};
  if(!live.legAction('cross')){live.legControl?.destroy();live.legControl=null;reject('请让车头朝向门槛，靠近中线，并停在门槛前至少 40 cm。');return;}
  cancel();phase='crossing';follower=null;paused=false;input={v:0,w:0,brake:true};postMessage({type:'crossStart',assisted});frame();
}
function tick(){
  if(!live||paused||['failed','complete'].includes(phase))return;
  for(let i=0;i<10;i++){
    let command=input;if(follower)command=follower.command(live);
    const s=live.state();if(!live.legControl&&showcase.trigger(s.x)){cancel();proof=gateProof=null;follower=null;routeSession=false;input={v:0,w:0,brake:true};postMessage({type:'showcaseBraking'});}
    if(showcase.locked)command={v:0,w:0,brake:true};
    if(!live.legControl&&s.goalDistance<.35)command={v:0,w:0,brake:true};live.step(command.v,command.w,command.brake);
    if(showcase.locked&&showcase.stage==='braking')showcaseStill=stable()&&live.state().speed<.008?showcaseStill+live.timestep:0;
    if(live.steps%10===0){const s=live.state(),c=live.contacts();if(c.high||c.wall||c.gateBody||s.tilt>30||!s.finite||s.legs?.error){paused=true;follower=null;phase='failed';cancel();postMessage({type:'missionFailed',reason:s.legs?.error||'碰到高石、车身触到门槛，或失去平衡。重试后可以换个走法。'});break;}}
    if(follower?.done){follower=null;input={v:0,w:0,brake:true};phase='gate';scan=live.observeGate();postMessage({type:'gateObserved',scan:{...scan,points:scan.points.length}});}
    if(phase==='explore'&&live.state().x>mission.dock[0]-.1)phase='gate';
    if(phase==='crossing'&&live.legControl?.mode==='complete'){phase='finish-drive';postMessage({type:'crossed'});}
    const now=live.state(),over=live.anchors().every(p=>p[0]-.086>mission.gate.far);
    held=now.goalDistance<.35&&now.speed<.035&&over&&!live.legControl?held+live.timestep:0;
    if(held>.35){phase='complete';paused=true;cancel();postMessage({type:'missionComplete',state:now,actions,modelWorlds:proof?.results.length||0});break;}
  }
  if(showcase.locked&&showcase.stage==='braking'&&showcaseStill>.45&&showcase.stopped()){saveCheckpoint('observation','高石观察点');postMessage({type:'showcasePrompt'});}
  if(gameMode==='explore'&&!checkpoints.has('threshold')&&phase==='gate'&&!follower&&!live.legControl&&live.state().x<mission.gate.near-.4&&Math.abs(live.state().y)<.12&&Math.abs(live.state().yaw)<.08&&live.observeGate().valid)saveCheckpoint('threshold','门槛整备点');
  if(gameMode==='explore'&&!checkpoints.has('finish')&&phase==='finish-drive'&&!live.legControl&&live.anchors().every(p=>p[0]-.086>mission.gate.far))saveCheckpoint('finish','门槛后');
  if(live.elapsed-lastSensor>.35){lastSensor=live.elapsed;postMessage({type:'observation',...live.observeRocks()});}
  if(showcase.locked||paused||['complete','failed'].includes(phase)||live.elapsed-lastLiveFrame>=.05){lastLiveFrame=live.elapsed;frame();}
}
onmessage=async({data:m})=>{
  try{
    if(m.type==='init'){
      mission=m.mission;gameMode=m.gameMode==='challenge'?'challenge':'explore';checkpoints.clear();checkpointRestarts=0;showcase=new MissionShowcase(m.showcase===true,mission.start[0]+.55);sensorVerticalFov=clamp(m.sensorVerticalFov||45,15,120);const [wasm,bundle]=await Promise.all([inflateGzip(m.wasm),inflateGzip(m.bundle)]);mj=await loadMujoco({wasmBinary:wasm});installAssets(mj,unpackTar(bundle));newLive();postMessage({type:'ready',engine:mj.mj_versionString()});postMessage({type:'observation',...live.observeRocks()});setInterval(tick,20);
    }else if(m.type==='reset'){gameMode=m.gameMode===undefined?gameMode:m.gameMode==='challenge'?'challenge':'explore';checkpoints.clear();checkpointRestarts=0;revision++;showcase=new MissionShowcase(showcase.enabled,mission.start[0]+.55);showcaseStill=0;cancel();proof=gateProof=scan=null;routeSession=false;follower=null;held=actions=lastSensor=lastLiveFrame=0;phase='explore';paused=false;input={v:0,w:0,brake:true};newLive();postMessage({type:'resetDone',gameMode});postMessage({type:'observation',...live.observeRocks()});}
    else if(m.type==='retryCheckpoint')restoreCheckpoint(m.checkpointId);
    else if(m.type==='selection'){
      cancel();revision++;selected=m.selected.filter(id=>mission.candidates.some(c=>c.task_id===id&&accepted(c,mission.thresholds)));policy=m.policy||'imagination';showcase.selectionChanged(selected);proof=gateProof=null;routeSession=false;follower=null;frame();
    }else if(m.type==='preview')await previewRoute(m);
    else if(m.type==='cancel'){cancel();proof=gateProof=null;routeSession=false;frame();}
    else if(m.type==='modelViewed'){if(m.rotated===true&&mission.candidates.some(c=>c.task_id===m.taskId&&c.target==='T1')&&showcase.view(m.taskId,selected))postMessage({type:'showcaseModelReady'});else reject('选择一份高石 A 的可信模型，转动后看看另一面。');frame();}
    else if(m.type==='manualContinue'){if(!showcase.release('manual',selected)){reject('先看看所选3D模型的另一面，再把驾驶交回给你。');return;}input={v:0,w:0,brake:true};paused=false;postMessage({type:'manualStarted'});frame();}
    else if(m.type==='execute'){
      if(!showcase.canContinue(selected)){reject('先看看完整模型的另一面，再决定走法。');return;}
      if(live.legControl||!usableProof(proof,live.state(),revision)){reject('这条路线尚未在当前位置和当前候选中预演通过；先停稳重新预演。');return;}
      showcase.release('assisted',selected);follower=new RouteFollower(proof.plan.path);routeSession=true;paused=false;input={v:0,w:0,brake:true};postMessage({type:'routeStarted',requestId:proof.requestId,revision:proof.revision,worlds:proof.results.length});frame();
    }else if(m.type==='follow'){
      if(live.legControl||!proof?.passed||proof.revision!==revision||!routeSession){reject('先执行一条在当前位置预演通过的路线。');return;}
      const progress=progressOnPath(live.state(),proof.plan.path);
      if(progress.distance>.09){reject('你已离开预演路线，旧结果无法验证新走法。停稳后重新试路。');return;}
      const s=live.state(),a=proof.plan.path[progress.index-1],b=proof.plan.path[progress.index],atTurn=Math.min(Math.hypot(s.x-a[0],s.y-a[1]),Math.hypot(s.x-b[0],s.y-b[1]))<.065;
      if(!stable()||!atTurn&&Math.abs(wrapAngle(s.yaw-Math.atan2(b[1]-a[1],b[0]-a[0])))>.08){reject('先停稳并沿原路线方向；偏离走向后，需要重新试路。');return;}
      follower=new RouteFollower(proof.plan.path);follower.index=progress.index;if(!atTurn){follower.phase='drive';follower.origin=a;}paused=false;frame();
    }else if(m.type==='input'){
      if(showcase.locked){input={v:0,w:0,brake:true};frame();return;}
      if(live.legControl||['failed','complete'].includes(phase))return;
      input={v:clamp(m.v,-.36,.36),w:clamp(m.w,-.8,.8),brake:!!m.brake};if(Math.abs(input.v)+Math.abs(input.w)>.005||input.brake)follower=null;frame();
    }else if(m.type==='pause'){if(showcase.stage==='braking'&&m.value){reject('机器人正在用轮子停稳，请稍等。');return;}paused=!!m.value;input={v:0,w:0,brake:true};frame();}
    else if(m.type==='sensorLens'){sensorVerticalFov=clamp(m.verticalFov,15,120);live.sensorVerticalFov=sensorVerticalFov;postMessage({type:'observation',...live.observeRocks()});}
    else if(m.type==='observe'){scan=live.observeGate();postMessage({type:'observed',rocks:live.observeRocks(),scan:{...scan,points:scan.points.length}});frame();}
    else if(m.type==='gatePreview')await previewGate(m);
    else if(m.type==='cross')startCross(!!m.assisted);
    else if(m.type==='legAction'&&!paused){
      if(showcase.enabled&&!showcase.completed){reject('先完成高石的3D观测，再继续操作。');return;}
      if((m.action==='lift'||!live.legControl)&&!stable()){reject('先刹车停稳，再抬腿。');return;}
      if(phase!=='crossing'){follower=null;routeSession=false;input={v:0,w:0,brake:true};cancel();}const ok=live.legAction(m.action);if(ok)actions++;else reject('先完成当前腿的动作，落地后再继续。');postMessage({type:'legCommand',ok,action:m.action});frame();
    }else if(m.type==='legSelect'){if(showcase.enabled&&!showcase.completed){reject('先完成高石的3D观测，再继续操作。');return;}if(!live.legControl&&!stable()){reject('先停稳再选腿。');return;}if(phase!=='crossing'){follower=null;routeSession=false;input={v:0,w:0,brake:true};cancel();}live.selectLeg(m.index);frame();}
    else if(m.type==='wheelMode'){if(!live.resumeWheels())reject('把抬起的腿放稳，再回轮行。');input={v:0,w:0,brake:true};frame();}
    else if(m.type==='pose'&&!live.legControl){live.setPose(m.value);frame();}
  }catch(error){paused=true;postMessage({type:'error',message:error.message||String(error)});}
};
