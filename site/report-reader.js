const pages=[...document.querySelectorAll('.report-pages .page')];
const links=[...document.querySelectorAll('[data-page-link]')];
const select=document.querySelector('#report-page-select');
let active=1,scheduled=false;
function update(n){
 active=n;for(const link of links){if(Number(link.dataset.pageLink)===n)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');}
 select.value=String(n);document.querySelector('#report-progress').textContent=`第 ${n} / ${pages.length} 页`;document.querySelector('#report-mobile-progress').textContent=`${n} / ${pages.length}`;
 document.querySelector('#report-prev').disabled=n===1;document.querySelector('#report-next').disabled=n===pages.length;
 document.documentElement.dataset.reportPage=String(n);
}
function go(n){
 n=Math.max(1,Math.min(pages.length,n));update(n);history.replaceState(null,'',`#page-${n}`);pages[n-1].scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
}
for(const link of links)link.onclick=e=>{e.preventDefault();go(Number(link.dataset.pageLink));};
select.onchange=()=>go(Number(select.value));document.querySelector('#report-prev').onclick=()=>go(active-1);document.querySelector('#report-next').onclick=()=>go(active+1);
function fromScroll(){scheduled=false;const line=innerHeight*.28;let n=1;pages.forEach((p,i)=>{if(p.getBoundingClientRect().top<=line)n=i+1;});update(n);}
addEventListener('scroll',()=>{if(!scheduled){scheduled=true;requestAnimationFrame(fromScroll);}},{passive:true});
const initial=Number(location.hash.match(/^#page-(\d+)$/)?.[1]||1);update(Math.max(1,Math.min(pages.length,initial)));if(initial>1)requestAnimationFrame(()=>go(initial));
