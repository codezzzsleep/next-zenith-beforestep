/** Observation-constrained route planning. Thresholds / map are frozen R1 inputs. */
export function admissionChecks(candidate, limits){
  const m=candidate.metrics;
  return [
    {key:'contour_iou',label:'可见轮廓吻合',value:m.contour_iou,limit:limits.contour_iou_min,pass:m.contour_iou>=limits.contour_iou_min},
    {key:'scale_ratio',label:'观测尺寸比例',value:m.scale_ratio,limit:[limits.scale_ratio.min,limits.scale_ratio.max],pass:m.scale_ratio>=limits.scale_ratio.min&&m.scale_ratio<=limits.scale_ratio.max},
    {key:'hidden_frac',label:'未知区域占比',value:m.hidden_frac,limit:limits.hidden_frac_min,pass:m.hidden_frac>=limits.hidden_frac_min},
    {key:'shell_contact',label:'可见表面贴合',value:m.shell_contact,limit:limits.shell_contact_min,pass:m.shell_contact>=limits.shell_contact_min},
    {key:'free_intrusion_frac',label:'侵入已知空地',value:m.free_intrusion_frac,limit:limits.free_intrusion_max,pass:m.free_intrusion_frac<=limits.free_intrusion_max},
  ];
}
export function accepted(candidate,limits){return admissionChecks(candidate,limits).every(c=>c.pass);}
export function occupancy(mission,selected=[],policy='imagination'){
  const state=mission.observation_state,out=new Uint8Array(state.length);
  for(let i=0;i<state.length;i++)out[i]=state[i]===1||state[i]===5||mission.known_nogo[i]?1:0;
  if(policy==='imagination')for(const candidate of mission.candidates){
    if(selected.includes(candidate.task_id)&&accepted(candidate,mission.thresholds))for(let i=0;i<out.length;i++)out[i]||=candidate.footprint[i];
  }
  if(policy==='conservative')for(let i=0;i<out.length;i++)if(state[i]===2||state[i]===3||state[i]===4)out[i]=1;
  return out;
}
function edt1d(f,n){
  const v=new Int32Array(n),z=new Float64Array(n+1),out=new Float64Array(n);let k=0;v[0]=0;z[0]=-Infinity;z[1]=Infinity;
  for(let q=1;q<n;q++){
    let p=v[k],s=((f[q]+q*q)-(f[p]+p*p))/(2*(q-p));
    while(s<=z[k]&&k>0){k--;p=v[k];s=((f[q]+q*q)-(f[p]+p*p))/(2*(q-p));}
    k++;v[k]=q;z[k]=s;z[k+1]=Infinity;
  }
  k=0;for(let q=0;q<n;q++){while(z[k+1]<q)k++;const d=q-v[k];out[q]=d*d+f[v[k]];}return out;
}
export function clearance(occ,grid){
  const {nx,ny,res}=grid,temp=new Float64Array(nx*ny),out=new Float64Array(nx*ny),f=new Float64Array(Math.max(nx,ny));
  for(let y=0;y<ny;y++){for(let x=0;x<nx;x++)f[x]=occ[x*ny+y]?0:1e20;const d=edt1d(f,nx);for(let x=0;x<nx;x++)temp[x*ny+y]=d[x];}
  for(let x=0;x<nx;x++){for(let y=0;y<ny;y++)f[y]=temp[x*ny+y];const d=edt1d(f,ny);for(let y=0;y<ny;y++)out[x*ny+y]=Math.sqrt(d[y])*res;}
  return out;
}
class Heap{
  constructor(){this.a=[];}
  push(value){let i=this.a.length;this.a.push(value);while(i){const p=(i-1)>>1;if(this.a[p][0]<=value[0])break;this.a[i]=this.a[p];i=p;}this.a[i]=value;}
  pop(){const a=this.a,first=a[0],last=a.pop();if(a.length){let i=0;while(i*2+1<a.length){let j=i*2+1;if(j+1<a.length&&a[j+1][0]<a[j][0])j++;if(a[j][0]>=last[0])break;a[i]=a[j];i=j;}a[i]=last;}return first;}
}
/** Matches R1 turn-point / straight-edge clearance, using A* search. */
export function planRoute(mission,selected=[],policy='imagination',start=mission.start,goal=mission.dock){
  const grid=mission.grid,{x0,y0,nx,ny,res,node_step,max_edge}=grid;
  // Extra room for this interactive motor controller; original R1 limits remain intact.
  const allowance=mission.control_allowance??.07,r_drive=grid.r_drive+allowance,r_turn=grid.r_turn+allowance;
  const occ=occupancy(mission,selected,policy),clr=clearance(occ,grid);
  const at=(x,y)=>{const i=Math.floor((x-x0)/res),j=Math.floor((y-y0)/res);return i<0||j<0||i>=nx||j>=ny?0:clr[i*ny+j];};
  const nodes=[[...start]];
  for(let x=x0+.5;x<x0+nx*res-.5-1e-8;x+=node_step)for(let y=y0+.3;y<y0+ny*res-.3-1e-8;y+=node_step)if(at(x,y)>=r_turn)nodes.push([x,y]);
  nodes.push([...goal]);const end=nodes.length-1,n=nodes.length;
  const dist=new Float64Array(n).fill(Infinity),prev=new Int32Array(n).fill(-1),done=new Uint8Array(n),heap=new Heap();
  dist[0]=0;heap.push([Math.hypot(goal[0]-start[0],goal[1]-start[1]),0]);let visited=0;
  function edge(a,b){
    const p=nodes[a],q=nodes[b],length=Math.hypot(q[0]-p[0],q[1]-p[1]),count=Math.max(2,Math.floor(length/.04));
    for(let i=0;i<count;i++){const t=i/(count-1);if(at(p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1]))<r_drive)return false;}return true;
  }
  while(heap.a.length){
    const [,a]=heap.pop();if(done[a])continue;done[a]=1;visited++;if(a===end)break;
    const p=nodes[a];
    for(let b=1;b<n;b++){
      if(done[b]||b===a)continue;const q=nodes[b],d=Math.hypot(q[0]-p[0],q[1]-p[1]);
      if(d<1e-6||d>max_edge||dist[a]+d+.35>=dist[b])continue;if(!edge(a,b))continue;
      dist[b]=dist[a]+d+.35;prev[b]=a;heap.push([dist[b]+Math.hypot(q[0]-goal[0],q[1]-goal[1]),b]);
    }
  }
  if(!Number.isFinite(dist[end]))return {path:null,policy,selected:[...selected],visited,reason:'no_route_with_required_clearance'};
  const ids=[];for(let k=end;k>=0;k=prev[k]){ids.push(k);if(k===0)break;}ids.reverse();
  const coarse=ids.map(i=>nodes[i]),path=[coarse[0]];let i=0;
  while(i<coarse.length-1){let j=coarse.length-1;while(j>i+1&&!edge(ids[i],ids[j]))j--;path.push(coarse[j]);i=j;}
  const length=path.slice(1).reduce((s,p,i)=>s+Math.hypot(p[0]-path[i][0],p[1]-path[i][1]),0);
  return {path,length,cost:dist[end],policy,selected:[...selected],visited,clearance:{drive:r_drive,turn:r_turn}};
}
export function modelWorlds(mission,selected){return mission.worlds.filter(w=>w.tasks.every(id=>selected.includes(id)));}
