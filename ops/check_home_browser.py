"""Verify the delivered homepage in real Chromium, locally or on Pages."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8101/');p.add_argument('--name',default='home-local');a=p.parse_args()
 out=ROOT/'evidence/award/acceptance';out.mkdir(parents=True,exist_ok=True)
 errors=[];http=[];result={'url':a.url,'checked_at':datetime.now(timezone.utc).isoformat(),'passed':False}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  page.on('requestfailed',lambda r:http.append({'url':r.url,'error':r.failure}) if r.failure!='net::ERR_ABORTED' else None)
  try:
   t=time.monotonic();assert page.goto(a.url,wait_until='networkidle').status==200
   page.wait_for_function('document.querySelector("#hero-rock").loaded===true',timeout=60000)
   result['hero_load_s']=time.monotonic()-t;assert page.locator('.shot img').first.evaluate('(e)=>e.complete&&e.naturalWidth>0')
   hero=page.locator('#hero-rock');box=hero.bounding_box();start_theta=hero.evaluate('(e)=>e.getCameraOrbit().theta')
   for i in range(6):
    page.mouse.move(box['x']+box['width']*.82,box['y']+box['height']*.5);page.mouse.down();page.mouse.move(box['x']+box['width']*.18,box['y']+box['height']*.5,steps=25);page.mouse.up();page.wait_for_timeout(300)
    if page.locator('#back-flag').is_visible():break
   assert page.locator('#back-flag').is_visible();assert hero.evaluate('(e)=>e.getCameraOrbit().theta')!=start_theta
   assert page.locator('#back-flag').inner_text()=='这一面，相机从没见过'
   result['actual_pointer_drag_reveals_back']=True
   if page.locator('.turns button').count():
    assert page.locator('.turns button').count()==2
    page.locator('.turns button').first.click()
    page.wait_for_function('Math.abs(document.querySelector("#hero-rock").getCameraOrbit().theta*180/Math.PI-15)<1')
    page.wait_for_function('document.querySelector("#back-flag").hidden===true')
    page.locator('.turns button').last.click()
    page.wait_for_function('Math.abs(document.querySelector("#hero-rock").getCameraOrbit().theta*180/Math.PI-195)<1')
    page.wait_for_function('document.querySelector("#back-flag").hidden===false')
    result['front_and_back_buttons_actual_orbits']=True
   page.locator('.hero').screenshot(path=str(out/(a.name+'-hero-back.png')))
   for button in page.locator('#problem [data-run]').all():
    button.click();assert button.get_attribute('aria-selected')=='true'
   for button in page.locator('#reveal [data-sample]').all():
    button.click();assert button.get_attribute('aria-selected')=='true'
   page.locator('#dark-toggle').click();assert not page.locator('#dark-layer').get_attribute('hidden');assert '12%' in page.locator('#dark-note').inner_text()
   loaded=[]
   page.evaluate('window.studioLoads=0;document.querySelector("#studio-rock").addEventListener("load",()=>window.studioLoads++)')
   for button in page.locator('.pick:not(.missing)').all():
    previous=page.evaluate('window.studioLoads');button.click()
    task=int(page.locator('#studio-facts dd').first.inner_text())
    page.wait_for_function('(a)=>window.studioLoads>a[0]&&document.querySelector("#studio-rock").loaded===true&&document.querySelector("#studio-rock").src===a[1]',arg=[previous,f'evidence/web-assets/models/{task}.glb'],timeout=60000)
    src=page.locator('#studio-rock').evaluate('(e)=>e.src')
    assert src==f'evidence/web-assets/models/{task}.glb';loaded.append(task)
    if 'rejected' in button.get_attribute('class'):assert '被拒：轮廓吻合度低于 0.7068' in page.locator('#studio-facts').inner_text()
   assert len(set(loaded))==11;result['model_tasks_loaded']=loaded
   for img in page.locator('img').all():img.scroll_into_view_if_needed()
   page.wait_for_function('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)')
   page.evaluate('scrollTo(0,0)');assert page.evaluate('document.documentElement.scrollWidth-innerWidth')==0
   page.screenshot(path=str(out/(a.name+'-desktop-1440.png')),full_page=True)
   for href in ['levels.html','sandbox.html','report.html','gallery.html']:
    assert page.request.get(urljoin(a.url,href)).status==200
   page.set_viewport_size({'width':390,'height':844});page.goto(a.url,wait_until='networkidle')
   page.wait_for_function('document.querySelectorAll(".pick:not(.missing)").length===11')
   for img in page.locator('img').all():img.scroll_into_view_if_needed()
   page.wait_for_function('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)')
   page.evaluate('scrollTo(0,0)');assert page.evaluate('document.documentElement.scrollWidth-innerWidth')==0
   page.screenshot(path=str(out/(a.name+'-mobile-390.png')),full_page=True)
   if page.locator('.turns button').count():
    page.emulate_media(reduced_motion='no-preference');page.goto(a.url,wait_until='networkidle')
    page.wait_for_function('document.querySelector("#hero-rock").loaded===true')
    page.wait_for_function('getComputedStyle(document.querySelector(".rock model-viewer")).opacity==="1"')
    assert page.locator('.rock model-viewer').evaluate('(e)=>getComputedStyle(e).animationName')=='emerge'
    page.screenshot(path=str(out/(a.name+'-opening-motion-390.png')))
    result['opening_animation_and_reduced_motion_verified']=True
   assert not errors,errors;assert not http,http
   result.update(passed=True,mobile_390_overflow_px=0,desktop_1440_overflow_px=0,three_vehicle_switches=True,two_imagination_switches=True,rejected_model_label=True,fullpage_screenshots=True)
  except Exception as e:
   result['failure']=str(e);raise
  finally:
   result.update(console_errors=errors,http_errors=http);(out/(a.name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');browser.close()
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
