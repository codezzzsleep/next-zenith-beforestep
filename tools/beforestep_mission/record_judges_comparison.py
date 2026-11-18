"""Record a clear, fixed-scale comparison at an actual observation checkpoint."""
import asyncio,json,os,traceback
from pathlib import Path
import record_judges_demo as mother
from playwright.async_api import async_playwright
ROOT=mother.ROOT
OUT=mother.args.out or ROOT/'recording-comparison'
OUT.mkdir(exist_ok=True);mother.OUT=OUT
async def main():
 report={'passed':False,'code_commit':os.environ.get('BEFORESTEP_RECORD_CODE'),'scope':'Current real UI supplement: original photo, same-input real candidates and registered local map. Independent observation checkpoint; no replay or pose injection.','chapters':[],'still_times':{},'page_errors':[],'pose_injected':False,'resolution':[1920,1080],'audio':'silent stereo track'}
 def save():(OUT/'recording.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=mother.CHROME,headless=True,args=['--no-sandbox','--enable-gpu','--ignore-gpu-blocklist','--disable-dev-shm-usage','--use-gl=angle','--use-angle=gl-egl'])
  context=await browser.new_context(viewport={'width':1920,'height':1080},device_scale_factor=1)
  page=await context.new_page();page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
  await mother.pointer(page);await mother.mirror_assets(page,ROOT)
  controls=mother.Controls(page);capture=mother.Capture(page)
  async def chapter(name):
   state=await page.evaluate('window.BeforeStepGame?.state||null');report['chapters'].append({'name':name,'video_seconds':capture.seconds(),'sim_seconds':state.get('elapsed') if state else None,'state':state,'map':await page.evaluate("()=>{try{return JSON.parse(document.querySelector('#dream')?.dataset.comparison||'null')}catch{return null}}")});save();print(name,round(capture.seconds(),2),flush=True)
  async def still(name):
   await page.mouse.move(30,210);await page.wait_for_timeout(1000)
   report['still_times'][name]={'video_seconds':capture.seconds(),'state':await page.evaluate('BeforeStepGame.state'),'selected':await page.evaluate('BeforeStepGame.selected'),'map':await page.evaluate("JSON.parse(document.querySelector('#dream').dataset.comparison)"),'canvas':await page.evaluate("()=>[document.querySelector('#world').width,document.querySelector('#world').height]"),'photo_source':await page.locator('#input-photo').get_attribute('src')};save()
  async def visible_map():
   rect=await page.locator('#dream').bounding_box();body=await page.locator('#brain .brain-body').bounding_box()
   ratio=max(0,min(rect['y']+rect['height'],body['y']+body['height'])-max(rect['y'],body['y']))/rect['height']
   assert ratio>.93,(rect,body,ratio)
   return {'canvas':rect,'body':body,'visible_ratio':ratio}
  try:
   await capture.start();await page.goto(mother.ENTRY,wait_until='domcontentloaded',timeout=90000)
   await chapter('ordinary_entry')
   await page.wait_for_function('window.BeforeStepGame?.state && !document.querySelector("#begin-mission").disabled',timeout=240000)
   report['renderer']=await page.evaluate("()=>{const g=document.querySelector('#world').getContext('webgl2');return g.getParameter(g.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL)}");assert 'NVIDIA' in report['renderer']
   await controls.click('#begin-mission');await controls.drive_until("BeforeStepGame.state.showcase.stage==='observe' && BeforeStepGame.state.paused")
   await page.wait_for_function('BeforeStepGame.state.judgmentReady')
   await controls.click('[data-judgment="unsure"]');await controls.click('#decision-imagine')
   await page.wait_for_function('document.querySelector("#raw-model").loaded',timeout=180000)
   checkpoint=await page.evaluate('BeforeStepGame.state')
   await chapter('original_input_first_front');await page.wait_for_timeout(2200)
   await controls.click('#model-back');await page.wait_for_timeout(3200)
   await chapter('first_original_back')
   photo=await page.locator('#input-photo').get_attribute('src')
   await controls.click('#switch-hypothesis')
   await page.wait_for_function('document.querySelector("#raw-model").loaded && BeforeStepGame.selected.includes(5958948)',timeout=180000)
   assert photo==await page.locator('#input-photo').get_attribute('src')
   await chapter('same_input_second_original_back');await page.wait_for_timeout(2500)
   await controls.click('[data-expand="models"]');await page.wait_for_function('document.querySelector("#raw-model-pair").loaded',timeout=180000)
   await page.wait_for_timeout(2200)
   report['pair_label_bounds']=await page.locator('#pair-model-label').bounding_box();assert report['pair_label_bounds']['height']<40
   await still('02-one-photo-two-backs-and-checks')
   await controls.click('#model-back');await page.wait_for_timeout(3200)
   await controls.click('#model-back');await page.wait_for_timeout(3200)
   await controls.click('#brain-restore');await controls.click('#rejected-example')
   await page.wait_for_function('document.querySelector("#raw-model").loaded',timeout=180000)
   await chapter('original_rejected_contour_check');await page.wait_for_timeout(3000)
   assert 5958642 not in await page.evaluate('BeforeStepGame.selected')
   await controls.click('#return-hypothesis');await page.wait_for_function('document.querySelector("#raw-model").loaded',timeout=180000)
   await controls.click('[data-expand="map"]');await page.wait_for_timeout(1500)
   await controls.click('[data-policy="optimistic"]');await page.wait_for_timeout(1600)
   report['map_visibility']=await visible_map()
   await chapter('fixed_map_first_candidate_5958948');await page.wait_for_timeout(2500)
   await controls.click('#switch-hypothesis');await page.wait_for_timeout(2600)
   await visible_map();await chapter('same_map_second_candidate_5959025');await page.wait_for_timeout(2500)
   await controls.click('#switch-hypothesis');await page.wait_for_timeout(2200)
   await controls.click('[data-policy="imagination"]');await page.wait_for_timeout(2200)
   await visible_map();await chapter('selected_hypothesis_and_route_decision')
   await still('03-footprint-and-route');await page.wait_for_timeout(3000)
   after=await page.evaluate('BeforeStepGame.state');assert all(checkpoint[k]==after[k] for k in ['x','y','z','yaw','elapsed'])
   report['final']=after;report['journal']=await page.evaluate('BeforeStepGame.journal')
   async with page.expect_download() as download:await controls.click('#export-run')
   await (await download.value).save_as(str(OUT/'comparison-session.json'))
   assert not report['page_errors'];report['passed']=True
  except Exception as e:
   report.update(failure=repr(e),traceback=traceback.format_exc());save();raise
  finally:
   await capture.stop();save();await context.close();await browser.close()
  (OUT/'00-full-run.mp4').rename(OUT/'02-03-space-comparison.mp4')
 print(json.dumps({'passed':report['passed'],'chapters':len(report['chapters']),'map_visibility':report.get('map_visibility')},ensure_ascii=False),flush=True)
asyncio.run(main())
