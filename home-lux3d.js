import './gallery-viewer.js';

const viewer=document.querySelector('#core-model');
const poster=document.querySelector('#model-poster');
const status=document.querySelector('#model-status');
const turn=document.querySelector('#model-turn');
const reset=document.querySelector('#model-reset');
let requested=false;
let homeDistance;
function fitHomeModel(preserveZoom=false){
  if(!viewer.loaded)return;
  const box=viewer.getBoundingClientRect();
  const aspect=box.width/Math.max(box.height,1);
  const zoom=preserveZoom&&homeDistance?viewer.distance/homeDistance:1;
  homeDistance=viewer.fitDistance*.55*Math.max(1,1.45/aspect);
  viewer.distance=homeDistance*zoom;
  viewer.requestRender();
}
new ResizeObserver(()=>fitHomeModel(true)).observe(document.querySelector('.model-stage'));
function loadModel(){
  if(requested)return;
  requested=true;
  const probe=document.createElement('canvas');
  const gl=probe.getContext('webgl2')||probe.getContext('webgl');
  if(!gl){status.textContent='可查看模型录屏，或下载原模型。';document.documentElement.dataset.modelFallback='true';return;}
  gl.getExtension('WEBGL_lose_context')?.loseContext();
  status.textContent='正在加载 Lux3D 返回的原模型…';
  viewer.hidden=false;
  viewer.src=viewer.dataset.source;
}
viewer.addEventListener('load',()=>{
  fitHomeModel();
  poster.hidden=true;
  status.textContent='拖动旋转 · 滚轮或双指缩放';
  turn.disabled=false;reset.disabled=false;
  document.documentElement.dataset.modelReady='true';
});
viewer.addEventListener('error',()=>{
  viewer.hidden=true;poster.hidden=false;
  status.textContent='3D 视图暂不可用，可查看录屏或下载原模型。';
  document.documentElement.dataset.modelFallback='true';
});
turn.addEventListener('click',()=>{viewer.yaw+=Math.PI;viewer.requestRender();});
reset.addEventListener('click',()=>{viewer.yaw=20*Math.PI/180;viewer.pitch=16*Math.PI/180;fitHomeModel();});
if('IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){observer.disconnect();loadModel();}},{rootMargin:'100px'});
  observer.observe(document.querySelector('.model-stage'));
}else loadModel();

const video=document.querySelector('#demo-video');
const error=document.querySelector('#video-error');
const chapterButtons=[...document.querySelectorAll('[data-video-time]')];
function activeChapter(){
  const eligible=chapterButtons.filter(b=>Number(b.dataset.videoTime)<=video.currentTime+.1);
  const active=eligible.at(-1);
  for(const button of chapterButtons)button.setAttribute('aria-pressed',String(button===active));
}
for(const button of chapterButtons)button.addEventListener('click',async()=>{
  const time=Number(button.dataset.videoTime);
  const seek=()=>{video.currentTime=time;video.play().catch(()=>{});};
  if(video.readyState>=1)seek();else video.addEventListener('loadedmetadata',seek,{once:true});
  video.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
});
video.addEventListener('timeupdate',activeChapter);
video.addEventListener('error',()=>error.hidden=false);
video.addEventListener('playing',()=>error.hidden=true);
video.addEventListener('loadeddata',()=>error.hidden=true);
activeChapter();
document.documentElement.dataset.homeReady='true';
