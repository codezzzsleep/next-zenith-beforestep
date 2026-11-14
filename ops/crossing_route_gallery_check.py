"""Check the optional official viewer through the existing gallery UI."""
import argparse
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from ops.crossing_check import Handler
from playwright.sync_api import sync_playwright


def check(url, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path='/root/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome', headless=True,
            args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        for width, height in [(1440, 1000), (390, 844)]:
            page = browser.new_page(viewport={'width': width, 'height': height})
            errors, failed = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
            page.on('response', lambda response: failed.append(response.url) if response.status >= 400 else None)
            page.goto(url + 'gallery.html', wait_until='networkidle', timeout=90000)
            page.wait_for_function('document.documentElement.dataset.galleryReady === "true"')
            page.locator('#gallery-load').click()
            page.wait_for_function('document.querySelector("#gallery-model").loaded === true', timeout=90000)
            model = page.locator('#gallery-model')
            model.scroll_into_view_if_needed()
            box = model.bounding_box()
            before = model.evaluate('(element)=>element.yaw')
            page.mouse.move(box['x'] + box['width'] * .7, box['y'] + box['height'] / 2)
            page.mouse.down()
            page.mouse.move(box['x'] + box['width'] * .3, box['y'] + box['height'] / 2, steps=20)
            page.mouse.up()
            page.wait_for_timeout(400)
            assert model.evaluate('(element)=>element.yaw') != before
            first_src = model.evaluate('(element)=>element.src')
            first_canvas = str(output / f'{width}-first-model.png')
            model.screenshot(path=first_canvas)
            page.locator('[data-task]').nth(1).click()
            page.wait_for_function('(first)=>document.querySelector("#gallery-model").loaded === true && document.querySelector("#gallery-model").src !== first', arg=first_src, timeout=90000)
            model.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            model.screenshot(path=str(output / f'{width}-second-model.png'))
            assert model.locator('canvas').count() == 1
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not errors, errors
            assert not failed, failed
            checks.append({'viewport': [width, height], 'official_element': model.evaluate('(e)=>e.tagName'),
                           'two_original_models_loaded': True, 'pointer_rotation': True,
                           'horizontal_overflow': False, 'console_errors': errors, 'http_errors': failed})
            page.close()
        browser.close()
    result = {'passed': True, 'url': url, 'checks': checks}
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url')
    parser.add_argument('--out', required=True)
    arguments = parser.parse_args()
    if arguments.url:
        check(arguments.url, arguments.out)
    else:
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            check(f'http://127.0.0.1:{server.server_port}/', arguments.out)
        finally:
            server.shutdown()
            server.server_close()
