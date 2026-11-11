"""Verify the separate revision tables, source links and mobile rendering."""
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8081/')
    parser.add_argument('--name', default='r3-local')
    args = parser.parse_args()
    data = json.loads((ROOT / 'evidence/reviews/beforestep_r3/summary.json').read_text())
    output = ROOT / 'outputs/qa/r3/final'
    output.mkdir(parents=True, exist_ok=True)
    errors, failures = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
            headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failures.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
        page.on('requestfailed', lambda r: failures.append({'url': r.url, 'failure': r.failure}) if r.failure != 'net::ERR_ABORTED' else None)
        assert page.goto(args.url, wait_until='networkidle').status == 200
        assert page.evaluate('document.getElementById("failure-analysis").compareDocumentPosition(document.getElementById("post-result-revision")) & Node.DOCUMENT_POSITION_FOLLOWING')
        assert page.evaluate('document.getElementById("post-result-revision").compareDocumentPosition(document.getElementById("sandbox")) & Node.DOCUMENT_POSITION_FOLLOWING')
        section = page.locator('#post-result-revision')
        assert '赛后修订' in section.inner_text() and '不是样本外证据' in section.inner_text()
        tables = section.locator('table')
        assert tables.count() == 3
        checked = []
        for index, rows in enumerate((data['frozen'], data['holdouts'])):
            actual = tables.nth(index).locator('tbody tr')
            assert actual.count() == len(rows)
            for j, row in enumerate(rows):
                cells = actual.nth(j).locator('td').all_inner_texts()
                assert cells[0] == row['scene'] and len(cells) == 6
                for cell, policy in zip(cells[1:], ('conservative', 'see_dark', 'optimistic', 'imagination', 'imagination_strict')):
                    summary = row['runs'].get(policy, {}).get('summary')
                    if summary:
                        assert f"{summary['looks']}眼" in cell
                        assert f"{summary['sim_time_s']:.2f}s" in cell
                        if summary['collision'] is not None or summary['result'] == 'collision':
                            assert '碰撞' in cell
                    else:
                        assert '未完成' in cell
                checked.append(row['scene'])
        if data['all_run_stats']['collisions']:
            warning = page.locator('#r3-collision-warning')
            assert warning.count() == 1
            for scene in data['all_run_stats']['collision_scenes']:
                assert scene in warning.inner_text()
        for href in section.locator('a[href]').evaluate_all('(es)=>es.map(e=>e.getAttribute("href"))'):
            if href.startswith('#'):
                continue
            assert page.request.get(urljoin(args.url, href)).status == 200
        page.screenshot(path=str(output / (args.name + '-desktop.png')), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(output / (args.name + '-mobile.png')), full_page=True)
        assert page.goto(urljoin(args.url, 'report.html'), wait_until='networkidle').status == 200
        assert '赛后修订：想象只解释太阳的影子' in page.locator('body').inner_text()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors, errors
        assert not failures, failures
        result = {'passed': True, 'url': args.url, 'checked_revision_scenes': checked,
                  'source_links_http_200': True, 'chapter_order_verified': True,
                  'width_390_no_overflow': True, 'page_errors': errors, 'http_errors': failures}
        (output / (args.name + '-browser.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(result, ensure_ascii=False))
        browser.close()


if __name__ == '__main__':
    main()
