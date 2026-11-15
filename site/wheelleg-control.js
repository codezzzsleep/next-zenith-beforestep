/** Interactive wheel-leg control, derived from the retained v72 analytic controller.
 * Every movement is applied as motor torque. Players gate each lift / swing / land.
 * The research controller and its recorded results remain unchanged.
 */
const R=.086, L1=.213,L2=.2264,SIDE=.0955;
export const LEG_NAMES=['FR','FL','RR','RL'];
const HIP=[[.1934,-.0465,0],[.1934,.0465,0],[-.1934,-.0465,0],[-.1934,.0465,0]];
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const copy=a=>a.map(x=>[...x]);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const rot=(m,v)=>[0,1,2].map(i=>m[i*3]*v[0]+m[i*3+1]*v[1]+m[i*3+2]*v[2]);
const transpose=m=>[m[0],m[3],m[6],m[1],m[4],m[7],m[2],m[5],m[8]];
function solve(a,b){
  const m=a.map((r,i)=>[...r,b[i]]),n=b.length;
  for(let k=0;k<n;k++){
    let p=k;for(let i=k+1;i<n;i++)if(Math.abs(m[i][k])>Math.abs(m[p][k]))p=i;
    if(Math.abs(m[p][k])<1e-9)return Array(n).fill(1/n);
    [m[k],m[p]]=[m[p],m[k]];const q=m[k][k];for(let j=k;j<=n;j++)m[k][j]/=q;
    for(let i=0;i<n;i++)if(i!==k){const v=m[i][k];for(let j=k;j<=n;j++)m[i][j]-=v*m[k][j];}
  }return m.map(r=>r[n]);
}
function weights(points,target){
  const a=[points.map(()=>1),points.map(p=>p[0]),points.map(p=>p[1])];
  const aa=a.map(r=>a.map(s=>r.reduce((v,x,i)=>v+x*s[i],0)));
  const v=solve(aa,[1,...target]);return points.map((_,k)=>a.reduce((s,r,i)=>s+r[k]*v[i],0));
}
export function legIK(relative,j){
  const [x,y,z]=sub(relative,HIP[j]),a=SIDE*(j===0||j===2?-1:1);
  const z0=-Math.sqrt(Math.max(1e-9,y*y+z*z-a*a));
  let hip=Math.atan2(z,y)-Math.atan2(z0,a);hip=Math.atan2(Math.sin(hip),Math.cos(hip));
  const cosine=(x*x+z0*z0-L1*L1-L2*L2)/(2*L1*L2);
  if(cosine < -1.0001||cosine>1.0001)return null;
  const calf=-Math.acos(clamp(cosine,-1,1));
  return [hip,Math.atan2(-x,-z0)-Math.atan2(L2*Math.sin(calf),L1+L2*Math.cos(calf)),calf];
}
export class WheelLegControl {
  constructor(world){
    this.w=world;this.mj=world.mj;this.m=world.model;this.d=world.data;
    this.bodies=LEG_NAMES.map(l=>this.mj.mj_name2id(this.m,1,l+'_wheel_link'));
    this.geoms=this.bodies.map(b=>Array.from(this.m.geom_bodyid).map((v,i)=>v===b?i:-1).filter(i=>i>=0));
    this.ground=new Set(Array.from(this.m.geom_type).map((t,i)=>t===0?i:-1).filter(i=>i>=0));
    this.jac=new this.mj.DoubleBuffer(this.m.nv*3);this.ang=new this.mj.DoubleBuffer(this.m.nv*3);this.force=new this.mj.DoubleBuffer(6);
    this.base=Array.from(this.d.qpos.slice(0,3));this.feet=this.anchors();this.yaw=world.state().yaw;
    this.swing=null;this.unloading=false;this.unloadFraction=1;this.adjust=[0,0,0,0];
    this.targets=this.jointPose();this.omega=[0,0,0,0];this.selected=0;this.busy=false;this.waiting=null;this.mode='manual';this.phase='ready';this.moves=0;this.crossed=[];this.error=null;
    this.lifted=false;this.manualOrigin=null;this.clock=0;this.iterator=null;
  }
  anchors(){return this.bodies.map(b=>Array.from(this.d.xpos.slice(b*3,b*3+3)));}
  jointPose(){return LEG_NAMES.map(l=>['hip','thigh','calf'].map(p=>this.d.qpos[this.w.joints[l+'_'+p].q]));}
  rotation(){return Array.from(this.d.xmat.slice(this.w.base*9,this.w.base*9+9));}
  contacts(){
    const points=this.anchors().map(p=>[p[0],p[1],0]),loads=[0,0,0,0],totals=Array.from({length:4},()=>[0,0,0]);
    const contacts=this.d.contact;
    try{for(let i=0;i<contacts.size();i++){
      const c=contacts.get(i);try{
        for(const [wheel,other]of [[c.geom1,c.geom2],[c.geom2,c.geom1]]){
          const j=this.geoms.findIndex(g=>g.includes(wheel));if(j<0||!this.ground.has(other))continue;
          this.mj.mj_contactForce(this.m,this.d,i,this.force);const f=Math.max(0,this.force.GetView()[0]);
          loads[j]+=f;for(let k=0;k<3;k++)totals[j][k]+=f*c.pos[k];
        }
      }finally{c.delete();}
    }}finally{contacts.delete();}
    for(let j=0;j<4;j++)if(loads[j]>1e-6)points[j]=totals[j].map(x=>x/loads[j]);
    return {points,loads};
  }
  inverseForces(points){
    const required=Array.from(this.d.qfrc_bias),rotation=this.rotation();
    const keep=[0,1,2,3].filter(j=>j!==this.swing),root=this.d.qpos;
    const moment=rot(rotation,required.slice(3,6)),f=required.slice(0,3);f[2]=clamp(f[2],5,80);
    let size=Math.hypot(f[0],f[1]);if(size>.55*f[2]){f[0]*=.55*f[2]/size;f[1]*=.55*f[2]/size;}
    const height=Math.max(.1,root[2]-keep.reduce((s,j)=>s+points[j][2],0)/keep.length);
    const cop=[root[0]+(-moment[1]-height*f[0])/f[2],root[1]+(moment[0]-height*f[1])/f[2]];
    let w=weights(keep.map(j=>points[j]),cop).map(v=>Math.max(.02,v));let total=w.reduce((a,b)=>a+b);w=w.map(v=>v/total);
    let ids=keep;
    if(this.swing!==null&&this.unloadFraction<1){
      const three=[0,0,0,0];keep.forEach((j,k)=>three[j]=w[k]);total=this.unloadLoads.reduce((a,b)=>a+b);
      w=this.unloadLoads.map((v,j)=>(1-this.unloadFraction)*v/total+this.unloadFraction*three[j]);ids=[0,1,2,3];
    }
    const centre=[0,1].map(k=>ids.reduce((s,j,i)=>s+w[i]*points[j][k],0));
    const lever=ids.map(j=>[points[j][0]-centre[0],points[j][1]-centre[1]]);
    const den=Math.max(1e-6,lever.reduce((s,p,i)=>s+w[i]*(p[0]**2+p[1]**2),0));
    const yaw=moment[2]-((centre[0]-root[0])*f[1]-(centre[1]-root[1])*f[0]);
    const tau=[...required];
    ids.forEach((j,k)=>{
      const normal=w[k]*f[2],horizontal=[w[k]*(f[0]-yaw*lever[k][1]/den),w[k]*(f[1]+yaw*lever[k][0]/den)];
      size=Math.hypot(...horizontal);if(size>.55*normal){horizontal[0]*=.55*normal/size;horizontal[1]*=.55*normal/size;}
      this.mj.mj_jac(this.m,this.d,this.jac,this.ang,points[j],this.bodies[j]);const jac=this.jac.GetView();
      for(let v=0;v<this.m.nv;v++)tau[v]-=jac[v]*horizontal[0]+jac[this.m.nv+v]*horizontal[1]+jac[2*this.m.nv+v]*normal;
    });return tau;
  }
  *move({base=this.base,feet=this.feet,seconds=2,phase='balance'}={}){
    const b0=[...this.base],f0=copy(this.feet),b=[...base],f=copy(feet);this.phase=phase;
    seconds*=this.mode==='crossing'?.5:.7;const n=Math.round(seconds/.01);
    for(let i=0;i<n;i++){
      const u=(i+1)/n,s=u*u*(3-2*u),v=6*u*(1-u)/seconds;
      yield {b:b.map((x,k)=>b0[k]+(x-b0[k])*s),f:f.map((p,j)=>p.map((x,k)=>f0[j][k]+(x-f0[j][k])*s)),fv:f.map((p,j)=>p.map((x,k)=>(x-f0[j][k])*v)),s,phase};
    }
    this.base=b;this.feet=f;
  }
  *balance(j){
    const margin=j===2?.16:.07;
    for(let k=0;k<5;k++){
      const {points,loads}=this.contacts(),keep=[0,1,2,3].filter(n=>n!==j),com=Array.from(this.d.subtree_com.slice(this.w.base*3,this.w.base*3+2));
      const w=weights(keep.map(n=>points[n]),com);if(Math.min(...w)>=margin&&keep.every(n=>loads[n]>1e-4))return;
      let safe=w.map(v=>Math.max(v,margin+.02)),sum=safe.reduce((a,b)=>a+b);safe=safe.map(v=>v/sum);
      const b=[...this.base];for(let a=0;a<2;a++)b[a]+=1.3*(keep.reduce((s,n,i)=>s+safe[i]*points[n][a],0)-com[a]);
      yield* this.move({base:b,seconds:2.5,phase:'balance'});
    }
  }
  *unload(j){
    yield* this.balance(j);this.feet[j][0]=this.anchors()[j][0];this.feet[j][1]=this.anchors()[j][1];
    this.unloadLoads=this.contacts().loads.map(v=>Math.max(.001,v));this.unloadInitial=copy(this.targets);this.swing=j;this.unloading=true;
    const f=copy(this.feet);f[j][2]+=.015;yield* this.move({feet:f,seconds:3,phase:'unload'});
    this.unloading=false;const actual=this.jointPose()[j],rotation=this.rotation(),axis=rotation[7]*Math.cos(actual[0])+rotation[8]*Math.sin(actual[0]),side=j===0||j===2?-1:1;
    const radius=R*Math.sqrt(Math.max(0,1-axis*axis))+.02630213*Math.abs(axis);
    this.feet[j]=this.anchors()[j];this.feet[j][2]=this.feet[j][2]-radius+side*.0503699327*axis+R;
  }
  *gate(action,j){this.selected=j;yield {gate:action,leg:j};}
  *swingTo(j,target,height,phase,gated=false){
    if(gated)yield* this.gate('lift',j);
    yield* this.unload(j);let f=copy(this.feet),b=[...this.base];f[j][2]=height;
    if(phase==='RL'){b[0]=this.far+.22+Math.max(0,this.high-.12)*2/3;b[2]=Math.max(.38,this.high+.27);f[j][1]=target[1];}
    else if(phase!=='RR')f[j][1]=target[1];
    yield* this.move({base:b,feet:f,seconds:phase==='RL'?4:2.5,phase:'lift'});this.lifted=true;
    if(gated)yield* this.gate('advance',j);
    f=copy(this.feet);f[j][0]=target[0];f[j][1]=target[1];b=[...this.base];
    if(phase==='front-right'){b[0]-=.06*(target[0]-this.feet[j][0]);b[2]-=.005;}
    yield* this.move({base:b,feet:f,seconds:Math.max(2,Math.hypot(...sub(f[j],this.feet[j]).slice(0,2))/.08),phase:'advance'});
    if(gated)yield* this.gate('land',j);
    if(phase==='front-right'){b=[...this.base];b[0]+=.020;yield* this.move({base:b,seconds:2,phase:'align'});}
    if(phase==='front-left'){
      b=[...this.base];b[0]=this.near;b[1]=this.lateral-.025;b[2]=Math.max(.38,this.high+.26);f=copy(this.feet);f[0][0]=this.far+.25;f[2][0]=f[3][0]=this.near-.24;
      yield* this.move({base:b,feet:f,seconds:8,phase:'balance'});
    }
    if(phase==='RR'){
      b=[...this.base];b[0]=this.far+.13;b[2]=Math.max(.39,this.high+.28);f=copy(this.feet);f[3][0]=this.near-.10;f[j][2]=target[2]+.05;
      yield* this.move({base:b,feet:f,seconds:4,phase:'balance'});
    }
    if(phase==='RL'){
      b=[...this.base];b[0]=this.far+.20;b[1]=this.lateral+.04;f=copy(this.feet);f[0][0]=f[1][0]=this.far+.32;
      yield* this.move({base:b,feet:f,seconds:4,phase:'balance'});
    }
    f=copy(this.feet);f[j][2]=target[2]-.003;yield* this.move({feet:f,seconds:4,phase:'land'});
    this.swing=null;this.lifted=false;yield* this.move({seconds:.5,phase:'seat'});if(gated)this.crossed.push(j);
  }
  *crossing(){
    const {near,far,high}=this.w.course.barrier;this.near=near;this.far=far;this.high=high;this.lateral=0;
    // Approach through wheel motors, stopping before the obstacle.
    this.phase='approach';for(let i=0;i<2000&&Math.min(...this.anchors().slice(0,2).map(p=>p[0]))<near-R-.040;i++)yield {drive:.07};
    this.base=Array.from(this.d.qpos.slice(0,3));this.feet=this.anchors();this.targets=this.jointPose();
    let b=[...this.base];b[0]-=.04;b[1]=-.055;b[2]=.32;yield* this.move({base:b,seconds:3,phase:'prepare'});
    let target=[near-.10,-.015,R+.001];yield* this.swingTo(1,target,R+.06,'narrow-left');
    b=[near-.33,.02,Math.max(.38,high+.27)];let f=copy(this.feet);f[2][0]=f[3][0]=near-.43;yield* this.move({base:b,feet:f,seconds:5,phase:'prepare'});
    b[0]=near-.12;f[2][0]=f[3][0]=near-.33;yield* this.move({base:b,feet:f,seconds:8,phase:'prepare'});
    const landing=far+R+.055,lift=high+R+.035;
    yield* this.swingTo(0,[landing,-.10,R+.001],lift,'front-right',true);
    b=[near-.06,-.085,Math.max(.38,high+.26)];yield* this.move({base:b,seconds:3,phase:'prepare'});
    yield* this.swingTo(1,[landing,.142,R+.001],lift,'front-left',true);
    b=[far-.10,-.025,Math.max(.38,high+.26)];f=copy(this.feet);f[0][0]=f[1][0]=far+.23;f[2][0]=f[3][0]=near-R-.040;yield* this.move({base:b,feet:f,seconds:5,phase:'body-over'});
    target=[...this.feet[3]];target[1]=-.04;target[2]=R+.001;yield* this.swingTo(3,target,R+.06,'narrow-rear-left');
    yield* this.move({base:[far+.10,0,Math.max(.38,high+.26)],seconds:4,phase:'body-over'});
    for(const [j,side]of [[2,1],[3,-1]]){
      b=[...this.base];b[1]=side*.025;b[0]=far+.10;b[2]=Math.max(.405,high+.285);f=copy(this.feet);
      if(j===3){b=[far+.17,0,Math.max(.38,high+.275)];f[0][0]=f[1][0]=far+.29;f[2][0]=far+R+.025;f[3][0]=near-.10;}
      yield* this.move({base:b,feet:f,seconds:3,phase:'prepare'});
      yield* this.swingTo(j,[far+R+.025,j===2?.015:.142,R+.001],lift,LEG_NAMES[j],true);
    }
    f=copy(this.feet);f[0][0]=f[1][0]=far+.60;f[2][0]=f[3][0]=far+.20;f.forEach((p,j)=>p[1]=j===0||j===2?-.142:.142);
    yield* this.move({base:[far+.39,0,.46],feet:f,seconds:7,phase:'restore'});
    this.phase='done';this.mode='complete';
  }
  *manual(action){
    const j=this.selected;
    if(action==='lift'){
      this.manualOrigin=[...this.anchors()[j]];yield* this.unload(j);const f=copy(this.feet);f[j][2]=Math.max(this.feet[j][2]+.075,R+.09);
      yield* this.move({feet:f,seconds:2.5,phase:'lift'});this.lifted=true;
    }else if(action==='advance'){
      const f=copy(this.feet),rotation=this.rotation();f[j][0]+=.10*rotation[0];f[j][1]+=.10*rotation[3];yield* this.move({feet:f,seconds:2,phase:'advance'});
    }else if(action==='land'){
      const f=copy(this.feet);f[j][2]=this.manualOrigin[2]-.003;yield* this.move({feet:f,seconds:4,phase:'land'});this.swing=null;this.lifted=false;yield* this.move({seconds:.5,phase:'seat'});
    }
  }
  command(action){
    if(this.error)return false;
    if(this.waiting){if(action!==this.waiting.action||this.selected!==this.waiting.leg)return false;this.waiting=null;this.busy=true;return true;}
    if(this.busy)return false;
    if(action==='cross'){
      if(!this.w.course.barrier)return false;
      const s=this.w.state();if(Math.abs(s.y)>.18||Math.abs(s.yaw)>.2||s.x>this.w.course.barrier.near-.40)return false;
      this.mode='crossing';this.iterator=this.crossing();this.busy=true;return true;
    }
    if(this.mode==='crossing'||(action==='lift'&&this.lifted)||(action!=='lift'&&!this.lifted))return false;
    this.iterator=this.manual(action);this.busy=true;return true;
  }
  select(j){if(!this.busy&&!this.lifted&&j>=0&&j<4)this.selected=j;}
  compute(frame){
    if(frame.drive!==undefined){this.w.driveMotors(frame.drive,0,false);return;}
    const {b,f,fv,s,phase}=frame;this.phase=phase;this.unloadFraction=phase==='unload'?s:1;
    const rotation=this.rotation(),level=[Math.cos(this.yaw),-Math.sin(this.yaw),0,Math.sin(this.yaw),Math.cos(this.yaw),0,0,0,1];
    const {points,loads}=this.contacts(),actual=this.jointPose(),references=copy(actual);
    for(let j=0;j<4;j++){
      const swing=j===this.swing&&!this.unloading;
      if(j!==this.swing)this.adjust[j]=clamp(this.adjust[j]+.01*(.0003*Math.min(4,Math.max(0,loads[j]-1))-.003*Math.max(0,1-loads[j])),-.025,0);
      const posture=[...b];for(let k=0;k<2;k++)posture[k]+=clamp(.8*(b[k]-this.d.qpos[k]),-.06,.06);
      const origin=swing?Array.from(this.d.qpos.slice(0,3)):posture,rotmat=swing?rotation:level,point=[...f[j]],adjust=swing?0:this.adjust[j];
      let q=legIK(rot(transpose(rotmat),sub(point,origin)),j),valid=!!q;
      if(q)for(let k=0;k<3;k++){
        const axis=rotmat[7]*Math.cos(q[0])+rotmat[8]*Math.sin(q[0]),side=j===0||j===2?-1:1,radius=R*Math.sqrt(Math.max(0,1-axis*axis))+.02630213*Math.abs(axis);
        point[2]=f[j][2]+radius-side*.0503699327*axis-R+adjust;q=legIK(rot(transpose(rotmat),sub(point,origin)),j);if(!q){valid=false;break;}
      }
      if(valid)references[j]=q;
      else if(swing){this.error='脚轮目标超出当前可达范围，请重新开始并缩短前移距离。';this.busy=false;this.iterator=null;}
    }
    const tau=this.inverseForces(points);
    for(let j=0;j<4;j++)for(let k=0;k<3;k++){
      const joint=this.w.joints[LEG_NAMES[j]+'_'+['hip','thigh','calf'][k]],range=this.m.jnt_range.slice(joint.id*2,joint.id*2+2);
      let target=clamp(references[j][k]+clamp(tau[joint.v],-10,10)/150,range[0],range[1]);
      if(phase==='unload')target=(1-s)*this.unloadInitial[j][k]+s*target;
      this.targets[j][k]=target;
    }
    const anchors=this.anchors();
    this.omega=LEG_NAMES.map((leg,j)=>{
      const turn=this.d.qvel[this.w.joints[leg+'_thigh'].v]+this.d.qvel[this.w.joints[leg+'_calf'].v]+this.d.qvel[4];
      let value=-turn;if(j!==this.swing||this.unloading)value+=fv[j][0]/R+8*(f[j][0]-anchors[j][0])/R;
      return clamp(value,-.15/R,.15/R);
    });
  }
  tick(){
    if(this.clock++%5===0){
      if(this.iterator&&!this.waiting){
        const next=this.iterator.next();
        if(next.done){this.iterator=null;this.busy=false;this.phase=this.mode==='complete'?'done':'ready';}
        else if(next.value.gate){this.waiting={action:next.value.gate,leg:next.value.leg};this.busy=false;}
        else{this.frame=next.value;this.moves++;}
      }
      if(this.frame)this.compute(this.frame);
    }
    if(this.frame?.drive!==undefined){this.w.driveMotors(this.frame.drive,0,false);return;}
    const {qpos:q,qvel:v,ctrl}=this.d;
    for(let j=0;j<4;j++){
      const leg=LEG_NAMES[j];for(let k=0;k<3;k++){
        const entry=this.w.joints[leg+'_'+['hip','thigh','calf'][k]];ctrl[entry.act]=clamp(150*(this.targets[j][k]-q[entry.q])-5*v[entry.v],-45,45);
      }
      const wheel=this.w.joints[leg+'_wheel'];ctrl[wheel.act]=clamp(1.2*(this.omega[j]-v[wheel.v]),-15,15);
    }
  }
  state(){
    const {loads}=this.contacts(),positions=this.anchors();
    return {selected:this.selected,mode:this.mode,phase:this.phase,busy:this.busy,waiting:this.waiting,lifted:this.lifted,swing:this.swing,positions,loads,crossed:[...this.crossed],error:this.error};
  }
  destroy(){this.jac.delete();this.ang.delete();this.force.delete();}
}
