"""Real Chromium acceptance for the R1 site, its appendices and served assets."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8081/')
parser.add_argument('--name', default='local')
parser.add_argument('--pdf', action='store_true')
parser.add_argument('--entry', default='index.html')
args = parser.parse_args()
qa = ROOT / 'outputs/qa/r1'
qa.mkdir(parents=True, exist_ok=True)
data = json.loads((ROOT / 'site/data/demo.json').read_text())
results = {'arrived': '到达终点', 'collision': '遇到碰撞', 'stuck': '无路线，停车', 'stopped_short': '未完成路线'}
errors, failures = [], []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome', headless=True, args=['--no-sandbox', '--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: failures.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
    page.on('requestfailed', lambda r: failures.append({'url': r.url, 'failure': r.failure}) if r.failure != 'net::ERR_ABORTED' else None)
    assert page.goto(urljoin(args.url, args.entry), wait_until='networkidle').status == 200
    page.wait_for_function("document.querySelector('#scene-title').textContent.includes('R1')")
    assert page.locator('#scene-select').input_value() == 'data/demo.json'
    assert page.locator('#controller-label').inner_text() == '同一场景 · 同一规则控制器'
    assert page.locator('#run-status').count() == 1
    assert page.locator('#run-status').inner_text() == '到达终点'
    assert page.locator('#rehearsals').inner_text() == '12/12'
    assert page.locator('#main-result-rows tr').count() == 5
    assert page.locator('#pane-gallery canvas').count() == 12
    assert page.locator('#physical-gap').inner_text() == '47.541 mm'
    assert '-0.062778 m' in page.locator('#xy-center-note').inner_text()
    assert '1223.6 s' in page.locator('#wall-note').inner_text()
    assert 'native_ok=false' in page.locator('#generation-note').inner_text()
    assert '历史' in page.locator('#video-description').inner_text()
    checked_runs = []
    for key in data['runs']:
        if key in ('optimistic', 'conservative', 'imagination'):
            page.locator('[data-policy=' + key + ']').click()
        else:
            page.locator('#audit-select').select_option(key)
        expected = data['runs'][key]
        assert page.locator('#run-status').inner_text() == results[expected['result']]
        assert float(page.locator('#duration').inner_text().removesuffix('s')) == expected['sim_time_s']
        assert page.locator('#looks').inner_text() == str(expected['looks'])
        assert page.locator('#run-evidence').get_attribute('href') == expected['evidence'] + '/run_identity.json'
        page.locator('#scrub').fill('1000')
        page.locator('#scrub').dispatch_event('input')
        assert page.locator('#time').inner_text() == f"{expected['trajectory'][-1][0]:.1f} s"
        checked_runs.append({'key': key, 'run_id': expected['run_id'], 'result': expected['result']})
    page.locator('[data-policy=imagination]').click()
    page.locator('#play').click()
    page.wait_for_function("Number(document.querySelector('#scrub').value)>0")
    page.locator('#play').click()
    page.locator('#model').scroll_into_view_if_needed()
    page.wait_for_function('document.querySelector("#model").loaded === true', timeout=60000)
    page.evaluate('window.qaModelLoads=0;document.querySelector("#model").addEventListener("load",()=>window.qaModelLoads++)')
    loaded = []
    for candidate in data['candidates']:
        if page.locator('#candidate-select').input_value() != candidate['id']:
            count = page.evaluate('window.qaModelLoads')
            page.locator('#candidate-select').select_option(candidate['id'])
            page.wait_for_function('(n)=>window.qaModelLoads>n && document.querySelector("#model").loaded===true', arg=count, timeout=60000)
        assert not page.locator('#model-error').is_visible()
        page.wait_for_function('document.querySelector("#input").complete && document.querySelector("#input").naturalWidth>0')
        loaded.append(candidate['task_id'])
    page.locator('#candidate-select').select_option('r1_T2_A2')
    page.wait_for_function('document.querySelector("#model").loaded===true', timeout=60000)
    images = page.locator('img').evaluate_all('(els)=>els.map(el=>({src:el.getAttribute("src"),ok:el.complete&&el.naturalWidth>0}))')
    assert all(i['ok'] for i in images), images
    links_checked = []
    for href in set(page.evaluate('Array.from(document.querySelectorAll("a[href]"),el=>el.getAttribute("href"))')):
        if not href or href.startswith(('#', 'https:', 'http:')):
            continue
        url = urljoin(args.url, href)
        response = page.request.get(url)
        assert response.status == 200, (url, response.status)
        links_checked.append(href)
    page.screenshot(path=str(qa / (args.name + '-desktop.png')), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(qa / (args.name + '-mobile.png')), full_page=True)
    historical = []
    index = json.loads((ROOT / 'site/data/scenes.json').read_text())
    for scene in index['scenes'][1:]:
        old = json.loads((ROOT / 'site' / scene['data']).read_text())
        page.locator('#scene-select').select_option(scene['data'])
        page.wait_for_function('(t)=>document.querySelector("#scene-title").textContent===t', arg=old['title'])
        for policy in ('optimistic', 'conservative', 'imagination'):
            page.locator('[data-policy=' + policy + ']').click()
            assert page.locator('#run-status').inner_text() == results[old['runs'][policy]['result']]
        page.locator('#model').scroll_into_view_if_needed()
        page.wait_for_function('document.querySelector("#model").loaded===true', timeout=60000)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert '历史' in page.locator('#video-title').inner_text()
        historical.append(scene['id'])
    report_name = 'project-report.html' if (ROOT / 'evidence/web-assets/technical-transfer.json').exists() else 'report.html'
    assert page.goto(urljoin(args.url, report_name), wait_until='networkidle').status == 200
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert all(page.locator('img').evaluate_all('(els)=>els.map(el=>el.complete&&el.naturalWidth>0)'))
    page.screenshot(path=str(qa / (args.name + '-report-mobile.png')), full_page=True)
    if args.pdf:
        page.pdf(path=str(ROOT / 'site/media/report.pdf'), print_background=True, prefer_css_page_size=True)
    assert page.goto(urljoin(args.url, 'learning.html'), wait_until='networkidle').status == 200
    page.wait_for_function("document.querySelector('#learning-status').textContent==='到达终点'")
    learning_count = page.locator('#learning-run option').count()
    assert learning_count == 20
    for index in range(learning_count):
        page.locator('#learning-run').select_option(index=index)
        page.locator('#learning-scrub').fill('800')
        page.locator('#learning-scrub').dispatch_event('input')
        assert page.locator('#learning-time').inner_text() != '0.0 s'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    file_hashes = {}
    for relative in ('media/demo.mp4', 'media/learning-demo.mp4', 'media/report.pdf', 'media/history/trained_gate_v03/report.pdf', 'data/demo.json'):
        response = page.request.get(args.url + relative)
        assert response.status == 200
        digest = hashlib.sha256(response.body()).hexdigest()
        assert digest == hashlib.sha256((ROOT / 'site' / relative).read_bytes()).hexdigest()
        file_hashes[relative] = digest
    assert not errors, errors
    assert not failures, failures
    report = {'schema': 'beforestep-r1-browser-acceptance/v1', 'url': args.url, 'passed': True,
              'default': 'stress_v8_r1 / rules / imagination', 'runs': checked_runs,
              'candidate_glbs_loaded': loaded, 'rehearsal_canvases': 12,
              'images_loaded': images, 'local_links_http_200': links_checked,
              'historical_scenes': historical, 'learning_replays': learning_count,
              'mobile_width_px': 390, 'no_horizontal_overflow': True,
              'page_errors': errors, 'http_errors': failures, 'served_sha256': file_hashes}
    (qa / (args.name + '-browser-validation.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
    browser.close()
