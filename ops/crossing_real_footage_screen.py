"""Record the actual R1 input/model pairs with their original task identities."""
import hashlib,json,shutil,subprocess,sys,threading,time
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
WORK=ROOT.parent/'real-footage-180';OUT=ROOT/'site/media/real-footage'
from playwright.sync_api import sync_playwright
from ops.crossing_check import Handler
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pairs=[]
for target,sample,task in [('T1','A1',5958685),('T2','A2',5958654)]:
 base=ROOT/'evidence/reviews/beforestep_r1/lux/original_b/looks/look1'/target
 request=json.loads((base/'lux_request.json').read_text());row=next(x for x in request['items'] if x['id']==sample);source=ROOT/row['path'];assert sha(source)==row['sha256']
 dest=OUT/f'r1-task-{task}-input.jpg';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
 glb=ROOT/f'assets/candidates/{task}/tex_mesh.glb';original_glb=OUT/f'r1-task-{task}-original.glb';shutil.copy2(glb,original_glb)
 import zipfile
 with zipfile.ZipFile(ROOT/f'outputs/generation/downloads/{task}_0') as z:
  member=next(x for x in z.namelist() if x.endswith('tex_mesh.glb'));assert hashlib.sha256(z.read(member)).hexdigest()==sha(glb)
 pairs.append({'target':target,'sample':sample,'task_id':task,'input':str(dest.relative_to(ROOT/'site')),'input_source':str(source.relative_to(ROOT)),'input_sha256':sha(source),'glb':str(original_glb.relative_to(ROOT/'site')),'glb_source':str(glb.relative_to(ROOT)),'glb_sha256':sha(glb),'original_download_glb_member_verified':True})
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><script type="module" src="vendor/model-viewer.min.js"></script><style>*{box-sizing:border-box}body{margin:0;background:#080b0d;color:#f5f0e9;font:24px/1.6 system-ui,"WenQuanYi Zen Hei",sans-serif}header{padding:45px 80px;font-size:30px}main{display:grid;grid-template-columns:1fr 1.1fr;gap:60px;padding:0 80px}img{width:700px;height:700px;object-fit:contain;background:#10171b}model-viewer{width:100%;height:740px;background:radial-gradient(#18232a,#080b0d);--poster-color:transparent}p{margin:10px 0;font-size:24px;color:#b5c0c6}.tag{font-size:18px;color:#e8b97c}</style><header id="task"></header><main><div><img id="input" alt="原任务实际上传的输入"><p>原样上传的这一面</p></div><div><model-viewer id="model" camera-controls auto-rotate auto-rotate-delay="0" rotation-per-second="16deg" camera-orbit="20deg 74deg 95%" exposure="1.3" interaction-prompt="none"></model-viewer><p>原任务返回的 GLB，可以转到背面看</p></div></main><script>const pairs=PAIRS;window.usePair=async(i)=>{const p=pairs[i],m=document.querySelector('#model');document.querySelector('#task').textContent=`R1 · 第一眼 · 石头 ${i===0?'A':'B'} · 原任务 ${p.task_id} / 已有任务产物`;document.querySelector('#input').src=p.input;const loaded=new Promise(r=>m.addEventListener('load',r,{once:true}));m.src=p.glb;await loaded;window.pairReady=i};usePair(0);</script></html>'''.replace('PAIRS',json.dumps(pairs,ensure_ascii=False))
(WORK/'candidate-page.html').write_text(html)
class RecordingHandler(Handler):
 def do_GET(self):
  if self.path=='/__candidate180.html':
   body=html.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),RecordingHandler);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  context=browser.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(WORK/'screen-raw'),record_video_size={'width':1920,'height':1080})
  page=context.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/__candidate180.html',wait_until='domcontentloaded');page.wait_for_function('window.pairReady===0',timeout=60000)
  started=time.monotonic();page.wait_for_timeout(11000);page.evaluate('usePair(1)');page.wait_for_timeout(max(0,22-(time.monotonic()-started))*1000);page.screenshot(path=str(WORK/'qc/candidate-record.jpg'))
  video=page.video;context.close();raw=WORK/'candidate-record.webm';video.save_as(str(raw));browser.close()
 metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(raw)],text=True));start=max(0,float(metadata['format']['duration'])-22)
 dest=OUT/'r1-candidate-records.mp4';subprocess.run(['ffmpeg','-v','error','-y','-filter_threads','1','-ss',str(start),'-i',str(raw),'-vf','fps=30,tpad=stop_mode=clone:stop_duration=1','-frames:v','660','-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads','1','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
 data={'status':'complete','id':'r1-candidate-records','path':str(dest.relative_to(ROOT/'site')),'duration_s':22,'actual_browser_screen_recording':True,'existing_task_results_only':True,'new_generation_tasks':0,'pairs':pairs,'sha256':sha(dest),'screen_recording_sha256':sha(raw),'screen_trim_start_s':start,'source_resolution':[1920,1080]}
 (ROOT/'site/data/real-footage-sources/r1-candidate-records.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(WORK/'screen.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print('ACTUAL R1 TASK/MODEL SCREEN RECORDING COMPLETE',flush=True)
finally:server.shutdown();server.server_close()
