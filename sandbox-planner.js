// Same 5 cm grid, turn nodes, straight edges and margins as navigation/map.py.
export const grid = {x0:-1,y0:-2,nx:280,ny:90,res:.05};
const at=(x,y)=>{const i=Math.trunc((x-grid.x0)/grid.res),j=Math.trunc((y-grid.y0)/grid.res);return i<0||i>=grid.nx||j<0||j>=grid.ny?-1:i*grid.ny+j;};
export function inside(p,poly){let hit=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){
  const a=poly[i],b=poly[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;}
export function polygons(def,library){return Object.entries(def.rocks).map(([id,r])=>{
  const base=library.find(a=>a.id===r.rock),c=Math.cos(r.yaw*Math.PI/180),s=Math.sin(r.yaw*Math.PI/180),k=r.height/base.height;
  return {id,rock:r,base,poly:base.footprint.map(p=>[r.x+k*(c*p[0]-s*p[1]),r.y+k*(s*p[0]+c*p[1])])};});}
export function raster(polys){const out=new Uint8Array(grid.nx*grid.ny);for(let i=0;i<grid.nx;i++)for(let j=0;j<grid.ny;j++){
  const p=[grid.x0+(i+.5)*grid.res,grid.y0+(j+.5)*grid.res];out[i*grid.ny+j]=polys.some(poly=>inside(p,poly))?1:0;}return out;}
export function nogo(def){const t=def.terrain||{type:'corridor',right_wall:true,craters:[]},out=new Uint8Array(grid.nx*grid.ny);
  for(let i=0;i<grid.nx;i++)for(let j=0;j<grid.ny;j++){const x=grid.x0+(i+.5)*grid.res,y=grid.y0+(j+.5)*grid.res;
    const edge=1.3+.12*Math.sin(.8*x+.4)-.2*Math.exp(-(((x-7.4)/1.3)**2));
    out[i*grid.ny+j]=(t.type==='corridor'&&y>edge-.05)||(t.right_wall&&y< -1.35)||(t.craters||[]).some(q=>Math.hypot(x-q.center[0],y-q.center[1])<=q.radius+.05)?1:0;}return out;}
function rayBlocked(a,b,poly){for(let i=0;i<poly.length;i++){const c=poly[i],d=poly[(i+1)%poly.length],u=[b[0]-a[0],b[1]-a[1]],v=[d[0]-c[0],d[1]-c[1]],det=u[0]*v[1]-u[1]*v[0];
  if(Math.abs(det)<1e-12)continue;const w=[c[0]-a[0],c[1]-a[1]],t=(w[0]*v[1]-w[1]*v[0])/det,s=(w[0]*u[1]-w[1]*u[0])/det;
  if(t>0&&t<.999&&s>=0&&s<=1)return true;}return false;}
export function observe(def,library,{sourceScene=null}={}){const rocks=polygons(def,library).map(r=>sourceScene?{...r,base:{...r.base,candidates:r.base.candidates.filter(c=>c.scene===sourceScene&&c.look===1)}}:r),truth=raster(rocks.map(r=>r.poly)),prior=nogo(def),state=new Uint8Array(truth.length);
  const cam=[def.first_stop[0]+.42,def.first_stop[1]],sun=def.sun||{elevation_deg:10,azimuth_deg:35},az=sun.azimuth_deg*Math.PI/180;
  const shadows=rocks.map(r=>({poly:r.poly,shift:[Math.cos(az)*r.rock.height/Math.tan(sun.elevation_deg*Math.PI/180),-Math.sin(az)*r.rock.height/Math.tan(sun.elevation_deg*Math.PI/180)]}));
  for(let i=0;i<grid.nx;i++)for(let j=0;j<grid.ny;j++){const z=i*grid.ny+j,p=[grid.x0+(i+.5)*grid.res,grid.y0+(j+.5)*grid.res],dx=p[0]-cam[0],dy=p[1]-cam[1];
    if(prior[z]){state[z]=5;continue;}if(Math.hypot(dx,dy)>9||Math.abs(Math.atan2(dy,dx))>43*Math.PI/180){state[z]=4;continue;}
    const hidden=rocks.some(r=>!inside(p,r.poly)&&rayBlocked(cam,p,r.poly));
    const dark=shadows.some(q=>rayBlocked(p,[p[0]-q.shift[0],p[1]-q.shift[1]],q.poly));
    state[z]=hidden?3:dark?2:truth[z]?1:0;}
  return {state,truth,prior,rocks};}
export function candidateMask(rocks){const out=new Uint8Array(grid.nx*grid.ny),missing=[];
  for(const r of rocks){if(!r.base.candidates.length){missing.push(r);continue;}for(const template of r.base.candidates){
    const cells=new Set(template.footprint.map(p=>at(...p))),a=(template.pose[2]-r.rock.yaw)*Math.PI/180,c=Math.cos(a),s=Math.sin(a),k=template.height/r.rock.height;
    for(let i=0;i<grid.nx;i++)for(let j=0;j<grid.ny;j++){const x=grid.x0+(i+.5)*grid.res-r.rock.x,y=grid.y0+(j+.5)*grid.res-r.rock.y;
      const sx=template.pose[0]+k*(c*x-s*y),sy=template.pose[1]+k*(s*x+c*y);if(cells.has(at(sx,sy)))out[i*grid.ny+j]=1;}}}
  return {out,missing};}
export function dilate(mask,n=1){let a=mask;for(let t=0;t<n;t++){const b=a.slice();for(let i=0;i<grid.nx;i++)for(let j=0;j<grid.ny;j++){const k=i*grid.ny+j;if(a[k]){if(i)b[k-grid.ny]=1;if(i+1<grid.nx)b[k+grid.ny]=1;if(j)b[k-1]=1;if(j+1<grid.ny)b[k+1]=1;}}a=b;}return a;}
export function occupancies(def,obs){const n=obs.state.length,optimistic=new Uint8Array(n),conservative=new Uint8Array(n),imagination=new Uint8Array(n),cand=candidateMask(obs.rocks);
  // A missing admitted template retains nearby unknown space, as in the chain.
  for(const r of cand.missing){const near=dilate(raster([r.poly]),30);for(let z=0;z<n;z++)if(near[z]&&[2,3,4].includes(obs.state[z]))cand.out[z]=1;}
  const imagined=dilate(cand.out,1);
  for(let i=0;i<grid.nx;i++)for(let j=0;j<grid.ny;j++){const z=i*grid.ny+j,x=grid.x0+(i+.5)*grid.res,y=grid.y0+(j+.5)*grid.res;
    const vx=def.first_stop[0]-def.start[0],vy=def.first_stop[1]-def.start[1],length=vx*vx+vy*vy;
    const t=length?Math.max(0,Math.min(1,((x-def.start[0])*vx+(y-def.start[1])*vy)/length)):0;
    const known=Math.hypot(x-def.start[0]-t*vx,y-def.start[1]-t*vy)<=.42;
    optimistic[z]=obs.prior[z]||obs.state[z]===1||obs.state[z]===5?1:0;
    conservative[z]=optimistic[z]||(!known&&[2,3,4].includes(obs.state[z]))?1:0;
    imagination[z]=optimistic[z]||imagined[z]?1:0;}
  return {optimistic,conservative,imagination};}
// Exact squared Euclidean distance transform (separable lower parabolas).
function edt1(f){const n=f.length,v=new Int32Array(n),z=new Float64Array(n+1),d=new Float64Array(n);let k=0;v[0]=0;z[0]=-Infinity;z[1]=Infinity;
  for(let q=1;q<n;q++){let s=((f[q]+q*q)-(f[v[k]]+v[k]*v[k]))/(2*q-2*v[k]);while(s<=z[k]){k--;s=((f[q]+q*q)-(f[v[k]]+v[k]*v[k]))/(2*q-2*v[k]);}k++;v[k]=q;z[k]=s;z[k+1]=Infinity;}
  k=0;for(let q=0;q<n;q++){while(z[k+1]<q)k++;d[q]=(q-v[k])**2+f[v[k]];}return d;}
export function clearance(occ){const out=new Float64Array(occ.length),f=new Float64Array(grid.ny);for(let i=0;i<grid.nx;i++){for(let j=0;j<grid.ny;j++)f[j]=occ[i*grid.ny+j]?0:1e12;out.set(edt1(f),i*grid.ny);}
  const col=new Float64Array(grid.nx);for(let j=0;j<grid.ny;j++){for(let i=0;i<grid.nx;i++)col[i]=out[i*grid.ny+j];const d=edt1(col);for(let i=0;i<grid.nx;i++)out[i*grid.ny+j]=Math.sqrt(d[i])*grid.res;}return out;}
class Heap{constructor(){this.a=[];}push(v){let i=this.a.length;this.a.push(v);while(i){const p=(i-1)>>1;if(this.less(this.a[p],v))break;this.a[i]=this.a[p];i=p;}this.a[i]=v;}
  less(a,b){return a[0]<b[0]||(a[0]===b[0]&&a[1]<=b[1]);}pop(){const v=this.a[0],tail=this.a.pop();if(this.a.length){let i=0;while(i*2+1<this.a.length){let j=i*2+1;if(j+1<this.a.length&&this.less(this.a[j+1],this.a[j]))j++;if(this.less(tail,this.a[j]))break;this.a[i]=this.a[j];i=j;}this.a[i]=tail;}return v;}}
export function plan(occ,start,goal,drive=.4,turn=.57){const clr=clearance(occ),cat=(x,y)=>{const i=Math.trunc((x-grid.x0)/grid.res),j=Math.trunc((y-grid.y0)/grid.res);return i<0||i>=grid.nx||j<0||j>=grid.ny?0:clr[i*grid.ny+j];},nodes=[start];
  for(let i=0;i<130;i++)for(let j=0;j<39;j++){const x=-.5+i*.1,y=-1.7+j*.1;if(cat(x,y)>=turn)nodes.push([x,y]);}nodes.push(goal);
  const seg=(a,b)=>{const L=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.max(2,Math.trunc(L/.04));for(let k=0;k<n;k++){const t=k/(n-1);if(cat(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))<drive)return false;}return true;};
  const n=nodes.length,dist=new Float64Array(n).fill(Infinity),prev=new Int32Array(n).fill(-1),done=new Uint8Array(n),heap=new Heap();dist[0]=0;heap.push([0,0]);
  while(heap.a.length){const [d,a]=heap.pop();if(done[a])continue;done[a]=1;if(a===n-1)break;for(let b=0;b<n;b++){if(done[b])continue;const L=Math.hypot(nodes[b][0]-nodes[a][0],nodes[b][1]-nodes[a][1]),nd=d+L+.35;if(L<=2.6&&L>1e-6&&nd<dist[b]&&seg(nodes[a],nodes[b])){dist[b]=nd;prev[b]=a;heap.push([nd,b]);}}}
  if(!Number.isFinite(dist[n-1]))return null;const route=[];for(let k=n-1;k>0;k=prev[k])route.push(nodes[k]);route.reverse();const pts=[start,...route],simple=[];let i=0;while(i<pts.length-1){let j=pts.length-1;while(j>i+1&&!seg(pts[i],pts[j]))j--;simple.push(pts[j]);i=j;}return simple;}
export function intrusion(path,start,truth,half=.33){if(!path)return null;const clr=clearance(truth);let least=Infinity;const pts=[start,...path];for(let p=0;p+1<pts.length;p++){const a=pts[p],b=pts[p+1],n=Math.max(2,Math.trunc(Math.hypot(b[0]-a[0],b[1]-a[1])/.03));for(let k=0;k<n;k++){const t=k/(n-1),index=at(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]));least=Math.min(least,clr[index]-half);}}return Math.max(0,-least);}
