"""Exercise actual navigation records and controls in Chromium, on site or Pages."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8104/navigation.html')
    p.add_argument('--name',default='browser-local');a=p.parse_args()
    out=ROOT/'evidence/learning/navigation_v1/acceptance';out.mkdir(parents=True,exist_ok=True)
    proof={'url':a.url,'checked_at':datetime.now(timezone.utc).isoformat(),'passed':False};errors=[];bad=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
          headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda e:errors.append(e.text) if e.type=='error' else None)
        page.on('response',lambda r:bad.append([r.url,r.status]) if r.status>=400 else None)
        try:
            assert page.goto(a.url,wait_until='networkidle').status==200
            page.wait_for_function('window.navigationReady===true')
            assert page.locator('#nav-results tr').count()==6
            expected={'test':128,'ood':128,'physical':8,'physical_start_v2':8};counts={}
            for split,count in expected.items():
                page.select_option('#nav-split',split)
                page.wait_for_function('(s)=>document.querySelector("#nav-map").dataset.seed===document.querySelector("#nav-scene").value',arg=split)
                assert page.locator('#nav-scene option').count()==count
                options=page.locator('#nav-scene option').evaluate_all('(items)=>items.map(x=>x.value)')
                # Validate every scene payload and stored trace without executing a policy again.
                for seed in options:
                    response=page.request.get(urljoin(a.url,f'data/navigation/{split}/{seed}.json'))
                    assert response.status==200;data=response.json();assert data['world']['seed']==int(seed)
                    assert len(data['episodes'])==(6 if split in ['test','ood'] else 2)
                    for episode in data['episodes'].values():
                        assert len(episode['trace_m'])==len(episode['time'])
                        assert all(len(point)==2 for point in episode['trace_m'])
                counts[split]=len(options)
                page.select_option('#nav-scene',options[-1]);page.wait_for_function('(s)=>document.querySelector("#nav-map").dataset.seed===s',arg=options[-1])
                for method in page.locator('#nav-method option').evaluate_all('(items)=>items.map(x=>x.value)'):
                    page.select_option('#nav-method',method)
                    assert page.locator('#nav-map').get_attribute('data-method')==method
                    assert page.request.get(urljoin(a.url,page.locator('#nav-evidence').get_attribute('href'))).status==200
                page.check('#nav-failures')
                assert all('到达' not in label.replace('未到达','') for label in page.locator('#nav-scene option').all_text_contents())
                page.uncheck('#nav-failures')
            page.select_option('#nav-split','test');page.select_option('#nav-method','learned')
            page.wait_for_function('document.querySelector("#nav-map").dataset.method==="learned"')
            page.locator('#nav-scrub').evaluate('(e)=>{e.value=0;e.dispatchEvent(new Event("input",{bubbles:true}))}')
            assert page.locator('#nav-map').get_attribute('data-frame')=='0'
            page.click('#nav-play');page.wait_for_function('Number(document.querySelector("#nav-map").dataset.frame)>0')
            page.click('#nav-play');page.uncheck('#nav-truth');page.check('#nav-prior')
            assert not page.locator('#nav-truth').is_checked() and page.locator('#nav-prior').is_checked()
            page.wait_for_function('Array.from(document.images).every(e=>e.complete&&e.naturalWidth>0)')
            assert page.evaluate('document.documentElement.scrollWidth-innerWidth')==0
            page.screenshot(path=str(out/(a.name+'-1440.png')),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth-innerWidth')==0
            page.screenshot(path=str(out/(a.name+'-390.png')),full_page=True)
            model=page.request.get(urljoin(a.url,'assets/models/navigation_v1/best.pt'));assert model.status==200
            assert hashlib.sha256(model.body()).hexdigest()==json.loads((ROOT/'evidence/learning/navigation_v1/result.json').read_text())['model_sha256']
            assert not errors and not bad,(errors,bad)
            proof.update(passed=True,scene_counts=counts,all_methods_switched=True,playback_advanced=True,
                         failure_filter=True,diagnostic_layers=True,desktop_overflow=0,mobile_overflow=0,downloaded_weight_sha_verified=True)
        except Exception as e:proof['failure']=str(e);raise
        finally:
            proof.update(console_errors=errors,http_errors=bad)
            (out/(a.name+'.json')).write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');browser.close()
    print(json.dumps(proof,ensure_ascii=False))


if __name__=='__main__':main()
