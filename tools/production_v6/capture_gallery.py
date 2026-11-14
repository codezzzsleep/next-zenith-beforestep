"""Capture the public official Aholo gallery without changing the website."""
import hashlib,json,os,subprocess,time,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from common import OUT,ROOT,save,sha,status

BASE='https://codezzzsleep.github.io/next-zenith-beforestep/'
DIRECTORY=OUT/'shots';DIRECTORY.mkdir(exist_ok=True)
JOB=OUT/'screen-job.json'
gallery=json.loads((ROOT/'site/data/gallery.json').read_text())
state={'status':'running','pid':os.getpid(),'shots':['r02-glb-A','r03-glb-B'],'completed':[],'new_generation_tasks':0}
save(JOB,state)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--renderer-process-limit=2'])
  for name,task in [('r02-glb-A',5958685),('r03-glb-B',5958654)]:
   dest=DIRECTORY/(name+'.mp4');ledger=DIRECTORY/(name+'.json')
   if dest.exists() and ledger.exists() and json.loads(ledger.read_text()).get('sha256')==sha(dest):
    state['completed'].append(name);continue
   state['current']=name;save(JOB,state)
   context=browser.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(OUT/'screen-raw'),record_video_size={'width':1920,'height':1080})
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   response=page.goto(BASE+'gallery.html',wait_until='domcontentloaded',timeout=60000)
   assert response.status==200,response.status
   page.wait_for_function('document.documentElement.dataset.galleryReady === "true"',timeout=60000)
   page.locator('#gallery-search').fill(str(task));page.locator(f'[data-task="{task}"]').click()
   page.wait_for_function('document.querySelector("#gallery-model").dataset.loaded === "true"',timeout=60000)
   raw_url=BASE+f'media/real-footage/r1-task-{task}-original.glb'
   page.evaluate('(url) => { document.querySelector("#gallery-model").src=url; }',raw_url)
   page.wait_for_function('document.querySelector("#gallery-model").dataset.loaded === "true"',timeout=60000)
   page.locator('.gallery-studio').scroll_into_view_if_needed();page.wait_for_timeout(1000)
   model=next(m for m in gallery['models'] if m['task_id']==task)
   actual=page.evaluate('''async () => {const e=document.querySelector('#gallery-model');const url=new URL(e.src,document.baseURI).href;const b=await(await fetch(url)).arrayBuffer();const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(x=>x.toString(16).padStart(2,'0')).join('');return {url,sha256:hash,yaw:e.yaw};}''')
   source=ROOT/f'site/media/real-footage/r1-task-{task}-original.glb'
   original=ROOT/f'assets/candidates/{task}/tex_mesh.glb'
   assert actual['sha256']==sha(source)==sha(original)
   box=page.locator('#gallery-model').bounding_box();x=box['x']+box['width']*.68;y=box['y']+box['height']*.5
   started=time.monotonic();page.mouse.move(x,y);page.mouse.down()
   for step in range(1,61):
    page.mouse.move(x-314*step/60,y);page.wait_for_timeout(100)
   page.mouse.up()
   page.wait_for_timeout(max(0,8-(time.monotonic()-started))*1000)
   end_yaw=page.evaluate('document.querySelector("#gallery-model").yaw');assert abs(end_yaw-actual['yaw'])>2
   snapshot=OUT/'screen-qc'/(name+'.png');snapshot.parent.mkdir(exist_ok=True);page.screenshot(path=str(snapshot))
   assert not page.locator('#gallery-error').is_visible();assert not errors,errors
   video=page.video;context.close();raw=OUT/'screen-raw'/(name+'.webm');video.save_as(str(raw))
   info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(raw)]));offset=max(0,float(info['format']['duration'])-8)
   temp=dest.with_name(dest.stem+'-recording.mp4')
   subprocess.run(['ffmpeg','-v','error','-y','-filter_threads','1','-ss',str(offset),'-i',str(raw),'-vf','fps=30','-frames:v','240','-an','-c:v','libx264','-crf','14','-preset','slow','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(temp)],check=True)
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(temp)]));s=probe['streams'][0]
   assert len(probe['streams'])==1 and (s['width'],s['height'],s['r_frame_rate'],int(s['nb_frames']))==(1920,1080,'30/1',240)
   subprocess.run(['ffmpeg','-v','error','-i',str(temp),'-f','null','-'],check=True);temp.replace(dest)
   row={'id':name,'status':'complete','path':str(dest),'sha256':sha(dest),'bytes':dest.stat().st_size,'duration_s':8,'frames':240,'public_page':page.url,'public_model':actual,'task_id':task,'original_glb_source':str(source.relative_to(ROOT)),'original_glb_sha256':sha(source),'viewer':'official @manycore/aholo-viewer 1.14.0','actual_browser_screen_recording':True,'original_website_modified':False,'recording_browser_model_override':'Loaded the already-public original download GLB through the existing official viewer. Default gallery GLB is a processed display copy. No published files changed.','default_gallery_model':model['model'],'raw_recording':str(raw),'raw_sha256':sha(raw),'trim_offset_s':offset,'browser_frames_conformed_to_30fps':True,'mouse_rotation_radians':end_yaw-actual['yaw'],'qc_screenshot':str(snapshot),'page_errors':errors,'physics_advanced':False,'new_generation_tasks':0,'sharpening':False,'ffprobe':probe}
   save(ledger,row);state['completed'].append(name);save(JOB,state);status('C 公网官方GLB旋转 '+name,ledger,'通过：原GLB SHA一致；8秒/1080p30/CRF14 slow/无音轨；原页面未改')
   print(name,'complete',flush=True)
  browser.close()
 state.update(status='complete',live_jobs=[]);state.pop('pid',None);save(JOB,state)
except BaseException as error:
 state.update(status='failed',error=str(error));save(JOB,state);raise
