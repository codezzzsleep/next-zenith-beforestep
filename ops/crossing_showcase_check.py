"""Review actual playback and presentation on desktop and phone."""
import argparse,json,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from ops.crossing_check import Handler
WORK=ROOT.parent/'showcase-real-footage'
def check(url,preview=False):
 report={'url':url,'preview':preview,'checks':[],'passed':False};out=WORK/'qc'/('preview' if preview else 'public' if 'github.io' in url else 'local');out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  for width,height in [(1440,1000),(390,844)]:
   page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for n in ['home','levels','crossing','sandbox']:
    path='showcase-'+n+'.html' if preview else 'index.html' if n=='home' else n+'.html'
    page.goto(url+path,wait_until='domcontentloaded',timeout=90000);page.wait_for_function('document.documentElement.dataset.showcaseReady==="true"',timeout=60000)
    assert page.evaluate('document.querySelectorAll("main canvas,main table").length')==0,'Front page still replaces action footage with diagrams/tables'
    assert page.evaluate('document.documentElement.scrollWidth-innerWidth')<=1
    sources=[]
    for v in page.locator('video[src]').all()[:2]:
     v.scroll_into_view_if_needed();v.evaluate('(v)=>v.play()');page.wait_for_timeout(750)
     state=v.evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,height:v.videoHeight,decoded:v.getVideoPlaybackQuality().totalVideoFrames,src:v.currentSrc})')
     assert state['width']>0 and state['decoded']>0 and state['time']>0,state;sources.append(state);v.evaluate('(v)=>v.pause()')
    if n=='home':
     root=page.locator('#journey [data-theatre]');root.scroll_into_view_if_needed();root.locator('[data-policies] button').first.click();page.wait_for_timeout(700)
     assert root.get_attribute('data-active-clip')=='stress_v8-optimistic',root.evaluate('(r)=>({active:r.dataset.activeClip,buttons:[...r.querySelectorAll("[data-policies] button")].map(x=>x.textContent),scene:r.querySelector("[data-scene]").value})')
     root.locator('[data-policies] button').last.click();page.wait_for_timeout(700)
     assert root.get_attribute('data-active-clip')=='stress_v8-imagination'
     model=page.locator('#hero-rock');model.scroll_into_view_if_needed();page.wait_for_function('document.querySelector("#hero-rock").loaded===true',timeout=60000)
     page.locator('[data-orbit]').nth(1).click();page.wait_for_timeout(500)
     assert abs(model.evaluate('(m)=>m.getCameraOrbit().theta*180/Math.PI')-195)<2
     page.locator('#model-picks button').nth(2).click();page.wait_for_function('document.querySelector("#hero-rock").loaded===true',timeout=60000)
     page.locator('#worlds').scroll_into_view_if_needed();page.locator('[data-world-list] button').nth(2).click();page.wait_for_timeout(500)
     assert page.locator('#worlds').get_attribute('data-active-clip')=='world-02'
     page.locator('#legs').screenshot(path=str(out/f'legs-{width}.jpg'))
     page.locator('#trust').screenshot(path=str(out/f'worlds-{width}.jpg'))
    if not preview:
     assert page.locator('[data-missing]:visible').count()==0
     for img in page.locator('img').all():img.scroll_into_view_if_needed()
     page.wait_for_function('Array.from(document.images).every(x=>x.complete&&x.naturalWidth>0)',timeout=60000)
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/f'{n}-{width}.jpg'),full_page=True,type='jpeg',quality=86)
    assert not errors,errors;report['checks'].append({'page':n,'viewport':[width,height],'overflow_px':page.evaluate('document.documentElement.scrollWidth-innerWidth'),'tables':0,'canvases':0,'actual_videos_decoded':sources,'console_errors':list(errors)})
   page.close()
  browser.close()
 report['passed']=True;(out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('BROWSER CHECK PASSED',url,preview,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--preview',action='store_true');a=ap.parse_args()
 if a.url:check(a.url,a.preview)
 else:
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
  try:check(f'http://127.0.0.1:{server.server_port}/',a.preview)
  finally:server.shutdown();server.server_close()
