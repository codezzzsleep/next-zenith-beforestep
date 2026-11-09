const $=id=>document.getElementById(id),route=$('learning-route'),ctx=route.getContext('2d'),actions=$('learning-actions'),g=actions.getContext('2d');
let data,run,index=0,playing=false,last=0;
const project=(x,y)=>[65+(x+1)*74,route.height*.5-y*65];
function line(points,color,width=3){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();points.forEach((p,i)=>{const q=project(...p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.stroke()}
function draw(){
 if(!run)return;ctx.fillStyle='#101720';ctx.fillRect(0,0,route.width,route.height);
 ctx.fillStyle='#1a2530';ctx.fillRect(0,290,1000,100);ctx.fillRect(0,0,1000,90);
 for(const rock of run.rocks){ctx.fillStyle='#778085';ctx.beginPath();rock.polygon.forEach((p,i)=>{const q=project(...p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.closePath();ctx.fill()}
 if(run.reference_path){ctx.setLineDash([7,5]);line([run.start,...run.reference_path],'#ff997c',2);ctx.setLineDash([])}
 if(run.selected_path)line([run.start,...run.selected_path],'#70dbb2',2);
 const frames=run.frames,i=Math.min(Math.floor(index*(frames.length-1)),frames.length-1),frame=frames[i];
 line(frames.slice(0,i+1).map(f=>[f.x,f.y]),'#70dbb2',3);const [gx,gy]=project(...run.goal);ctx.strokeStyle='#70dbb2';ctx.strokeRect(gx-12,gy-12,24,24);
 const [x,y]=project(frame.x,frame.y);ctx.save();ctx.translate(x,y);ctx.rotate(-frame.yaw);ctx.fillStyle='#e6edf1';ctx.fillRect(-20,-12,40,24);ctx.fillStyle='#ef9f5e';ctx.fillRect(12,-8,6,16);ctx.restore();
 $('learning-time').textContent=`${frame.elapsed.toFixed(1)} s`;$('learning-source').textContent=frame.source==='learned'?'训练模型':frame.source==='brake'?'停稳制动':frame.source;
 g.fillStyle='#101720';g.fillRect(0,0,actions.width,actions.height);g.strokeStyle='#2d3844';g.beginPath();g.moveTo(35,120);g.lineTo(980,120);g.stroke();
 const colors=['#77a7f4','#bc90ed','#70dbb2','#ff997c'];for(let channel=0;channel<4;channel++){g.strokeStyle=colors[channel];g.lineWidth=2;g.beginPath();frames.forEach((f,j)=>{const px=35+j/(frames.length-1)*945,py=120-f.action[channel]*95;j?g.lineTo(px,py):g.moveTo(px,py)});g.stroke()}
 g.strokeStyle='#e6edf1';g.beginPath();g.moveTo(35+index*945,20);g.lineTo(35+index*945,220);g.stroke();
}
function select(){run=data.runs.find(r=>r.id===$('learning-run').value);index=0;playing=false;$('learning-play').textContent='▶ 播放';$('learning-scrub').value=0;
 $('learning-title').textContent=run.title;$('learning-note').textContent=run.note;$('learning-status').textContent={arrived:'到达终点',stuck:'预演未通过，停下',collision:'碰撞停止',stopped_short:'未完成'}[run.result]||run.result;
 $('learning-duration').textContent=`${run.duration.toFixed(2)} s`;$('learning-panes').textContent=run.panes?`${run.panes_passed}/${run.panes}`:'—';$('learning-evidence').href=run.evidence;draw();}
function evaluations(){const container=$('evaluation-results');container.replaceChildren();for(const evaluation of data.evaluations){const article=document.createElement('article');article.className='learning-evaluation';const h=document.createElement('h3');h.textContent=evaluation.title;article.append(h);const table=document.createElement('table');const head=document.createElement('thead');head.innerHTML='<tr><th>控制模型</th><th>成功 / 任务数</th><th>成功率</th></tr>';table.append(head);const body=document.createElement('tbody');for(const row of evaluation.controllers){const tr=document.createElement('tr');for(const value of [row.label,`${row.successes}/${row.episodes}`,`${(row.success_rate*100).toFixed(1)}%`]){const td=document.createElement('td');td.textContent=value;tr.append(td)}body.append(tr)}table.append(body);article.append(table);const p=document.createElement('p');p.className='caption';p.textContent=evaluation.note;article.append(p);container.append(article)}}
$('learning-run').addEventListener('change',select);$('learning-play').addEventListener('click',()=>{if(index>=1)index=0;playing=!playing;$('learning-play').textContent=playing?'Ⅱ 暂停':'▶ 播放'});$('learning-scrub').addEventListener('input',e=>{index=Number(e.target.value)/1000;draw()});
function tick(now){if(playing&&run){index=Math.min(1,index+(now-last)/18000);$('learning-scrub').value=index*1000;draw();if(index>=1){playing=false;$('learning-play').textContent='↻ 重播'}}last=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);
try{const response=await fetch('data/learning.json');if(!response.ok)throw Error('missing');data=await response.json();for(const r of data.runs){const option=document.createElement('option');option.value=r.id;option.textContent=r.title;$('learning-run').append(option)}evaluations();select()}catch(e){$('learning-status').textContent='训练材料暂未加载';$('evaluation-results').textContent='请通过 beforestep serve 打开，并检查材料是否完整。'}
