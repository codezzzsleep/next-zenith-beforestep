const $=id=>document.getElementById(id);
const names={optimistic:['直接走','把阴影和遮挡当作可以通过的空间。当前关口能够到达；未使用生成几何和物理预演。'],conservative:['看清再走','未知空间先保守处理，通过新的观察补足信息，然后通行。'],imagination:['想一想再走','真实 Lux3D 候选经过冻结自检，三个候选分别预演通过，再执行路线到达终点。']};
const results={collision:'遇到碰撞',stuck:'停下，证据不足',arrived:'到达终点',stopped_short:'未完成路线'};
let data,policy='imagination',playing=false,progress=0,last=0,loadVersion=0;
const canvas=$('route'),ctx=canvas.getContext('2d');
function project(x,y){return [65+(x+1)*74,canvas.height*.5-y*65]}
function draw(){
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#101720';ctx.fillRect(0,0,canvas.width,canvas.height);
 ctx.strokeStyle='#202b38';ctx.lineWidth=1;for(let x=0;x<13;x++){const [xx]=project(x,0);ctx.beginPath();ctx.moveTo(xx,25);ctx.lineTo(xx,365);ctx.stroke()}
 ctx.fillStyle='#1a2530';ctx.fillRect(0,canvas.height*.5+90,1000,200);ctx.fillStyle='#1b2834';ctx.fillRect(0,0,1000,canvas.height*.5-90);
 if(data){
  for(const rock of data.rocks){const [x,y]=project(rock.x,rock.y);ctx.fillStyle='#27313d';ctx.fillRect(x+15,y-55,125,90);ctx.fillStyle='#7e8588';ctx.beginPath();rock.polygon.forEach((point,index)=>{const p=project(...point);index?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.closePath();ctx.fill()}
  if(policy==='imagination'){ctx.fillStyle='#70dbb24d';for(const point of data.imagined_footprint||[]){const [x,y]=project(...point);ctx.fillRect(x-2,y-2,4,4)}}
 }
 ctx.fillStyle='#657687';ctx.font='13px sans-serif';ctx.fillText('月溪 · 禁行',70,45);ctx.fillText('岩壁 · 禁行',70,350);
 const [gx,gy]=project(...(data?.goal||[8.5,0]));ctx.strokeStyle='#70dbb2';ctx.setLineDash([4,4]);ctx.strokeRect(gx-12,gy-12,24,24);ctx.setLineDash([]);ctx.fillStyle='#70dbb2';ctx.fillText('终点',gx-14,gy+35);
 const run=data?.runs[policy];if(!run?.trajectory?.length){ctx.fillStyle='#93a4b5';ctx.fillText('正在加载真实运行数据…',340,195);return}
 const limit=Math.floor(progress*(run.trajectory.length-1)),track=run.trajectory;
 ctx.lineWidth=3;ctx.strokeStyle=policy==='optimistic'?'#ff997c':'#70dbb2';ctx.beginPath();track.slice(0,limit+1).forEach((v,i)=>{const p=project(v[1],v[2]);i?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.stroke();
 const pose=track[limit],p=project(pose[1],pose[2]);ctx.save();ctx.translate(...p);ctx.rotate(-pose[3]);ctx.fillStyle='#e3edf0';ctx.fillRect(-20,-12,40,24);ctx.fillStyle='#ee9c57';ctx.fillRect(10,-9,8,18);ctx.restore();$('time').textContent=`${pose[0].toFixed(1)} s`;
}
function select(key){
 policy=key;progress=0;playing=false;$('play').textContent='▶ 播放';$('scrub').value=0;
 document.querySelectorAll('[data-policy]').forEach(b=>b.classList.toggle('active',b.dataset.policy===key));const run=data?.runs[key];
 $('strategy').textContent=names[key][0];$('description').textContent=names[key][1];
 if(run?.controller==='learned'){
  const count=data.generation?.admitted||run.rehearsals||0;
  $('description').textContent={optimistic:'同一训练模型，仅根据实测可见几何与禁行先验规划；本次实际执行到达。',
   conservative:run.result==='arrived'?'同一训练模型，通过安全观察点补充真实观测，然后完成通行。':'同一训练模型未完成计划观察点的姿态要求，保留未完成终态。',
   imagination:`实际 RGB-D 约束真实 Lux3D 候选，${count} 份采纳几何参与完整物理预演；训练模型在独立环境执行。`}[key];
 }
 if(data?.scene_id==='stress_v8')$('description').textContent={optimistic:'旧双盲区压力场景中，直接走会碰撞。',conservative:'旧压力场景中，多次观察后仍未找到路线。',imagination:'旧压力场景的第二块候选全被拒绝，因此停下。仅作为历史反例。'}[key];
 $('status').textContent=run?results[run.result]||run.result:'运行数据尚未生成';$('looks').textContent=run?.looks??'—';$('duration').textContent=run?`${run.sim_time_s}s`:'—';$('rehearsals').textContent=run?.rehearsals?`${run.rehearsals_passed}/${run.rehearsals}`:'—';draw();
}
function drawDecision(){
 const d=data?.decision,panel=$('decision-effect');panel.hidden=!d;if(!d)return;
 const ref=d.reference_rehearsals||[],exe=d.execution_rehearsals||[];
 const passed=list=>list.filter(p=>p.completed&&!p.collided).length;
 $('decision-status').textContent=d.path_changed?'生成几何改变了路线':'同一观测，路线一致';
 $('reference-check').textContent=ref.length?`${passed(ref)}/${ref.length}`:'未重复预演';
 $('execution-check').textContent=exe.length?`${passed(exe)}/${exe.length}`:'—';
 $('decision-explanation').textContent=ref.some(p=>p.collided||!p.completed)?'参照路线未通过全部候选检验；机器人选择了另一条通过检验的路线。':d.path_changed?'候选占据改变了规划路线；分别保留两条路线的预演和实际执行结果。':'本次候选支持原路线，执行前仍完成物理预演。';
 const margin=m=>m?.drive_margin_m==null?'—':`${Math.round(m.drive_margin_m*1000)}毫米`;
 $('decision-margin').textContent=`独立几何估计余量：参照 ${margin(d.reference_margin_vs_truth)} → 选择 ${margin(d.selected_margin_vs_truth)}`;
 const c=$('decision-map'),g=c.getContext('2d');g.fillStyle='#101720';g.fillRect(0,0,c.width,c.height);
 const center=data.rocks[0]?.x||4.55,xmin=center-2,xmax=center+2.5,ymin=-1.55,ymax=1.5;
 const q=(x,y)=>[(x-xmin)/(xmax-xmin)*c.width,(ymax-y)/(ymax-ymin)*c.height];
 const cells=d.observed_cells,colors=['#152d28','#707a7b','#18212e','#27313c','#111923','#14202b'];
 if(cells){const [nx,ny]=cells.shape,r=cells.resolution,[ox,oy]=cells.origin;for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){const x=ox+(i+.5)*r,y=oy+(j+.5)*r;if(x<xmin||x>xmax||y<ymin||y>ymax)continue;const [px,py]=q(x,y);g.fillStyle=colors[cells.values[i*ny+j]];g.fillRect(px-r*c.width/(xmax-xmin)/2,py-r*c.height/(ymax-ymin)/2,r*c.width/(xmax-xmin)+1,r*c.height/(ymax-ymin)+1)}}
 for(const rock of data.rocks){g.strokeStyle='#bec6cb';g.lineWidth=1.5;g.beginPath();rock.polygon.forEach((p,i)=>{const v=q(...p);i?g.lineTo(...v):g.moveTo(...v)});g.closePath();g.stroke()}
 g.fillStyle='#70dbb24d';for(const p of data.imagined_footprint||[]){const [x,y]=q(...p);g.fillRect(x-3,y-3,6,6)}
 for(const [path,color,dash] of [[d.reference_path,'#ff997c',[10,6]],[d.selected_path,'#70dbb2',[]]]){if(!path)continue;g.strokeStyle=color;g.lineWidth=4;g.setLineDash(dash);g.beginPath();[d.start,...path].forEach((p,i)=>{const v=q(...p);i?g.lineTo(...v):g.moveTo(...v)});g.stroke();g.setLineDash([])}
 g.font='18px sans-serif';g.fillStyle='#9aaaba';g.fillText('已见地面 / 盲区 / 扫描轮廓',24,32);
}
function choose(){const c=data?.candidates.find(c=>c.id===$('candidate-select').value);if(!c)return;$('model-error').hidden=true;$('model').src=c.glb;$('input').src=c.input;$('model-download').href=c.glb;$('candidate-info').textContent=`真实任务 ${c.task_id} · ${c.verdict}`}
async function loadScene(path){
 const version=++loadVersion;playing=false;const response=await fetch(path);if(!response.ok)throw Error('Scene data unavailable');const next=await response.json();if(version!==loadVersion)return;data=next;
 $('scene-title').textContent=data.title||'历史压力场景';const options=$('candidate-select');options.replaceChildren();for(const c of data.candidates){const o=document.createElement('option');o.value=c.id;o.textContent=c.label;options.append(o)}
 const accepted=data.candidates.find(c=>c.admitted);if(accepted)options.value=accepted.id;
 const video=document.querySelector('video');video.src=data.video||'media/demo.mp4';video.poster=data.poster||'media/demo-poster.jpg';video.load();select(policy);choose();drawDecision();
}
$('candidate-select').addEventListener('change',choose);
document.querySelectorAll('[data-policy]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.policy)));
$('play').addEventListener('click',()=>{playing=!playing;$('play').textContent=playing?'Ⅱ 暂停':'▶ 播放';if(progress>=1)progress=0});$('scrub').addEventListener('input',e=>{progress=Number(e.target.value)/1000;draw()});
function tick(now){if(playing&&data){progress=Math.min(1,progress+(now-last)/20000);$('scrub').value=progress*1000;draw();if(progress===1){playing=false;$('play').textContent='↻ 重播'}}last=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);draw();
try{const response=await fetch('data/scenes.json');if(!response.ok)throw Error('Index');const index=await response.json(),select=$('scene-select');for(const scene of index.scenes){const option=document.createElement('option');option.value=scene.data;option.textContent=scene.label;option.selected=scene.id===index.default;select.append(option)}select.addEventListener('change',()=>loadScene(select.value).catch(()=>{$('status').textContent='场景数据加载失败'}));await loadScene(select.value)}catch(e){$('status').textContent='运行数据暂不可用';$('description').textContent='请检查场景材料是否完整。'}
$('model').addEventListener('error',()=>{$('model-error').hidden=false});
