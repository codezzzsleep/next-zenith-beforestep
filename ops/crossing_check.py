"""One desktop/mobile check of the actual crossing page and interactions."""
import argparse,functools,json,threading,sys
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
ROOT=Path(__file__).resolve().parents[1]
from playwright.sync_api import sync_playwright

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        from urllib.parse import urlsplit,unquote
        rel=unquote(urlsplit(path).path).lstrip('/')
        base=ROOT if rel.startswith(('evidence/','docs/','config/')) else ROOT/'site'
        p=(base/rel).resolve()
        return str(p) if p.is_relative_to(base) else str(base/'__missing__')
    def log_message(self,*args):pass

def check(url,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[]
    measured=json.loads((ROOT/'evidence/crossing/calibration/capability.json').read_text())
    cells=sum(g['method']=='fixed' for g in measured['groups'])
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome')
        for width,height in [(1440,1000),(390,844)]:
            page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1);errors=[];http=[]
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            page.goto(url+'crossing.html',wait_until='networkidle',timeout=90000)
            page.wait_for_function("document.querySelector('#crossing-table button')!==null")
            assert page.locator('#crossing-table button').count()==cells
            assert str(measured['trial_count']) in page.locator('#crossing-summary').inner_text()
            page.select_option('#crossing-method','high');page.locator('#crossing-table button[aria-label="高8厘米深20厘米，3场通过，查看记录"]').click()
            assert '3 场合格通过 / 3 场' in page.locator('#crossing-detail').inner_text()
            page.locator('#crossing-table button').last.click();assert '失稳' in page.locator('#crossing-detail').inner_text()
            page.select_option('#crossing-method','gait')
            assert page.locator('#crossing-table button').count()==cells
            group=next(g for g in measured['groups'] if g['method']=='gait' and g['height_m']==.10 and g['depth_m']==.15)
            page.locator(f'#crossing-table button[aria-label="高10厘米深15厘米，{group["support_compliant_passed"]}场通过，查看记录"]').click()
            assert '实际指令轮不承重时' in page.locator('#crossing-detail').inner_text()
            assert page.locator('#crossing-rocks tbody tr').count()==3
            overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth');assert not overflow;assert not errors,errors;assert not http,http
            page.screenshot(path=str(out/f'{width}.png'),full_page=True)
            rows.append({'viewport':[width,height],'cells':cells,'three_method_switch':True,'actual_cell_details':True,'three_rock_comparisons':True,'horizontal_overflow':overflow,'console_errors':errors,'http_errors':http})
            page.close()
        browser.close()
    result={'passed':True,'url':url,'checks':rows};(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url');ap.add_argument('--out',required=True);a=ap.parse_args()
    if a.url:check(a.url,a.out)
    else:
        s=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=s.serve_forever,daemon=True).start()
        try:check(f'http://127.0.0.1:{s.server_port}/',a.out)
        finally:s.shutdown();s.server_close()
