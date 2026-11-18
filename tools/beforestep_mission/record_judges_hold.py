import asyncio,json,os,time,traceback
from pathlib import Path
import record_judges_demo as mother
from playwright.async_api import async_playwright
ROOT=mother.ROOT
OUT=mother.args.out or ROOT/'recording-hold';OUT.mkdir(exist_ok=True)
mother.OUT=OUT
async def main():
 report={'passed':False,'code_commit':os.environ.get('BEFORESTEP_RECORD_CODE'),'scope':'Current playable branch: changed selection and real supplemental observation invalidate old permission; player chooses to stop. This is not the frozen R3 automatic insufficient-evidence stop.','chapters':[],'page_errors':[],'pose_injected':False,'resolution':[1920,1080],'audio':'silent stereo track'}
 def save():(OUT/'recording.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=mother.CHROME,headless=True,args=['--no-sandbox','--enable-gpu','--ignore-gpu-blocklist','--disable-dev-shm-usage','--use-gl=angle','--use-angle=gl-egl'])
  context=await browser.new_context(viewport={'width':1920,'height':1080},device_scale_factor=1)
  page=await context.new_page();page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
  await mother.pointer(page);await mother.mirror_assets(page,ROOT)
  controls=mother.Controls(page);capture=mother.Capture(page)
  async def chapter(name):
   state=await page.evaluate('window.BeforeStepGame?.state||null');report['chapters'].append({'name':name,'video_seconds':capture.seconds(),'sim_seconds':state.get('elapsed') if state else None,'state':state});save();print(name,round(capture.seconds(),2),flush=True)
  try:
   await capture.start();await page.goto(mother.ENTRY,wait_until='domcontentloaded',timeout=90000)
   await chapter('ordinary_entry')
   await page.wait_for_function('window.BeforeStepGame?.state && !document.querySelector("#begin-mission").disabled',timeout=240000)
   await controls.click('#begin-mission');await controls.drive_until("BeforeStepGame.state.showcase.stage==='observe' && BeforeStepGame.state.paused")
   await page.wait_for_function('BeforeStepGame.state.judgmentReady',timeout=15000)
   await controls.click('[data-judgment="unsure"]');await controls.click('#decision-imagine')
   await page.wait_for_function('document.querySelector("#raw-model").loaded',timeout=180000)
   await controls.click('#both-hypotheses');await controls.click('[data-policy="imagination"]')
   await controls.click('#preview');await chapter('two_world_trial_start')
   before=await page.evaluate('BeforeStepGame.state')
   await page.wait_for_function('BeforeStepGame.state.proof?.usable',timeout=240000)
   after=await page.evaluate('BeforeStepGame.state');assert all(before[k]==after[k] for k in ['x','y','z','yaw','elapsed'])
   report['old_preview']=await page.evaluate('BeforeStepGame.preview');assert len(report['old_preview']['results'])==2
   await chapter('old_combination_passed_and_departure_enabled');await page.wait_for_timeout(2200)
   await controls.click('#both-hypotheses');await page.wait_for_function('!BeforeStepGame.state.proof',timeout=15000)
   assert await page.locator('#execute').is_hidden() or await page.locator('#execute').is_disabled()
   await chapter('changed_combination_revokes_departure_permission');await page.wait_for_timeout(2600)
   await controls.click('#manual-continue');await controls.drive_until('BeforeStepGame.state.yaw>.38',forward=0,turn=1)
   await controls.drive_until('BeforeStepGame.state.x>3.20');await controls.brake();await controls.click('#pause')
   await page.wait_for_function('BeforeStepGame.state.paused',timeout=15000)
   await chapter('move_on_same_approach_side_and_stop')
   version=(await page.evaluate('BeforeStepGame.state'))['observationVersion']
   await controls.click('#observe');await page.wait_for_function("BeforeStepGame.journal.events.some(e=>e.type==='observationChanged'||e.type==='observationUnchanged')",timeout=30000)
   report['supplemental']=await page.evaluate("BeforeStepGame.journal.events.filter(e=>e.type==='observationChanged'||e.type==='observationUnchanged').at(-1)")
   await chapter('real_sensor_surface_observation');await page.wait_for_timeout(2800)
   count=await page.evaluate("BeforeStepGame.journal.events.filter(e=>e.type==='observationChanged'||e.type==='observationUnchanged').length")
   await controls.click('#observe');await page.wait_for_function("BeforeStepGame.journal.events.filter(e=>e.type==='observationChanged'||e.type==='observationUnchanged').length>"+str(count),timeout=30000)
   report['repeat_observation']=await page.evaluate("BeforeStepGame.journal.events.filter(e=>e.type==='observationChanged'||e.type==='observationUnchanged').at(-1)")
   await chapter('same_angle_still_lacks_back_surface_information');await page.wait_for_timeout(2800)
   await controls.click('#think');await controls.click('#brain-hold')
   await page.wait_for_function("BeforeStepGame.state.phase==='stopped' && BeforeStepGame.state.paused",timeout=30000)
   await chapter('without_current_permission_player_holds_position')
   report['final']=await page.evaluate('BeforeStepGame.state');report['journal']=await page.evaluate('BeforeStepGame.journal')
   assert not report['final']['proof'] and report['final']['actionCount']==0 and not report['page_errors']
   async with page.expect_download() as download:await controls.click('#export-run')
   await (await download.value).save_as(str(OUT/'hold-session.json'))
   await page.wait_for_timeout(3500);report['passed']=True
  except Exception as e:
   report.update(failure=repr(e),traceback=traceback.format_exc());save();raise
  finally:
   await capture.stop();save();await context.close();await browser.close()
  (OUT/'00-full-run.mp4').rename(OUT/'04b-hold.mp4')
 print(json.dumps({'passed':report['passed'],'chapters':len(report['chapters']),'final':report.get('final')},ensure_ascii=False),flush=True)
asyncio.run(main())
