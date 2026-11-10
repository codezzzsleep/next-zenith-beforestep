"""Real-browser five-step acceptance, all choices, meshes and score integrity."""
import argparse
import copy
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8081/levels.html')
    parser.add_argument('--name', default='levels-local')
    args = parser.parse_args()
    expected = json.loads((ROOT / 'site/data/levels.json').read_text())
    output = ROOT / 'outputs/qa/r2'
    output.mkdir(parents=True, exist_ok=True)
    errors, failures, checked = [], [], []
    status = {'arrived': '到达终点', 'collision': '发生碰撞', 'stuck': '安全停车', 'stopped_short': '未完成路线'}
    def outcome(run):
        return 'collision' if run['collision'] is not None or run['result'] == 'collision' else run['result']
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
            headless=True, args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failures.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
        page.on('requestfailed', lambda r: failures.append({'url': r.url, 'error': r.failure}) if r.failure != 'net::ERR_ABORTED' else None)
        assert page.goto(args.url, wait_until='networkidle').status == 200
        page.wait_for_function("document.querySelector('#level-number').textContent.includes('第 1 关')")
        player = 0; fixed = dict.fromkeys(('optimistic', 'conservative', 'imagination'), 0)
        for index, level in enumerate(expected['levels']):
            assert page.locator('[aria-current=step]').inner_text() == '看'
            assert page.locator('#level-reveal-panel').is_hidden()
            assert page.locator('#level-score-panel').is_hidden()
            assert page.locator('#level-run-status').inner_text() == ''
            page.wait_for_function('document.querySelector("#level-image").complete&&document.querySelector("#level-image").naturalWidth>0')
            page.locator('#level-choose').click()
            assert page.locator('[aria-current=step]').inner_text() == '选'
            page.locator('[data-level-choice=optimistic]').click()
            assert page.locator('[aria-current=step]').inner_text() == '走'
            page.locator('#level-finish').click()
            assert page.locator('#level-run-status').inner_text() == status[outcome(level['runs']['optimistic'])]
            page.locator('#level-reveal').click()
            assert page.locator('[aria-current=step]').inner_text() == '揭晓'
            assert page.locator('#level-results article').count() == 3
            models = []
            for candidate in level['candidates']:
                page.locator('#level-candidate').select_option(candidate['id'])
                page.locator('[data-level-model=candidate]').click()
                if candidate['model']:
                    page.locator('#level-model').scroll_into_view_if_needed()
                    page.wait_for_function('(src)=>document.querySelector("#level-model").src.endsWith(src)&&document.querySelector("#level-model").loaded', arg=candidate['model'], timeout=60000)
                    assert page.locator('#level-model-error').is_hidden()
                    models.append(candidate['id'])
                page.locator('[data-level-model=truth]').click()
                page.wait_for_function('(src)=>document.querySelector("#level-model").src.endsWith(src)&&document.querySelector("#level-model").loaded', arg=candidate['truth_model'], timeout=60000)
            page.locator('[data-level-model=truth]').click()
            for rock in level['truth']['rocks']:
                page.locator('#level-truth-rock').select_option(rock['id'])
                page.wait_for_function('(src)=>document.querySelector("#level-model").src.endsWith(src)&&document.querySelector("#level-model").loaded', arg=rock['model'], timeout=60000)
            page.evaluate('document.querySelector("#level-model").cameraOrbit="140deg 65deg 2m";document.querySelector("#level-model").jumpCameraToGoal()')
            for key in ('conservative', 'imagination'):
                page.locator('[data-level-rewatch=' + key + ']').click()
                page.locator('#level-finish').click()
                assert page.locator('#level-run-status').inner_text() == status[outcome(level['runs'][key])]
                page.locator('#level-reveal').click()
            page.locator('#level-score').click()
            assert page.locator('[aria-current=step]').inner_text() == '记分'
            player += outcome(level['runs']['optimistic']) == 'arrived'
            for key in fixed:
                fixed[key] += outcome(level['runs'][key]) == 'arrived'
            values = page.locator('#level-scoreboard .metric').all_inner_texts()
            assert values == [f'{player} / {index+1}', *[f'{fixed[k]} / {index+1}' for k in fixed]]
            checked.append({'scene': level['id'], 'all_five_steps': True, 'all_three_actual_replays': True,
                            'candidate_meshes_loaded': models, 'first_choice_score_preserved': True})
            if index+1 < len(expected['levels']):
                page.locator('#level-next').click()
        page.screenshot(path=str(output / (args.name + '-desktop.png')), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.locator('#level-reset').click()
        assert page.locator('[aria-current=step]').inner_text() == '看'
        page.locator('#level-choose').click(); page.locator('[data-level-choice=imagination]').click()
        page.locator('#level-finish').click(); page.locator('#level-reveal').click()
        page.locator('#level-model').scroll_into_view_if_needed()
        page.wait_for_function('document.querySelector("#level-model").loaded', timeout=60000)
        page.wait_for_timeout(500)
        page.locator('#level-model').screenshot(path=str(output / (args.name + '-mobile-model.png')))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(output / (args.name + '-mobile.png')), full_page=True)
        # Exercise the absence branch without inventing an experimental result:
        # intercept only the browser payload in this test and retain real scans.
        fixture = copy.deepcopy(expected)
        fixture['levels'] = fixture['levels'][:1]
        fixture['levels'][0]['candidates'] = []
        page.route('**/data/levels.json', lambda route: route.fulfill(json=fixture))
        page.reload(wait_until='networkidle')
        page.locator('#level-choose').click(); page.locator('[data-level-choice=imagination]').click()
        page.locator('#level-finish').click(); page.locator('#level-reveal').click()
        page.locator('[data-level-model=truth]').click()
        page.locator('#level-model').scroll_into_view_if_needed()
        truth_src = fixture['levels'][0]['truth']['rocks'][0]['model']
        page.wait_for_function('(src)=>document.querySelector("#level-model").src.endsWith(src)&&document.querySelector("#level-model").loaded', arg=truth_src, timeout=60000)
        assert page.locator('#level-model-error').is_hidden()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        # Browser-only contract fixture: an arrival label cannot suppress a
        # contact record. The actual experiment payload remains unchanged.
        contact = expected['levels'][0]['runs']['optimistic']['collision']
        assert contact is not None
        fixture['levels'][0]['runs']['imagination'].update(result='arrived', collision=contact)
        page.reload(wait_until='networkidle')
        page.locator('#level-choose').click()
        page.locator('[data-level-choice=imagination]').click()
        page.locator('#level-finish').click()
        assert page.locator('#level-run-status').inner_text() == status['collision']
        page.locator('#level-reveal').click()
        assert page.locator('#level-results .metric').all_inner_texts()[-1] == status['collision']
        page.locator('#level-score').click()
        values = page.locator('#level-scoreboard .metric').all_inner_texts()
        assert values[0] == '0 / 1' and values[-1] == '0 / 1'
        assert not errors, errors
        assert not failures, failures
        report = {'schema': 'beforestep-levels-browser-acceptance/v1', 'passed': True,
                  'url': args.url, 'levels': checked, 'width_390_no_overflow': True,
                  'page_errors': errors, 'http_errors': failures,
                  'anchor_only_development': expected.get('anchor_only_development', False)}
        report['no_candidate_truth_access_verified_with_ui_fixture'] = True
        report['contact_priority_verified_with_ui_fixture'] = True
        (output / (args.name + '-browser.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(report, ensure_ascii=False), flush=True)
        browser.close()


if __name__ == '__main__':
    main()
