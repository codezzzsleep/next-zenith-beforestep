"""Continue a live A identity and start D immediately at its terminal result."""
import fcntl,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LIVE=ROOT.parent/'.memory/live'

def record(data):
    path=LIVE/'addendum3-execution.json'
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temporary.replace(path)

def run(command,log):
    with (LIVE/log).open('a') as stream:
        process=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        record({'pid':os.getpid(),'phase':'D','child_pid':process.pid,'command':command,'log':str(LIVE/log)})
        if process.wait():raise RuntimeError('D program interrupted; preserve log and repair before recovery')

if __name__=='__main__':
    LIVE.mkdir(parents=True,exist_ok=True)
    with (LIVE/'addendum3-execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        base=ROOT/'outputs/crossing/route/stress_v8_gate'
        record({'pid':os.getpid(),'phase':'waiting_A','source':str(base/'A')})
        while not (base/'A/result.json').exists():
            p=json.loads((ROOT/'outputs/crossing/route/progress.json').read_text())
            pid=p['steps']['A'].get('pid')
            if not pid or not Path(f'/proc/{pid}/cmdline').exists():
                raise RuntimeError('A process disappeared before terminal result; inspect existing attempt')
            time.sleep(2)
        if not (base/'D/result.json').exists():
            run([sys.executable,'ops/crossing_route_run.py','--vehicle','D','--reuse',str((base/'A/segment1').relative_to(ROOT))],'route-formal-D.log')
        record({'pid':os.getpid(),'phase':'D_terminal','result':str(base/'D/result.json'),'at_unix':time.time()})
        # Extra-scene worker begins before publication, independent of D outcome.
        extra=ROOT/'ops/crossing_route_additional.py'
        if extra.exists():
            with (LIVE/'route-additional.log').open('a') as stream:
                proc=subprocess.Popen([sys.executable,str(extra)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
                record({'pid':os.getpid(),'phase':'extra_started','child_pid':proc.pid,'at_unix':time.time()})
        for command in [[sys.executable,'ops/crossing_route_summary.py'],[sys.executable,'ops/crossing_route_text.py'],
                        [sys.executable,'ops/crossing_route_publish.py','--stage','first-four-terminal','--message','Publish all four route outcomes without selecting results']]:
            subprocess.run(command,cwd=ROOT,check=True)
        record({'pid':os.getpid(),'phase':'first_published','at_unix':time.time()})
