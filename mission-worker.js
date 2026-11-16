import loadMujoco from './vendor/mujoco/mujoco.js';
import {inflateGzip,unpackTar,installAssets} from './robot-physics.js?v=mission-1';
import {MissionWorld,RouteFollower,clamp} from './mission-world.js?v=immersive-1';
import {planRoute,modelWorlds,accepted} from './mission-planner.js?v=mission-1';
import {rehearseRoute,rehearseCrossing} from './mission-rehearsal.js?v=immersive-1';
import {usableProof,progressOnPath,wrapAngle} from './mission-session.js?v=immersive-1';
let mj,mission,live,phase='explore',paused=false,input={v:0,w:0,brake:true},follower=null;
let token=0,revision=0,selected=[],policy='imagination',proof=null,gateProof=null,scan=null,held=0,actions=0,lastSensor=0,routeSession=false,lastLiveFrame=0,sensorVerticalFov=45;
const yieldFrame=()=>new Promise(r=>setTimeout(r,8));
const stable=()=>live.state().speed<.025&&Math.abs(live.data.qvel[5])<.08;
function reject(reason){postMessage({type:'commandRejected',reason});}
function packet(w,channel,requestId){postMessage({type:'world',channel,requestId,model:w.packet()});}
function frame(w=live,channel='live',requestId){
  if(!w)return;const data=w.renderData(),s=w.state();
  postMessage({type:'state',channel,requestId,state:{...s,phase,paused,automatic:!!follower,revision,actionCount:actions,stable:stable(),scan:scan?{...scan,points:undefined}:null,proof:proof?{passed:proof.passed,requestId:proof.requestId,usable:!live.legControl&&usableProof(proof,live.state(),revision),routeSession,revision:proof.revision,worlds:proof.results.length,path:proof.plan.path,length:proof.plan.length,anchor:proof.anchor}:null,gateProof:gateProof?{passed:gateProof.passed,requestId:gateProof.requestId,usable:!live.legControl&&usableProof(gateProof,live.state(),revision)}:null},data},Object.values(data).map(x=>x.buffer));
}
function cancel(){token++;postMessage({type:'dreamClosed'});}
function newLive(){live?.destroy();live=new MissionWorld(mj,mission);live.sensorVerticalFov=sensorVerticalFov;packet(live,'live');frame();}
async function previewRoute(message){
  const requestId=message.requestId;
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
  if(!stable()||live.legControl){reject('停稳后，才能试跨门槛。');return;}scan=live.observeGate();
  if(!scan.valid){reject('相机还没看清门槛；请靠近、对正，再按“观察”。');return;}
  cancel();gateProof=null;follower=null;const key=token,anchor=live.state(),dream=new MissionWorld(mj,mission,'truth.xml',live.physicalState());dream.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};packet(dream,'dream',requestId);postMessage({type:'gatePreviewStart',requestId});
  let result;try{result=await rehearseCrossing(dream,{onFrame:()=>{if(key===token)frame(dream,'dream',requestId);},cancelled:()=>key!==token,yieldFrame});}finally{dream.destroy();}
  if(key!==token||result.cancelled)return;gateProof={...result,revision,anchor,requestId};postMessage({type:'gatePreviewDone',requestId,result});frame();
}
function startCross(assisted){
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
    const s=live.state();if(!live.legControl&&s.goalDistance<.35)command={v:0,w:0,brake:true};live.step(command.v,command.w,command.brake);
    if(live.steps%10===0){const s=live.state(),c=live.contacts();if(c.high||c.wall||c.gateBody||s.tilt>30||!s.finite||s.legs?.error){paused=true;follower=null;phase='failed';cancel();postMessage({type:'missionFailed',reason:s.legs?.error||'碰到高石、车身触到门槛，或失去平衡。重试后可以换个走法。'});break;}}
    if(follower?.done){follower=null;input={v:0,w:0,brake:true};phase='gate';scan=live.observeGate();postMessage({type:'gateObserved',scan:{...scan,points:scan.points.length}});}
    if(phase==='explore'&&live.state().x>mission.dock[0]-.1)phase='gate';
    if(phase==='crossing'&&live.legControl?.mode==='complete'){phase='finish-drive';postMessage({type:'crossed'});}
    const now=live.state(),over=live.anchors().every(p=>p[0]-.086>mission.gate.far);
    held=now.goalDistance<.35&&now.speed<.035&&over&&!live.legControl?held+live.timestep:0;
    if(held>.35){phase='complete';paused=true;cancel();postMessage({type:'missionComplete',state:now,actions,modelWorlds:proof?.results.length||0});break;}
  }
  if(live.elapsed-lastSensor>.35){lastSensor=live.elapsed;postMessage({type:'observation',...live.observeRocks()});}
  if(paused||['complete','failed'].includes(phase)||live.elapsed-lastLiveFrame>=.05){lastLiveFrame=live.elapsed;frame();}
}
onmessage=async({data:m})=>{
  try{
    if(m.type==='init'){
      mission=m.mission;sensorVerticalFov=clamp(m.sensorVerticalFov||45,15,120);const [wasm,bundle]=await Promise.all([inflateGzip(m.wasm),inflateGzip(m.bundle)]);mj=await loadMujoco({wasmBinary:wasm});installAssets(mj,unpackTar(bundle));newLive();postMessage({type:'ready',engine:mj.mj_versionString()});postMessage({type:'observation',...live.observeRocks()});setInterval(tick,20);
    }else if(m.type==='reset'){cancel();proof=gateProof=scan=null;routeSession=false;follower=null;held=actions=lastSensor=lastLiveFrame=0;phase='explore';paused=false;input={v:0,w:0,brake:true};newLive();postMessage({type:'resetDone'});postMessage({type:'observation',...live.observeRocks()});}
    else if(m.type==='selection'){
      cancel();revision++;selected=m.selected.filter(id=>mission.candidates.some(c=>c.task_id===id&&accepted(c,mission.thresholds)));policy=m.policy||'imagination';proof=gateProof=null;routeSession=false;follower=null;frame();
    }else if(m.type==='preview')await previewRoute(m);
    else if(m.type==='cancel'){cancel();proof=gateProof=null;routeSession=false;frame();}
    else if(m.type==='execute'){
      if(live.legControl||!usableProof(proof,live.state(),revision)){reject('这条路线尚未在当前位置和当前候选中预演通过；先停稳重新预演。');return;}
      follower=new RouteFollower(proof.plan.path);routeSession=true;paused=false;input={v:0,w:0,brake:true};postMessage({type:'routeStarted'});frame();
    }else if(m.type==='follow'){
      if(live.legControl||!proof?.passed||proof.revision!==revision||!routeSession){reject('先执行一条在当前位置预演通过的路线。');return;}
      const progress=progressOnPath(live.state(),proof.plan.path);
      if(progress.distance>.09){reject('你已离开预演路线，旧结果无法验证新走法。停稳后重新试路。');return;}
      const s=live.state(),a=proof.plan.path[progress.index-1],b=proof.plan.path[progress.index],atTurn=Math.min(Math.hypot(s.x-a[0],s.y-a[1]),Math.hypot(s.x-b[0],s.y-b[1]))<.065;
      if(!stable()||!atTurn&&Math.abs(wrapAngle(s.yaw-Math.atan2(b[1]-a[1],b[0]-a[0])))>.08){reject('先停稳并沿原路线方向；偏离走向后，需要重新试路。');return;}
      follower=new RouteFollower(proof.plan.path);follower.index=progress.index;if(!atTurn){follower.phase='drive';follower.origin=a;}paused=false;frame();
    }else if(m.type==='input'){
      if(live.legControl||['failed','complete'].includes(phase))return;
      input={v:clamp(m.v,-.36,.36),w:clamp(m.w,-.8,.8),brake:!!m.brake};if(Math.abs(input.v)+Math.abs(input.w)>.005||input.brake)follower=null;frame();
    }else if(m.type==='pause'){paused=!!m.value;input={v:0,w:0,brake:true};frame();}
    else if(m.type==='sensorLens'){sensorVerticalFov=clamp(m.verticalFov,15,120);live.sensorVerticalFov=sensorVerticalFov;postMessage({type:'observation',...live.observeRocks()});}
    else if(m.type==='observe'){scan=live.observeGate();postMessage({type:'observed',rocks:live.observeRocks(),scan:{...scan,points:scan.points.length}});frame();}
    else if(m.type==='gatePreview')await previewGate(m);
    else if(m.type==='cross')startCross(!!m.assisted);
    else if(m.type==='legAction'&&!paused){
      if((m.action==='lift'||!live.legControl)&&!stable()){reject('先刹车停稳，再抬腿。');return;}
      if(phase!=='crossing'){follower=null;routeSession=false;input={v:0,w:0,brake:true};cancel();}const ok=live.legAction(m.action);if(ok)actions++;else reject('先完成当前腿的动作，落地后再继续。');postMessage({type:'legCommand',ok,action:m.action});frame();
    }else if(m.type==='legSelect'){if(!live.legControl&&!stable()){reject('先停稳再选腿。');return;}if(phase!=='crossing'){follower=null;routeSession=false;input={v:0,w:0,brake:true};cancel();}live.selectLeg(m.index);frame();}
    else if(m.type==='wheelMode'){if(!live.resumeWheels())reject('把抬起的腿放稳，再回轮行。');input={v:0,w:0,brake:true};frame();}
    else if(m.type==='pose'&&!live.legControl){live.setPose(m.value);frame();}
  }catch(error){paused=true;postMessage({type:'error',message:error.message||String(error)});}
};
