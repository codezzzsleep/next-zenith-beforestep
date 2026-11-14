"""Play the entire film at normal speed and verify seeks in a local browser."""
from pathlib import Path
import http.server
import json
import os
import re
import threading
import time
from playwright.sync_api import sync_playwright
from common import OUT, sha, save

tl=json.loads((OUT/'timeline.json').read_text())
preview='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>先见一步 · Lux3D Demo</title><style>body{margin:0;background:#0b1419;color:#edf4f1;font:16px system-ui}main{max-width:1120px;margin:24px auto;padding:0 18px}h1{font-size:26px;font-weight:600}video{display:block;width:100%;aspect-ratio:16/9;background:#000}p{color:#afc0bb;line-height:1.6}button,a{font:inherit;color:#d2ece3}button{background:#21473e;border:1px solid #568b7a;border-radius:6px;padding:9px 22px;margin:15px 14px 0 0}a{margin-right:14px}</style><main><h1>先见一步 · 从一张照片到一次行动</h1><video id="film" controls playsinline preload="metadata" src="BeforeStep-Lux3D-Demo.mp4"></video><button id="play" onclick="document.getElementById('film').play()">播放 Demo</button><a href="BeforeStep-Lux3D-Demo.mp4" download>下载 MP4</a><a href="BeforeStep-Lux3D-submission.zip" download>视频与报告</a><p>Lux3D 照片生成 3D → 模型核对 → 路线预演 → 机器人行动。中文配音与烧录字幕；MuJoCo 仿真运行回放及真实返回模型录屏。</p></main></html>'''
(OUT/'preview.html').write_text(preview)
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(OUT),**kwargs)
    def log_message(self,*args):pass
    def send_head(self):
        self.remaining=None
        path=Path(self.translate_path(self.path));request=self.headers.get('Range')
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
threading.Thread(target=server.serve_forever,daemon=True).start()
job={'id':'Lux3D-demo-playback','pid':os.getpid(),'status':'running','port':server.server_port,'rate':1}
save(OUT/'playback-job.json',job)
errors=[];seeks=[];checkpoints=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',args=['--no-sandbox','--disable-gpu'])
        page=browser.new_page(viewport={'width':1280,'height':900})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(f'http://127.0.0.1:{server.server_port}/preview.html',wait_until='domcontentloaded')
        page.wait_for_function('document.querySelector("video").readyState>=1')
        meta=page.evaluate('''()=>{let v=document.querySelector('video');return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?v.error.code:null}}''')
        assert abs(meta['duration']-tl['duration_s'])<.1 and (meta['width'],meta['height'])==(1920,1080) and meta['error'] is None
        page.click('#play');page.wait_for_function('document.querySelector("video").currentTime>1')
        first_play=page.evaluate('''()=>{let v=document.querySelector('video');return {time:v.currentTime,muted:v.muted,paused:v.paused,rate:v.playbackRate,error:v.error?v.error.code:null}}''')
        assert not first_play['muted'] and not first_play['paused'] and first_play['error'] is None
        for t in [g['start_s']+.8 for g in tl['groups']]:
            page.evaluate('(t)=>{let v=document.querySelector("video");v.pause();v.currentTime=t}',t)
            page.wait_for_function('(t)=>Math.abs(document.querySelector("video").currentTime-t)<.1&&!document.querySelector("video").seeking',arg=t)
            row=page.evaluate('''()=>{let v=document.querySelector('video');return {time:v.currentTime,readyState:v.readyState,error:v.error?v.error.code:null}}''')
            assert row['error'] is None;seeks.append(row)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(OUT/'qc'/'browser-mobile.jpg'),type='jpeg',quality=90)
        page.set_viewport_size({'width':1280,'height':900})
        page.evaluate('()=>{let v=document.querySelector("video");v.currentTime=0;v.playbackRate=1;v.play()}')
        started=time.monotonic();next_check=0
        while True:
            row=page.evaluate('''()=>{let v=document.querySelector('video'),q=v.getVideoPlaybackQuality();return {time:v.currentTime,ended:v.ended,paused:v.paused,muted:v.muted,rate:v.playbackRate,error:v.error?v.error.code:null,totalFrames:q.totalVideoFrames,droppedFrames:q.droppedVideoFrames}}''')
            assert row['error'] is None and not row['muted'] and row['rate']==1
            assert time.monotonic()-started<tl['duration_s']+70,'Full playback stalled'
            if row['time']>=next_check or row['ended']:
                checkpoints.append(row)
                page.screenshot(path=str(OUT/'qc'/f'browser-play-{len(checkpoints):02d}.jpg'),type='jpeg',quality=85)
                save(OUT/'playback-progress.json',{'status':'playing_full_film','checkpoints':checkpoints})
                print('Normal playback',round(row['time'],1),'seconds',flush=True)
                next_check=row['time']+12
            if row['ended']:
                assert abs(row['time']-tl['duration_s'])<.1;break
            page.wait_for_timeout(2000)
        page.screenshot(path=str(OUT/'qc'/'browser-desktop.jpg'),type='jpeg',quality=90)
        browser.close()
    assert not errors
    result={'status':'complete','passed':True,'video_sha256':sha(OUT/'BeforeStep-Lux3D-Demo.mp4'),
        'metadata':meta,'first_unmuted_playback':first_play,'seeks':seeks,'continuous_full_playback':{'passed':True,'rate':1,'checkpoints':checkpoints,'ended':True},
        'page_errors':errors,'desktop_and_mobile_no_overflow':True,'server_closed':True,'published':False}
    save(OUT/'playback.json',result);job.update(status='complete');save(OUT/'playback-job.json',job)
    print('FULL NORMAL PLAYBACK AND SEEKS PASSED',flush=True)
except BaseException as error:
    job.update(status='failed',error=str(error));save(OUT/'playback-job.json',job)
    raise
finally:
    server.shutdown();server.server_close()
