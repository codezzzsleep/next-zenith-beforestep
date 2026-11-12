"""Exercise the real arena replay at 1440/390, locally or against published Pages."""
import argparse
import functools
import hashlib
import json
import threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import sys
import traceback
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,'/tmp/beforestep-browser-deps')
from playwright.sync_api import sync_playwright


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        local=Path(super().translate_path(path))
        relative=local.relative_to(ROOT/'site')
        return str(ROOT/relative) if relative.parts and relative.parts[0] in ['assets','evidence','docs','config'] else str(local)
    def log_message(self,*args):pass


def run(base,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    index=json.loads((ROOT/'site/data/arena.json').read_text());records=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome')
        for width,height in [(1440,900),(390,844)]:
            page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce');errors=[];http=[]
            page.set_default_timeout(120000)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
            page.goto(base+'arena.html',wait_until='networkidle',timeout=120000)
            page.wait_for_function("document.querySelector('#arena-title').textContent.includes('种子')")
            assert page.locator('.arena-cell').count()==len(index['worlds'])
            assert page.locator('#arena-results .arena-result').count()==8
            for method in [m['id'] for m in index['methods']]:
                page.select_option('#arena-method',method)
                assert page.locator('.arena-cell').count()==len(index['worlds'])
            page.select_option('#arena-method','learned')
            page.check('#arena-failures');assert page.locator('.arena-cell').count()==len(index['failed_learned_worlds'])
            page.uncheck('#arena-failures')
            seed=next(w['seed'] for w in index['worlds'] if w['results']['optimistic'] in ['arrived','collision'])
            page.select_option('#arena-method','optimistic')
            page.locator(f'.arena-cell[title^="{seed} "]').click()
            page.wait_for_function('(seed)=>document.querySelector("#arena-title").textContent.includes(String(seed))&&document.querySelector("#arena-status").textContent!=="加载记录…"',arg=seed)
            page.locator('#arena-scrub').press('Home');before=page.locator('#arena-map').evaluate('(c)=>c.toDataURL()')
            page.click('#arena-play');page.wait_for_timeout(800)
            assert page.locator('#arena-play').inner_text()=='Ⅱ 暂停'
            after=page.locator('#arena-map').evaluate('(c)=>c.toDataURL()');assert after!=before
            page.click('#arena-play');page.locator('#arena-scrub').press('End')
            before=page.locator('#arena-map').evaluate('(c)=>c.toDataURL()');page.check('#arena-truth')
            assert page.locator('#arena-map').evaluate('(c)=>c.toDataURL()')!=before
            page.uncheck('#arena-truth');page.select_option('#arena-method','learned')
            page.uncheck('#arena-hypotheses');page.uncheck('#arena-risk')
            before=page.locator('#arena-map').evaluate('(c)=>c.toDataURL()');page.check('#arena-risk')
            assert page.locator('#arena-map').evaluate('(c)=>c.toDataURL()')!=before,'Learned risk layer did not change the actual canvas'
            before=page.locator('#arena-map').evaluate('(c)=>c.toDataURL()');page.check('#arena-hypotheses')
            assert page.locator('#arena-map').evaluate('(c)=>c.toDataURL()')!=before,'Hypothesis layer did not change the actual canvas'
            old_title=page.locator('#arena-title').inner_text();page.click('#arena-random')
            page.wait_for_function('(old)=>document.querySelector("#arena-title").textContent!==old&&document.querySelector("#arena-status").textContent!=="加载记录…"',arg=old_title)
            assert page.locator('#arena-parallel canvas').count()==3
            for canvas in page.locator('#arena-parallel canvas').all():
                assert canvas.evaluate('(c)=>c.getContext("2d").getImageData(0,0,c.width,c.height).data.some(v=>v!==0)')
            overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not overflow, f'Horizontal overflow at {width}'
            for image in page.locator('.arena-plots img').all():assert image.evaluate('(i)=>i.complete&&i.naturalWidth>0')
            page.screenshot(path=str(out/f'arena-{width}.png'),full_page=True,timeout=120000)
            assert not errors and not http, {'console':errors,'http':http}
            records.append({'width':width,'height':height,'passed':True,'worlds':len(index['worlds']),'methods':8,'console_errors':errors,'http_errors':http,'horizontal_overflow':overflow})
            page.close()
        # Download the actual fixed weights, not an HTML fallback or LFS pointer.
        request=browser.new_context().request
        for variant in ['lux','no_lux']:
            relative=f'assets/models/arena_v2/{variant}/best.pt'
            response=request.get(base+relative,timeout=120000);assert response.ok
            expected=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest();assert hashlib.sha256(response.body()).hexdigest()==expected
        browser.close()
    (out/'result.json').write_text(json.dumps({'passed':True,'base':base,'checks':records},ensure_ascii=False,indent=2)+'\n')
    print('Arena desktop/mobile interactions and weight bytes passed')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--base');ap.add_argument('--out',required=True);a=ap.parse_args()
    try:
        if a.base:run(a.base.rstrip('/')+'/',a.out)
        else:
            server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT/'site')))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:run(f'http://127.0.0.1:{server.server_port}/',a.out)
            finally:server.shutdown();server.server_close()
    except Exception:
        folder=Path(a.out)/'history';folder.mkdir(parents=True,exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        (folder/f'failure-{stamp}.json').write_text(json.dumps({'passed':False,'base':a.base or 'local',
            'traceback':traceback.format_exc()},ensure_ascii=False,indent=2)+'\n')
        raise
