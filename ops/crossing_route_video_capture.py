"""Record the published site with real pointer actions for the storyboard."""
import argparse,json,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from playwright.sync_api import sync_playwright
from experimental.crossing.runtime import write,sha
OUT=ROOT/'outputs/crossing/route/video/pages'
PUBLIC='https://codezzzsleep.github.io/next-zenith-beforestep/'

def drag(page,selector,seconds=4):
    element=page.locator(selector);element.scroll_into_view_if_needed()
    page.wait_for_function('(s)=>document.querySelector(s).loaded===true',arg=selector,timeout=60000)
    box=element.bounding_box();page.mouse.move(box['x']+box['width']*.78,box['y']+box['height']*.5);page.mouse.down()
    for i in range(40):
        page.mouse.move(box['x']+box['width']*(.78-.58*(i+1)/40),box['y']+box['height']*.5)
        page.wait_for_timeout(seconds*1000/40)
    page.mouse.up()

def record(browser,shot,force=False):
    OUT.mkdir(parents=True,exist_ok=True);index=OUT/f'{shot}.json'
    if index.exists() and json.loads(index.read_text()).get('status')=='complete' and not force:return
    url=PUBLIC+('crossing.html' if shot=='7-table' else '')
    duration={'2':10,'3':14,'4':14,'5':12,'7-table':8,'8':16,'9':10}[shot]
    context=browser.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(OUT/'raw'),record_video_size={'width':1920,'height':1080},reduced_motion='reduce')
    started=time.monotonic();page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    result={'shot':shot,'url':url,'width':1920,'height':1080,'duration_s':duration,'status':'running','real_public_page_recording':True}
    write(index,result)
    try:
        response=page.goto(url,wait_until='networkidle',timeout=90000)
        assert response and response.status==200
        import hashlib
        result['public_html_sha256']=hashlib.sha256(response.body()).hexdigest()
        if shot=='7-table':
            page.wait_for_function('document.documentElement.dataset.crossingReady==="true"',timeout=90000)
            page.locator('#route-results').scroll_into_view_if_needed()
            with urllib.request.urlopen(PUBLIC+'evidence/crossing/route/summary.json',timeout=60) as remote:result['summary_sha256']=hashlib.sha256(remote.read()).hexdigest()
        else:
            page.wait_for_function('document.querySelector("#hero-rock").loaded===true',timeout=90000)
            if shot=='3':page.locator('#wall').scroll_into_view_if_needed()
            if shot=='4':page.locator('#reveal').scroll_into_view_if_needed();page.locator('#twin-rock').scroll_into_view_if_needed();page.wait_for_function('document.querySelector("#twin-rock").loaded===true',timeout=60000)
            if shot=='5':page.locator('#worlds').scroll_into_view_if_needed()
            if shot=='8':page.locator('#result').scroll_into_view_if_needed()
            if shot in ['2','9']:page.evaluate('scrollTo(0,0)')
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT/f'{shot}-still.jpg'),type='jpeg',quality=94)
        result['stable_start_s']=time.monotonic()-started;capture_start=time.monotonic()
        if shot=='2':
            drag(page,'#hero-rock',3)
            if not page.locator('#back-flag').is_visible():drag(page,'#hero-rock',3)
            result['back_flag_visible']=page.locator('#back-flag').is_visible()
        elif shot=='3':
            page.wait_for_timeout(4500);page.locator('#wall [data-show="c"]').click();page.wait_for_timeout(1000)
            page.locator('#wall-grid').hover();result['filter_clicked']='c'
        elif shot=='4':
            drag(page,'#twin-rock',5);page.locator('#twin-views button').nth(1).click();page.wait_for_timeout(1000)
            result['real_overlay_pointer_drag']=True
        elif shot=='8':
            page.wait_for_timeout(5000);page.locator('#crashlab').scroll_into_view_if_needed()
            page.wait_for_timeout(1800);page.locator('#crash-views button').nth(1).click();page.wait_for_timeout(1500)
            result['crash_back_view_clicked']=True
        elapsed=time.monotonic()-capture_start
        page.wait_for_timeout(max(0,duration-elapsed)*1000)
        page.screenshot(path=str(OUT/f'{shot}-end.jpg'),type='jpeg',quality=94)
        result.update(status='complete',console_errors=errors)
    except Exception as error:
        result.update(status='fallback',failure=str(error),console_errors=errors)
        try:page.screenshot(path=str(OUT/f'{shot}-still.jpg'),type='jpeg',quality=94)
        except Exception:pass
        document=ROOT/'docs/video.md';note=f'\n- 镜头 {shot} 页面录屏替换为对应公网页面静帧：{str(error).splitlines()[0]}。\n'
        if note not in document.read_text():document.write_text(document.read_text()+note)
    finally:
        video=page.video;context.close()
        if video:
            destination=OUT/f'{shot}.webm';video.save_as(str(destination));result.update(path=str(destination.relative_to(ROOT)),sha256=sha(destination))
        write(index,result)
    print(json.dumps({k:result.get(k) for k in ['shot','status','failure']},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--shot',default='all');parser.add_argument('--force',action='store_true');a=parser.parse_args()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        try:
            for shot in ['2','3','4','5','7-table','8','9'] if a.shot=='all' else [a.shot]:record(browser,shot,a.force)
        finally:browser.close()
