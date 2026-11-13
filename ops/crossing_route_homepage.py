"""Audit the added claims and check the author's homepage on both viewports."""
import argparse,json,sys,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from ops.crossing_check import Handler
from experimental.crossing.runtime import write,sha

def audit():
    gate=json.loads((ROOT/'evidence/crossing/calibration/gate.json').read_text())
    capability=json.loads((ROOT/'evidence/crossing/calibration/capability-v72.json').read_text())
    low=json.loads((ROOT/'evidence/crossing/route/low-stone.json').read_text())
    claims=[]
    def add(text,value,ok,source,note=''):
        claims.append({'claim':text,'measured':value,'matches':bool(ok),'source':source,'note':note})
    add('轮行0/90，两姿态，10到15厘米',[gate['wheel_passes_at_band_heights'],gate['wheel_trials_at_band_heights']],gate['wheel_passes_at_band_heights']==0 and gate['wheel_trials_at_band_heights']==90,'evidence/crossing/calibration/gate.json','离散高度10/12/15厘米；未验证连续高度区间')
    add('抬腿24/24',[gate['band_gait_clean_trials'],gate['band_gait_trials']],gate['band_gait_clean_trials']==gate['band_gait_trials']==24,'evidence/crossing/calibration/gate.json')
    clean=[x for x in capability['rocks'] if x.get('status')=='clean_pass']
    add('3块真石都跨过',gate['conditions'][2]['count'],gate['conditions'][2]['count']==3,'evidence/crossing/calibration/gate.json')
    maximum=capability['maximum'];add('轮行最高8厘米',maximum,all(maximum[k]['any_pass_height_m']==.08 for k in ['fixed','high']),'evidence/crossing/calibration/capability-v72.json')
    add('腿能跨最高15厘米',gate['gait_three_of_three_height_m'],gate['gait_three_of_three_height_m']==.15,'evidence/crossing/calibration/gate.json','本轮冻结能力范围')
    camera=[];blind=[]
    valid={r['seed'] for r in json.loads((ROOT/'evidence/crossing/development-validity-scene-dev-v9.json').read_text())['scenes'] if r['valid']}
    for path in (ROOT/'evidence/crossing').glob('development-blindness*.json'):
        data=json.loads(path.read_text())
        for scene in data.get('scenes',[]):
            if 'camera_world' in scene:camera.append(scene['camera_world']['world_pos'][2])
            if scene.get('revision')=='scene-dev-v9' and scene['seed'] in valid:blind.extend(t['unseen_far_m'] for t in scene['tracks'])
    # The current low-stone and v9 measurements give the relevant blind region.
    add('相机离地38厘米',camera,any(round(v*100)==38 for v in camera),'evidence/crossing/development-blindness*.json','冻结常规姿态的观测高度；不是所有腿姿态的固定高度')
    if not blind:
        data=json.loads((ROOT/'evidence/crossing/development-blindness-scene-dev-v9.json','仅统计六轮行全不过的有效门槛；22002可轮行，排除').read_text()) if (ROOT/'evidence/crossing/development-blindness-scene-dev-v9.json','仅统计六轮行全不过的有效门槛；22002可轮行，排除').exists() else {}
        blind=[t['unseen_far_m'] for s in data.get('scenes',[]) for t in s['tracks']]
    add('看不见部分1到8厘米',blind, bool(blind) and min(blind)>=.005 and max(blind)<.085,'evidence/crossing/development-blindness-scene-dev-v9.json','仅统计六轮行全不过的有效门槛；22002可轮行，排除')
    add('191秒干净跨过',low['B'],low['B']['status']=='clean_pass' and round(low['B']['sim_seconds'])==191,'evidence/crossing/route/low-stone.json')
    add('用想象的车停下；4份准入',[low['D']['status'],len(low['models'])],low['D']['status']=='stopped' and len(low['models'])==4,'evidence/crossing/route/low-stone.json')
    # Compare far edges, as the STORY does, rather than mixing extrema of depth.
    source=ROOT/'outputs/crossing/development/scene-dev-v9/seed-22001/scene.json'
    scene=json.loads(source.read_text());truth=scene['truth_geometry']
    delta=[m['geometry']['far'][i]-truth['far'][i] for m in low['models'] for i in range(2)]
    add('想长约5厘米',delta,min(delta)>.04 and max(delta)<.065,'evidence/crossing/route/low-stone.json; docs/story.md §2','四份模型沿两条轮迹的远边额外约4.5到6.0厘米')
    report={'schema':'beforestep-home-v2-added-claims/v1','passed':all(c['matches'] for c in claims),'claims':claims,'design_and_copy_unchanged':True}
    write(ROOT/'evidence/crossing/route/home-v2-numbers.json',report)
    if not report['passed']:print(json.dumps([c for c in claims if not c['matches']],ensure_ascii=False));raise RuntimeError('Author homepage numeric discrepancy; retain copy and report')
    return report

def check(url,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        for width,height in [(1440,1000),(390,844)]:
            page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce');errors=[];http=[]
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            page.goto(url,wait_until='networkidle',timeout=90000)
            page.wait_for_function('document.querySelector("#hero-rock").loaded===true',timeout=60000)
            assert page.locator('#legs').count()==1
            loaded=[]
            for button in page.locator('.pick:not(.missing)').all():
                button.scroll_into_view_if_needed();button.click()
                task=int(page.locator('#studio-facts dd').first.inner_text())
                page.locator('#studio-rock').scroll_into_view_if_needed()
                page.wait_for_function('(id)=>document.querySelector("#studio-rock").loaded===true&&document.querySelector("#studio-rock").src.endsWith("/"+id+".glb")',arg=task,timeout=60000)
                loaded.append(task)
            assert len(set(loaded))==11
            for image in page.locator('img').all():image.scroll_into_view_if_needed()
            page.wait_for_function('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)',timeout=60000)
            assert page.evaluate('document.documentElement.scrollWidth-innerWidth')==0
            page.locator('#legs').screenshot(path=str(out/f'legs-{width}.png'))
            page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/f'{width}.png'),full_page=True)
            assert not errors,errors;assert not http,http
            rows.append({'viewport':[width,height],'eleven_model_tasks_loaded':loaded,'legs_section':True,'horizontal_overflow':False,'console_errors':errors,'http_errors':http});page.close()
        browser.close()
    write(out/'result.json',{'passed':True,'url':url,'checks':rows});print(json.dumps({'passed':True,'url':url,'viewports':[1440,390],'models':11}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',required=True);ap.add_argument('--audit-only',action='store_true');a=ap.parse_args()
    audit()
    if not a.audit_only:
        if a.url:check(a.url,a.out)
        else:
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
            try:check(f'http://127.0.0.1:{server.server_port}/',a.out)
            finally:server.shutdown();server.server_close()
