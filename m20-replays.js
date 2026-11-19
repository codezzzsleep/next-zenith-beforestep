const video=document.querySelector('#m20-video');
const buttons=[...document.querySelectorAll('.m20-chapters button')];
function active(button){for(const b of buttons)b.setAttribute('aria-pressed',String(b===button));}
for(const button of buttons)button.addEventListener('click',()=>{
  active(button);
  if(button.dataset.file){video.src='media/m20-showcase/'+button.dataset.file;video.load();video.play().catch(()=>{});}
  else{const seek=()=>{video.currentTime=Number(button.dataset.time);video.play().catch(()=>{});};if(video.readyState>=1)seek();else video.addEventListener('loadedmetadata',seek,{once:true});}
});
video?.addEventListener('timeupdate',()=>{const chapter=buttons.filter(b=>b.dataset.time!==undefined&&Number(b.dataset.time)<=video.currentTime+.1).at(-1);if(chapter)active(chapter);});
const select=document.querySelector('#record-scene');
if(select){
  const names={optimistic:'直接走 · 乐观',conservative:'看清再走 · 保守',imagination:'空间想象 + 预演'};
  const results={arrived:'到达',collision:'碰撞',stuck:'停车',stopped:'停车',stopped_short:'未完成'};
  let sequence=0;
  async function show(){
    const current=++sequence,tbody=document.querySelector('#record-results');tbody.replaceChildren();
    const rows=await Promise.all(Object.keys(names).map(async policy=>{
      const response=await fetch(`data/recordings/${select.value}-${policy}.json`);
      if(!response.ok)return null;
      const data=await response.json(),result=data.original_result;
      const row=document.createElement('tr');
      for(const value of [names[policy],`${result.looks??'—'} 眼`,`${Number(result.sim_time_s??0).toFixed(2)} s`,results[result.result]||result.result]){
        const cell=document.createElement('td');cell.textContent=value;if(value==='到达')cell.className='arrived';row.append(cell);
      }
      return row;
    }));
    if(current===sequence)tbody.replaceChildren(...rows.filter(Boolean));
  }
  try{
    const response=await fetch('data/footage.json');if(!response.ok)throw Error('records');
    const data=await response.json();for(const row of data.levels){const label=row.id==='stress_v8'?'R1 · 月溪窄道':row.id.replace('suite_r2_v4_','');select.add(new Option(label,row.id));}
    select.addEventListener('change',()=>show().catch(()=>{}));await show();
  }catch{document.querySelector('#record-results').textContent='记录暂未加载，可从报告继续查看。';}
}
document.documentElement.dataset.m20ReplayReady='true';
