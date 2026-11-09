const $=id=>document.getElementById(id);
const names={optimistic:['直接走','把阴影当作可以通过的空间，机器人会遇到岩石背面的真实碰撞。'],conservative:['看清再走','始终把看不见的地方视作障碍。观察多次，仍然可能无法找到路线。'],imagination:['想一想再走','Lux3D 提供多种候选几何。自检通过才参与预演；没有足够证据时，再看一眼或停下。']};
const results={collision:'遇到碰撞',stuck:'停下，证据不足',arrived:'到达终点',stopped_short:'未完成路线'};
let data,policy='imagination',playing=false,progress=0,last=0;
const canvas=$('route'),ctx=canvas.getContext('2d');
function project(x,y){return [65+(x+1)*74,canvas.height*.5-y*65]}
function draw(){
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#101720';ctx.fillRect(0,0,canvas.width,canvas.height);
 ctx.strokeStyle='#202b38';ctx.lineWidth=1;for(let x=0;x<13;x++){const [xx]=project(x,0);ctx.beginPath();ctx.moveTo(xx,25);ctx.lineTo(xx,365);ctx.stroke()}
 ctx.fillStyle='#1a2530';ctx.fillRect(0,canvas.height*.5+90,1000,200);ctx.fillStyle='#1b2834';ctx.fillRect(0,0,1000,canvas.height*.5-90);
 if(data){for(const rock of data.rocks){const [x,y]=project(rock.x,rock.y);ctx.fillStyle='#27313d';ctx.fillRect(x+15,y-55,125,90);ctx.fillStyle='#7e8588';ctx.beginPath();rock.polygon.forEach((point,index)=>{const p=project(...point);index?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.closePath();ctx.fill()}}
 ctx.fillStyle='#657687';ctx.font='13px sans-serif';ctx.fillText('月溪 · 禁行',70,45);ctx.fillText('岩壁 · 禁行',70,350);
 const [gx,gy]=project(10.5,0);ctx.strokeStyle='#70dbb2';ctx.setLineDash([4,4]);ctx.strokeRect(gx-12,gy-12,24,24);ctx.setLineDash([]);ctx.fillStyle='#70dbb2';ctx.fillText('终点',gx-14,gy+35);
 const run=data?.runs[policy];if(!run?.trajectory?.length){ctx.fillStyle='#93a4b5';ctx.fillText('正在加载真实运行数据…',340,195);return}
 const limit=Math.floor(progress*(run.trajectory.length-1));const track=run.trajectory;
 ctx.lineWidth=3;ctx.strokeStyle=policy==='optimistic'?'#ff997c':'#70dbb2';ctx.beginPath();track.slice(0,limit+1).forEach((v,i)=>{const p=project(v[1],v[2]);i?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.stroke();
 const pose=track[limit],p=project(pose[1],pose[2]);ctx.save();ctx.translate(...p);ctx.rotate(-pose[3]);ctx.fillStyle='#e3edf0';ctx.fillRect(-20,-12,40,24);ctx.fillStyle='#ee9c57';ctx.fillRect(10,-9,8,18);ctx.restore();$('time').textContent=`${pose[0].toFixed(1)} s`;
}
function select(key){policy=key;progress=0;playing=false;$('play').textContent='▶ 播放';$('scrub').value=0;document.querySelectorAll('[data-policy]').forEach(b=>b.classList.toggle('active',b.dataset.policy===key));const run=data?.runs[key];$('strategy').textContent=names[key][0];$('description').textContent=names[key][1];$('status').textContent=run?results[run.result]||run.result:'运行数据尚未生成';$('looks').textContent=run?.looks??'—';$('duration').textContent=run?`${run.sim_time_s}s`:'—';draw()}
document.querySelectorAll('[data-policy]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.policy)));
$('play').addEventListener('click',()=>{playing=!playing;$('play').textContent=playing?'Ⅱ 暂停':'▶ 播放';if(progress>=1)progress=0});$('scrub').addEventListener('input',e=>{progress=Number(e.target.value)/1000;draw()});
function tick(now){if(playing&&data){progress=Math.min(1,progress+(now-last)/20000);$('scrub').value=progress*1000;draw();if(progress===1){playing=false;$('play').textContent='↻ 重播'}}last=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);draw();
try{const response=await fetch('data/demo.json');if(!response.ok)throw Error('data');data=await response.json();select(policy);const options=$('candidate-select');for(const c of data.candidates){const o=document.createElement('option');o.value=c.id;o.textContent=c.label;options.append(o)}function choose(){const c=data.candidates.find(c=>c.id===options.value);if(!c)return;$('model').src=c.glb;$('input').src=c.input;$('candidate-info').textContent=`真实任务 ${c.task_id} · ${c.verdict}`};options.addEventListener('change',choose);choose()}catch(e){$('status').textContent='运行数据暂不可用';$('description').textContent='请运行源码中的材料生成命令，然后刷新此页。'}
$('model').addEventListener('error',()=>{$('model-error').hidden=false});
