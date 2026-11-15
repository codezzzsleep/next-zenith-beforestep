import {WheelLegControl} from './wheelleg-control.js';
/** Real MuJoCo control: only reset assigns pose; driving writes actuator torque. */
export const COURSES = [
  {id:'practice', title:'01 · 轮行与抬腿', goal:[2.4,0], start:[0,0], instruction:'先开进绿色区域，再停下来试试：选一条腿，抬起、前移、落地。', rocks:false, threshold:false},
  {id:'wheel-legs', title:'02 · 跨过门槛', goal:[3.4,0], start:[1.15,0], instruction:'12 厘米门槛横贯通道。先试轮行，再用逐腿跨越：每条腿的抬起、前移、落地由你决定。', rocks:false, threshold:true, barrier:{near:1.8,far:1.84,high:.12}},
  {id:'blind-rocks', title:'03 · 看清再绕行', goal:[10,0], start:[0,-.5], instruction:'高石超过抬腿能力。查看同一张照片生成的完整模型，选择绕行路线，自己开过去。', rocks:true, threshold:false},
];
export const clamp = (x,a,b)=>Math.max(a,Math.min(b,x));
const parts=['hip','thigh','calf'];
const legs=['FR','FL','RR','RL'];
const poses={normal:[0,.85,-1.65],high:[0,.55,-1.05],low:[0,1.0,-2.0]};

export async function inflateGzip(bytes){
  const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}
export function unpackTar(bytes){
  const decoder=new TextDecoder(), files=[];
  for(let offset=0;offset+512<=bytes.length;){
    const header=bytes.subarray(offset,offset+512);
    const name=decoder.decode(header.subarray(0,100)).split('\0')[0];
    if(!name)break;
    const size=parseInt(decoder.decode(header.subarray(124,136)).replace(/\0/g,'').trim(),8)||0;
    if(name.includes('..')||name.startsWith('/'))throw new Error('Invalid asset path');
    files.push({name,bytes:bytes.slice(offset+512,offset+512+size)});
    offset+=512+Math.ceil(size/512)*512;
  }
  return files;
}
export function installAssets(mj,files){
  mj.FS.mkdir('/play');mj.FS.mkdir('/play/assets');
  for(const file of files)mj.FS.writeFile('/play/'+file.name,file.bytes);
}
export class RobotWorld {
  constructor(mj, manifest){
    this.mj=mj;this.manifest=manifest;
    this.model=mj.MjModel.from_xml_path('/play/scene.xml');
    this.data=new mj.MjData(this.model);this.timestep=this.model.opt.timestep;
    this.joints={};
    const id=(kind,name)=>mj.mj_name2id(this.model,kind,name);
    for(const leg of legs)for(const part of [...parts,'wheel']){
      const joint=id(3,leg+'_'+part+'_joint');
      this.joints[leg+'_'+part]={q:this.model.jnt_qposadr[joint],id:joint,v:this.model.jnt_dofadr[joint],act:id(19,leg+'_'+part)};
    }
    this.geom={};for(const name of ['rock_A','rock_B','threshold','hypothesis_A','hypothesis_B'])this.geom[name]=id(5,name);
    this.base=id(1,'base_link');this.robotBodies=new Set();for(let body=1;body<this.model.nbody;body++){let parent=body;while(parent&&parent!==this.base)parent=this.model.body_parentid[parent];if(parent===this.base)this.robotBodies.add(body);}this.wheelBodies=new Set(legs.map(l=>id(1,l+'_wheel_link')));this.steps=0;
    this.course=COURSES[0];this.reset(0);
  }
  reset(index=this.courseIndex||0){
    this.courseIndex=index;this.course=COURSES[index];
    this.legControl?.destroy();this.legControl=null;this.poseName='normal';this.pose=[...poses.normal];this.driveV=0;this.driveW=0;
    const m=this.model,d=this.data;
    const a=this.geom.rock_A,b=this.geom.rock_B,t=this.geom.threshold;
    const bodyA=m.geom_bodyid[a],bodyB=m.geom_bodyid[b];
    m.body_pos.set(this.course.rocks?[4.55,-.735,0]:[100,0,0],bodyA*3);
    m.body_pos.set(this.course.rocks?[6.86,.22,0]:[100,0,0],bodyB*3);
    m.body_quat.set([Math.cos(Math.PI/4),0,0,Math.sin(Math.PI/4)],bodyA*4);
    const angle=-26*Math.PI/180;m.body_quat.set([Math.cos(angle/2),0,0,Math.sin(angle/2)],bodyB*4);
    m.geom_contype[t]=this.course.threshold?1:0;m.geom_conaffinity[t]=this.course.threshold?1:0;
    this.mj.mj_resetData(m,d);
    d.qpos.set(m.qpos0);d.qpos[0]=this.course.start[0];d.qpos[1]=this.course.start[1];d.qpos[2]=.42;
    d.qpos.set([1,0,0,0],3);
    for(const leg of legs)for(let k=0;k<3;k++)d.qpos[this.joints[leg+'_'+parts[k]].q]=this.pose[k];
    d.qvel.fill(0);d.ctrl.fill(0);this.mj.mj_forward(m,d);
    for(let i=0;i<700;i++)this.step(0,0,true);
    this.elapsed=0;this.steps=0;
    return this.state();
  }
  setPose(name){if(poses[name])this.poseName=name;}
  step(v=0,w=0,brake=false){
    if(this.legControl){this.legControl.tick();}else this.driveMotors(v,w,brake);
    this.mj.mj_step(this.model,this.data);this.steps++;this.elapsed=(this.elapsed||0)+this.timestep;
  }
  driveMotors(v=0,w=0,brake=false){
    const d=this.data,dt=this.timestep,q=d.qpos,velocity=d.qvel,ctrl=d.ctrl;
    const desired=poses[this.poseName];
    for(let i=0;i<3;i++)this.pose[i]+=clamp(desired[i]-this.pose[i],-.55*dt,.55*dt);
    this.driveV+=clamp(v-this.driveV,-.55*dt,.55*dt);
    this.driveW+=clamp(w-this.driveW,-2.0*dt,2.0*dt);
    // Close the yaw-rate loop through wheel torque. Four-wheel lateral scrub
    // otherwise makes the open-loop differential command sluggish on lunar ground.
    const yawCommand=clamp(this.driveW+3*(this.driveW-velocity[5]),-3.2,3.2);
    for(const leg of legs){
      for(let k=0;k<3;k++){
        const j=this.joints[leg+'_'+parts[k]];
        ctrl[j.act]=clamp(150*(this.pose[k]-q[j.q])-5*velocity[j.v],-45,45);
      }
      const j=this.joints[leg+'_wheel'];
      const target=clamp((this.driveV+(leg.endsWith('R')?1:-1)*yawCommand*.2837/2)/.08599,-6,6);
      ctrl[j.act]=brake?clamp(-6*velocity[j.v],-15,15):clamp(1.2*(target-velocity[j.v]),-15,15);
    }

  }
  legAction(action){
    if(this.state().speed>.08)return false;
    if(action==='cross'){const s=this.state();if(!this.course.barrier||Math.abs(s.y)>.18||Math.abs(s.yaw)>.2||s.x>this.course.barrier.near-.40)return false;}
    if(!this.legControl)this.legControl=new WheelLegControl(this);
    return this.legControl.command(action);
  }
  selectLeg(index){if(!this.legControl)this.legControl=new WheelLegControl(this);this.legControl.select(index);}
  resumeWheels(){if(this.legControl&&!this.legControl.busy&&!this.legControl.lifted&&!this.legControl.waiting){this.legControl.destroy();this.legControl=null;return true;}return false;}
  state(){
    const d=this.data,q=d.qpos;
    const yaw=Math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]*q[5]+q[6]*q[6]));
    const tilt=Math.acos(clamp(1-2*(q[4]*q[4]+q[5]*q[5]),-1,1))*180/Math.PI;
    return {x:q[0],y:q[1],z:q[2],yaw,tilt,speed:Math.hypot(d.qvel[0],d.qvel[1]),
      elapsed:this.elapsed,steps:this.steps,contacts:d.ncon,pose:this.poseName,
      goalDistance:Math.hypot(q[0]-this.course.goal[0],q[1]-this.course.goal[1]),
      finite:Array.from(q).every(Number.isFinite)};
  }
  bodyContact(){
    const contacts=this.data.contact;let touch=false;
    const obstacle=new Set([this.geom.rock_A,this.geom.rock_B,this.geom.threshold]);
    try{
      for(let i=0;i<contacts.size();i++){
        const c=contacts.get(i);
        try{
          const a=c.geom1,b=c.geom2;
          const robot=obstacle.has(a)?b:obstacle.has(b)?a:-1;if(robot>=0){const body=this.model.geom_bodyid[robot];if(this.robotBodies.has(body)&&!this.wheelBodies.has(body))touch=true;}
        }finally{c?.delete();}
      }
    }finally{contacts.delete();}
    return touch;
  }
  destroy(){this.legControl?.destroy();this.data.delete();this.model.delete();}
}

function inside(x,y,poly){
  let hit=false;
  for(let i=0,j=poly.length-1;i<poly.length;j=i++){
    const a=poly[i],b=poly[j];
    if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])hit=!hit;
  }
  return hit;
}
function polygonDistance(x,y,poly){
  if(inside(x,y,poly))return 0;
  let best=Infinity;
  for(let i=0;i<poly.length;i++){
    const a=poly[i],b=poly[(i+1)%poly.length],dx=b[0]-a[0],dy=b[1]-a[1];
    const u=clamp(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy||1),0,1);
    best=Math.min(best,Math.hypot(x-a[0]-u*dx,y-a[1]-u*dy));
  }
  return best;
}
/** Route uses retained generated polygons, never the collision-world rock meshes. */
export function modelRoute(start,goal,models){
  const res=.12,x0=-.9,y0=-2.3,nx=100,ny=39,pad=.58;
  const cell=p=>[clamp(Math.round((p[0]-x0)/res),0,nx-1),clamp(Math.round((p[1]-y0)/res),0,ny-1)];
  const point=i=>[x0+Math.floor(i/ny)*res,y0+(i%ny)*res];
  const block=new Uint8Array(nx*ny);
  for(let i=0;i<block.length;i++){
    const [x,y]=point(i);if(models.some(m=>polygonDistance(x,y,m.polygon)<pad))block[i]=1;
  }
  const s=cell(start),g=cell(goal),first=s[0]*ny+s[1],last=g[0]*ny+g[1];
  if(block[first]||block[last])return null;
  const distance=new Float64Array(block.length).fill(Infinity),parent=new Int32Array(block.length).fill(-1);
  const open=[first],closed=new Uint8Array(block.length);distance[first]=0;
  const heuristic=i=>{const p=point(i);return Math.hypot(p[0]-goal[0],p[1]-goal[1])/res;};
  while(open.length){
    let best=0;for(let k=1;k<open.length;k++)if(distance[open[k]]+heuristic(open[k])<distance[open[best]]+heuristic(open[best]))best=k;
    const current=open.splice(best,1)[0];if(closed[current])continue;
    if(current===last){
      const path=[];let node=last;while(node!==first){path.push(point(node));node=parent[node];}
      path.reverse();return [start,...path,goal];
    }
    closed[current]=1;const i=Math.floor(current/ny),j=current%ny;
    for(const [di,dj]of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]){
      const a=i+di,b=j+dj;if(a<0||a>=nx||b<0||b>=ny)continue;
      const next=a*ny+b;if(block[next]||closed[next]||(di&&dj&&(block[(i+di)*ny+j]||block[i*ny+j+dj])))continue;
      const value=distance[current]+Math.hypot(di,dj);
      if(value<distance[next]){distance[next]=value;parent[next]=current;open.push(next);}
    }
  }
  return null;
}
