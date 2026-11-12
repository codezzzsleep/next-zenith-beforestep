"""Offline model-viewer cover renders; verify each real GLB loads and rotates."""
import argparse
import asyncio
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urljoin
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
SETTINGS={'camera-orbit':'20deg 74deg 92%','exposure':'1.4','shadow-intensity':'0.7','shadow-softness':'0.9','width':320,'height':320}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');t.replace(p)
async def run(a):
 data=json.loads((ROOT/'site/data/gallery.json').read_text());out=ROOT/'evidence/web-assets/gallery/posters';out.mkdir(parents=True,exist_ok=True);index=out/'index.json';old=json.loads(index.read_text()) if index.exists() else {'models':[]};records={r['task_id']:r for r in old['models']};jobs=asyncio.Queue()
 for m in data['models']:
  p=ROOT/m['poster'];r=records.get(m['task_id']);
  if r and r['source_sha256']==m['web_sha256'] and r['settings']==SETTINGS and p.exists() and sha(p)==r['sha256']:continue
  jobs.put_nowait(m)
 job={'status':'running','pid':os.getpid(),'started_at':datetime.now(timezone.utc).isoformat(),'models_total':len(data['models']),'completed':len(records),'paid_tasks':0,'index':str(index.relative_to(ROOT))};ledger=Path(a.ledger)
 def save():write(index,{'schema':'beforestep-gallery-model-viewer-covers/v1','settings':SETTINGS,'models':sorted(records.values(),key=lambda r:r['task_id'])});job['completed']=len(records);write(ledger,job)
 save()
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  async def worker():
   page=await browser.new_page(viewport={'width':320,'height':320},reduced_motion='reduce');errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
   await page.goto(urljoin(a.url,'gallery-render-shell.html'),wait_until='networkidle')
   await page.set_content(f'<html><head><base href="{a.url}"><script type="module" src="vendor/model-viewer.min.js"></script><style>html,body{{margin:0;background:#0a0b0c}}model-viewer{{width:320px;height:320px;background:radial-gradient(ellipse at 50% 62%,#1b2024 0%,#0a0b0c 68%)}}</style></head><body><model-viewer camera-orbit="20deg 74deg 92%" exposure="1.4" shadow-intensity="0.7" shadow-softness="0.9" loading="eager" interaction-prompt="none"></model-viewer></body></html>')
   await page.wait_for_function('customElements.get("model-viewer")!==undefined')
   await page.evaluate('window.loads=0;document.querySelector("model-viewer").addEventListener("load",()=>window.loads++)')
   while not jobs.empty():
    m=jobs.get_nowait();prior=await page.evaluate('window.loads');await page.evaluate('(src)=>document.querySelector("model-viewer").src=src',urljoin(a.url,m['model']))
    await page.wait_for_function('(n)=>window.loads>n&&document.querySelector("model-viewer").loaded===true',arg=prior,timeout=60000)
    theta=await page.locator('model-viewer').evaluate('(e)=>e.getCameraOrbit().theta');await page.locator('model-viewer').evaluate('(e)=>{e.cameraOrbit="200deg 74deg 92%";e.jumpCameraToGoal()}');await page.wait_for_timeout(100)
    assert abs(await page.locator('model-viewer').evaluate('(e)=>e.getCameraOrbit().theta')-theta)>1
    await page.locator('model-viewer').evaluate('(e)=>{e.cameraOrbit="20deg 74deg 92%";e.jumpCameraToGoal()}');await page.wait_for_timeout(160)
    p=ROOT/m['poster'];await page.locator('model-viewer').screenshot(path=str(p),type='jpeg',quality=88);assert not errors,errors
    records[m['task_id']]={'task_id':m['task_id'],'path':m['poster'],'sha256':sha(p),'bytes':p.stat().st_size,'source':m['model'],'source_sha256':m['web_sha256'],'settings':SETTINGS,'loaded':True,'rotation_checked':True}
    save();jobs.task_done()
    if len(records)%12==0:print(json.dumps({'rendered_and_rotated':len(records)}),flush=True)
   await page.close()
  try:await asyncio.gather(*(worker() for _ in range(a.workers)))
  except Exception as e:job.update(status='failed',error=str(e));save();raise
  finally:await browser.close()
 job.update(status='complete',completed_at=datetime.now(timezone.utc).isoformat());save();print(json.dumps({'passed':True,'models':len(records),'settings':SETTINGS}))
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8101/');p.add_argument('--workers',type=int,default=3);p.add_argument('--ledger',default=str(ROOT/'outputs/qa/award/gallery-posters-job.json'));a=p.parse_args();asyncio.run(run(a))
if __name__=='__main__':main()
