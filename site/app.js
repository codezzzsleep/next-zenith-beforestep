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
 if(data?.scene_id==='stress_v8')$('description').textContent={optimistic:'旧双盲区压力场景中，直接走会碰撞。',conservative:'旧压力场景中，多次观察后仍未找到路线。',imagination:'旧压力场景的第二块候选全被拒绝，因此停下。仅作为历史反例。'}[key];
 $('status').textContent=run?results[run.result]||run.result:'运行数据尚未生成';$('looks').textContent=run?.looks??'—';$('duration').textContent=run?`${run.sim_time_s}s`:'—';$('rehearsals').textContent=run?.rehearsals?`${run.rehearsals_passed}/${run.rehearsals}`:'—';draw();
}
function choose(){const c=data?.candidates.find(c=>c.id===$('candidate-select').value);if(!c)return;$('model-error').hidden=true;$('model').src=c.glb;$('input').src=c.input;$('model-download').href=c.glb;$('candidate-info').textContent=`真实任务 ${c.task_id} · ${c.verdict}`}
async function loadScene(path){
 const version=++loadVersion;playing=false;const response=await fetch(path);if(!response.ok)throw Error('Scene data unavailable');const next=await response.json();if(version!==loadVersion)return;data=next;
 $('scene-title').textContent=data.title||'历史压力场景';const options=$('candidate-select');options.replaceChildren();for(const c of data.candidates){const o=document.createElement('option');o.value=c.id;o.textContent=c.label;options.append(o)}
 const video=document.querySelector('video');video.src=data.video||'media/demo.mp4';video.poster=data.poster||'media/demo-poster.jpg';video.load();select(policy);choose();
}
$('candidate-select').addEventListener('change',choose);
document.querySelectorAll('[data-policy]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.policy)));
$('play').addEventListener('click',()=>{playing=!playing;$('play').textContent=playing?'Ⅱ 暂停':'▶ 播放';if(progress>=1)progress=0});$('scrub').addEventListener('input',e=>{progress=Number(e.target.value)/1000;draw()});
function tick(now){if(playing&&data){progress=Math.min(1,progress+(now-last)/20000);$('scrub').value=progress*1000;draw();if(progress===1){playing=false;$('play').textContent='↻ 重播'}}last=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);draw();
try{const response=await fetch('data/scenes.json');if(!response.ok)throw Error('Index');const index=await response.json(),select=$('scene-select');for(const scene of index.scenes){const option=document.createElement('option');option.value=scene.data;option.textContent=scene.label;option.selected=scene.id===index.default;select.append(option)}select.addEventListener('change',()=>loadScene(select.value).catch(()=>{$('status').textContent='场景数据加载失败'}));await loadScene(select.value)}catch(e){$('status').textContent='运行数据暂不可用';$('description').textContent='请检查场景材料是否完整。'}
$('model').addEventListener('error',()=>{$('model-error').hidden=false});
