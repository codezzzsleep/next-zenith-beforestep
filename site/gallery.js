const $=s=>document.querySelector(s);
try{
const response=await fetch('data/gallery.json');if(!response.ok)throw Error('陈列室数据加载失败');const data=await response.json();
const models=data.models,viewer=$('#gallery-model');let selected=models.find(m=>m.task_id===5958685)||models[0],filter='all',scene='all',query='';
const stats=[['真实任务',data.stats.real_tasks],['返回模型',data.stats.returned_models],['通过检查',data.stats.admitted],['被拒',data.stats.rejected],['被拒中信了会撞',data.stats.rejected_would_collide]];
for(const [label,value] of stats){const span=document.createElement('span');span.innerHTML=`<strong>${value}</strong>${label}`;$('#gallery-stats').append(span);}
for(const name of [...new Set(models.map(m=>m.scene))].sort()){const option=new Option(name,name);$('#gallery-scene').add(option);}
const fmt=v=>v===undefined||v===null?'未记录':String(v);
function facts(context){const metrics=context.metrics;const verdict=context.admitted?'通过那次观测检查':'被拒：'+context.reason;const cf=selected.counterfactuals;const outcome=selected.would_collide?'信了会撞（已有实际反事实验证）':cf.length?'已验证的反事实运行未碰撞':'未验证';
const values=[['观测来源',`${context.scene} / ${context.target} / ${context.look}`],['检查结论',verdict]];if(cf.length||selected.would_collide)values.push(['反事实执行',outcome]);
$('#gallery-facts').replaceChildren();for(const [label,value] of values){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;$('#gallery-facts').append(dt,dd);}
$('#gallery-detail').replaceChildren();const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='完整指标与来源';details.append(summary);const dl=document.createElement('dl');dl.className='facts';for(const key of ['contour_iou','scale_ratio','hidden_frac','shell_contact','free_intrusion_frac','intrusion_depth_p95_mm']){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=fmt(metrics[key]);dl.append(dt,dd);}details.append(dl);const counterNote=document.createElement('p');counterNote.textContent='反事实验证记录：'+outcome;details.append(counterNote);
const source=document.createElement('a');source.href=context.source_decision;source.textContent='原始生产决策';details.append(source);const sha=document.createElement('p');sha.textContent='原GLB SHA-256：'+selected.source_sha256;sha.style.overflowWrap='anywhere';details.append(sha);
for(const run of cf){const p=document.createElement('p');p.textContent=`${run.scope} · ${run.scene} · ${run.policy} · ${run.result}`;const a=document.createElement('a');a.href=run.source;a.textContent=' 查看验证记录';p.append(a);details.append(p);}$('#gallery-detail').append(details);}
const imageRevisions=new WeakMap();
function stableImage(element,url){
 const revision=(imageRevisions.get(element)||0)+1;imageRevisions.set(element,revision);
 const image=new Image();image.onload=()=>{if(imageRevisions.get(element)===revision){element.src=url;element.hidden=element.id==='gallery-cover'&&viewer.loaded&&!viewer.hidden;}};
 image.onerror=()=>{if(imageRevisions.get(element)===revision)$('#gallery-error').hidden=false;};image.src=url;
}
function choose(model,load=true){
 selected=model;$('#gallery-title').textContent=`候选 ${model.sample}`;$('#gallery-selected-id').textContent='Lux3D · '+model.task_id;
 stableImage($('#gallery-cover'),model.poster);$('#gallery-cover').hidden=false;viewer.poster=model.poster;
 stableImage($('#gallery-source-input'),model.input);$('#gallery-input-link').href=model.input;$('#gallery-input-open').href=model.input;$('#gallery-download').href=model.model;
 $('#gallery-context').replaceChildren();model.contexts.forEach((c,i)=>$('#gallery-context').add(new Option(`${c.scene} · ${c.look} · ${c.target} · ${c.run_id==='historical'?'历史实验':c.run.includes('/r3/')?'赛后修订':'原运行'}`,i)));
 facts(model.contexts[0]);document.querySelectorAll('[data-task]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.task)===model.task_id)));
 $('#gallery-turn').disabled=true;$('#gallery-reset').disabled=true;
 if(load){viewer.hidden=false;viewer.src=model.model;$('#gallery-load').hidden=true;$('#gallery-error').hidden=true;$('#gallery-model-status').textContent='正在打开这份模型…';}
}
let fittedDistance;
function fitGallery(preserve=false){if(!viewer.loaded)return;const box=viewer.getBoundingClientRect(),aspect=box.width/Math.max(1,box.height),zoom=preserve&&fittedDistance?viewer.distance/fittedDistance:1;fittedDistance=viewer.fitDistance*.65*Math.max(1,1.45/aspect);viewer.distance=fittedDistance*zoom;viewer.requestRender();}
new ResizeObserver(()=>fitGallery(true)).observe(document.querySelector('.gallery-view'));
viewer.addEventListener('load',()=>{fitGallery();$('#gallery-cover').hidden=true;$('#gallery-load').hidden=true;$('#gallery-turn').disabled=false;$('#gallery-reset').disabled=false;$('#gallery-model-status').textContent='拖动旋转 · 滚轮或双指缩放';});
viewer.addEventListener('error',()=>{viewer.hidden=true;$('#gallery-cover').hidden=false;$('#gallery-load').hidden=false;$('#gallery-turn').disabled=true;$('#gallery-reset').disabled=true;$('#gallery-model-status').textContent='可以重新打开，或下载当前模型';});
$('#gallery-turn').onclick=()=>{viewer.yaw+=Math.PI;viewer.requestRender();};
$('#gallery-reset').onclick=()=>{viewer.yaw=20*Math.PI/180;viewer.pitch=16*Math.PI/180;fitGallery();viewer.requestRender();};
function render(){const visible=models.filter(m=>(scene==='all'||m.scene===scene)&&(!query||`${m.task_id} ${m.sample}`.toLowerCase().includes(query))&&(filter==='all'||filter==='admitted'&&m.admitted||filter==='rejected'&&!m.admitted||filter==='collision'&&m.would_collide&&!m.admitted));$('#gallery-count').textContent=`${visible.length} 份模型`;
const groups=new Map();for(const model of visible){const key=model.scene;const rows=groups.get(key)||new Map();const rockKey=`${model.target} · ${model.look}`;const row=rows.get(rockKey)||[];row.push(model);rows.set(rockKey,row);groups.set(key,rows);}const fragment=document.createDocumentFragment();
for(const [scene,rows] of groups){const section=document.createElement('section');section.className='gallery-scene';const h=document.createElement('h2');h.textContent=scene;section.append(h);for(const [rock,candidates] of rows){const row=document.createElement('div');row.className='gallery-row';const figure=document.createElement('figure');figure.className='gallery-input';const input=document.createElement('img');input.src=candidates[0].input;input.loading='lazy';input.width=160;input.height=160;input.alt='原样上传给Lux3D的照片';const caption=document.createElement('figcaption');caption.textContent=rock+' · 原上传图';figure.append(input,caption);const picks=document.createElement('div');picks.className='gallery-picks';for(const m of candidates){const button=document.createElement('button');button.type='button';button.className='pick'+(m.admitted?'':' rejected')+(m.would_collide?' crash':'');button.dataset.task=m.task_id;button.setAttribute('aria-pressed',String(selected.task_id===m.task_id));const img=document.createElement('img');img.src=m.poster;img.alt=`Lux3D ${m.task_id} ${m.sample}`;img.width=320;img.height=320;img.loading='lazy';const label=document.createElement('span');label.textContent=`${m.sample} · ${m.admitted?'通过':'被拒'}${m.would_collide?' · 信了会撞':''}\n${m.task_id}`;button.append(img,label);button.addEventListener('click',()=>{choose(m);$('.gallery-studio').scrollIntoView({behavior:'smooth',block:'start'});});picks.append(button);}row.append(figure,picks);section.append(row);}fragment.append(section);}if(!visible.length){const p=document.createElement('p');p.className='gallery-empty';p.textContent='这个筛选下没有模型。';fragment.append(p);}$('#gallery-groups').replaceChildren(fragment);}
$('#gallery-context').addEventListener('change',e=>facts(selected.contexts[Number(e.target.value)]));$('#gallery-load').addEventListener('click',()=>choose(selected));viewer.addEventListener('error',()=>$('#gallery-error').hidden=false);
for(const button of document.querySelectorAll('[data-filter]'))button.addEventListener('click',()=>{filter=button.dataset.filter;document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-selected',String(b===button)));render();});$('#gallery-scene').addEventListener('change',e=>{scene=e.target.value;render();});$('#gallery-search').addEventListener('input',e=>{query=e.target.value.trim().toLowerCase();render();});choose(selected,false);render();document.documentElement.dataset.galleryReady='true';

}catch(error){const panel=$('#gallery-error');panel.hidden=false;panel.textContent='模型资料暂时未加载，刷新页面即可重试。';}
