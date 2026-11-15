import loadMujoco from './vendor/mujoco/mujoco.js';
import {inflateGzip,unpackTar,installAssets} from './robot-physics.js?v=mission-1';
import {MissionWorld,RouteFollower,clamp} from './mission-world.js?v=mission-1';
import {planRoute,modelWorlds,accepted} from './mission-planner.js?v=mission-1';
import {rehearseRoute,rehearseCrossing} from './mission-rehearsal.js?v=mission-1';

let mj,mission,world,phase='observation',paused=true,input={v:0,w:0,brake:true},follower=null,token=0,plan=null,preview=null,scan=null,gatePreview=null,dockState=null,held=0;
const yieldFrame=()=>new Promise(r=>setTimeout(r,0));
function frame(){if(!world)return;const data=world.renderData();postMessage({type:'state',state:{...world.state(),phase,paused,automatic:!!follower,scan:scan?{...scan,points:undefined}:null},data},Object.values(data).map(x=>x.buffer));}
function replace(file,initial=null){world?.destroy();world=new MissionWorld(mj,mission,file,initial);postMessage({type:'world',model:world.packet()});frame();}
function invalidate(){token++;preview=gatePreview=null;follower=null;paused=true;input={v:0,w:0,brake:true};}
async function previewRoute(message){
  invalidate();phase='preview';plan=planRoute(mission,message.selected,message.policy||'imagination');
  const worlds=modelWorlds(mission,message.selected),key=token;
  postMessage({type:'plan',plan,worlds});
  if(!plan.path||!worlds.length){postMessage({type:'previewDone',passed:false,reason:plan.path?'select_both_targets':plan.reason,results:[]});phase='candidates';return;}
  const results=[];
  for(let i=0;i<worlds.length;i++){
    if(key!==token)return;replace(worlds[i].file);postMessage({type:'previewProgress',index:i,total:worlds.length,world:worlds[i]});
    const result=await rehearseRoute(world,plan.path,{onFrame:frame,cancelled:()=>key!==token,yieldFrame});
    if(result.cancelled)return;results.push({...result,tasks:worlds[i].tasks});postMessage({type:'previewResult',index:i,result:results.at(-1)});
  }
  preview={passed:results.every(r=>r.passed),selected:[...message.selected],policy:message.policy||'imagination',results,plan};phase='decision';postMessage({type:'previewDone',...preview});frame();
}
async function previewGate(){
  if(!scan?.valid||!dockState){postMessage({type:'commandRejected',reason:'当前相机没有看清门槛，请重新对齐机器人。'});frame();return;}invalidate();const key=token;phase='gate-preview';replace('truth.xml',dockState);world.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};
  const result=await rehearseCrossing(world,{onFrame:frame,cancelled:()=>key!==token,yieldFrame});if(result.cancelled)return;
  gatePreview=result;phase='gate';replace('truth.xml',dockState);world.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};postMessage({type:'gatePreviewDone',result});frame();
}
async function tryWheels(){
  if(!dockState||phase!=='gate')return;const key=++token;phase='wheel-trial';paused=true;replace('truth.xml',dockState);
  let clear=false;
  for(let block=0;block<50;block++){
    for(let i=0;i<500;i++){if(key!==token)return;world.step(.18,0,false);}
    frame();clear=world.anchors().every(p=>p[0]-.086>mission.gate.far);if(clear||world.state().tilt>30)break;await yieldFrame();
  }
  const final=world.state();phase='gate';replace('truth.xml',dockState);world.course.barrier={near:scan.near,far:scan.far+.004,high:scan.high};postMessage({type:'wheelTrialDone',clear,final});frame();
}
function tick(){
  if(!world||paused||!['execute','gate','crossing','finish-drive'].includes(phase))return;
  for(let i=0;i<20;i++){
    let command=input;if(follower)command=follower.command(world);if(phase==='finish-drive'&&!world.legControl&&world.state().goalDistance<.35)command={v:0,w:0,brake:true};world.step(command.v,command.w,command.brake);
    if(world.steps%10===0){const s=world.state(),c=world.contacts();if(c.high||c.wall||c.gateBody||s.tilt>30||!s.finite||s.legs?.error){paused=true;follower=null;phase='failed';postMessage({type:'missionFailed',reason:s.legs?.error||'发生碰撞或失去平衡，请重新选择路线。'});break;}}
    if(phase==='execute'&&(follower?.done||(!follower&&Math.hypot(world.state().x-mission.dock[0],world.state().y-mission.dock[1])<.07&&world.state().speed<.02&&Math.abs(world.state().yaw)<.12))){
      follower=null;paused=true;input={v:0,w:0,brake:true};scan=world.observeGate();dockState=world.physicalState();phase='gate';postMessage({type:'gateObserved',scan:{...scan,points:scan.points.length}});break;
    }
    if(phase==='crossing'&&world.legControl.mode==='complete'){phase='finish-drive';postMessage({type:'crossed'});}
    if(phase==='finish-drive'){
      const s=world.state(),over=world.anchors().every(p=>p[0]-.086>mission.gate.far);held=s.goalDistance<.35&&s.speed<.035&&over&&!world.legControl?held+world.timestep:0;
      if(held>.35){phase='complete';paused=true;postMessage({type:'missionComplete',state:s});break;}
    }
  }
  frame();
}
onmessage=async({data:message})=>{
  try{
    if(message.type==='init'){
      mission=message.mission;const [wasm,bundle]=await Promise.all([inflateGzip(message.wasm),inflateGzip(message.bundle)]);mj=await loadMujoco({wasmBinary:wasm});installAssets(mj,unpackTar(bundle));replace('truth.xml');postMessage({type:'ready',engine:mj.mj_versionString()});setInterval(tick,20);
    }else if(message.type==='reset'){invalidate();phase='observation';scan=dockState=null;held=0;replace('truth.xml');postMessage({type:'resetDone'});}
    else if(message.type==='inspect'){invalidate();phase='candidates';const ids=message.selected.filter(id=>mission.candidates.some(c=>c.task_id===id&&accepted(c,mission.thresholds))),worlds=modelWorlds(mission,ids);if(worlds.length)replace(worlds[0].file);frame();}
    else if(message.type==='preview')await previewRoute(message);
    else if(message.type==='cancel'){invalidate();phase='candidates';frame();}
    else if(message.type==='execute'){
      if(!preview?.passed){postMessage({type:'commandRejected',reason:'先让所选模型中的完整预演通过。'});return;}
      token++;phase='execute';replace('truth.xml');follower=message.manual?null:new RouteFollower(preview.plan.path);paused=false;input={v:0,w:0,brake:true};frame();
    }else if(message.type==='input'){
      if(!['execute','gate','finish-drive'].includes(phase)||world.legControl)return;
      input={v:clamp(message.v,-.36,.36),w:clamp(message.w,-.8,.8),brake:!!message.brake};if(Math.abs(input.v)+Math.abs(input.w)>.005||input.brake)follower=null;frame();
    }else if(message.type==='follow'&&phase==='execute'){plan=planRoute(mission,preview.selected,preview.policy,[world.state().x,world.state().y]);if(plan.path){follower=new RouteFollower(plan.path);paused=false;}frame();}
    else if(message.type==='pause'){paused=message.value;input={v:0,w:0,brake:true};frame();}
    else if(message.type==='gatePreview')await previewGate();
    else if(message.type==='wheelTrial')await tryWheels();
    else if(message.type==='cross'){
      if(!gatePreview?.passed){postMessage({type:'commandRejected',reason:'先预演可见门槛的跨越动作。'});return;}
      phase='crossing';paused=false;input={v:0,w:0,brake:true};world.legAction('cross');frame();
    }else if(message.type==='legAction'&&phase==='crossing'&&!paused){const ok=world.legAction(message.action);postMessage({type:'legCommand',ok,action:message.action});frame();}
    else if(message.type==='legSelect'&&phase==='crossing'){world.selectLeg(message.index);frame();}
    else if(message.type==='wheelMode'&&phase==='finish-drive'){world.resumeWheels();input={v:0,w:0,brake:true};frame();}
    else if(message.type==='pose'&&!world.legControl){world.setPose(message.value);frame();}
  }catch(error){paused=true;postMessage({type:'error',message:error.message||String(error)});}
};
