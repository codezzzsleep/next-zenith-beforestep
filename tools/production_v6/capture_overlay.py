"""Record the public original overlay page; preserve its real source geometry."""
import json,os,subprocess,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from common import OUT,ROOT,save,sha,status

BASE='https://codezzzsleep.github.io/next-zenith-beforestep/'
name='r01-reveal';folder=OUT/'shots';folder.mkdir(exist_ok=True)
job=OUT/'overlay-screen-job.json'
save(job,{'status':'running','pid':os.getpid(),'id':name,'new_generation_tasks':0})
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--renderer-process-limit=2'])
  context=browser.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(OUT/'screen-raw'),record_video_size={'width':1920,'height':1080})
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  response=page.goto(BASE+'overlays.html',wait_until='domcontentloaded',timeout=60000);assert response.status==200
  page.wait_for_function('document.documentElement.dataset.overlaysReady === "true"',timeout=60000)
  data=json.loads((ROOT/'evidence/web-assets/overlays/index.json').read_text());index=next(i for i,m in enumerate(data['models']) if m['task_id']==5958654);source=data['models'][index]
  page.locator('#overlay-select').select_option(str(index));page.wait_for_function('document.querySelector("#overlay-model").loaded',timeout=60000)
  page.evaluate('''() => {const e=document.querySelector('#overlay-model');e.cameraOrbit='270deg 66deg 105%';e.jumpCameraToGoal();}''')
  page.wait_for_timeout(800);box=page.locator('#overlay-model').bounding_box()
  actual=page.evaluate('''async()=>{const e=document.querySelector('#overlay-model'),url=new URL(e.src,document.baseURI).href,b=await(await fetch(url)).arrayBuffer();return {url,sha256:Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join(''),theta:e.getCameraOrbit().theta};}''');assert actual['sha256']==sha(ROOT/source['path'])
  started=time.monotonic();page.mouse.move(box['x']+box['width']*.75,box['y']+box['height']*.5);page.mouse.down()
  for n in range(1,81):
   page.mouse.move(box['x']+box['width']*(.75-.50*n/80),box['y']+box['height']*.5);page.wait_for_timeout(100)
  page.mouse.up();page.wait_for_timeout(max(0,12-(time.monotonic()-started))*1000)
  theta=page.evaluate('document.querySelector("#overlay-model").getCameraOrbit().theta');assert abs(theta-actual['theta'])>1
  snapshot=OUT/'screen-qc'/(name+'.png');page.screenshot(path=str(snapshot));assert not errors,errors
  video=page.video;context.close();raw=OUT/'screen-raw'/(name+'.webm');video.save_as(str(raw));browser.close()
 duration=float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(raw)]))['format']['duration']);offset=max(0,duration-12);dest=folder/(name+'.mp4')
 subprocess.run(['ffmpeg','-v','error','-y','-filter_threads','1','-ss',str(offset),'-i',str(raw),'-vf','fps=30','-frames:v','360','-an','-c:v','libx264','-crf','14','-preset','slow','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(dest)]));s=probe['streams'][0];assert len(probe['streams'])==1 and (s['width'],s['height'],int(s['nb_frames']))==(1920,1080,360)
 subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'],check=True)
 row={'id':name,'status':'complete','path':str(dest),'sha256':sha(dest),'duration_s':12,'frames':360,'actual_browser_screen_recording':True,'public_page':BASE+'overlays.html','requested_page_exception':'Current home has no reveal section; preserved preview showcase-home.html returned HTTP503. Used the public original overlay page with the same task and frozen 0.70m comparison; website unchanged.','source_model':source,'public_model':actual,'rotation_radians':theta-actual['theta'],'raw_recording':str(raw),'raw_sha256':sha(raw),'trim_offset_s':offset,'qc_screenshot':str(snapshot),'page_errors':errors,'original_website_modified':False,'new_generation_tasks':0,'physics_advanced':False,'sharpening':False,'ffprobe':probe}
 save(folder/(name+'.json'),row);save(job,{'status':'complete','live_jobs':[],'id':name,'ledger':str(folder/(name+'.json'))});status('C 公网真假叠合 r01',folder/(name+'.json'),'通过：12秒/1080p30/CRF14 slow；原0.70米任务与GLB SHA；主页无reveal，改录原公开overlays页并注明')
except BaseException as e:
 save(job,{'status':'failed','id':name,'error':str(e)});raise
