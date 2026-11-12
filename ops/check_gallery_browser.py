"""Verify all catalog identities/covers, filters and lazy real model interaction."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8101/');p.add_argument('--name',default='C2-gallery-local');a=p.parse_args();out=ROOT/'evidence/award/acceptance';d=json.loads((ROOT/'site/data/gallery.json').read_text());facts=json.loads((ROOT/d['facts']).read_text());assert d['stats']==facts['stats']
 covers=json.loads((ROOT/'evidence/web-assets/gallery/posters/index.json').read_text());assert {r['task_id'] for r in covers['models']}=={r['task_id'] for r in d['models']}
 for r in covers['models']:
  assert r['loaded'] and r['rotation_checked'];assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
 errors=[];http=[];glbs=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']);page=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None);page.on('request',lambda r:glbs.append(r.url) if '.glb' in r.url else None)
  assert page.goto(urljoin(a.url,'gallery.html'),wait_until='networkidle').status==200;page.wait_for_function('document.documentElement.dataset.galleryReady==="true"');assert not glbs,'Initial screen must load no GLB'
  ids=[int(v) for v in page.locator('[data-task]').evaluate_all('(es)=>es.map(e=>e.dataset.task)')];assert set(ids)=={r['task_id'] for r in d['models']}
  expected={'all':len(d['models']),'admitted':d['stats']['admitted'],'rejected':d['stats']['rejected'],'collision':d['stats']['rejected_would_collide']};checked={}
  for key,n in expected.items():page.locator(f'[data-filter="{key}"]').click();assert page.locator('[data-task]').count()==n;checked[key]=n
  button=page.locator('[data-task]').first;task=int(button.get_attribute('data-task'));button.click();page.wait_for_function('document.querySelector("#gallery-model").loaded===true',timeout=60000);assert str(task) in page.locator('#gallery-facts').inner_text();assert '信了会撞' in page.locator('#gallery-facts').inner_text()
  viewer=page.locator('#gallery-model');theta=viewer.evaluate('(e)=>e.getCameraOrbit().theta');box=viewer.bounding_box();page.mouse.move(box['x']+box['width']*.8,box['y']+box['height']*.5);page.mouse.down();page.mouse.move(box['x']+box['width']*.2,box['y']+box['height']*.5,steps=25);page.mouse.up();page.wait_for_timeout(200);assert viewer.evaluate('(e)=>e.getCameraOrbit().theta')!=theta
  page.locator('[data-filter="all"]').click();page.locator('#gallery-search').fill(str(task));assert page.locator('[data-task]').count()==1;page.locator('#gallery-search').fill('');
  for scene in sorted({m['scene'] for m in d['models']}):page.locator('#gallery-scene').select_option(scene);assert page.locator('[data-task]').count()==sum(m['scene']==scene for m in d['models'])
  page.locator('#gallery-scene').select_option('all')
  for img in page.locator('img:visible').all():img.scroll_into_view_if_needed()
  page.wait_for_function('Array.from(document.querySelectorAll(".gallery-picks img,.gallery-input img")).every(e=>e.complete&&e.naturalWidth>0)')
  page.evaluate('scrollTo(0,0)');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/(a.name+'-1440.png')),full_page=True)
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/(a.name+'-390.png')),full_page=True)
  assert not errors,errors;assert not http,http;b.close()
 result={'passed':True,'checked_at':datetime.now(timezone.utc).isoformat(),'url':a.url,'catalog_models':len(ids),'stats':d['stats'],'stats_equal_gallery_facts':True,'all_covers_source_sha_loaded_rotated':len(covers['models']),'filters':checked,'all_scenes_checked':len({m['scene'] for m in d['models']}),'initial_glb_requests':0,'actual_pointer_rotation':True,'task_search':True,'mobile_390_no_overflow':True,'console_errors':errors,'http_errors':http};(out/(a.name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
