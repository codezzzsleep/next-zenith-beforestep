"""Load and rotate every registered truth/imagined overlay in Chromium."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8101/');p.add_argument('--name',default='C4-overlays-local');a=p.parse_args();out=ROOT/'evidence/award/acceptance';d=json.loads((ROOT/'evidence/web-assets/overlays/index.json').read_text());errors=[];http=[];loaded=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',args=['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None);page.goto(urljoin(a.url,'overlays.html'),wait_until='networkidle');page.wait_for_function('document.querySelector("#overlay-model").loaded===true');page.evaluate('window.overlayLoads=0;document.querySelector("#overlay-model").addEventListener("load",()=>window.overlayLoads++)')
  for i,m in enumerate(d['models']):
   if i:
    n=page.evaluate('window.overlayLoads');page.locator('#overlay-select').select_option(str(i));page.wait_for_function('(n)=>window.overlayLoads>n&&document.querySelector("#overlay-model").loaded===true',arg=n,timeout=60000)
   viewer=page.locator('#overlay-model');assert viewer.evaluate('(e)=>e.src')==m['path'];theta=viewer.evaluate('(e)=>e.getCameraOrbit().theta');viewer.evaluate('(e)=>{e.cameraOrbit="200deg 74deg 92%";e.jumpCameraToGoal()}');assert viewer.evaluate('(e)=>e.getCameraOrbit().theta')!=theta;viewer.evaluate('(e)=>{e.cameraOrbit="20deg 74deg 92%";e.jumpCameraToGoal()}');loaded.append(m['task_id'])
   if i in [0,1,9,17,25]:page.screenshot(path=str(out/(a.name+'-'+str(m['task_id'])+'.png')),full_page=True)
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/(a.name+'-390.png')),full_page=True);assert not errors,errors;assert not http,http;b.close()
 result={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'url':a.url,'loaded_and_rotated_tasks':loaded,'overlay_count':len(loaded),'mobile_390_no_overflow':True,'console_errors':errors,'http_errors':http};(out/(a.name+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'overlays':len(loaded)}))
if __name__=='__main__':main()
