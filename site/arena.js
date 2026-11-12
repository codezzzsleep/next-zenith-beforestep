const $=s=>document.querySelector(s), pct=x=>x==null?'—':`${(x*100).toFixed(1)}%`;
const names={conservative:'保守规则',optimistic:'乐观规则',imagination:'原想象规则',strict:'严格规则',strict_llm:'严格 + LLM',learned:'学习 + Lux3D',learned_no_lux:'学习，去掉 Lux3D',see_dark:'能看见黑影 · 参照'};
const states=['#e5dfd2','#6a6256','#b9a79b','#c3bfb5','#efede7','#736b61'];
let index,current,payload,playing=false,last=0,progress=1;
const decoded=new WeakMap();
const tiles=new WeakMap(),rgb=states.map(s=>s.slice(1).match(/../g).map(v=>parseInt(v,16)));
function unpack(s){return Uint8Array.from(atob(s),c=>c.charCodeAt(0));}
function grid(s){if(typeof s==='string')return unpack(s);const a=new Uint8Array(s.length);let k=0;for(const [n,v]of s.runs){a.fill(v,k,k+n);k+=n;}return a;}
function method(){return $('#arena-method').value;}
function selected(){return payload?.methods[method()];}
function imageData(p,entry,eye){
  let cache=decoded.get(entry);if(!cache){cache={states:entry.states.map(grid),risks:entry.risks.map(grid)};decoded.set(entry,cache);}
  return {state:cache.states[Math.min(eye,cache.states.length-1)],risk:cache.risks[Math.min(eye,cache.risks.length-1)]};
}
function draw(canvas,entry){
  if(!payload||!entry){canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);return;}
  const ctx=canvas.getContext('2d'),[nx,ny]=payload.shape,[x0,x1,y0,y1]=payload.bounds;
  const trace=entry.trace,stop=Math.max(0,Math.floor(progress*(trace.length-1)));
  let eye=0;for(let k=0;k<entry.eye_indices.length;k++)if(entry.eye_indices[k]<=stop)eye=k;
  const key=[eye,$('#arena-risk').checked,$('#arena-truth').checked,$('#arena-hypotheses').checked].join('-');
  let cached=tiles.get(entry);if(!cached){cached=new Map();tiles.set(entry,cached);}
  let tile=cached.get(key);
  if(!tile){
  const {state,risk}=imageData(payload,entry,eye),truth=payload.truth_decoded||(payload.truth_decoded=grid(payload.truth));
  tile=document.createElement('canvas');tile.width=nx;tile.height=ny;const tc=tile.getContext('2d'),im=tc.createImageData(nx,ny);
  for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){
    const k=i*ny+j,offset=((ny-1-j)*nx+i)*4;
    let color=rgb[state[k]]||rgb[4];
    if($('#arena-risk').checked&&risk&&[2,3,4].includes(state[k])){const v=risk[k]/255;color=[Math.round(240-84*v),Math.round(231-153*v),Math.round(210-145*v)];}
    if($('#arena-truth').checked&&truth[k])color=[157,118,73];
    im.data.set([...color,255],offset);
  }
  tc.putImageData(im,0,0);
  if($('#arena-hypotheses').checked){for(const hypothesis of payload.hypotheses){tc.fillStyle=hypothesis.admitted?'#4d769448':'#9c6b5c2c';for(const point of hypothesis.cells){tc.fillRect((point[0]-x0)/(x1-x0)*nx,(y1-point[1])/(y1-y0)*ny,1,1);}}}
  cached.set(key,tile);
  }
  ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(tile,0,0,canvas.width,canvas.height);
  const xy=q=>[(q[0]-x0)/(x1-x0)*canvas.width,(y1-q[1])/(y1-y0)*canvas.height];
  ctx.strokeStyle='#2f806c';ctx.lineWidth=3;ctx.beginPath();trace.slice(0,stop+1).forEach((q,k)=>{const [x,y]=xy(q);k?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
  for(let k=0;k<=eye;k++){const [x,y]=xy(entry.observations[k].position);ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.strokeStyle='#fffdf7';ctx.lineWidth=2;ctx.stroke();}
  const [gx,gy]=xy(payload.goal);ctx.fillStyle='#bf9143';ctx.fillRect(gx-5,gy-5,10,10);
  const [cx,cy]=xy(trace[stop]||trace[0]);ctx.beginPath();ctx.arc(cx,cy,5,0,Math.PI*2);ctx.fillStyle='#1e5447';ctx.fill();
}
function render(){draw($('#arena-map'),selected());for(const c of document.querySelectorAll('#arena-parallel canvas'))draw(c,payload?.methods[c.dataset.method]);$('#arena-scrub').value=Math.round(progress*1000);}
function wall(){
  const target=$('#arena-wall');target.replaceChildren();
  for(const w of index.worlds){if($('#arena-failures').checked&&w.results.learned==='arrived')continue;const b=document.createElement('button'),status=w.results[method()]||'missing';b.className=`arena-cell ${status}`;b.title=`${w.seed} · ${names[method()]} · ${status}`;b.setAttribute('aria-label',b.title);b.setAttribute('aria-pressed',String(w.seed===current));b.onclick=()=>open(w.seed);target.append(b);}
}
async function open(seed){
  current=seed;payload=null;wall();$('#arena-status').textContent='加载记录…';
  const requested=seed,response=await fetch(`data/arena/worlds/${seed}.json.gz`);if(!response.ok)throw Error(`World ${seed}: HTTP ${response.status}`);
  const bytes=new Uint8Array(await response.arrayBuffer());
  const raw=bytes[0]===31&&bytes[1]===139?await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text():new TextDecoder().decode(bytes);
  if(current!==requested)return;payload=JSON.parse(raw);progress=1;facts();render();
}
function facts(){
  const entry=selected();$('#arena-title').textContent=`种子 ${current} · ${payload.capsule_id}`;
  $('#arena-status').textContent=entry?({arrived:'到达',collision:'碰撞',stopped:'停车'}[entry.status]||entry.status):'不在 LLM 子集中';
  $('#arena-facts').replaceChildren();if(!entry){$('#arena-evidence').removeAttribute('href');return;}
  for(const [term,value]of [['方法',names[method()]],['观测次数',entry.observations.length],['路径长度',`${entry.path_length_m.toFixed(2)} m`],['含观察耗时',`${entry.elapsed_seconds.toFixed(2)} s`],['真值规划可达',payload.reachable?'是':'否']]){const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=term;dd.textContent=value;div.append(dt,dd);$('#arena-facts').append(div);}
  $('#arena-evidence').href=entry.evidence;
}
function frame(now){if(playing){progress=Math.min(1,progress+(now-last)/18000);if(progress===1){playing=false;$('#arena-play').textContent='▶ 播放';}render();}last=now;requestAnimationFrame(frame);}
async function boot(){
  const response=await fetch('data/arena.json');if(!response.ok)throw Error(`Index: HTTP ${response.status}`);index=await response.json();
  $('#arena-headline').textContent=index.headline;
  for(const m of index.methods){const option=document.createElement('option');option.value=m.id;option.textContent=names[m.id];$('#arena-method').append(option);const card=document.createElement('article');card.className='arena-result';const h=document.createElement('h3');h.textContent=names[m.id];card.append(h);for(const text of [`${m.worlds} 场`, `到达 ${pct(m.arrival_rate)}`,`碰撞 ${pct(m.collision_rate)}`,`停车 ${pct(m.stop_rate)}`]){const p=document.createElement('p');p.textContent=text;card.append(p);}$('#arena-results').append(card);}
  $('#arena-method').value='learned';$('#arena-verdict').textContent=index.verdict_text;$('#arena-effects').textContent=index.effects_text;$('#arena-training').textContent=index.training_text;$('#arena-llm').textContent=index.llm_text;
  for(const r of index.real_heldouts){const card=document.createElement('article');card.className='arena-result';const title=document.createElement('h3');title.textContent=r.scene;card.append(title);for(const [key,label]of [['learned','学习模型'],['strict','既有严格'],['imagination','既有原想象'],['see_dark','既有参照']]){const p=document.createElement('p');p.textContent=`${label}：${r[key]??'未记录'}`;card.append(p);}$('#arena-real').append(card);}
  for(const id of ['optimistic','strict','learned']){const div=document.createElement('div'),h=document.createElement('h4'),canvas=document.createElement('canvas');h.textContent=names[id];canvas.width=1120;canvas.height=360;canvas.dataset.method=id;div.append(h,canvas);$('#arena-parallel').append(div);}
  $('#arena-method').onchange=()=>{wall();if(payload){facts();render();}};$('#arena-failures').onchange=wall;
  $('#arena-random').onclick=()=>{const visible=index.worlds.filter(w=>!$('#arena-failures').checked||w.results.learned!=='arrived'),other=visible.filter(w=>w.seed!==current),candidates=other.length?other:visible;if(candidates.length)open(candidates[Math.floor(Math.random()*candidates.length)].seed).catch(fail);};
  $('#arena-play').onclick=()=>{if(!payload)return;playing=!playing;if(playing&&progress===1)progress=0;$('#arena-play').textContent=playing?'Ⅱ 暂停':'▶ 播放';};$('#arena-scrub').oninput=e=>{progress=Number(e.target.value)/1000;render();};
  for(const id of ['arena-truth','arena-hypotheses','arena-risk'])$('#'+id).onchange=render;
  await open(index.representatives[0]??index.worlds[0].seed);requestAnimationFrame(frame);
}
function fail(error){$('#arena-status').textContent=error.message;$('#arena-headline').textContent='实验记录暂时无法加载，请查看完整报告。';console.error(error);}
boot().catch(fail);
