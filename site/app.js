const $=id=>document.getElementById(id);
const names={optimistic:['直接走','将未知空间作为可通行区域。'],conservative:['看清再走','保持未知，通过实际补充观察寻找路线。'],imagination:['想一想再走','生成几何通过冻结自检，再预演和执行。']};
const results={collision:'遇到碰撞',stuck:'无路线，停车',arrived:'到达终点',stopped_short:'未完成路线'};
let data,policy='imagination',playing=false,progress=0,last=0,loadVersion=0,background,backgroundData,backgroundPolicy;
const canvas=$('route'),ctx=canvas.getContext('2d');
const r1=()=>data?.review_id==='R1';
function project(x,y){return r1()?[50+(x+1)*64,35+(2.5-y)*64]:[65+(x+1)*74,canvas.height*.5-y*65]}
function paintBackground(){
 ctx.fillStyle='#101720';ctx.fillRect(0,0,canvas.width,canvas.height);
 if(r1()){
  const cells=data.decision?.observed_cells;
  if(cells){const [nx,ny]=cells.shape;for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){const v=cells.values[i*ny+j];if(v!==2&&v!==3)continue;const p=project(cells.origin[0]+(i+.5)*cells.resolution,cells.origin[1]+(j+.5)*cells.resolution);ctx.fillStyle=v===2?'#6f4eb02b':'#bd825125';ctx.fillRect(p[0]-1.6,p[1]-1.6,3.5,3.5)}}
  ctx.fillStyle='#243945';ctx.beginPath();ctx.moveTo(...project(-1,2.5));for(const p of data.rille_edge)ctx.lineTo(...project(p[0],p[1]-.05));ctx.lineTo(...project(13,2.5));ctx.closePath();ctx.fill();const a=project(-1,data.wall_y),b=project(13,-2);ctx.fillRect(a[0],a[1],b[0]-a[0],b[1]-a[1]);
 }else{ctx.fillStyle='#1a2530';ctx.fillRect(0,canvas.height*.5+90,1000,200);ctx.fillStyle='#1b2834';ctx.fillRect(0,0,1000,canvas.height*.5-90)}
 ctx.strokeStyle='#273641';ctx.lineWidth=1;for(let x=0;x<13;x++){const [xx]=project(x,0);ctx.beginPath();ctx.moveTo(xx,25);ctx.lineTo(xx,365);ctx.stroke()}
 for(const rock of data?.rocks||[]){ctx.fillStyle=r1()?'#8a92917a':'#7e8588';ctx.strokeStyle='#939c9b';ctx.beginPath();rock.polygon.forEach((point,index)=>{const p=project(...point);index?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.closePath();ctx.fill();ctx.stroke();if(r1()){const p=project(rock.x,rock.y);ctx.fillStyle='#e5e9e8';ctx.font='12px sans-serif';ctx.fillText(rock.id,p[0]-4,p[1]+4)}}
 if(policy==='imagination'||policy==='replay'){ctx.fillStyle='#70dbb24d';for(const point of data?.imagined_footprint||[]){const p=project(...point);ctx.fillRect(p[0]-1.6,p[1]-1.6,3.2,3.2)}}
 ctx.fillStyle='#91a5b2';ctx.font='12px sans-serif';ctx.fillText('月溪 · 禁行',70,45);ctx.fillText('大石堆 · 禁行',70,350);
 const [gx,gy]=project(...(data?.goal||[8.5,0]));ctx.strokeStyle='#70dbb2';ctx.setLineDash([4,4]);ctx.strokeRect(gx-12,gy-12,24,24);ctx.setLineDash([]);ctx.fillStyle='#70dbb2';ctx.fillText('终点',gx-14,gy+32);
 background=document.createElement('canvas');background.width=canvas.width;background.height=canvas.height;background.getContext('2d').drawImage(canvas,0,0);backgroundData=data;backgroundPolicy=policy;
}
function draw(){
 if(!background||backgroundData!==data||backgroundPolicy!==policy)paintBackground();else ctx.drawImage(background,0,0);
 const run=data?.runs[policy];if(!run?.trajectory?.length){ctx.fillStyle='#93a4b5';ctx.fillText('正在加载真实运行数据…',340,195);return}
 const limit=Math.floor(progress*(run.trajectory.length-1)),track=run.trajectory;
 ctx.lineWidth=3;ctx.strokeStyle=policy==='optimistic'?'#ff997c':'#70dbb2';ctx.beginPath();track.slice(0,limit+1).forEach((v,i)=>{const p=project(v[1],v[2]);i?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.stroke();
 const pose=track[limit],p=project(pose[1],pose[2]);ctx.save();ctx.translate(...p);ctx.rotate(-pose[3]);ctx.fillStyle='#e3edf0';const l=r1()?data.robot_envelope.half_len*64:20,w=r1()?data.robot_envelope.half_wid*64:12;ctx.fillRect(-l,-w,2*l,2*w);ctx.fillStyle='#ee9c57';ctx.fillRect(l*.5,-w*.75,l*.4,w*1.5);ctx.restore();$('time').textContent=`${pose[0].toFixed(1)} s`;
}
function select(key){
 if(!data?.runs[key])key='imagination';policy=key;progress=0;playing=false;$('play').textContent='▶ 播放';$('scrub').value=0;
 document.querySelectorAll('[data-policy]').forEach(b=>b.classList.toggle('active',b.dataset.policy===key));const run=data?.runs[key];
 $('strategy').textContent=data?.labels?.[key]||names[key]?.[0]||key;$('description').textContent=data?.descriptions?.[key]||names[key]?.[1]||'';
 if(!r1()&&run?.controller==='learned')$('description').textContent={optimistic:'同一训练模型，仅根据可见几何与禁行先验规划；本次实际到达。',conservative:run.result==='arrived'?'同一训练模型，通过安全观察点补充真实观测，然后完成通行。':'同一训练模型未完成观察姿态，保留未完成终态。',imagination:'实际 RGB-D 约束真实 Lux3D 候选；训练模型完成预演并在独立环境执行。'}[key];
 if(!r1()&&data?.scene_id==='stress_v8')$('description').textContent={optimistic:'旧双盲区压力实验中，直接走会碰撞。',conservative:'旧压力实验中，多次观察后仍未找到路线。',imagination:'旧压力实验的 B 候选被拒绝，因此停下；这是保留的历史边界。'}[key];
 $('run-status').textContent=run?results[run.result]||run.result:'数据尚未生成';$('looks').textContent=run?.looks??'—';$('duration').textContent=run?`${run.sim_time_s}s`:'—';$('rehearsals').textContent=run?.rehearsals?`${run.rehearsals_passed}/${run.rehearsals}`:'—';
 $('audit-select').value=key in (data?.runs||{})&&!names[key]?key:'';const link=$('run-evidence');link.href=run?.evidence?run.evidence+'/run_identity.json':'report.html';draw();
}
function drawDecision(){
 const d=data?.decision;$('decision-effect').hidden=!d;if(!d)return;
 const ref=d.reference_rehearsals||[],exe=d.execution_rehearsals||[];const passed=list=>list.filter(p=>p.completed&&!p.collided).length;
 $('decision-status').textContent=d.path_changed?'生成几何改变了路线':'同一观测，路线一致';$('execution-check').textContent=exe.length?`${passed(exe)}/${exe.length}`:'—';
 $('reference-label').textContent=r1()?'乐观策略实际终态':'参照路线预演';$('reference-check').textContent=r1()?results[data.runs.optimistic.result]:ref.length?`${passed(ref)}/${ref.length}`:'未重复预演';
 $('decision-explanation').textContent=r1()?'相同窄道、相同传感器链和规则控制器：乐观碰撞，真实 Lux 路线完整预演后到达。':ref.some(p=>p.collided||!p.completed)?'参照路线没有通过全部候选检验；另一条路线完成检验。':d.path_changed?'候选占据改变了规划路线，保留实际预演和执行结果。':'候选支持原路线，执行前仍完成物理预演。';
 $('decision-margin').textContent=r1()?`赛后复盘：乐观原计划压入 B ${(data.audit.optimistic_intrusion_m*1000).toFixed(3)} mm；Lux 实际三维间隙 ${(data.audit.physical_clearance_B_m*1000).toFixed(3)} mm。`:'扫描余量作为赛后诊断，完整数值见原运行证据。';
 const c=$('decision-map'),g=c.getContext('2d');g.fillStyle='#101720';g.fillRect(0,0,c.width,c.height);const center=data.rocks[0]?.x||4.55,xmin=r1()?2:center-2,xmax=r1()?10.8:center+2.5,ymin=-1.55,ymax=1.5;const q=(x,y)=>[(x-xmin)/(xmax-xmin)*c.width,(ymax-y)/(ymax-ymin)*c.height];
 const cells=d.observed_cells,colors=['#152d28','#707a7b','#302344','#473326','#111923','#243945'];if(cells){const [nx,ny]=cells.shape,r=cells.resolution,[ox,oy]=cells.origin;for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){const x=ox+(i+.5)*r,y=oy+(j+.5)*r;if(x<xmin||x>xmax||y<ymin||y>ymax)continue;const [px,py]=q(x,y);g.fillStyle=colors[cells.values[i*ny+j]];g.fillRect(px-r*c.width/(xmax-xmin)/2,py-r*c.height/(ymax-ymin)/2,r*c.width/(xmax-xmin)+1,r*c.height/(ymax-ymin)+1)}}
 for(const rock of data.rocks){g.strokeStyle='#bec6cb';g.lineWidth=1.5;g.beginPath();rock.polygon.forEach((p,i)=>{const v=q(...p);i?g.lineTo(...v):g.moveTo(...v)});g.closePath();g.stroke()}
 g.fillStyle='#70dbb24d';for(const p of data.imagined_footprint||[]){const [x,y]=q(...p);g.fillRect(x-3,y-3,6,6)}
 for(const [path,color,dash] of [[d.reference_path,'#ff997c',[10,6]],[d.selected_path,'#70dbb2',[]]]){if(!path)continue;g.strokeStyle=color;g.lineWidth=4;g.setLineDash(dash);g.beginPath();[d.start,...path].forEach((p,i)=>{const v=q(...p);i?g.lineTo(...v):g.moveTo(...v)});g.stroke();g.setLineDash([])}g.font='16px sans-serif';g.fillStyle='#a8b8c1';g.fillText('第一眼观测 / 生成占据 / 扫描轮廓（复盘）',24,30);
}
function renderDetails(){
 for(const id of ['audit-controls','r1-admission','observation-rule','rehearsal-gallery','truth-audit','counterfactual'])$(id).hidden=!r1();
 $('controller-label').textContent=r1()?'同一场景 · 同一规则控制器':data.runs.imagination.controller==='learned'?'迭代附录 · 同一训练模型':'历史实验 · 同一规则控制器';
 $('main-result-rows').replaceChildren();$('admission-rows').replaceChildren();$('counterfactual-rows').replaceChildren();$('pane-gallery').replaceChildren();$('generation-note').textContent='';
 if(!r1())return;
 const append=(body,values)=>{const tr=document.createElement('tr');for(const v of values){const td=document.createElement('td');td.textContent=v;tr.append(td)}body.append(tr)};
 for(const key of ['conservative','see_dark','optimistic','imagination','truth']){const run=data.runs[key];append($('main-result-rows'),[data.labels[key],results[run.result],run.looks,run.sim_time_s+' s'])}
 for(const id of ['A1','A2','B1','B2','C1','C2']){const c=data.candidates.find(c=>c.target==='T2'&&c.sample_id===id),failed=data.generation.failed_tasks.find(c=>c.target==='T2'&&c.sample===id);append($('admission-rows'),['B/'+id,c?.task_id||failed?.task_id,c?.contour_iou??'—',c?.scale_ratio??'—',c?(c.admitted?'准入':c.rejection_reason):'生成失败'])}
 $('generation-note').textContent=`${data.generation.tasks} 个真实任务 · ${data.generation.succeeded} 个原 GLB · ${data.generation.admitted} 份准入。B 原图目标高度 ${data.target_states.T2.crop_native_px} px，native_ok=${data.target_states.T2.native_ok}，未达到 512 px 输入规格；本批仍有两份符合观测自检。`;
 for(const id of ['A1','B1','C2']){const run=data.runs['trust_'+id];append($('counterfactual-rows'),['B/'+id,results[run.result],run.sim_time_s+' s'])}
 $('xy-center-note').textContent=`二维中心距离减半车宽最小为 ${data.audit.xy_center_minus_half_width_B_m.toFixed(6)} m；与二维包络间隙 ${data.audit.xy_envelope_clearance_B_m} 同时报告。`;
 $('wall-note').textContent=`原运行墙钟${data.audit.cold_wall_s} s，含冷配准和预演、不含云端排队，不是端到端延迟。`;
 $('physical-gap').textContent=(data.audit.physical_clearance_B_m*1000).toFixed(3)+' mm';
 for(const pane of data.gallery){const card=document.createElement('a');card.className='pane-card';card.href=pane.evidence;card.target='_blank';card.rel='noopener';const title=document.createElement('h3');title.textContent=`${String(pane.pane+1).padStart(2,'0')} / ${pane.label}`;const badge=document.createElement('span');badge.className='pill';badge.textContent=pane.completed&&!pane.collided?'完整完成 · 无碰撞':'未通过';const c=document.createElement('canvas');c.width=320;c.height=130;c.setAttribute('aria-label',pane.label+' 的实际预演轨迹');const g=c.getContext('2d');g.fillStyle='#101820';g.fillRect(0,0,320,130);g.strokeStyle='#70dbb2';g.lineWidth=2;g.beginPath();pane.trajectory.forEach((v,i)=>{const p=[12+(v[1]+1)*24,65-v[2]*25];i?g.lineTo(...p):g.moveTo(...p)});g.stroke();card.append(title,badge,c);$('pane-gallery').append(card)}
}
function choose(){const c=data?.candidates.find(c=>c.id===$('candidate-select').value);if(!c)return;$('model-error').hidden=true;$('model').src=c.glb;$('input').src=c.input;$('model-download').href=c.glb;$('candidate-info').textContent=`真实任务 ${c.task_id} · ${c.verdict}`}
async function loadScene(path){
 const version=++loadVersion;playing=false;const response=await fetch(path);if(!response.ok)throw Error('Scene data unavailable');const next=await response.json();if(version!==loadVersion)return;data=next;
 $('scene-title').textContent=data.title||'历史实验';const options=$('candidate-select');options.replaceChildren();for(const c of data.candidates){const o=document.createElement('option');o.value=c.id;o.textContent=c.label;options.append(o)}const accepted=data.candidates.find(c=>c.target==='T2'&&c.admitted)||data.candidates.find(c=>c.admitted);if(accepted)options.value=accepted.id;
 const video=document.querySelector('video');video.src=data.video||'media/demo.mp4';video.poster=data.poster||'media/demo-poster.jpg';video.load();$('video-title').textContent=r1()?'R1 Demo 位置保留。':'历史完整任务回放。';$('video-description').textContent=r1()?'负责人将用本次完整数据制作新 Demo。现有视频为 v0.3 历史实验，保留供迭代比较。':'这是所选历史实验的真实仿真回放；原发布、训练与失败结果保持。';$('video-download').href=video.getAttribute('src');$('video-download').textContent='下载历史 Demo ↓';renderDetails();select(policy);choose();drawDecision();
}
$('candidate-select').addEventListener('change',choose);$('audit-select').addEventListener('change',e=>{if(e.target.value)select(e.target.value)});
document.querySelectorAll('[data-policy]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.policy)));
$('play').addEventListener('click',()=>{playing=!playing;$('play').textContent=playing?'Ⅱ 暂停':'▶ 播放';if(progress>=1)progress=0});$('scrub').addEventListener('input',e=>{progress=Number(e.target.value)/1000;draw()});
function tick(now){if(playing&&data){progress=Math.min(1,progress+(now-last)/20000);$('scrub').value=progress*1000;draw();if(progress===1){playing=false;$('play').textContent='↻ 重播'}}last=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);draw();
try{const response=await fetch('data/scenes.json');if(!response.ok)throw Error('Index');const index=await response.json(),select=$('scene-select');for(const scene of index.scenes){const option=document.createElement('option');option.value=scene.data;option.textContent=scene.label;option.selected=scene.id===index.default;select.append(option)}select.addEventListener('change',()=>loadScene(select.value).catch(()=>{$('run-status').textContent='实验数据加载失败'}));await loadScene(select.value)}catch(e){$('run-status').textContent='运行数据暂不可用';$('description').textContent='请检查实验材料是否完整。'}
$('model').addEventListener('error',()=>{$('model-error').hidden=false});
