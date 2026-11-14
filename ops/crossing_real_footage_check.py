"""Exercise native playback, chapter seeking and recovery without WebGL."""
import argparse,json,re,sys,threading,time
from pathlib import Path
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright
from ops.crossing_check import Handler
WORK=ROOT.parent/'real-footage-180'
class RangeHandler(Handler):
 def send_head(self):
  path=Path(self.translate_path(self.path));value=self.headers.get('Range')
  if value and path.is_file():
   match=re.fullmatch(r'bytes=(\d+)-(\d*)',value)
   if match:
    size=path.stat().st_size;start=int(match[1]);end=min(int(match[2]) if match[2] else size-1,size-1)
    if start>=size:self.send_error(416);return None
    f=path.open('rb');f.seek(start);self._remaining=end-start+1;self.send_response(206);self.send_header('Content-Type',self.guess_type(str(path)));self.send_header('Accept-Ranges','bytes');self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.send_header('Content-Length',str(self._remaining));self.end_headers();return f
  self._remaining=None;return super().send_head()
 def copyfile(self,source,out):
  try:
   if self._remaining is None:super().copyfile(source,out)
   else:
    while self._remaining:
     block=source.read(min(2**18,self._remaining))
     if not block:break
     out.write(block);self._remaining-=len(block)
  except (BrokenPipeError,ConnectionResetError):pass
def check(url,preview=False):
 folder='preview' if preview else 'public' if 'github.io' in url else 'local';out=WORK/'qc'/folder;out.mkdir(parents=True,exist_ok=True);checks=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--disable-webgl','--disable-webgl2'])
  for width,height in [(1440,1000),(390,844)]:
   page=browser.new_page(viewport={'width':width,'height':height});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));start=time.monotonic()
   page.goto(url+('real-footage-preview.html' if preview else 'index.html'),wait_until='domcontentloaded',timeout=90000);page.wait_for_function('document.documentElement.dataset.realFootageReady==="true"')
   assert page.evaluate('document.querySelectorAll("main canvas,main table,model-viewer").length')==0
   assert page.evaluate('document.documentElement.scrollWidth-innerWidth')<=1
   assert page.locator('#current-caption').inner_text()
   assert page.locator('#current-caption').evaluate('(p)=>parseFloat(getComputedStyle(p).fontSize)')>=14
   page.locator('#play-recording').focus();page.keyboard.press('Enter');page.wait_for_function('document.querySelector("#main-player").currentTime>0',timeout=10000)
   first=time.monotonic()-start;assert first<10,first
   video=page.locator('#main-player');info=video.evaluate('(v)=>({width:v.videoWidth,height:v.videoHeight,duration:v.duration,decoded:v.getVideoPlaybackQuality().totalVideoFrames,controls:v.controls,objectFit:getComputedStyle(v).objectFit})')
   assert (info['width'],info['height'],info['duration'])==(1920,1080,25 if preview else 180);assert info['decoded']>0 and info['controls'] and info['objectFit']=='contain'
   video.evaluate('(v)=>v.muted=true');assert video.evaluate('(v)=>v.muted');video.evaluate('(v)=>v.pause()')
   if not preview:
    assert page.locator('[data-chapter]').count()==8
    for at in [15,35,75,105,151,163]:
     if at==151:video.evaluate('(v)=>v.currentTime=151')
     else:page.locator(f'[data-start="{at}"]').click()
     page.wait_for_function('(t)=>Math.abs(document.querySelector("#main-player").currentTime-t)<2',arg=at,timeout=15000);video.evaluate('(v)=>v.pause()')
    video.evaluate('(v)=>v.textTracks[0].mode="showing"');page.wait_for_function('document.querySelector("#main-player").textTracks[0].cues?.length>0')
    page.locator('#play-preview').click();page.wait_for_function('document.querySelector("#main-player").duration===25');page.locator('#play-recording').click();page.wait_for_function('document.querySelector("#main-player").duration===180');video.evaluate('(v)=>v.pause()')
    page.locator('#source-details summary').click();assert page.locator('#current-sources a').count()>=1
   page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/f'{width}.jpg'),full_page=True);assert not errors,errors
   checks.append({'viewport':[width,height],'webgl_disabled':True,'native_keyboard_play':True,'first_decoded_frame_s':first,'video':info,'mobile_full_16_9_frame':True,'no_overflow':True,'chapter_seek_and_subtitles':not preview,'errors':errors});page.close()
  page=browser.new_page();pattern='**/media/real-footage/low-stone-preview.mp4' if preview else '**/media/demo-v4.mp4';page.route(pattern,lambda route:route.abort());page.goto(url+('real-footage-preview.html' if preview else 'index.html'),wait_until='domcontentloaded');page.locator('#play-recording').click();page.wait_for_selector('#video-error:not([hidden])',timeout=15000);assert page.locator('#main-player').get_attribute('poster');assert page.locator('#direct-download').get_attribute('href').endswith('.mp4');page.close();browser.close()
 result={'passed':True,'url':url,'preview':preview,'checks':checks,'failed_video_retains_real_poster_and_download':True};(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('NATIVE VIDEO WITHOUT WEBGL VERIFIED',folder,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--preview',action='store_true');a=ap.parse_args()
 if a.url:check(a.url,a.preview)
 else:
  server=ThreadingHTTPServer(('127.0.0.1',0),RangeHandler);threading.Thread(target=server.serve_forever,daemon=True).start()
  try:check(f'http://127.0.0.1:{server.server_port}/',a.preview)
  finally:server.shutdown();server.server_close()
