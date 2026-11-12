"""Check the supplemental demo against its saved runs in real Chromium."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8101/')
    parser.add_argument('--name', default='C7-demo-local')
    args = parser.parse_args()
    data = json.loads((ROOT / 'site/data/award-demo.json').read_text())
    result = json.loads((ROOT / 'evidence/award/demo/result.json').read_text())
    assert len(data['runs']) == 6
    for policy, run in data['runs'].items():
        assert run['summary'] == result['runs'].get(policy, {}).get('summary')
    assert all(row['prefix_verified'] for row in data['counterfactuals'])
    out = ROOT / 'evidence/award/acceptance'
    out.mkdir(parents=True, exist_ok=True)
    errors, http, loaded, checked = [], [], [], []
    report = {'passed': False, 'checked_at': datetime.now(timezone.utc).isoformat(), 'url': args.url}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
            headless=True, args=['--no-sandbox', '--enable-webgl', '--use-gl=angle',
                '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
        page.on('response', lambda response: http.append({'url': response.url, 'status': response.status})
            if response.status >= 400 else None)
        page.on('requestfailed', lambda request: http.append({'url': request.url, 'error': request.failure})
            if request.failure != 'net::ERR_ABORTED' else None)
        try:
            assert page.goto(urljoin(args.url, 'award-demo.html'), wait_until='networkidle').status == 200
            page.wait_for_function('document.documentElement.dataset.demoReady === "true"')
            assert page.request.get(urljoin(args.url, 'data/award-demo.json')).json() == data
            assert data['label'] in page.locator('.award-warning').inner_text()
            assert page.locator('#demo-first').evaluate('(e)=>e.complete&&e.naturalWidth>0')
            first = page.request.get(urljoin(args.url, data['image'])).body()
            assert hashlib.sha256(first).hexdigest() == data['image_source_sha256']
            assert page.request.get(urljoin(args.url, data['manifest'])).status == 200
            assert page.locator('header.bar').count() == page.locator('footer.foot').count() == 1
            page.screenshot(path=str(out / (args.name + '-observe-1440.png')), full_page=True)
            page.evaluate('window.demoLoads=0;document.querySelector("#demo-model").addEventListener("load",()=>window.demoLoads++)')
            page.locator('[data-demo-step="generate"]').click()
            for i, candidate in enumerate(data['candidates']):
                previous = page.evaluate('window.demoLoads')
                page.locator('#demo-candidate').select_option(str(i))
                page.wait_for_function('(a)=>{const e=document.querySelector("#demo-model");return e.src===a[0]&&e.loaded&&(a[1]===0||window.demoLoads>a[2])}',
                    arg=[candidate['glb'], i, previous], timeout=60000)
                assert str(candidate['task_id']) in page.locator('#demo-check').inner_text()
                model = page.request.get(urljoin(args.url, candidate['glb'])).body()
                assert hashlib.sha256(model).hexdigest() == candidate['glb_sha256']
                viewer = page.locator('#demo-model')
                before = viewer.evaluate('(e)=>e.getCameraOrbit().theta')
                box = viewer.bounding_box()
                page.mouse.move(box['x'] + box['width'] * .8, box['y'] + box['height'] * .5)
                page.mouse.down()
                page.mouse.move(box['x'] + box['width'] * .2, box['y'] + box['height'] * .5, steps=20)
                page.mouse.up()
                page.wait_for_timeout(150)
                assert viewer.evaluate('(e)=>e.getCameraOrbit().theta') != before
                loaded.append(candidate['task_id'])
            for step, rows in [('rehearse', data['rehearsals']), ('act', data['runs']), ('cf', data['counterfactuals'])]:
                page.locator('[data-demo-step="' + step + '"]').click()
                assert page.locator('#demo-run option').count() == len(rows)
                keys = list(rows) if isinstance(rows, dict) else [str(i) for i in range(len(rows))]
                for key in keys:
                    row = rows[key] if isinstance(rows, dict) else rows[int(key)]
                    page.locator('#demo-run').select_option(key)
                    summary = row.get('summary')
                    if summary:
                        shown = page.locator('#demo-result').inner_text()
                        assert summary['result'] in shown
                        assert str(summary['sim_time_s']) + 's' in shown
                    elif step == 'rehearse':
                        expected = '完整预演完成，无碰撞' if row['completed'] and not row['collided'] else '预演未通过'
                        assert page.locator('#demo-result').inner_text() == expected
                    else:
                        assert '未完成' in page.locator('#demo-result').inner_text()
                    if row.get('trajectory'):
                        before = hashlib.sha256(page.locator('#demo-route').screenshot()).hexdigest()
                        page.locator('#demo-progress').evaluate('(e)=>{e.value=1000;e.dispatchEvent(new Event("input",{bubbles:true}))}')
                        assert page.locator('#demo-time').inner_text() == f"{row['trajectory'][-1][0]:.1f} s"
                        after = hashlib.sha256(page.locator('#demo-route').screenshot()).hexdigest()
                        if any(abs(point[1]-row['trajectory'][0][1]) + abs(point[2]-row['trajectory'][0][2]) > data['map']['resolution'] for point in row['trajectory']):
                            assert before != after
                    checked.append(step + '/' + key)
                if keys:
                    page.locator('#demo-run').select_option(keys[0])
                    page.locator('#demo-play').click()
                    page.wait_for_function('Number(document.querySelector("#demo-progress").value)>0')
                    page.locator('#demo-play').click()
                page.screenshot(path=str(out / (args.name + '-' + step + '-1440.png')), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            for step in ['observe', 'generate', 'rehearse', 'act', 'cf']:
                page.locator('[data-demo-step="' + step + '"]').click()
                assert page.evaluate('document.documentElement.scrollWidth-innerWidth') == 0, step
            page.screenshot(path=str(out / (args.name + '-390.png')), full_page=True)
            assert not errors, errors
            assert not http, http
            report.update(passed=True, six_columns_exact=True, actual_pointer_rotation=True,
                loaded_task_ids=loaded, checked_tracks=checked, image_sha_exact=True,
                candidate_sha_exact=True, counterfactual_prefixes_verified=True,
                mobile_390_no_overflow=True, homepage_chrome=True)
        finally:
            report.update(console_errors=errors, http_errors=http)
            (out / (args.name + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            browser.close()
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
