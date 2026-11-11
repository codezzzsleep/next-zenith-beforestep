"""Exercise real observations, choices, models and mobile presentation in Chromium."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8081/')
    parser.add_argument('--name', default='award-local')
    parser.add_argument('--assets', action='store_true')
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    out = ROOT / 'evidence/award/browser'
    out.mkdir(parents=True, exist_ok=True)
    errors, failures = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
            headless=True, args=['--no-sandbox', '--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader',
                               '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('response', lambda r: failures.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
        page.on('requestfailed', lambda r: failures.append({'url': r.url, 'error': r.failure})
                if r.failure != 'net::ERR_ABORTED' else None)
        assert page.goto(args.url, wait_until='networkidle').status == 200
        page.wait_for_function('document.documentElement.dataset.awardReady === "true"')
        assert page.locator('.orbit').count() == 0
        assert page.locator('#hero-real-image .rock-tag').all_inner_texts() == ['A', 'B']
        assert 'F1_003' in page.locator('#r3-collision-warning').inner_text()
        assert 'F1_003' in page.locator('#award-footer-warning').inner_text()
        page.screenshot(path=str(out / (args.name + '-desktop-1440.png')))
        solar = page.locator('.shadow-card').first.locator('.shadow-photo')
        before_solar = hashlib.sha256(solar.screenshot()).hexdigest()
        before_map = hashlib.sha256(page.locator('#shadow-map').screenshot()).hexdigest()
        start = time.monotonic()
        page.locator('#shadow-toggle').click()
        page.wait_for_function('document.querySelector("#shadow-view").textContent.includes("第二眼")')
        elapsed = time.monotonic() - start
        assert elapsed < 2, elapsed
        page.wait_for_function('getComputedStyle(document.querySelector("#shadow-second")).opacity === "1"')
        assert before_solar == hashlib.sha256(solar.screenshot()).hexdigest()
        assert before_map != hashlib.sha256(page.locator('#shadow-map').screenshot()).hexdigest()
        page.locator('#shadows').screenshot(path=str(out / (args.name + '-two-shadows.png')))
        page.locator('#shadow-range').fill('0')
        page.locator('#shadow-range').dispatch_event('input')
        assert '第一眼' in page.locator('#shadow-view').inner_text()
        data = json.loads((ROOT / 'site/data/demo.json').read_text())
        checked = []
        for card in page.locator('[data-award-choice]').all():
            key = card.get_attribute('data-award-choice')
            card.click()
            s = data['runs'][key]
            assert str(s['looks']) + '眼' in card.inner_text()
            assert str(s['sim_time_s']) + 's' in card.inner_text()
            checked.append(key)
        page.locator('#model').scroll_into_view_if_needed()
        page.wait_for_function('document.querySelector("#model").loaded === true', timeout=60000)
        page.locator('#award-model-rotate').click()
        assert page.locator('#model').evaluate('(e)=>e.cameraOrbit') == '180deg 65deg auto'
        for href in ['en.html', 'award-assets.html', 'evidence/award/observations.json']:
            assert page.request.get(urljoin(args.url, href)).status == 200
        if args.final:
            for id_, suffix in [('award-choices', 'choices'), ('failure-analysis', 'failures'), ('post-result-revision', 'revision')]:
                page.locator('#' + id_).screenshot(path=str(out / (args.name + '-' + suffix + '.png')))
            assert page.locator('#award-lux-pipeline').count() == 1
            for href in ['en.html', 'report.html', 'media/report.pdf', 'evidence/award/facts.json']:
                assert page.request.get(urljoin(args.url, href)).status == 200
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(args.url, wait_until='networkidle')
        page.wait_for_function('document.documentElement.dataset.awardReady === "true"')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(out / (args.name + '-mobile-390.png')))
        page.locator('#shadow-toggle').click()
        assert '第二眼' in page.locator('#shadow-view').inner_text()
        if args.assets:
            page.set_viewport_size({'width': 1440, 'height': 1150})
            assert page.goto(urljoin(args.url, 'award-assets.html'), wait_until='networkidle').status == 200
            for model in page.locator('model-viewer').all():
                model.scroll_into_view_if_needed()
                page.wait_for_function('(src)=>Array.from(document.querySelectorAll("model-viewer")).find(e=>e.getAttribute("src")===src).loaded===true',
                                       arg=model.get_attribute('src'), timeout=60000)
            assert all(page.locator('img').evaluate_all('(es)=>es.map(e=>e.complete&&e.naturalWidth>0)'))
            page.screenshot(path=str(ROOT / 'site/media/award/asset-iterations.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        revision_checked = []
        if args.final:
            page.set_viewport_size({'width': 1440, 'height': 1000})
            page.goto(urljoin(args.url, 'levels.html'), wait_until='networkidle')
            levels = json.loads((ROOT / 'site/data/levels.json').read_text())['levels']
            revision = json.loads((ROOT / 'site/data/award-revisions.json').read_text())['runs']
            for i, level in enumerate(levels):
                page.locator('#level-choose').click()
                page.locator('[data-level-choice=imagination]').click()
                page.locator('#level-finish').click()
                page.locator('#level-reveal').click()
                page.locator('#level-revision-rewatch').click()
                page.locator('#level-finish').click()
                run = revision[level['id']]
                expected = {'stuck': '安全停车', 'arrived': '到达终点', 'collision': '发生碰撞', 'stopped_short': '未完成路线'}[run['result']]
                assert page.locator('#level-run-status').inner_text() == expected
                revision_checked.append(level['id'])
                page.locator('#level-reveal').click()
                page.locator('#level-score').click()
                if i + 1 < len(levels):
                    page.locator('#level-next').click()
        assert not errors, errors
        assert not failures, failures
        result = {'passed': True, 'url': args.url, 'real_first_second_views': True,
                  'solar_reference_unchanged': True, 'actual_map_changed': True,
                  'button_response_s': elapsed, 'four_policy_choices': checked,
                  'local_real_glb_loaded_and_rotated': True, 'mobile_390_no_overflow': True,
                  'oldv2_collision_visible_in_hero_and_footer': True, 'console_errors': errors,
                  'http_errors': failures, 'six_asset_renders': args.assets,
                  'revision_level_replays_checked': revision_checked}
        (out / (args.name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False))
        browser.close()


if __name__ == '__main__':
    main()
