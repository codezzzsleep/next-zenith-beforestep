"""Native GPU screen recording through Chromium screencast and H.264 encoding."""
import asyncio,base64,json,os,time,datetime,traceback,argparse
from pathlib import Path
from playwright.async_api import async_playwright
from check_judges_browser import Controls,mirror_assets

DEFAULT_ROOT=Path(__file__).resolve().parent
if not (DEFAULT_ROOT/'site/play.html').is_file():DEFAULT_ROOT=DEFAULT_ROOT.parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path(os.environ.get('BEFORESTEP_RECORD_ROOT',str(DEFAULT_ROOT))))
parser.add_argument('--url',default=os.environ.get('BEFORESTEP_RECORD_URL','http://127.0.0.1:8000/site/play.html'))
parser.add_argument('--out',type=Path)
parser.add_argument('--chromium',default=os.environ.get('BEFORESTEP_RECORD_CHROMIUM'))
args=parser.parse_args()
ROOT=args.root.resolve()
packaged=ROOT/'chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell'
CHROME=args.chromium or (str(packaged) if packaged.exists() else None)
OUT=args.out or ROOT/'recording'
ENTRY=args.url+('&' if '?' in args.url else '?')+'capture=1' 
OUT.mkdir(exist_ok=True)

class Capture:
    def __init__(self,page):
        self.page=page;self.frames=[];self.samples=[];self.queue=asyncio.Queue()
        self.first_monotonic=None;self.cdp=None;self.active=True
    async def start(self):
        self.log=(OUT/'capture-encode.log').open('wb')
        self.process=await asyncio.create_subprocess_exec('ffmpeg','-y','-hide_banner','-loglevel','warning',
            '-use_wallclock_as_timestamps','1','-f','image2pipe','-framerate','30','-vcodec','mjpeg','-i','pipe:0',
            '-an','-vf','setpts=PTS-STARTPTS,fps=30','-c:v','libx264','-preset','fast',
            '-crf','17','-threads','8','-pix_fmt','yuv420p','-movflags','+faststart',
            str(OUT/'00-full-run-video.mp4'),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.DEVNULL,stderr=self.log)
        self.writer=asyncio.create_task(self.write())
        self.cdp=await self.page.context.new_cdp_session(self.page)
        async def frame(event):
            await self.cdp.send('Page.screencastFrameAck',{'sessionId':event['sessionId']})
            now=time.monotonic()
            if self.first_monotonic is None:self.first_monotonic=now
            self.frames.append({'seconds':now-self.first_monotonic,'capture_timestamp':event.get('metadata',{}).get('timestamp')})
            await self.queue.put(base64.b64decode(event['data']))
        self.cdp.on('Page.screencastFrame',frame)
        await self.cdp.send('Page.startScreencast',{'format':'jpeg','quality':96,'maxWidth':1920,'maxHeight':1080,'everyNthFrame':1})
        self.sampler=asyncio.create_task(self.sample())
    async def write(self):
        while True:
            frame=await self.queue.get()
            if frame is None:break
            self.process.stdin.write(frame);await self.process.stdin.drain()
    def seconds(self):
        return max(0,time.monotonic()-(self.first_monotonic or time.monotonic()))
    async def sample(self):
        while self.active:
            try:
                value=await self.page.evaluate("()=>({state:window.BeforeStepGame?.state,drawCount:Number(document.querySelector('#world')?.dataset.drawCount||0),canvas:[document.querySelector('#world')?.width,document.querySelector('#world')?.height]})")
                self.samples.append({'video_seconds':self.seconds(),**value})
            except Exception:pass
            await asyncio.sleep(1)
    async def stop(self):
        self.active=False
        await self.cdp.send('Page.stopScreencast')
        await self.queue.put(None);await self.writer
        self.process.stdin.close();await self.process.stdin.wait_closed()
        code=await self.process.wait();self.log.close();await self.sampler
        assert code==0,('H.264 capture encoding failed',code)
        (OUT/'capture-frames.json').write_text(json.dumps(self.frames,indent=2)+'\n')
        (OUT/'physical-samples.json').write_text(json.dumps(self.samples,ensure_ascii=False,indent=2)+'\n')
        mux=await asyncio.create_subprocess_exec('ffmpeg','-y','-hide_banner','-loglevel','error',
            '-i',str(OUT/'00-full-run-video.mp4'),'-f','lavfi','-i','anullsrc=r=48000:cl=stereo',
            '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k',
            '-shortest','-movflags','+faststart',str(OUT/'00-full-run.mp4'))
        assert await mux.wait()==0

async def pointer(page):
    await page.add_init_script("""(() => {
      addEventListener('DOMContentLoaded',()=> {
        const cursor=document.createElement('div');cursor.id='record-pointer';
        cursor.style.cssText='position:fixed;left:20px;top:200px;width:18px;height:24px;pointer-events:none;z-index:9999;filter:drop-shadow(0 1px 2px #000)';
        cursor.innerHTML='<svg viewBox="0 0 18 24"><path d="M1 1v18l5-5 4 9 4-2-4-8h7Z" fill="white" stroke="#152235" stroke-width="1.2"/></svg>';
        const key=document.createElement('div');key.id='record-key';
        key.style.cssText='position:fixed;left:20px;top:140px;padding:6px 12px;color:#f5f2ea;background:#142236dd;border:1px solid #d5ad67;border-radius:7px;font:14px sans-serif;z-index:9998;pointer-events:none;display:none';
        document.body.append(cursor,key);
        addEventListener('pointermove',e=>{cursor.style.left=e.clientX+'px';cursor.style.top=e.clientY+'px'});
        addEventListener('pointerdown',()=>{cursor.animate([{transform:'scale(1)'},{transform:'scale(1.5)'},{transform:'scale(1)'}],{duration:300})});
        addEventListener('keydown',e=>{if(!e.repeat){key.textContent=e.key===' '?'空格 · 刹车':e.key.toUpperCase();key.style.display='block'}});
        addEventListener('keyup',()=>{key.style.display='none'});
      });
    })();""")

async def main():
    report={'passed':False,'source':'Current playable UI with real keyboard/button input and independent MuJoCo states',
        'code_commit':os.environ.get('BEFORESTEP_RECORD_CODE',(ROOT/'code-version.txt').read_text().strip() if (ROOT/'code-version.txt').exists() else 'not_recorded'),'capture_method':'Chromium CDP screencast of native GPU page; actual cadence is measured separately','capture_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'resolution':[1920,1080],'target_fps':30,
        'rendering':'RTX 4090 NVIDIA OpenGL','encoding':'CPU libx264 CRF17; NVENC OpenEncodeSessionEx reports unsupported device on this instance',
        'asset_delivery':'Exact frozen assets mirrored locally; not a public CDN speed test',
        'audio':'In-game sound disabled; separate silent stereo AAC track',
        'chapters':[],'still_times':{},'page_errors':[],'pose_injected':False}
    def save():(OUT/'recording.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=CHROME,headless=True,
            args=['--no-sandbox','--enable-gpu','--ignore-gpu-blocklist','--disable-dev-shm-usage','--use-gl=angle','--use-angle=gl-egl'])
        context=await browser.new_context(viewport={'width':1920,'height':1080},device_scale_factor=1)
        page=await context.new_page();page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
        await pointer(page);await mirror_assets(page,ROOT)
        controls=Controls(page)
        capture=Capture(page)
        async def chapter(name):
            state=await page.evaluate('window.BeforeStepGame?.state||null')
            report['chapters'].append({'name':name,'video_seconds':capture.seconds(),'sim_seconds':state.get('elapsed') if state else None,'state':state})
            save();print(name,round(capture.seconds(),2),flush=True)
        async def still(name):
            await page.mouse.move(30,200)
            await page.wait_for_timeout(700)
            report['still_times'][name]={'video_seconds':capture.seconds(),'state':await page.evaluate('BeforeStepGame.state'),'selected':await page.evaluate('BeforeStepGame.selected'),'map':await page.evaluate("()=>{try{return JSON.parse(document.querySelector('#dream')?.dataset.comparison||'null')}catch{return null}}"),'canvas':await page.evaluate("()=>[document.querySelector('#world').width,document.querySelector('#world').height]"),'photo_source':await page.locator('#input-photo').get_attribute('src')}
            save()
        try:
            await capture.start()
            await page.goto(ENTRY,wait_until='domcontentloaded',timeout=90000)
            await chapter('ordinary_entry_and_actual_loading')
            await page.wait_for_function("window.BeforeStepGame?.state && !document.querySelector('#begin-mission').disabled",timeout=240000)
            report['renderer']=await page.evaluate("()=>{const g=document.querySelector('#world').getContext('webgl2');return g.getParameter(g.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL)}")
            assert 'NVIDIA' in report['renderer']
            await page.wait_for_timeout(2000)
            await controls.click('#begin-mission')
            await chapter('third_person_M20_approach')
            await page.wait_for_timeout(2000)
            await controls.drive_until("BeforeStepGame.state.showcase.stage==='observe' && BeforeStepGame.state.paused")
            await chapter('limited_first_look')
            await page.wait_for_function("BeforeStepGame.state.judgmentReady",timeout=15000)
            await page.wait_for_timeout(2000)
            await still('01-limited-first-look')
            await controls.click('[data-judgment="pass"]')
            await page.wait_for_function("BeforeStepGame.state.initialJudgment==='pass'")
            await chapter('initial_judgment_pass')
            await page.wait_for_timeout(1800)
            await controls.click('#decision-imagine')
            await page.wait_for_function("document.querySelector('#raw-model').loaded",timeout=180000)
            await chapter('original_photo_and_first_real_hypothesis')
            await page.wait_for_timeout(2000)
            await controls.click('#model-back')
            await page.wait_for_timeout(3200)
            await controls.click('#switch-hypothesis')
            await page.wait_for_function("document.querySelector('#raw-model').loaded && BeforeStepGame.selected.includes(5958948)",timeout=180000)
            await chapter('same_input_second_back')
            await page.wait_for_timeout(2000)
            await controls.click('[data-expand="models"]')
            await page.wait_for_function("document.querySelector('#raw-model-pair').loaded",timeout=180000)
            await page.wait_for_timeout(2200)
            await still('02-one-photo-two-backs-and-checks')
            await controls.click('#model-back');await page.wait_for_timeout(3200)
            await controls.click('#model-back');await page.wait_for_timeout(3200)
            await controls.click('#brain-restore')
            await controls.click('#rejected-example')
            await page.wait_for_function("document.querySelector('#raw-model').loaded",timeout=180000)
            await chapter('real_rejected_example_original_contour_check')
            await page.wait_for_timeout(3000)
            await controls.click('#return-hypothesis')
            await page.wait_for_function("document.querySelector('#raw-model').loaded",timeout=180000)
            await controls.click('[data-expand="map"]')
            await chapter('registered_footprint_and_visible_route')
            await page.wait_for_timeout(3000)
            await controls.click('#switch-hypothesis')
            await page.wait_for_timeout(3000)
            await controls.click('#switch-hypothesis')
            await page.wait_for_timeout(2500)
            await controls.click('[data-policy="imagination"]')
            await chapter('imagination_changes_route_basis')
            await still('03-footprint-and-route')
            await page.wait_for_timeout(2000)
            await controls.click('#both-hypotheses')
            await controls.click('#brain-restore')
            await controls.click('button[data-view="0"]')
            before=await page.evaluate('BeforeStepGame.state')
            await controls.click('#preview')
            await chapter('two_real_world_rehearsal_start_live_M20_stopped')
            await page.wait_for_function("BeforeStepGame.state.proof?.usable",timeout=240000)
            proof=await page.evaluate('BeforeStepGame.preview')
            assert len(proof['results'])==2 and all(r['passed'] and r['reason']=='completed' for r in proof['results'])
            after=await page.evaluate('BeforeStepGame.state')
            assert all(before[k]==after[k] for k in ['x','y','z','yaw','elapsed'])
            await chapter('two_worlds_completed_assisted_departure_allowed')
            await page.wait_for_timeout(2000)
            await still('04-rehearsal-decision')
            await controls.click('button[data-view="1"]')
            await controls.click('#execute')
            await chapter('first_person_actual_drive')
            await page.wait_for_function("BeforeStepGame.state.x>5.55 || BeforeStepGame.state.phase==='failed'",timeout=240000)
            assert (await page.evaluate('BeforeStepGame.state.phase'))!='failed'
            await controls.click('button[data-view="0"]')
            await chapter('same_drive_rear_side_view_and_new_back_angle')
            await page.wait_for_function("BeforeStepGame.state.phase==='gate' && BeforeStepGame.state.stable",timeout=240000)
            await chapter('visible_low_threshold')
            await page.wait_for_timeout(2000)
            await controls.click('#cross-direct')
            await chapter('twelve_player_leg_commands_begin')
            for count in range(12):
                await page.wait_for_function("BeforeStepGame.state.legs?.waiting",timeout=90000)
                waiting=await page.evaluate('BeforeStepGame.state.legs.waiting')
                await chapter('leg_'+str(count+1)+'_'+waiting['action'])
                await page.wait_for_timeout(800)
                await controls.click('#leg-actions [data-action="'+waiting['action']+'"]')
                await page.wait_for_function('BeforeStepGame.state.actionCount>'+str(count),timeout=30000)
                if count==1:
                    await page.wait_for_timeout(700);await still('05-M20-leg-action')
            await page.wait_for_function("BeforeStepGame.state.phase==='finish-drive'",timeout=180000)
            await chapter('all_four_legs_over_threshold')
            await controls.click('#wheel-mode')
            await page.wait_for_function("!BeforeStepGame.state.legs",timeout=30000)
            await controls.drive_until("BeforeStepGame.state.phase==='complete'",timeout=120000)
            await chapter('beacon_arrival_and_actual_recap')
            report['final']=await page.evaluate('BeforeStepGame.state');report['run']=await page.evaluate('BeforeStepGame.game')
            report['journal']=await page.evaluate('BeforeStepGame.journal')
            assert report['final']['actionCount']==12 and report['final']['goalDistance']<.35
            async with page.expect_download() as download:
                await controls.click('#export-run')
            await (await download.value).save_as(str(OUT/'mother-session.json'))
            await page.mouse.move(35,210);await page.wait_for_timeout(3500);await page.mouse.move(36,210)
            await page.wait_for_timeout(500)
            assert not report['page_errors'],report['page_errors']
            report['passed']=True
        except Exception as e:
            report.update(failure=repr(e),traceback=traceback.format_exc())
            try:report['failure_state']=await page.evaluate('BeforeStepGame.state')
            except Exception:pass
            save();raise
        finally:
            await capture.stop();save()
            await context.close();await browser.close()
    print(json.dumps({'passed':report['passed'],'chapters':len(report['chapters']),'frames':len(capture.frames),'final':report.get('final')},ensure_ascii=False),flush=True)

if __name__=='__main__':asyncio.run(main())
