const byId=id=>document.getElementById(id);
const resultNames={arrived:'到达',stuck:'停车',collision:'碰撞',stopped_short:'未到达'};
let observations,view=0;
function showObservation(next){
 view=next;
 byId('shadow-second').style.opacity=String(view);
 byId('shadow-range').value=String(view*100);
 byId('shadow-view').textContent=view?'第二眼 · 保守车真实补看':'第一眼 · 与原 Lux 运行同字节';
 byId('shadow-toggle').textContent=view?'回到第一眼':'再看一眼 →';
 const map=observations.map,[nx,ny]=map.shape,c=byId('shadow-map'),g=c.getContext('2d'),values=view?map.second:map.first;
 const colors=['#264b3c','#a1aba8','#b98749','#76589b','#17232e'];
 for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){g.fillStyle=colors[values[i*ny+j]];g.fillRect(i*c.width/nx,(ny-j-1)*c.height/ny,c.width/nx+.2,c.height/ny+.2)}
 byId('shadow-map-caption').textContent=view?'第二眼的实际地图：视线遮挡随观察位置变化。太阳、岩石与传感器保持原配置。':'第一眼的实际地图：棕色 DARK，紫色 HIDDEN。移到另一个真实观察位置，看看地图如何改变。';
}
function drawTrack(canvas,run,rocks){
 const g=canvas.getContext('2d'),q=(x,y)=>[(x+1)/14*canvas.width,(2.5-y)/4.5*canvas.height];
 g.fillStyle='#101820';g.fillRect(0,0,canvas.width,canvas.height);
 for(const rock of rocks){g.fillStyle='#8b98986b';g.beginPath();rock.polygon.forEach((p,i)=>{const xy=q(...p);i?g.lineTo(...xy):g.moveTo(...xy)});g.closePath();g.fill()}
 g.strokeStyle=run.result==='collision'?'#ff9575':'#70dbb2';g.lineWidth=2;g.beginPath();run.trajectory.forEach((p,i)=>{const xy=q(p[1],p[2]);i?g.lineTo(...xy):g.moveTo(...xy)});g.stroke();
}
async function setup(){
 const response=await fetch('data/award-observations.json');if(!response.ok)throw Error('真实观测未加载');observations=await response.json();
 const figure=byId('hero-real-image');for(const tag of observations.labels){const el=document.createElement('span');el.className='rock-tag';el.textContent=tag.label;el.style.left=tag.x_percent+'%';el.style.top=tag.y_percent+'%';figure.append(el)}
 byId('shadow-range').addEventListener('input',e=>showObservation(Number(e.target.value)>=50?1:0));
 byId('shadow-toggle').addEventListener('click',()=>showObservation(1-view));showObservation(0);
 const sceneResponse=await fetch('data/demo.json');if(!sceneResponse.ok)throw Error('真实轨迹未加载');const data=await sceneResponse.json();
 for(const card of document.querySelectorAll('[data-award-choice]')){
  const key=card.dataset.awardChoice,run=data.runs[key];drawTrack(card.querySelector('canvas'),run,data.rocks);
  card.addEventListener('click',()=>{card.querySelector('.choice-outcome').textContent=`${resultNames[run.result]} · ${run.looks}眼 · ${run.sim_time_s}s 仿真`;card.setAttribute('aria-pressed','true');});
 }
 byId('award-model-rotate').addEventListener('click',()=>{const model=byId('model');model.cameraOrbit='180deg 65deg auto';model.jumpCameraToGoal();});
 document.documentElement.dataset.awardReady='true';
}
setup().catch(error=>{byId('shadow-view').textContent=error.message;document.documentElement.dataset.awardReady='error';});
