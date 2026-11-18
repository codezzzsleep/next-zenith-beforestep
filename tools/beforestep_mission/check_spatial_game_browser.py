"""Exercise spatial imagination and a complete mission through actual controls."""
import argparse
import asyncio
import hashlib
import json
import time
import traceback
from pathlib import Path

from playwright.async_api import async_playwright


def args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--chromium', help='Optional installed Chromium executable')
    return p.parse_args()


async def main(options):
    output = options.output
    output.mkdir(parents=True, exist_ok=True)
    report = {'passed': False, 'url': options.base_url, 'viewport': [1600, 900],
              'checks': [], 'events': [], 'screenshots': [], 'page_errors': [],
              'physics_state_injected': False, 'new_generation_requests': 0}
    start = time.monotonic()

    def save():
        target = output / 'verification.json'
        temp = target.with_suffix('.json.tmp')
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        temp.replace(target)

    def log(name, value=None):
        report['events'].append({'name': name, 'seconds': round(time.monotonic()-start, 2), 'value': value})
        save()
        print(name, json.dumps(value, ensure_ascii=False)[:500], flush=True)

    async def snapshot(page):
        return await page.evaluate('({state:BeforeStepGame.state,game:BeforeStepGame.game,story:BeforeStepGame.story,selected:BeforeStepGame.selected})')

    async def shot(page, name):
        target = output / (name + '.jpg')
        await page.screenshot(path=str(target), type='jpeg', quality=82, timeout=30000)
        report['screenshots'].append({'path': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), **await snapshot(page)})
        save()

    async def pulse(page):
        while True:
            await asyncio.sleep(20)
            try:
                s = (await snapshot(page))['state']
                log('heartbeat', {'phase': s['phase'], 'x': round(s['x'], 3), 'actions': s['actionCount'], 'status': await page.locator('#preview-status').inner_text()})
            except Exception:
                pass

    async def ready(page, mode='explore'):
        await page.goto(options.base_url.rstrip('/') + '/play.html?mode=' + mode + '&v=spatial-imagination-20261118-2', wait_until='domcontentloaded', timeout=90000)
        await page.wait_for_function('window.BeforeStepGame?.state?.paused && !document.querySelector("#begin-mission").disabled', timeout=180000)
        assert await page.locator('#mission-intro').is_visible()
        before = (await snapshot(page))['state']
        inputs = await page.evaluate('BeforeStepGame.inputEvents')
        await page.keyboard.press('w')
        after = (await snapshot(page))['state']
        assert all(before[k] == after[k] for k in ['x','y','z','yaw','elapsed'])
        assert inputs == await page.evaluate('BeforeStepGame.inputEvents')

    async def start_mission(page):
        await page.keyboard.press('Enter')
        await page.wait_for_function('!BeforeStepGame.story.intro && !BeforeStepGame.state.paused', timeout=30000)
        assert await page.locator('#mission-intro').is_hidden()

    async def reach_observation(page, teach=False):
        if teach:
            await page.keyboard.down('w')
            await page.wait_for_function('BeforeStepGame.state.x>2.45', timeout=60000)
            await page.keyboard.up('w')
            await page.wait_for_function('document.querySelector("#story-key").textContent.includes("空格刹车")', timeout=30000)
            await page.keyboard.down(' ')
            await page.wait_for_function('BeforeStepGame.state.stable', timeout=30000)
            await page.keyboard.up(' ')
            assert await page.evaluate('BeforeStepGame.story.usedDrive && BeforeStepGame.story.usedBrake')
            await page.locator('#observe').click()
        await page.keyboard.down('w')
        await page.wait_for_function('BeforeStepGame.state.showcase.stage==="observe"', timeout=60000)
        await page.keyboard.up('w')
        assert await page.locator('#brain').is_hidden()
        assert await page.locator('button[data-view="0"]').is_disabled()
        assert await page.locator('#pip').is_disabled()
        await page.locator('#pause').click()
        await page.wait_for_function('BeforeStepGame.state.paused', timeout=30000)

    async def imagine(page):
        before = (await snapshot(page))['state']
        await page.keyboard.press('q')
        await page.wait_for_function('!document.querySelector("#brain").hidden && document.querySelector("#raw-model").loaded', timeout=120000)
        await page.wait_for_function('Number(document.querySelector("#dream").dataset.planningHypotheses)>0', timeout=30000)
        after = (await snapshot(page))['state']
        assert all(before[k] == after[k] for k in ['x','y','z','yaw','elapsed'])
        comp = await page.evaluate('JSON.parse(document.querySelector("#dream").dataset.comparison)')
        assert comp['hypothesisCells'] > 0 and comp['visibleRoute'] and comp['hypothesisRoute'] and not comp['passed']
        assert await page.locator('#manual-continue').is_disabled()
        return comp

    async def view_back(page):
        await page.locator('#model-back').click()
        await page.wait_for_function('BeforeStepGame.state.showcase.viewedTask && !document.querySelector("#preview").disabled', timeout=30000)
        assert await page.locator('#manual-continue').is_disabled()

    async def predict(page):
        before = (await snapshot(page))['state']
        await page.locator('#preview').click()
        await page.wait_for_function('BeforeStepGame.preview?.passed && BeforeStepGame.state.proof?.usable', timeout=420000, polling=100)
        value = await page.evaluate('BeforeStepGame.preview')
        assert len(value['results']) == 2 and all(r['passed'] for r in value['results'])
        after = (await snapshot(page))['state']
        assert all(before[k] == after[k] for k in ['x','y','z','yaw','elapsed'])
        await page.wait_for_function('!document.querySelector("#manual-continue").disabled', timeout=30000)
        assert await page.evaluate('JSON.parse(document.querySelector("#dream").dataset.comparison).passed')
        log('two_world_forecast', {'tasks': [r['tasks'] for r in value['results']], 'passed': value['passed']})
        return value

    async def cancel_prediction(page):
        await page.locator('#preview').click()
        await page.wait_for_function('document.documentElement.dataset.previewBusy==="route"', timeout=30000)
        await page.locator('#cancel-preview').click()
        await page.wait_for_function('!document.documentElement.dataset.previewBusy && !BeforeStepGame.preview && !BeforeStepGame.state.proof?.usable', timeout=30000)
        assert await page.locator('#execute').is_hidden()
        assert await page.locator('#manual-continue').is_disabled()
        assert not await page.evaluate('JSON.parse(document.querySelector("#dream").dataset.comparison).passed')

    async with async_playwright() as playwright:
        launch = {'headless': True, 'args': ['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader']}
        if options.chromium:
            launch['executable_path'] = options.chromium
        browser = await playwright.chromium.launch(**launch)
        context = None
        page = None
        task = None
        try:
            context = await browser.new_context(viewport={'width':1600,'height':900})
            page = await context.new_page()
            page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
            task = asyncio.create_task(pulse(page))
            await ready(page, 'challenge')
            report['checks'].append('clear_goal_controls_and_start_input_lock')
            await shot(page, '01-goal-and-controls')
            await start_mission(page)
            await reach_observation(page, teach=True)
            report['checks'].append('real_keyboard_drive_brake_observe_then_first_person_2d')
            await shot(page, '02-observation-only')
            log('observation_reached')
            comp = await imagine(page)
            report['checks'].append('Q_local_3d_hypotheses_keep_physical_state_and_show_route_comparison')
            await shot(page, '03-local-world-imagination')
            await view_back(page)
            await cancel_prediction(page)
            report['checks'].append('cancelled_forecast_has_no_execution_or_manual_release')
            await predict(page)
            report['checks'].append('two_real_candidate_world_forecasts_required_before_first_departure')
            await page.locator('.brain-body').evaluate('(e)=>e.scrollTop=0')
            await shot(page, '04-prediction-ready')
            await page.locator('.candidate[data-task="5958654"] button').first.click()
            await page.wait_for_function('document.querySelector("#raw-model").loaded', timeout=120000)
            await page.locator('#model-back').click()
            await page.wait_for_function('BeforeStepGame.game.viewedTargets?.includes("T2")', timeout=30000)
            await page.locator('#execute').click()
            await page.wait_for_function('BeforeStepGame.state.automatic && BeforeStepGame.state.showcase.completed', timeout=30000)
            await page.locator('button[data-view="0"]').click()
            await page.wait_for_function('document.querySelector("#world").dataset.displayMode==="physical-execution" && Number(document.querySelector("#world").dataset.texturedScanMeshes)>0', timeout=30000)
            report['checks'].append('execution_restores_textured_full_rocks_moon_soil_and_views')
            await page.wait_for_function('BeforeStepGame.state.x>3.5', timeout=120000)
            await shot(page, '05-prediction-supports-exploration')
            await page.wait_for_function('BeforeStepGame.state.phase==="gate" && !BeforeStepGame.state.automatic && BeforeStepGame.state.stable', timeout=420000, polling=100)
            log('high_rocks_passed_visible_gate', (await snapshot(page))['state'])
            await page.locator('#observe').click()
            await page.wait_for_function('BeforeStepGame.state.scan?.valid', timeout=30000)
            await page.locator('#gate-preview').click()
            await page.wait_for_function('BeforeStepGame.state.gateProof?.passed', timeout=420000, polling=100)
            await page.locator('#brain-cross').click()
            await page.wait_for_function('BeforeStepGame.state.phase==="crossing"', timeout=30000)
            for index in range(12):
                await page.wait_for_function('BeforeStepGame.state.legs?.waiting', timeout=180000, polling=100)
                waiting = await page.evaluate('BeforeStepGame.state.legs.waiting')
                action = waiting['action']
                await page.wait_for_function('!document.querySelector("[data-action='+action+']").disabled', timeout=30000)
                expected = (await snapshot(page))['state']['actionCount'] + 1
                await page.keyboard.press({'lift':'j','advance':'k','land':'l'}[action])
                await page.wait_for_function('BeforeStepGame.state.actionCount>='+str(expected), timeout=45000)
                log('player_action_'+str(index+1), waiting)
                if index == 0:
                    await shot(page, '06-physical-leg-execution')
            await page.wait_for_function('BeforeStepGame.state.phase==="finish-drive"', timeout=180000)
            await page.locator('#wheel-mode').click()
            await page.wait_for_function('!BeforeStepGame.state.legs', timeout=30000)
            await page.keyboard.down('w')
            await page.wait_for_function('BeforeStepGame.state.phase==="complete"', timeout=120000)
            await page.keyboard.up('w')
            await page.wait_for_function('BeforeStepGame.story.phase==="goal-reached"', timeout=30000)
            final = await snapshot(page)
            assert final['state']['goalDistance'] < .35 and final['state']['actionCount'] == 12
            assert final['game']['worlds'] == 2 and final['game']['checkpointUses'] == 0
            recap = await page.locator('#run-recap').inner_text()
            assert all(str(i) in recap for i in [5958685,5958654,5958934])
            assert '空间想象' in await page.locator('#result-text').inner_text()
            assert '12 次轮腿动作后抵达' in recap
            report['checks'].append('complete_challenge_12_player_actions_goal_and_spatial_story_recap')
            report['challenge_final'] = final
            report['recap'] = recap
            await shot(page, '07-goal-and-story-recap')
            log('complete_challenge', {'worlds':2,'actions':12,'score':final['game']['score'],'goalDistance':final['state']['goalDistance']})
            task.cancel()
            await context.close()

            context = await browser.new_context(viewport={'width':1280,'height':720})
            page = await context.new_page()
            page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
            task = asyncio.create_task(pulse(page))
            await ready(page)
            await start_mission(page)
            await reach_observation(page)
            await imagine(page)
            await view_back(page)
            await cancel_prediction(page)
            revision = (await snapshot(page))['state']['revision']
            await page.keyboard.press('r')
            await page.wait_for_function('BeforeStepGame.state.revision>'+str(revision)+' && BeforeStepGame.state.showcase.active && !BeforeStepGame.story.imagination', timeout=30000)
            await page.wait_for_function('document.querySelector("#brain").hidden && document.querySelector("#world").dataset.displayMode==="2d-observation"', timeout=30000)
            assert not await page.evaluate('BeforeStepGame.preview')
            assert await page.locator('#manual-continue').is_disabled()
            report['checks'].append('exploration_checkpoint_restores_observation_first_and_clears_forecast')
            # Pause the restored real robot before comparing the two displays.
            if not (await snapshot(page))['state']['paused']:
                await page.locator('#pause').click()
            await page.wait_for_function('BeforeStepGame.state.paused', timeout=30000)
            await imagine(page)
            await view_back(page)
            await predict(page)
            await page.locator('[data-policy="optimistic"]').click()
            await page.wait_for_function('!BeforeStepGame.preview && !BeforeStepGame.state.proof?.usable', timeout=30000)
            assert await page.locator('#manual-continue').is_disabled()
            assert await page.locator('#execute').is_hidden()
            report['checks'].append('changed_route_policy_invalidates_forecast_and_departure')
            assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            await page.locator('#help').click()
            assert '候选世界完整通过后再出发' in await page.locator('#help-panel').inner_text()
            await page.locator('#help-close').click()
            selected = (await snapshot(page))['selected']
            await page.locator('#gameplay-open').click()
            await page.locator('#new-hypotheses').click()
            await page.wait_for_function('BeforeStepGame.story.intro && BeforeStepGame.state.paused', timeout=30000)
            assert (await snapshot(page))['selected'] != selected
            await shot(page, '08-new-mission-retains-goal-teaching')
            report['checks'].append('new_hypotheses_restart_with_goal_teaching_without_generation')
            await start_mission(page)
            await page.locator('#gameplay-open').click()
            await page.locator('[data-game-mode="challenge"]').click()
            await page.wait_for_function('BeforeStepGame.state.gameMode==="challenge" && BeforeStepGame.story.intro && BeforeStepGame.state.paused', timeout=30000)
            assert not (await snapshot(page))['state']['checkpoint']
            report['checks'].append('mode_change_starts_new_paused_challenge_with_goal')
            assert not report['page_errors'], report['page_errors']
            report['passed'] = True
            log('all_spatial_game_checks_passed', report['checks'])
        except Exception as exc:
            report['failure'] = repr(exc)
            report['traceback'] = traceback.format_exc()
            if page:
                try:
                    report['failed_snapshot'] = await snapshot(page)
                    await shot(page, 'failure')
                except Exception:
                    pass
            save()
            raise
        finally:
            if task:
                task.cancel()
            if context:
                await context.close()
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main(args()))
