"""Play and seek the local deliverable in a fresh browser; publish nothing."""
from pathlib import Path
import datetime
import http.server
import json
import os
import sys
import threading
import re
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import load_state, resolve, OUT,sha,save,status
from playwright.sync_api import sync_playwright

work=OUT/'film';qc=work/'qc'
preview='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BeforeStep · 完整视频</title><style>body{margin:0;background:#090e11;color:#e8eeee;font:16px system-ui}main{max-width:1120px;margin:32px auto;padding:0 20px}h1{font-weight:600;font-size:26px}video{display:block;width:100%;aspect-ratio:16/9;background:#000}button,a{font:inherit;color:#cbebe5}button{background:#183936;border:1px solid #41615d;padding:10px 22px;margin-top:18px;border-radius:6px}a{margin-left:18px}p{color:#a6b2b2;line-height:1.7}</style><main><h1>BeforeStep · 先检验，再迈步</h1><video id="film" controls preload="metadata" src="../demo-v6.mp4"></video><button id="play" onclick="document.getElementById('film').play()">播放</button><a href="../demo-v6.mp4" download>下载视频</a><a href="../BeforeStep-demo-v6.zip" download>下载压缩包</a><p>3 分 05 秒 · 中文配音与烧录字幕 · 仿真运行回放及原页面录屏</p></main></html>'''
(work/'preview.html').write_text(preview)
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(OUT),**kw)
    def log_message(self,*a):pass
    def send_head(self):
        self.remaining=None
        path=Path(self.translate_path(self.path))
        request=self.headers.get('Range')
        if path.suffix=='.mp4' and request and path.is_file():
            match=re.fullmatch(r'bytes=(\d+)-(\d*)',request)
            if not match:self.send_error(416);return None
            size=path.stat().st_size;start=int(match[1]);end=min(int(match[2]) if match[2] else size-1,size-1)
            if start>end:self.send_error(416);return None
            self.send_response(206);self.send_header('Content-Type','video/mp4');self.send_header('Accept-Ranges','bytes')
            self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.send_header('Content-Length',str(end-start+1));self.end_headers()
            stream=path.open('rb');stream.seek(start);self.remaining=end-start+1;return stream
        return super().send_head()
    def copyfile(self,source,output):
        try:
            while self.remaining is None or self.remaining>0:
                data=source.read(65536 if self.remaining is None else min(65536,self.remaining))
                if not data:break
                output.write(data)
                if self.remaining is not None:self.remaining-=len(data)
        except (BrokenPipeError,ConnectionResetError):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
job={'id':'local-film-playback-QC','pid':os.getpid(),'status':'running','loopback_port':server.server_port,'published':False}
save(work/'playback-job.json',job)
state=load_state(work / 'state.json');state.update(status='local_playback_verification',live_jobs=[{'id':job['id'],'pid':os.getpid(),'ledger':str(work/'playback-job.json')}]);save(work/'state.json',state)
errors=[];checks=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-gpu'])
        page=browser.new_page(viewport={'width':1280,'height':900})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/film/preview.html',wait_until='domcontentloaded')
        page.wait_for_function('document.querySelector("video").readyState >= 1')
        meta=page.evaluate('''() => { const v=document.querySelector('video');return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?{code:v.error.code,message:v.error.message}:null}}''')
        assert abs(meta['duration']-185)<.1 and (meta['width'],meta['height'])==(1920,1080) and meta['error'] is None
        page.click('#play');page.wait_for_function('document.querySelector("video").currentTime > 1')
        playback=page.evaluate('''() => {let v=document.querySelector('video');return {paused:v.paused,muted:v.muted,currentTime:v.currentTime,decodedFrames:v.getVideoPlaybackQuality().totalVideoFrames,error:v.error?v.error.code:null}}''')
        assert not playback['paused'] and not playback['muted'] and playback['decodedFrames']>0 and playback['error'] is None
        for seconds in [24,68,98,125,139.3,153,163,168,180]:
            page.evaluate('(t)=>{let v=document.querySelector("video");v.pause();v.currentTime=t}',seconds)
            page.wait_for_function('(t)=>Math.abs(document.querySelector("video").currentTime-t)<.1 && !document.querySelector("video").seeking',arg=seconds)
            checks.append({'time_s':seconds,**page.evaluate('''() => {let v=document.querySelector('video');return {readyState:v.readyState,error:v.error?v.error.code:null}}''')})
            assert checks[-1]['error'] is None
        page.screenshot(path=str(qc/'browser-desktop.jpg'),type='jpeg',quality=90)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(qc/'browser-mobile.jpg'),type='jpeg',quality=90)
        browser.close()
    assert not errors
    result={'status':'complete','passed':True,'video_sha256':sha(OUT/'demo-v6.mp4'),'metadata':meta,'playback':playback,'seeks':checks,'page_errors':errors,'desktop_and_mobile_layout_checked':True,'published':False,'server_lifetime':'Only loopback during this verification; closed at completion'}
    save(work/'playback.json',result);status('成片实际播放核验',work/'playback.json','通过：Chromium有声播放推进/9处seek/视频无错误；桌面及手机本地预览无溢出；只本地检查，未发布')
    job.update(status='complete');save(work/'playback-job.json',job)
    state.update(status='playback_passed_final_visual_review',live_jobs=[],next='Finish visual review and ZIP packaging');save(work/'state.json',state)
    print(json.dumps({'passed':True,'duration_s':meta['duration'],'seeks':len(checks),'page_errors':errors},ensure_ascii=False))
except BaseException as error:
    job.update(status='failed',error=str(error));save(work/'playback-job.json',job)
    state.update(status='playback_test_error_review_required',live_jobs=[],next='Inspect local test server and playback log; preserve final video')
    save(work/'state.json',state)
    raise
finally:
    server.shutdown();server.server_close()
