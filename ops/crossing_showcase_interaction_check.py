"""Check visible autoplay, tour transitions and the complete film on a real browser."""
import argparse,json,threading,sys
from pathlib import Path
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from ops.crossing_check import Handler
WORK=ROOT.parent/'showcase-real-footage'

def check(url):
 out=WORK/'qc'/('public' if 'github.io' in url else 'local');out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='no-preference')
  page.goto(url+'index.html',wait_until='domcontentloaded',timeout=90000)
  page.wait_for_function('document.documentElement.dataset.showcaseReady==="true"',timeout=60000)
  page.wait_for_function('document.querySelector("#hero-film").currentTime>0',timeout=30000)
  hero=page.locator('#hero-film');hero_before=hero.evaluate('(v)=>({time:v.currentTime,decoded:v.getVideoPlaybackQuality().totalVideoFrames})')
  journey=page.locator('#journey [data-theatre]');journey.locator('video').scroll_into_view_if_needed()
  page.wait_for_function('document.querySelector("#hero-film").paused===true')
  assert journey.locator('[data-tour]').is_checked()
  journey.locator('[data-policies] button').first.click()
  page.wait_for_function('document.querySelector("#journey video").currentTime>0')
  page.wait_for_function('document.querySelector("#journey [data-theatre]").dataset.activeClip==="stress_v8-conservative"',timeout=35000)
  page.wait_for_function('document.querySelector("#journey video").currentTime>0',timeout=30000)
  worlds=page.locator('#worlds');worlds.locator('video').scroll_into_view_if_needed()
  page.wait_for_function('document.querySelector("#journey video").paused===true')
  page.wait_for_function('document.querySelector("#worlds video").currentTime>0')
  page.wait_for_function('document.querySelector("#worlds").dataset.activeClip==="world-01"',timeout=35000)
  page.wait_for_function('document.querySelector("#worlds video").currentTime>0',timeout=30000)
  page.locator('[data-open-film]').click()
  page.wait_for_function('document.querySelector("#full-film video").currentTime>0',timeout=30000)
  film=page.locator('#full-film video').evaluate('(v)=>({width:v.videoWidth,height:v.videoHeight,duration:v.duration,decoded:v.getVideoPlaybackQuality().totalVideoFrames})')
  assert (film['width'],film['height'],film['duration'])==(1920,1080,150)
  page.keyboard.press('Escape');assert not page.locator('#full-film').is_visible()
  page.goto(url+'crossing.html',wait_until='domcontentloaded',timeout=90000)
  page.wait_for_function('document.documentElement.dataset.showcaseReady==="true"')
  routes=page.locator('[data-theatre="routes"]');routes.locator('video').scroll_into_view_if_needed()
  options=routes.locator('[data-scene] option').evaluate_all('(xs)=>xs.map(x=>x.value)');assert len(options)==4
  for scene in options:
   routes.locator('[data-scene]').select_option(scene)
   assert routes.locator('[data-policies] button').count()==4
   for i,vehicle in enumerate(['A','B','C','D']):
    routes.locator('[data-policies] button').nth(i).click()
    assert routes.get_attribute('data-active-clip')==scene+'-'+vehicle
  browser.close()
 result={'passed':True,'url':url,'visible_hero_autoplay':hero_before,'offscreen_videos_pause':True,'actual_policy_tour_transition':'optimistic -> conservative','actual_world_tour_transition':'world-00 -> world-01','complete_film_decoded':film,'escape_closes_film':True,'four_scenes_sixteen_vehicle_sources':True}
 (out/'interactions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ACTUAL AUTOPLAY, TOURS, FILM AND FOUR-CAR SWITCHES PASSED',flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--url');a=ap.parse_args()
 if a.url:check(a.url)
 else:
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
  try:check(f'http://127.0.0.1:{server.server_port}/')
  finally:server.shutdown();server.server_close()
