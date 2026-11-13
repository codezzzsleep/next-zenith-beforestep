"""Complete frame/video/PDF deliveries at evidence boundaries and deadlines."""
import fcntl,json,os,subprocess,sys,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import ROUTE,EVIDENCE
LIVE=ROOT.parent/'.memory/live';DEADLINE=datetime(2026,11,15,10,tzinfo=timezone.utc)

def call(script,*args):
    with (LIVE/'addendum3-delivery.log').open('a') as stream:subprocess.run([sys.executable,'ops/'+script,*args],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)

def complete(path):return path.exists() and json.loads(path.read_text()).get('status')=='complete'

def published_summary_current():
    import hashlib
    try:
        with urllib.request.urlopen('https://codezzzsleep.github.io/next-zenith-beforestep/evidence/crossing/route/summary.json',timeout=20) as response:remote=response.read()
        return hashlib.sha256(remote).hexdigest()==sha(EVIDENCE/'summary.json')
    except Exception:return False

if __name__=='__main__':
    with (LIVE/'addendum3-delivery.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state={'pid':os.getpid(),'status':'running','video':False,'pdf':False,'handoff':False};write(LIVE/'addendum3-delivery.json',state)
        while not all(state[k] for k in ['video','pdf','handoff']):
            terminal=(ROUTE/'stress_v8_gate/D/result.json').exists()
            plan=json.loads((EVIDENCE/'additional-scenes.json').read_text()) if (EVIDENCE/'additional-scenes.json').exists() else {'scenes':[]}
            all_extra=bool(plan['scenes']) and all(r['status']=='终态' for r in plan['scenes'])
            if not state['pdf'] and ((terminal and all_extra) or datetime.now(timezone.utc)>=DEADLINE):
                call('crossing_route_summary.py');call('crossing_route_text.py');call('crossing_route_report_assets.py','--usage-only');call('crossing_route_report.py')
                call('crossing_route_pdf.py');call('crossing_route_publish.py','--stage','pdf-addendum3','--message','Publish the one updated complete report and retain its prior PDF','--pdf')
                state['pdf']=True;write(LIVE/'addendum3-delivery.json',state)
            ready=all(complete(ROUTE/'handoff/frames'/clip/'index.json') for clip in ['wheel-stuck','leg-cross','sill-close','connect'])
            if ready and not state['video'] and published_summary_current():
                call('crossing_route_video_capture.py','--shot','7-table','--force')
                call('crossing_route_video.py')
                if complete(ROOT/'outputs/crossing/route/video/render-state.json'):
                    check=ROOT/'docs/hackathon-submission.md';text=check.read_text().replace('demo-v2.mp4) 合成中','demo-v2.mp4) 初版已合成并核验');check.write_text(text)
                    call('crossing_route_publish.py','--stage','video-v2-first','--message','Publish the 154-second evidence-checked subtitled demo','--video')
                    state['video']=True;write(LIVE/'addendum3-delivery.json',state)
            post=LIVE/'post-frames.json';post_complete=post.exists() and json.loads(post.read_text()).get('status')=='complete'
            if ready and terminal and post_complete and not state['handoff']:
                call('crossing_route_package.py','--stage','first-raw');call('crossing_route_package.py','--stage','final-handoff')
                call('crossing_route_publish.py','--stage','route-handoff-final','--message','Publish complete physical sources, frame indexes, and handoff provenance')
                state['handoff']=True;write(LIVE/'addendum3-delivery.json',state)
            time.sleep(10)
        state.update(status='complete',finished_at=datetime.now(timezone.utc).isoformat());write(LIVE/'addendum3-delivery.json',state)
        with (ROOT.parent/'MEMORY.md').open('a') as memory:memory.write('\n补充3普通交付worker完成视频初版/PDF唯一更新/原始与帧handoff公开，具体证据在.memory/live/addendum3-delivery.json及各publication stage。仍须负责人看片，视频定版核实际D与追加全终态并最终九条报告。\n')
        print(json.dumps(state),flush=True)
