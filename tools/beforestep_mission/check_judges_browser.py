"""Exercise the ordinary playable entry with real keyboard or touch input.

No robot pose or worker proof is injected. An optional asset mirror serves
identical frozen bytes for development; public acceptance omits --asset-root.
"""
import argparse
import asyncio
import json
import time
import traceback
from pathlib import Path
from playwright.async_api import async_playwright

ORIGINAL_BASE = "https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/3e4acf64d18e638d0c1342793fc367ed92955135/"

async def mirror_assets(page, root):
    async def handle(route):
        url = route.request.url
        if "BeforeStep-startup-cdn-assets-20261118.zip" in url:
            data = (root / "startup-cdn.zip").read_bytes()
            headers = {"Access-Control-Allow-Origin": "*", "Accept-Ranges": "bytes", "Content-Type": "application/zip"}
            byte_range = route.request.headers.get("range")
            if byte_range:
                a, b = byte_range.removeprefix("bytes=").split("-")
                a, b = int(a), int(b) if b else len(data)-1
                headers["Content-Range"] = f"bytes {a}-{b}/{len(data)}"
                await route.fulfill(status=206, headers=headers, body=data[a:b+1])
            else:
                await route.fulfill(status=200, headers=headers, body=data)
        elif url.startswith(ORIGINAL_BASE) and (root / url.split(ORIGINAL_BASE, 1)[1].split("?", 1)[0]).is_file():
            await route.fulfill(path=str(root / url.split(ORIGINAL_BASE, 1)[1].split("?", 1)[0]),
                                headers={"Access-Control-Allow-Origin": "*"})
        else:
            await route.continue_()
    await page.route("**/*", handle)

class Controls:
    def __init__(self, page, touch=False):
        self.page, self.touch = page, touch
        self.cdp = None

    async def click(self, selector):
        locator = self.page.locator(selector)
        if self.touch:
            await locator.tap()
        else:
            await locator.click()

    async def direction(self, forward=0, turn=0):
        if self.touch:
            self.cdp = self.cdp or await self.page.context.new_cdp_session(self.page)
            await self.page.locator("#joystick").wait_for(state="visible", timeout=30000)
            box = await self.page.locator("#joystick").bounding_box()
            await self.cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{
                "id": 1, "x": box["x"]+box["width"]/2-turn*box["width"]*.28,
                "y": box["y"]+box["height"]/2-forward*box["height"]*.28,
            }]})
        else:
            await self.page.locator("#world").focus()
            for key in (["w"] if forward else [])+(["a"] if turn > 0 else ["d"] if turn < 0 else []):
                await self.page.keyboard.down(key)

    async def release(self):
        if self.touch and self.cdp:
            await self.cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        else:
            for key in ["w", "a", "d"]:
                await self.page.keyboard.up(key)

    async def brake(self):
        if self.touch:
            self.cdp = self.cdp or await self.page.context.new_cdp_session(self.page)
            box = await self.page.locator("#touch-brake").bounding_box()
            await self.cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{
                "id": 2, "x": box["x"]+box["width"]/2, "y": box["y"]+box["height"]/2,
            }]})
        else:
            await self.page.keyboard.down(" ")
        await self.page.wait_for_function("BeforeStepGame.state.stable && BeforeStepGame.state.speed<.008", timeout=30000)
        if self.touch:
            await self.cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        else:
            await self.page.keyboard.up(" ")

    async def drive_until(self, condition, forward=1, turn=0, timeout=60000):
        await self.direction(forward, turn)
        try:
            await self.page.wait_for_function(condition, timeout=timeout)
        finally:
            await self.release()

async def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    width, height = (390, 844) if args.touch else (1920, 1080)
    report = {"passed": False, "checks": [], "page_errors": [], "pose_injected": False,
              "viewport": [width, height], "touch_simulation": args.touch,
              "physical_phone_test": False, "asset_mirror": bool(args.asset_root),
              "url": args.url, "scope": "Current interactive mission; separate from frozen R1/R2/R3"}
    def save():
        (out / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    def passed(name):
        report["checks"].append(name); save(); print(name, flush=True)
    async with async_playwright() as p:
        flags = ["--no-sandbox", "--disable-dev-shm-usage"]
        flags += ["--enable-gpu", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=gl-egl"] if args.gpu else ["--enable-unsafe-swiftshader", "--use-angle=swiftshader"]
        browser = await p.chromium.launch(executable_path=args.chromium, headless=True, args=flags)
        context = await browser.new_context(viewport={"width": width, "height": height},
                                            device_scale_factor=1, is_mobile=args.touch, has_touch=args.touch)
        page = await context.new_page()
        page.on("pageerror", lambda e: report["page_errors"].append(str(e)))
        controls = Controls(page, args.touch)
        if args.asset_root:
            await mirror_assets(page, Path(args.asset_root))
        async def shot(name):
            await page.screenshot(path=str(out/(name+".jpg")), type="jpeg", quality=86, timeout=30000)
        async def state():
            return await page.evaluate("BeforeStepGame.state")
        try:
            started = time.monotonic()
            await page.goto(args.url, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_function("window.BeforeStepGame?.state && !document.querySelector('#begin-mission').disabled", timeout=240000)
            report["startup_seconds"] = time.monotonic()-started
            report["renderer"] = await page.evaluate("()=>{const g=document.querySelector('#world').getContext('webgl2');return g.getParameter(g.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL)}")
            if args.gpu:
                assert "NVIDIA" in report["renderer"]
            assert await page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
            await shot("01-goal")
            await controls.click("#begin-mission")
            await controls.drive_until("BeforeStepGame.state.showcase.stage==='observe' && BeforeStepGame.state.paused")
            await page.wait_for_function("BeforeStepGame.state.judgmentReady", timeout=15000)
            assert await page.locator("#brain").is_hidden()
            assert not await page.locator("#raw-model").get_attribute("src")
            checkpoint = await state()
            await shot("02-first-look")
            await controls.click('[data-judgment="pass"]')
            await controls.click("#decision-manual")
            await controls.drive_until("BeforeStepGame.state.x>3.04")
            await controls.brake()
            assert await page.locator("#brain").is_hidden()
            assert not await page.locator("#raw-model").get_attribute("src")
            passed("initial_judgment_and_manual_without_Lux")

            for count in [1, 2]:
                await controls.click("#reset")
                await page.wait_for_function(f"BeforeStepGame.state.checkpointRestarts==={count} && BeforeStepGame.state.paused && !BeforeStepGame.state.initialJudgment", timeout=30000)
                restored = await state()
                assert all(restored[k] == checkpoint[k] for k in ["x", "y", "z", "yaw", "elapsed"])
                assert restored["observationVersion"] == checkpoint["observationVersion"] and not restored["proof"]
                await page.wait_for_function("BeforeStepGame.state.judgmentReady", timeout=15000)
                if count == 1:
                    await controls.click('[data-judgment="unsure"]')
                    await controls.click("#decision-manual")
                    await controls.drive_until("BeforeStepGame.state.yaw>.38", forward=0, turn=1)
                    await controls.drive_until("BeforeStepGame.state.x>3.20")
                    await controls.brake()
                    await controls.click("#pause")
                    await page.wait_for_function("BeforeStepGame.state.paused", timeout=15000)
                    before = await state()
                    await controls.click("#observe")
                    await page.wait_for_function("BeforeStepGame.journal.events.some(e=>e.type==='observationChanged'||e.type==='observationUnchanged')", timeout=30000)
                    after = await state()
                    report["supplemental_observation"] = {"before_version": before["observationVersion"], "after_version": after["observationVersion"], "measured_cells": after["measuredCells"]}
                    assert after["observationVersion"] > before["observationVersion"]
                    count_events = await page.evaluate("BeforeStepGame.journal.events.filter(e=>e.type==='observationChanged'||e.type==='observationUnchanged').length")
                    await controls.click("#observe")
                    await page.wait_for_function("BeforeStepGame.journal.events.filter(e=>e.type==='observationChanged'||e.type==='observationUnchanged').length>"+str(count_events), timeout=30000)
                    latest = await page.evaluate("BeforeStepGame.journal.events.filter(e=>e.type==='observationChanged'||e.type==='observationUnchanged').at(-1)")
                    await page.wait_for_function("BeforeStepGame.state.observationVersion==="+str(latest["detail"]["version"]),timeout=15000)
                    repeated = await state()
                    assert repeated["observationVersion"] == after["observationVersion"]+int(latest["detail"]["changed"])
                    report["repeat_observation"] = latest
                    await shot("03-supplemental")
            passed("effective_surface_observation_and_two_exact_checkpoint_restores")

            await controls.click('[data-judgment="pass"]')
            await controls.click("#decision-imagine")
            await page.wait_for_function("document.querySelector('#raw-model').loaded", timeout=180000)
            photo = await page.locator("#input-photo").get_attribute("src")
            before = await state()
            await controls.click("#model-back")
            await page.wait_for_timeout(1800)
            await controls.click("#switch-hypothesis")
            await page.wait_for_function("document.querySelector('#raw-model').loaded && BeforeStepGame.selected.includes(5958948)", timeout=180000)
            assert photo == await page.locator("#input-photo").get_attribute("src")
            current = await state()
            assert all(current[k] == before[k] for k in ["x", "y", "z", "yaw", "elapsed"])
            await controls.click("#rejected-example")
            await page.wait_for_function("document.querySelector('#raw-model').loaded", timeout=180000)
            assert 5958642 not in await page.evaluate("BeforeStepGame.selected")
            assert "未通过" in await page.locator("#pair-metrics").inner_text()
            await controls.click("#return-hypothesis")
            await page.wait_for_function("document.querySelector('#raw-model').loaded", timeout=180000)
            await controls.click("#both-hypotheses")
            await controls.click('[data-policy="imagination"]')
            await shot("04-model-and-route")
            passed("same_input_real_pair_and_rejected_inspection")

            before = await state()
            await controls.click("#preview")
            await page.wait_for_function("document.documentElement.dataset.previewBusy==='route'", timeout=30000)
            await controls.click("#cancel-preview")
            await page.wait_for_function("!BeforeStepGame.state.proof", timeout=30000)
            current = await state()
            assert all(current[k] == before[k] for k in ["x", "y", "z", "yaw", "elapsed"])
            assert await page.locator("#execute").is_hidden() or await page.locator("#execute").is_disabled()
            await controls.click("#preview")
            await page.wait_for_function("BeforeStepGame.state.proof?.usable", timeout=240000)
            proof = await page.evaluate("BeforeStepGame.preview")
            assert len(proof["expectedWorlds"]) == 2 and len(proof["results"]) == 2
            assert all(r["passed"] and r["reason"] == "completed" for r in proof["results"])
            current = await state()
            assert all(current[k] == before[k] for k in ["x", "y", "z", "yaw", "elapsed"])
            await controls.click("#both-hypotheses")
            await page.wait_for_function("!BeforeStepGame.state.proof", timeout=30000)
            assert await page.locator("#execute").is_hidden() or await page.locator("#execute").is_disabled()
            await controls.click("#both-hypotheses")
            await controls.click("#preview")
            await page.wait_for_function("BeforeStepGame.state.proof?.usable", timeout=240000)
            await shot("05-permission")
            passed("cancel_and_changed_combinations_cannot_release_stale_results")
            await controls.click("#execute")
            await page.wait_for_function("BeforeStepGame.state.automatic", timeout=30000)
            await page.wait_for_function("BeforeStepGame.state.x>3.8", timeout=90000)
            await controls.brake()
            await page.wait_for_function("!BeforeStepGame.state.automatic && BeforeStepGame.state.stable", timeout=30000)
            assert await page.evaluate("BeforeStepGame.journal.events.some(e=>e.type==='executionMode' && e.detail.takeover)")
            await controls.click("#follow")
            await page.wait_for_timeout(1000)
            if not (await state())["automatic"]:
                report["original_resume_blocked_reason"] = await page.locator("#status").inner_text()
                assert (await state())["phase"] != "failed"
                await controls.click("#think")
                await controls.click("#preview")
                await page.wait_for_function("BeforeStepGame.state.proof?.usable", timeout=240000)
                await controls.click("#execute")
                await page.wait_for_function("BeforeStepGame.state.automatic", timeout=30000)
            passed("assisted_route_manual_takeover_and_valid_rehearsed_departure")
            await page.wait_for_function("BeforeStepGame.state.x>5.3 || BeforeStepGame.state.phase==='failed'", timeout=240000)
            assert (await state())["phase"] != "failed"
            await controls.click('button[data-view="0"]')
            await shot("06-drive-reveal")
            await page.wait_for_function("BeforeStepGame.state.phase==='gate' && !BeforeStepGame.state.automatic && BeforeStepGame.state.stable", timeout=240000)
            await controls.click("#cross-direct")
            await page.wait_for_function("BeforeStepGame.state.phase==='crossing'", timeout=15000)
            for count in range(12):
                await page.wait_for_function("BeforeStepGame.state.legs?.waiting", timeout=90000)
                action = (await state())["legs"]["waiting"]["action"]
                await controls.click(f'#leg-actions [data-action="{action}"]')
                await page.wait_for_function(f"BeforeStepGame.state.actionCount>{count}", timeout=30000)
                if count == 1:
                    await shot("07-leg-action")
            await page.wait_for_function("BeforeStepGame.state.phase==='finish-drive'", timeout=180000)
            await controls.click("#wheel-mode")
            await page.wait_for_function("!BeforeStepGame.state.legs", timeout=30000)
            await controls.drive_until("BeforeStepGame.state.phase==='complete'", timeout=120000)
            await shot("08-result")
            final = await state()
            assert final["actionCount"] == 12 and final["goalDistance"] < .35
            assert "初判：" in await page.locator("#run-recap").inner_text()
            report["final"] = final
            report["run"] = await page.evaluate("BeforeStepGame.game")
            report["journal"] = await page.evaluate("BeforeStepGame.journal")
            passed("real_two_world_release_twelve_player_actions_and_arrival")
            assert not report["page_errors"], report["page_errors"]
            report["passed"] = True; save()
        except Exception as e:
            report.update(failure=repr(e), traceback=traceback.format_exc())
            try:
                report["failure_state"] = await state()
                report["failure_journal"] = await page.evaluate("BeforeStepGame.journal")
                report["failure_status"] = await page.locator("#status").inner_text()
            except Exception:
                pass
            save()
            try:
                await shot("failure")
            except Exception:
                pass
            raise
        finally:
            await context.close()
            await browser.close()
    print(json.dumps({"passed": True, "checks": report["checks"], "touch_simulation": args.touch}), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--chromium", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--touch", action="store_true")
    parser.add_argument("--asset-root")
    asyncio.run(run(parser.parse_args()))
