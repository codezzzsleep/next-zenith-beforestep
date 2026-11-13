"""Validate the four-section page once on desktop and mobile."""
import argparse,json,sys,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from http.server import ThreadingHTTPServer
from ops.crossing_check import Handler
from playwright.sync_api import sync_playwright

def check(url,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    low=json.loads((ROOT/'evidence/crossing/route/low-stone.json').read_text());rows=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome')
        for width,height in [(1440,1000),(390,844)]:
            page=browser.new_page(viewport={'width':width,'height':height});errors=[];http=[]
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            page.goto(url+'crossing.html',wait_until='networkidle',timeout=90000)
            page.wait_for_function("document.documentElement.dataset.crossingReady==='true'",timeout=60000)
            assert page.locator('main>section').count()==4
            assert '机器人只拍到石头的一面' in page.locator('#story-opening').inner_text()
            for method in ['fixed','high','gait']:
                page.select_option('#crossing-method',method);page.locator('#crossing-table button').first.click()
                assert page.locator('#crossing-detail').inner_text()
            assert page.locator('#low-model-select option').count()==len(low['models'])
            page.select_option('#low-model-select','1');page.wait_for_function("document.querySelector('#low-model').loaded===true",timeout=60000)
            assert str(low['threshold_created']) in page.locator('#low-count-note').inner_text()
            assert page.locator('#route-results tbody tr').count()==4
            assert page.locator('#route-panels canvas').count()==4
            page.locator('#route-play').click();page.wait_for_timeout(150);page.locator('#route-play').click()
            assert float(page.locator('#route-timeline').input_value())>0
            overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not overflow;assert not errors,errors;assert not http,http
            page.screenshot(path=str(out/f'{width}.png'),full_page=True)
            rows.append({'viewport':[width,height],'four_sections':True,'ability_detail':True,'model_overlay_loaded':True,
                'four_car_timeline':True,'horizontal_overflow':False,'console_errors':errors,'http_errors':http})
            page.close()
        browser.close()
    result={'passed':True,'url':url,'checks':rows};(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',required=True);a=ap.parse_args()
    if a.url:check(a.url,a.out)
    else:
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        try:check(f'http://127.0.0.1:{server.server_port}/',a.out)
        finally:server.shutdown();server.server_close()
