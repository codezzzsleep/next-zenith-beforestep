"""Browser keyboard verification; only button/key actions and read-only state inspection.

Requires Python Playwright and its Chromium. The recorded video is live simulation,
not a prerecorded gameplay substitute. Outputs belong to a caller-selected directory.
"""
import asyncio,json,os,time,argparse
from pathlib import Path
from playwright.async_api import async_playwright
parser=argparse.ArgumentParser(description='Run actual keyboard game actions and record a complete simulated task.')
parser.add_argument('--url',default='https://codezzzsleep.github.io/next-zenith-beforestep')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--chromium',default=os.environ.get('BEFORESTEP_CHROMIUM'))
args=parser.parse_args();l=args.output.parent;l.mkdir(parents=True,exist_ok=True);base=args.url.rstrip('/')
result={'checks':[],'errors':[]};start=time.time()

def save(): args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
def check(name,info=None): result['checks'].append({'name':name,'info':info,'seconds':round(time.time()-start,1)});save();print(name,json.dumps(info,ensure_ascii=False)[:220],flush=True)
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path=args.chromium,args=['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader'])
  context=await browser.new_context(viewport={'width':1280,'height':800},record_video_dir=str(l/'recording'),record_video_size={'width':1280,'height':800});page=await context.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)))
  try:
   await page.goto(base+'/play.html',wait_until='domcontentloaded');await page.wait_for_function('window.BeforeStepGame?.state && document.documentElement.dataset.missionReady',timeout=90000)
   s=await page.evaluate('BeforeStepGame.state');assert s['phase']=='explore' and not s['paused'];check('immediate_real_driving',s)
   await page.keyboard.down('w');await page.wait_for_timeout(1100);await page.keyboard.up('w');await page.keyboard.down(' ');await page.wait_for_timeout(700);await page.keyboard.up(' ')
   await page.wait_for_function('BeforeStepGame.state.stable',timeout=30000);s2=await page.evaluate('BeforeStepGame.state');assert s2['x']>s['x']+.08;check('keyboard_drive_before_models',{'before':s['x'],'after':s2['x']})
   await page.locator('button[data-view="0"]').click();await page.wait_for_timeout(700);await page.locator('button[data-view="2"]').click();await page.wait_for_timeout(700);await page.locator('button[data-view="1"]').click();check('three_views_same_live_world',await page.locator('#world').evaluate('(e)=>({view:e.dataset.view,time:e.dataset.simulationTime,pip:e.dataset.pip,observed:e.dataset.observedVertices,total:e.dataset.totalRockVertices})'))
   await page.locator('#observe').click();await page.locator('#think').click();await page.wait_for_function('document.querySelector("#raw-model").loaded',timeout=90000);check('official_raw_lux3d_model_in_thought_bubble',await page.locator('#raw-model').get_attribute('src'))
   await page.locator('#model-turn').click();await page.locator('#raw-model').hover();await page.mouse.down();await page.mouse.move(1120,350,steps=6);await page.mouse.up()
   await page.locator('#preview').click();await page.wait_for_function('BeforeStepGame.state.proof?.passed',timeout=420000,polling=100);s=await page.evaluate('BeforeStepGame.state');assert s['proof']['usable'];check('two_real_model_worlds_rehearsed_from_live_pose',s['proof'])
   # Selection invalidation was verified in the retained first run.
   await page.locator('#execute').click();await page.wait_for_function('BeforeStepGame.state.automatic',timeout=30000);await page.wait_for_timeout(1300);await page.keyboard.down(' ');await page.wait_for_timeout(650);await page.keyboard.up(' ');await page.wait_for_function('!BeforeStepGame.state.automatic',timeout=30000);check('keyboard_takeover_of_rehearsed_route')
   await page.locator('#follow').click();await page.wait_for_function('BeforeStepGame.state.automatic',timeout=30000);await page.locator('button[data-view="0"]').click();await page.wait_for_function('BeforeStepGame.state.phase==="gate" && !BeforeStepGame.state.automatic',timeout=420000,polling=100);check('original_rehearsed_path_resumed_without_replanning',await page.evaluate('BeforeStepGame.state'))
   await page.wait_for_function('BeforeStepGame.state.stable',timeout=30000);await page.locator('#observe').click();await page.locator('#gate-preview').click();await page.wait_for_function('BeforeStepGame.state.gateProof?.passed',timeout=420000,polling=100);check('visible_threshold_real_crossing_rehearsal');await page.locator('#brain-cross').click();await page.wait_for_function('BeforeStepGame.state.phase==="crossing"',timeout=30000)
   for i in range(12):
    await page.wait_for_function('BeforeStepGame.state.legs?.waiting',timeout=180000,polling=100)
    waiting=await page.evaluate('BeforeStepGame.state.legs.waiting')
    key={'lift':'j','advance':'k','land':'l'}[waiting['action']]
    await page.wait_for_function("!document.querySelector('[data-action=%s]').disabled" % waiting['action'],timeout=30000)
    expected=(await page.evaluate('BeforeStepGame.state.actionCount'))+1
    await page.keyboard.press(key)
    await page.wait_for_function('BeforeStepGame.state.actionCount >= '+str(expected),timeout=45000,polling=100)
    check(f'player_leg_action_{i+1}',waiting)
   await page.wait_for_function('BeforeStepGame.state.phase==="finish-drive"',timeout=180000,polling=100);await page.locator('#wheel-mode').click();await page.wait_for_function('!BeforeStepGame.state.legs',timeout=30000);await page.keyboard.down('w');await page.wait_for_function('BeforeStepGame.state.phase==="complete"',timeout=120000,polling=100);await page.keyboard.up('w');check('full_task_reached_goal',await page.evaluate('BeforeStepGame.state'));result['passed']=not result['errors'];save()
   await page.screenshot(path=str(l/'completed.jpg'),type='jpeg',quality=70,timeout=90000)
  except Exception as e:result['failed']=str(e);result['state']=await page.evaluate('window.BeforeStepGame?.state');save();print('FAIL',str(e)[:350],flush=True)
  finally:
   result['video']=await page.video.path();save();await context.close();await browser.close()
asyncio.run(main())
if not result.get('passed'): raise SystemExit(1)
