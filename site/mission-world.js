import {WheelLegControl} from './wheelleg-control.js?v=mission-1';
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const legs=['FR','FL','RR','RL'],parts=['hip','thigh','calf'];
/** Independent truth or Lux-derived physical world. Only reset assigns state. */
export class MissionWorld{
  constructor(mj,mission,file='truth.xml',initial=null){
    this.mj=mj;this.manifest=mission;this.file=file;this.model=mj.MjModel.from_xml_path('/play/'+file);this.data=new mj.MjData(this.model);this.timestep=this.model.opt.timestep;
    const m=this.model,id=(type,name)=>mj.mj_name2id(m,type,name);this.base=id(1,'base_link');this.gate=id(5,'mission_gate');this.terrain=id(5,'terrain');
    this.joints={};for(const leg of legs)for(const part of [...parts,'wheel']){const j=id(3,leg+'_'+part+'_joint');this.joints[leg+'_'+part]={q:m.jnt_qposadr[j],v:m.jnt_dofadr[j],id:j,act:id(19,leg+'_'+part)};}
    this.wheelBodies=legs.map(l=>id(1,l+'_wheel_link'));this.robotBodies=new Set();this.highBodies=new Set([id(1,'obstacle0'),id(1,'obstacle1')]);this.obstacleBodies=new Set();
    for(let b=1;b<m.nbody;b++){let parent=b;while(parent&&parent!==this.base)parent=m.body_parentid[parent];if(parent===this.base)this.robotBodies.add(b);else if(mj.mj_id2name(m,1,b)?.startsWith('obstacle'))this.obstacleBodies.add(b);}
    this.course={start:mission.start,goal:mission.goal,barrier:{...mission.gate}};
    this.rayGeom=new mj.IntBuffer(1);this.rayNormal=new mj.DoubleBuffer(3);this.reset(initial);
  }
  ground(x,y){
    const m=this.model,id=m.geom_dataid[this.terrain],adr=m.hfield_adr[id],nr=m.hfield_nrow[id],nc=m.hfield_ncol[id],s=m.hfield_size.slice(id*4,id*4+4),p=m.geom_pos.slice(this.terrain*3,this.terrain*3+3);
    const u=clamp((x-p[0]+s[0])/(2*s[0])*(nc-1),0,nc-1),v=clamp((y-p[1]+s[1])/(2*s[1])*(nr-1),0,nr-1),c0=Math.floor(u),r0=Math.floor(v),c1=Math.min(c0+1,nc-1),r1=Math.min(r0+1,nr-1),fu=u-c0,fv=v-r0,a=m.hfield_data;
    return p[2]+s[2]*(a[adr+r0*nc+c0]*(1-fu)*(1-fv)+a[adr+r0*nc+c1]*fu*(1-fv)+a[adr+r1*nc+c0]*(1-fu)*fv+a[adr+r1*nc+c1]*fu*fv);
  }
  reset(initial=null){
    this.legControl?.destroy();this.legControl=null;this.driveV=this.driveW=0;this.poseName='normal';this.pose=[0,.85,-1.65];const m=this.model,d=this.data;this.mj.mj_resetData(m,d);d.qpos.set(m.qpos0);
    if(initial){d.qpos.set(initial.qpos);d.qvel.set(initial.qvel);this.poseName=initial.poseName||'normal';if(initial.pose)this.pose=[...initial.pose];this.driveV=initial.driveV||0;this.driveW=initial.driveW||0;}
    else{d.qpos[0]=this.manifest.start[0];d.qpos[1]=this.manifest.start[1];d.qpos[2]=this.ground(d.qpos[0],d.qpos[1])+.42;d.qpos.set([1,0,0,0],3);for(const leg of legs)for(let k=0;k<3;k++)d.qpos[this.joints[leg+'_'+parts[k]].q]=this.pose[k];d.qvel.fill(0);}
    d.ctrl.fill(0);this.mj.mj_forward(m,d);this.steps=0;this.elapsed=0;
    if(!initial)for(let i=0;i<700;i++)this.step(0,0,true);this.steps=0;this.elapsed=0;
  }
  setPose(name){if(['normal','high','low'].includes(name))this.poseName=name;}
  driveMotors(v=0,w=0,brake=false){
    const dt=this.timestep,d=this.data,q=d.qpos,velocity=d.qvel;
    const desired=this.poseName==='high'?[0,.55,-1.05]:this.poseName==='low'?[0,1,-2]:[0,.85,-1.65];for(let k=0;k<3;k++)this.pose[k]+=clamp(desired[k]-this.pose[k],-.55*dt,.55*dt);
    this.driveV+=clamp(v-this.driveV,-.55*dt,.55*dt);this.driveW+=clamp(w-this.driveW,-2*dt,2*dt);const yaw=clamp(this.driveW+3*(this.driveW-velocity[5]),-3.2,3.2);
    for(const leg of legs){for(let k=0;k<3;k++){const j=this.joints[leg+'_'+parts[k]];d.ctrl[j.act]=clamp(150*(this.pose[k]-q[j.q])-5*velocity[j.v],-45,45);}
      const j=this.joints[leg+'_wheel'],target=clamp((this.driveV+(leg.endsWith('R')?1:-1)*yaw*.2837/2)/.08599,-6,6);d.ctrl[j.act]=brake?clamp(-6*velocity[j.v],-15,15):clamp(1.2*(target-velocity[j.v]),-15,15);}
  }
  step(v=0,w=0,brake=false){if(this.legControl)this.legControl.tick();else this.driveMotors(v,w,brake);this.mj.mj_step(this.model,this.data);this.steps++;this.elapsed+=this.timestep;}
  state(){
    const q=this.data.qpos,v=this.data.qvel,yaw=Math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2)),tilt=Math.acos(clamp(1-2*(q[4]**2+q[5]**2),-1,1))*180/Math.PI;
    return {x:q[0],y:q[1],z:q[2],poseName:this.poseName,yaw,tilt,speed:Math.hypot(v[0],v[1]),elapsed:this.elapsed,steps:this.steps,finite:Array.from(q).every(Number.isFinite),goalDistance:Math.hypot(q[0]-this.course.goal[0],q[1]-this.course.goal[1]),legs:this.legControl?.state()||null};
  }
  anchors(){return this.wheelBodies.map(b=>Array.from(this.data.xpos.slice(b*3,b*3+3)));}
  contacts(){
    const contacts=this.data.contact;let high=false,wall=false,gateBody=false,groundBody=false;
    try{for(let i=0;i<contacts.size();i++){const c=contacts.get(i);try{
      const ba=this.model.geom_bodyid[c.geom1],bb=this.model.geom_bodyid[c.geom2];if(!this.robotBodies.has(ba)&&!this.robotBodies.has(bb))continue;
      const robot=this.robotBodies.has(ba)?ba:bb,other=this.robotBodies.has(ba)?bb:ba,g=this.robotBodies.has(ba)?c.geom2:c.geom1,wheel=this.wheelBodies.includes(robot);
      if(this.highBodies.has(other))high=true;else if(this.obstacleBodies.has(other))wall=true;
      if(g===this.gate&&!wheel)gateBody=true;if(g===this.terrain&&!wheel)groundBody=true;
    }finally{c.delete();}}}finally{contacts.delete();}return {high,wall,gateBody,groundBody};
  }
  bodyContact(){const c=this.contacts();return c.gateBody||c.high||c.wall;}
  physicalState(){return {qpos:Array.from(this.data.qpos),qvel:Array.from(this.data.qvel),poseName:this.poseName,pose:[...this.pose],driveV:this.driveV,driveW:this.driveW};}
  legAction(action){if(!this.legControl)this.legControl=new WheelLegControl(this);return this.legControl.command(action);}
  selectLeg(index){if(!this.legControl)this.legControl=new WheelLegControl(this);this.legControl.select(index);}
  resumeWheels(){if(this.legControl&&!this.legControl.busy&&!this.legControl.lifted&&!this.legControl.waiting){this.legControl.destroy();this.legControl=null;this.setPose('high');return true;}return false;}
  /** Rays from the current robot camera, retaining only visible threshold hits. */
  observeGate(){
    const s=this.state(),camera=[s.x+.42*Math.cos(s.yaw),s.y+.42*Math.sin(s.yaw),s.z-.00125],points=[];
    for(let x=camera[0]+.1;x<=camera[0]+.95;x+=.004)for(let y=s.y-.25;y<=s.y+.25;y+=.014){
      let vector=[x-camera[0],y-camera[1],-camera[2]],length=Math.hypot(...vector);vector=vector.map(v=>v/length);const pitch=Math.atan2(-vector[2],Math.hypot(vector[0],vector[1]))*180/Math.PI,azimuth=Math.atan2(Math.sin(Math.atan2(vector[1],vector[0])-s.yaw),Math.cos(Math.atan2(vector[1],vector[0])-s.yaw));if(Math.abs(pitch-24.83)>35||Math.abs(azimuth)>34*Math.PI/180)continue;
      const distance=this.mj.mj_ray(this.model,this.data,camera,vector,[1,0,0,0,0,0],true,this.base,this.rayGeom,this.rayNormal);
      if(distance>0&&this.rayGeom.GetView()[0]===this.gate)points.push(vector.map((v,k)=>camera[k]+distance*v));
    }
    if(points.length<10)return {valid:false,reason:'threshold_not_visible_from_current_pose',camera,points};
    const near=Math.min(...points.map(p=>p[0])),far=Math.max(...points.map(p=>p[0])),high=Math.max(...points.map(p=>p[2]));
    return {valid:true,near,far,high,heightAboveGround:high-this.ground((near+far)/2,s.y),depth:far-near,camera,points:points.filter((_,i)=>i%Math.max(1,Math.floor(points.length/400))===0),source:'Current MuJoCo camera rays; visible geometry, no Lux3D request'};
  }
  /** Live sensor rays; only hit surfaces are exposed in every player camera. */
  observeRocks(){
    const s=this.state(),r=this.data.xmat.slice(this.base*9,this.base*9+9),rotate=v=>[0,1,2].map(i=>r[i*3]*v[0]+r[i*3+1]*v[1]+r[i*3+2]*v[2]),offset=rotate([.42,0,-.00125]),camera=[s.x+offset[0],s.y+offset[1],s.z+offset[2]],hits=[],targets=new Set();
    for(let col=0;col<60;col++)for(let row=0;row<34;row++){
      const az=(col/59-.5)*68*Math.PI/180,pitch=(-6+(row/33-.5)*(this.sensorVerticalFov||45))*Math.PI/180;
      const ray=rotate([Math.cos(pitch)*Math.cos(az),Math.cos(pitch)*Math.sin(az),Math.sin(pitch)]);
      const distance=this.mj.mj_ray(this.model,this.data,camera,ray,[1,0,0,0,0,0],true,this.base,this.rayGeom,this.rayNormal);
      const g=this.rayGeom.GetView()[0],b=g>=0?this.model.geom_bodyid[g]:-1;
      if(distance>0&&this.highBodies.has(b)){
        const target=b===this.mj.mj_name2id(this.model,1,'obstacle0')?'T1':'T2';targets.add(target);hits.push({target,point:ray.map((v,k)=>camera[k]+distance*v),normal:Array.from(this.rayNormal.GetView())});
      }
    }
    return {camera,hits,targets:[...targets],source:'Live MuJoCo visible-surface rays'};
  }
  packet(){
    const m=this.model,model={ngeom:m.ngeom,nmesh:m.nmesh,file:this.file,geom_roles:Array.from({length:m.ngeom},(_,g)=>{const b=m.geom_bodyid[g];return this.highBodies.has(b)?(b===this.mj.mj_name2id(m,1,'obstacle0')?'T1':'T2'):this.robotBodies.has(b)?'robot':'environment';}),leg_geoms:Array.from({length:m.ngeom},(_,g)=>this.wheelBodies.indexOf(m.geom_bodyid[g])),mesh_names:Array.from({length:m.nmesh},(_,i)=>this.mj.mj_id2name(m,10,i))};
    for(const key of ['geom_group','geom_type','geom_size','geom_dataid','mesh_vertadr','mesh_vertnum','mesh_faceadr','mesh_facenum','mesh_vert','mesh_face','geom_rgba','geom_matid','mat_rgba','mesh_pos','mesh_quat','hfield_adr','hfield_nrow','hfield_ncol','hfield_size','hfield_data'])model[key]=m[key].slice();return model;
  }
  renderData(){return {qpos:this.data.qpos.slice(),geom_xpos:this.data.geom_xpos.slice(),geom_xmat:this.data.geom_xmat.slice()};}
  destroy(){this.legControl?.destroy();this.rayGeom.delete();this.rayNormal.delete();this.data.delete();this.model.delete();}
}
/** Piecewise straight route with observed-position and heading feedback. */
export class RouteFollower{
  constructor(path){this.path=path;this.index=1;this.done=false;this.phase='turn';this.origin=null;}
  command(world){
    const s=world.state(),stop={v:0,w:0,brake:true},wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));if(this.done)return stop;
    const t=this.path[this.index],distance=Math.hypot(t[0]-s.x,t[1]-s.y);
    if(this.phase==='brake'){
      if(s.speed>.012)return stop;
      if(this.index<this.path.length-1){this.index++;this.phase='turn';this.origin=null;}else this.phase='align';
      return stop;
    }
    if(this.phase==='align'){
      const angle=wrap(-s.yaw);if(Math.abs(angle)<.03){this.done=true;return stop;}return {v:0,w:Math.sign(angle)*Math.max(.18,Math.min(.65,Math.abs(angle)*3)),brake:false};
    }
    if(this.phase==='turn'){
      const angle=wrap(Math.atan2(t[1]-s.y,t[0]-s.x)-s.yaw);
      if(Math.abs(angle)<.03){this.phase='drive';this.origin=[s.x,s.y];return stop;}
      return {v:0,w:Math.sign(angle)*Math.max(.18,Math.min(.65,Math.abs(angle)*3)),brake:false};
    }
    if(distance<.035){this.phase='brake';return stop;}
    const dx=t[0]-this.origin[0],dy=t[1]-this.origin[1],length=Math.hypot(dx,dy),cross=(-(s.x-this.origin[0])*dy+(s.y-this.origin[1])*dx)/length;
    const angle=wrap(Math.atan2(dy,dx)-clamp(2*cross,-.35,.35)-s.yaw);
    return {v:Math.min(.23,Math.max(.025,.65*distance)),w:clamp(angle*3,-.7,.7),brake:false};
  }
}
