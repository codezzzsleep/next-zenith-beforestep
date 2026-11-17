"""Keyboard/touch validation of the game modes, objectives and personal records.

Only UI actions drive the robot. --full completes a challenge without injecting
physics state or recording a video. Requires Playwright and Chromium.
"""
import argparse
import asyncio
import json
import os
import traceback
from pathlib import Path
from playwright.async_api import async_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='https://codezzzsleep.github.io/next-zenith-beforestep')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--chromium', default=os.environ.get('BEFORESTEP_CHROMIUM'))
parser.add_argument('--full', action='store_true')
args = parser.parse_args()
folder = args.output.parent
folder.mkdir(parents=True, exist_ok=True)
base = args.url.rstrip('/')
result = {'checks': [], 'errors': [], 'scope': 'New playable game and owner-published promotion; separate from research'}


def save():
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


def check(name, data=None):
    result['checks'].append({'name': name, 'data': data})
    save()
    print(name, json.dumps(data, ensure_ascii=False)[:250], flush=True)


async def wait_ready(page):
    await page.wait_for_function('window.BeforeStepGame?.state && document.documentElement.dataset.missionReady', timeout=90000)


async def panel_mode(page, mode, touch=False):
    if touch:
        await page.locator('#gameplay-open').tap()
        await page.locator(f'[data-game-mode="{mode}"]').tap()
    else:
        await page.locator('#gameplay-open').click()
        await page.locator(f'[data-game-mode="{mode}"]').click()
    await page.wait_for_function(f'BeforeStepGame.state.gameMode==="{mode}" && BeforeStepGame.state.x<2.4 && !BeforeStepGame.state.paused')


async def turn_model(page, touch=False):
    await page.wait_for_function('document.querySelector("#raw-model").loaded', timeout=90000)
    if touch:
        await page.locator('#model-back').tap()
    else:
        await page.locator('#model-back').click()
    await page.wait_for_function('BeforeStepGame.state.showcase.stage==="model-seen"', timeout=30000)


async def desktop(browser):
    context = await browser.new_context(viewport={'width': 1280, 'height': 800}, permissions=['clipboard-read', 'clipboard-write'])
    page = await context.new_page()
    page.on('pageerror', lambda error: result['errors'].append(str(error)))
    await page.goto(base + '/play.html', wait_until='domcontentloaded')
    await wait_ready(page)
    assert await page.locator('#mission-route li').count() == 4
    assert await page.evaluate('document.documentElement.scrollWidth===innerWidth')
    check('desktop_four_goal_stages')
    await page.locator('#gameplay-open').click()
    await page.wait_for_function('BeforeStepGame.state.paused')
    assert await page.locator('#gameplay-panel').is_visible()
    await page.screenshot(path=str(folder / 'desktop-modes.jpg'), type='jpeg', quality=55)
    await page.locator('#gameplay-close').click()
    await page.wait_for_function('!BeforeStepGame.state.paused')
    check('mode_panel_pauses_and_resumes_actual_simulation')
    await panel_mode(page, 'challenge')
    assert await page.evaluate('BeforeStepGame.state.checkpoint===null && BeforeStepGame.game.mode==="challenge"')
    await panel_mode(page, 'explore')
    check('both_modes_start_new_rounds_without_old_proof')
    await page.keyboard.down('w')
    await page.wait_for_function('BeforeStepGame.state.showcase.stage==="observe"', timeout=60000, polling=100)
    await page.keyboard.up('w')
    assert await page.evaluate('BeforeStepGame.state.checkpoint.id==="observation" && !BeforeStepGame.state.proof')
    await turn_model(page)
    await page.locator('#manual-continue').click()
    await page.wait_for_function('BeforeStepGame.state.showcase.completed')
    await page.keyboard.down('w')
    await page.wait_for_timeout(1500)
    await page.keyboard.up('w')
    await page.keyboard.down(' ')
    await page.wait_for_timeout(650)
    await page.keyboard.up(' ')
    assert await page.evaluate('BeforeStepGame.game.manualMeters>.6 && document.documentElement.dataset.modelCarry==="true"')
    await page.screenshot(path=str(folder / 'desktop-manual.jpg'), type='jpeg', quality=55)
    check('manual_real_motion_keeps_original_3d_visible')
    await page.keyboard.down('w')
    await page.wait_for_function('BeforeStepGame.state.phase==="failed"', timeout=60000, polling=100)
    await page.keyboard.up('w')
    assert await page.locator('#result-checkpoint').is_visible()
    assert await page.evaluate('BeforeStepGame.game.recordCount===0 && !BeforeStepGame.game.completed')
    await page.screenshot(path=str(folder / 'failed-checkpoint.jpg'), type='jpeg', quality=55)
    check('actual_collision_offers_fast_retry_without_completed_record')
    await page.locator('#result-checkpoint').click()
    await page.wait_for_function('BeforeStepGame.state.showcase.stage==="observe" && BeforeStepGame.game.checkpointUses===1')
    assert await page.evaluate('!BeforeStepGame.state.proof && !BeforeStepGame.state.gateProof && BeforeStepGame.state.x<2.9')
    check('keyboard_retry_restores_checkpoint_and_clears_certificates')
    selected = await page.evaluate('BeforeStepGame.selected')
    await page.locator('#gameplay-open').click()
    await page.locator('#new-hypotheses').click()
    await page.wait_for_function('BeforeStepGame.state.showcase.stage==="approach" && BeforeStepGame.game.checkpointUses===0')
    new_selected = await page.evaluate('BeforeStepGame.selected')
    assert new_selected != selected
    check('new_round_changes_real_selected_hypothesis', {'before': selected, 'after': new_selected})
    if args.full:
        # Return to the default published combination for a comparable full check.
        await page.goto(base + '/play.html?mode=challenge', wait_until='domcontentloaded')
        await wait_ready(page)
        await page.keyboard.down('w')
        await page.wait_for_function('BeforeStepGame.state.showcase.stage==="observe"', timeout=60000, polling=100)
        await page.keyboard.up('w')
        await turn_model(page)
        await page.locator('#preview').click()
        await page.wait_for_function('BeforeStepGame.state.proof?.passed && BeforeStepGame.state.proof.usable', timeout=420000, polling=100)
        await page.locator('#execute').click()
        await page.wait_for_function('BeforeStepGame.state.automatic')
        check('challenge_executes_actual_two_world_rehearsal')
        await page.wait_for_function('BeforeStepGame.state.phase==="gate" && !BeforeStepGame.state.automatic', timeout=420000, polling=100)
        await page.wait_for_function('BeforeStepGame.state.stable')
        await page.locator('#think').click()
        if '高石 A' in await page.locator('#target-label').inner_text():
            await page.locator('#compare').click()
        await page.wait_for_function('document.querySelector("#raw-model").loaded')
        await page.locator('#model-back').click()
        await page.wait_for_function('BeforeStepGame.game.badges.some(b=>b.id==="observer"&&b.earned)', timeout=30000)
        await page.locator('#brain-close').click()
        check('two_original_model_turns_earn_observer_mark')
        await page.locator('#gate-preview').click()
        await page.wait_for_function('BeforeStepGame.state.gateProof?.passed', timeout=420000, polling=100)
        await page.locator('#brain-cross').click()
        for index in range(12):
            await page.wait_for_function('BeforeStepGame.state.legs?.waiting && !BeforeStepGame.state.legs.busy && (BeforeStepGame.state.legs.waiting.action!=="lift"||BeforeStepGame.state.stable)', timeout=120000, polling=100)
            waiting = await page.evaluate('BeforeStepGame.state.legs.waiting')
            await page.wait_for_function(f'!document.querySelector("[data-action=\\"{waiting["action"]}\\"]").disabled')
            await page.keyboard.press({'lift': 'j', 'advance': 'k', 'land': 'l'}[waiting['action']])
            await page.wait_for_function(f'BeforeStepGame.state.actionCount==={index + 1}')
        await page.wait_for_function('BeforeStepGame.state.phase==="finish-drive"', timeout=120000)
        await page.locator('#wheel-mode').click()
        await page.wait_for_function('!BeforeStepGame.state.legs')
        await page.keyboard.down('w')
        await page.wait_for_function('BeforeStepGame.state.phase==="complete"', timeout=60000, polling=100)
        await page.keyboard.up('w')
        await page.wait_for_function('BeforeStepGame.game.completed && BeforeStepGame.game.recordCount===1')
        game = await page.evaluate('BeforeStepGame.game')
        assert game['actions'] == 12 and game['checkpointUses'] == 0 and game['worlds'] == 2
        assert game['score'] == 100 and all(b['earned'] for b in game['badges'])
        assert await page.locator('#result').is_visible()
        await page.screenshot(path=str(folder / 'challenge-complete.jpg'), type='jpeg', quality=55)
        check('full_keyboard_challenge_complete_with_six_marks_and_local_record', game)
        await page.locator('#copy-game-result').click()
        text = await page.evaluate('navigator.clipboard.readText()')
        assert '100/100' in text and 'b23.tv/4CAPaLu' in text
        await page.reload(wait_until='domcontentloaded')
        await wait_ready(page)
        await page.locator('#gameplay-open').click()
        assert '100 分' in await page.locator('#personal-records').inner_text()
        check('completed_record_survives_reload_and_copy_contains_real_result')
    await page.goto(base + '/index.html', wait_until='domcontentloaded')
    await page.wait_for_function('document.documentElement.dataset.homeReady==="true"')
    assert await page.locator('.bilibili-primary [data-primary-video]').get_attribute('href') == 'https://b23.tv/4CAPaLu'
    assert not await page.locator('#archive-demo').evaluate('(e)=>e.open')
    assert '主报告 V3' in await page.locator('.bilibili-primary').inner_text()
    await page.locator('.bilibili-primary').screenshot(path=str(folder / 'bilibili-primary.jpg'), type='jpeg', quality=55)
    assert await page.evaluate('document.documentElement.scrollWidth===innerWidth')
    check('home_prefers_bilibili_and_v3_and_keeps_complete_demo_archive')
    await context.close()


async def mobile(browser):
    context = await browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=1)
    page = await context.new_page()
    page.on('pageerror', lambda error: result['errors'].append(str(error)))
    await page.goto(base + '/play.html', wait_until='domcontentloaded')
    await wait_ready(page)
    assert await page.evaluate('document.documentElement.scrollWidth===innerWidth')
    await page.locator('#gameplay-open').tap()
    assert await page.locator('#gameplay-panel').is_visible()
    bounds = await page.locator('#gameplay-panel').bounding_box()
    assert bounds['x'] >= 0 and bounds['x'] + bounds['width'] <= 390
    await page.screenshot(path=str(folder / 'mobile-modes.jpg'), type='jpeg', quality=55)
    await page.locator('[data-game-mode="challenge"]').tap()
    await page.wait_for_function('BeforeStepGame.state.gameMode==="challenge" && !BeforeStepGame.state.paused')
    await panel_mode(page, 'explore', touch=True)
    check('mobile_touch_mode_choices_and_panel_fit')
    cdp = await context.new_cdp_session(page)
    box = await page.locator('#joystick').bounding_box()
    finger = {'x': box['x'] + box['width'] / 2, 'y': box['y'] + box['height'] / 2 - box['width'] * .32}
    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [finger]})
    await page.wait_for_function('BeforeStepGame.state.showcase.stage==="observe"', timeout=60000, polling=100)
    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    await turn_model(page, touch=True)
    await page.screenshot(path=str(folder / 'mobile-observation.jpg'), type='jpeg', quality=55)
    await page.locator('#manual-continue').tap()
    await page.wait_for_function('document.documentElement.dataset.modelCarry==="true"')
    await page.screenshot(path=str(folder / 'mobile-manual.jpg'), type='jpeg', quality=55)
    assert await page.evaluate('document.documentElement.scrollWidth===innerWidth')
    check('touch_driving_mandatory_original_model_and_carry_remain_playable')
    await page.locator('#reset').tap()
    await page.wait_for_function('BeforeStepGame.game.checkpointUses===1 && BeforeStepGame.state.showcase.stage==="observe"')
    assert await page.evaluate('!BeforeStepGame.state.proof && !BeforeStepGame.state.gateProof')
    check('touch_checkpoint_retry_clears_old_proof')
    await page.goto(base + '/index.html', wait_until='domcontentloaded')
    await page.wait_for_function('document.documentElement.dataset.homeReady==="true"')
    assert await page.evaluate('document.documentElement.scrollWidth===innerWidth')
    check('mobile_home_bilibili_entry_has_no_horizontal_overflow')
    await context.close()


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, executable_path=args.chromium, args=['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'])
        try:
            await desktop(browser)
            await mobile(browser)
        except Exception as error:
            result['failure'] = str(error)
            result['traceback'] = traceback.format_exc()
            for context in browser.contexts:
                for page in context.pages:
                    try:
                        result['failure_state'] = await page.evaluate('({url:location.href,state:window.BeforeStepGame?.state,game:window.BeforeStepGame?.game,controls:[...document.querySelectorAll("[data-action]")].map(b=>({action:b.dataset.action,disabled:b.disabled}))})')
                        await page.screenshot(path=str(folder / 'failure.jpg'), type='jpeg', quality=55)
                    except Exception:
                        pass
            print(str(error), flush=True)
        finally:
            await browser.close()
        result['passed'] = not result.get('failure') and not result['errors']
        result['full_challenge_requested'] = args.full
        result['limits'] = ['Software WebGL; mobile uses real touch-event emulation, not a physical handset benchmark', 'Scores and records describe this game, not original research or the judges score']
        save()
        print(json.dumps({'passed': result['passed'], 'checks': len(result['checks']), 'errors': result['errors'], 'output': str(args.output)}, ensure_ascii=False), flush=True)


asyncio.run(main())
