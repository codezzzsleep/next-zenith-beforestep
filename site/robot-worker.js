import loadMujoco from './vendor/mujoco/mujoco.js';
import {RobotWorld,inflateGzip,unpackTar,installAssets,clamp} from './robot-physics.js';
let world,paused=true,input={v:0,w:0,brake:false},route=null,index=0,automatic=false;
let ticks=0,touch=false,brakeUntil=0,resetSeq=0;
function emit(){
  const state={...world.state(),paused,auto:automatic,bodyContact:touch,resetSeq,courseIndex:world.courseIndex,legs:world.legControl?.state()||null};
  const data={qpos:world.data.qpos.slice(),geom_xpos:world.data.geom_xpos.slice(),geom_xmat:world.data.geom_xmat.slice()};
  postMessage({type:'state',state,data},Object.values(data).map(x=>x.buffer));
}
function tick(){
  if(!world||paused)return;
  let {v,w,brake}=input;const before=world.state();
  if(automatic&&route){
    while(index<route.length-1&&Math.hypot(route[index][0]-before.x,route[index][1]-before.y)<.38)index++;
    const target=route[index],difference=Math.atan2(target[1]-before.y,target[0]-before.x)-before.yaw;
    const angle=Math.atan2(Math.sin(difference),Math.cos(difference));
    w=clamp(angle*2.5,-.95,.95);v=Math.abs(angle)>1?0:.34*Math.max(.16,Math.cos(angle)**3);
  }
  if(before.goalDistance<.5||before.elapsed<brakeUntil){v=w=0;brake=true;}
  for(let i=0;i<10;i++)world.step(v,w,brake);
  ticks++;
  if(ticks%5===0){touch=world.bodyContact();if(touch&&automatic){automatic=false;brakeUntil=world.elapsed+.5;}}
  const state=world.state();if(state.tilt>58||!state.finite){paused=true;automatic=false;input={v:0,w:0,brake:true};}
  emit();
}
onmessage=async event=>{
  try{
    const message=event.data;
    if(message.type==='init'){
      const [wasm,bundle]=await Promise.all([inflateGzip(message.wasm),inflateGzip(message.bundle)]);
      const mj=await loadMujoco({wasmBinary:wasm});installAssets(mj,unpackTar(bundle));world=new RobotWorld(mj,message.manifest);
      const m=world.model,model={ngeom:m.ngeom,nmesh:m.nmesh,thresholdGeom:world.geom.threshold,mesh_names:Array.from({length:m.nmesh},(_,i)=>mj.mj_id2name(m,10,i))};
      for(const key of ['geom_group','geom_type','geom_size','geom_dataid','mesh_vertadr','mesh_vertnum','mesh_faceadr','mesh_facenum','mesh_vert','mesh_face','geom_rgba','geom_matid','mat_rgba','mesh_pos','mesh_quat'])model[key]=m[key].slice();
      postMessage({type:'ready',model,engine:mj.mj_versionString()},Object.values(model).filter(ArrayBuffer.isView).map(x=>x.buffer));
      emit();setInterval(()=>{try{tick();}catch(e){paused=true;postMessage({type:'error',message:String(e)});}},20);
    }else if(message.type==='input'){
      input={v:clamp(message.v,-.45,.45),w:clamp(message.w,-.95,.95),brake:!!message.brake};
      if(Math.abs(input.v)>.005||Math.abs(input.w)>.005||input.brake)automatic=false;
    }else if(message.type==='paused'){paused=message.value;if(paused){automatic=false;input={v:0,w:0,brake:true};}emit();}
    else if(message.type==='pose'){if(!world.legControl)world.setPose(message.value);emit();}
    else if(message.type==='legSelect'){world.selectLeg(message.index);emit();}
    else if(message.type==='legAction'){automatic=false;input={v:0,w:0,brake:false};const ok=world.legAction(message.action);postMessage({type:'legCommand',ok,action:message.action});emit();}
    else if(message.type==='wheelMode'){const ok=world.resumeWheels();if(ok)world.setPose('high');postMessage({type:'legCommand',ok,action:'wheelMode'});emit();}
    else if(message.type==='reset'){automatic=false;touch=false;route=null;brakeUntil=0;input={v:0,w:0,brake:false};world.reset(message.index);resetSeq=message.seq;paused=!message.running;emit();}
    else if(message.type==='auto'){route=message.route;index=0;automatic=!!route;paused=false;input={v:0,w:0,brake:false};emit();}
    else if(message.type==='cancelAuto'){automatic=false;input={v:0,w:0,brake:false};emit();}
  }catch(e){postMessage({type:'error',message:String(e)});}
};
