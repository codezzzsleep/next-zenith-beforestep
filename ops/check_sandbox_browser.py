"""Check actual sandbox editing, route calculation and valid JSON export."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8081/sandbox.html')
    parser.add_argument('--name', default='sandbox-local')
    args = parser.parse_args()
    output = ROOT / 'outputs/qa/r2'
    output.mkdir(parents=True, exist_ok=True)
    errors, failures = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome',
                                     headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failures.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
        page.on('requestfailed', lambda r: failures.append({'url': r.url, 'error': r.failure})
                if r.failure != 'net::ERR_ABORTED' else None)
        assert page.goto(args.url).status == 200
        page.wait_for_selector('#sandbox-map[data-revision]', timeout=60000)
        page.wait_for_function('document.querySelectorAll("#sandbox-results article").length===3')
        data = json.loads((ROOT / 'site/data/sandbox.json').read_text())
        presets_checked = []
        assert page.locator('#sandbox-preset option').count() == len(data['presets'])
        for index, preset in enumerate(data['presets']):
            previous = int(page.locator('#sandbox-map').get_attribute('data-revision'))
            page.locator('#sandbox-preset').select_option(str(index))
            page.wait_for_function('(n)=>Number(document.querySelector("#sandbox-map").dataset.revision)>n', arg=previous, timeout=60000)
            assert page.locator('#sandbox-results article').count() == 3
            assert page.locator('#sandbox-error').is_hidden()
            presets_checked.append({'scene': preset['id'], 'three_plans_displayed': True})
        previous = int(page.locator('#sandbox-map').get_attribute('data-revision'))
        page.locator('#sandbox-preset').select_option('0')
        page.wait_for_function('(n)=>Number(document.querySelector("#sandbox-map").dataset.revision)>n', arg=previous)
        first = int(page.locator('#sandbox-map').get_attribute('data-revision'))
        page.locator('[data-asset=boulder_01]').click()
        page.wait_for_function('(n)=>Number(document.querySelector("#sandbox-map").dataset.revision)>n', arg=first)
        # Drag the newly added rock from world (5,.1) to (5.5,-.3).
        box = page.locator('#sandbox-map').bounding_box()
        def position(x, y):
            return box['x']+(x+1)/14*box['width'], box['y']+(2.5-y)/4.5*box['height']
        revision = int(page.locator('#sandbox-map').get_attribute('data-revision'))
        page.mouse.move(*position(5, .1)); page.mouse.down()
        page.mouse.move(*position(5.5, -.3), steps=4); page.mouse.up()
        page.wait_for_function('(n)=>Number(document.querySelector("#sandbox-map").dataset.revision)>n', arg=revision)
        page.locator('#sandbox-yaw').fill('45'); page.locator('#sandbox-yaw').dispatch_event('input')
        page.locator('#sandbox-height').fill('.45'); page.locator('#sandbox-height').dispatch_event('change')
        page.locator('#sandbox-crater').click()
        page.locator('#sandbox-sun').fill('50'); page.locator('#sandbox-sun').dispatch_event('input')
        page.locator('#sandbox-terrain').select_option('plain')
        page.wait_for_timeout(500)
        with page.expect_download() as dl:
            page.locator('#sandbox-export').click()
        destination = output / (args.name + '-export.json')
        dl.value.save_as(destination)
        scene = json.loads(destination.read_text())
        assert scene['rocks']['R1']['yaw'] == 45
        assert scene['rocks']['R1']['height'] == .45
        assert abs(scene['rocks']['R1']['x'] - 5.5) < .03 and abs(scene['rocks']['R1']['y'] + .3) < .03
        assert scene['terrain']['type'] == 'plain' and len(scene['terrain']['craters']) == 1
        assert scene['sun']['azimuth_deg'] == 50
        assert scene['asset_cache_precision'] == 'exact' and scene['rehearse_reference'] is False
        page.locator('#sandbox-delete').click()
        # Exercise the browser's actual library drag-and-drop path as well as
        # moving a rock already on the map. A click does not cover this path.
        box = page.locator('#sandbox-map').bounding_box()
        revision = int(page.locator('#sandbox-map').get_attribute('data-revision'))
        page.locator('[data-asset=rock_07]').drag_to(page.locator('#sandbox-map'),
            target_position={'x': (10+1)/14*box['width'], 'y': (2.5+1.5)/4.5*box['height']})
        page.wait_for_function('(n)=>Number(document.querySelector("#sandbox-map").dataset.revision)>n', arg=revision)
        with page.expect_download() as drop_dl:
            page.locator('#sandbox-export').click()
        drop_destination = output / (args.name + '-drop-export.json')
        drop_dl.value.save_as(drop_destination)
        dropped = json.loads(drop_destination.read_text())['rocks']['R2']
        assert dropped['rock'] == 'rock_07'
        assert abs(dropped['x']-10) < .03 and abs(dropped['y']+1.5) < .03
        page.locator('#sandbox-delete').click()
        page.locator('#sandbox-animate').click()
        page.locator('#sandbox-layer').select_option('imagination')
        page.wait_for_timeout(800)
        assert page.locator('#sandbox-error').is_hidden()
        page.screenshot(path=str(output / (args.name+'-desktop.png')), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(output / (args.name+'-mobile.png')), full_page=True)
        assert not errors, errors
        assert not failures, failures
        result = {'passed': True, 'url': args.url, 'rock_drag_rotate_height': True,
            'presets_checked': presets_checked,
            'development_partial_suite': data['development_partial_suite'],
            'library_drag_and_drop': True,
            'crater_add_delete': True, 'sun_changed': True, 'three_plans_displayed': True,
            'export_validated': str(destination.relative_to(ROOT)), 'width_390_no_overflow': True,
            'page_errors': errors, 'http_errors': failures}
        (output / (args.name+'-browser.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps(result, ensure_ascii=False))
        browser.close()


if __name__ == '__main__':
    main()
