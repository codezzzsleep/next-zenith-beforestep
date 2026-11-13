"""Run independent physical checks in two ordinary Python processes."""
import argparse,concurrent.futures,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experimental.crossing.runtime import write
from experimental.crossing.route.world import build,ROUTE,EVIDENCE

def run_one(scene,check,stance=None,position=None):
    tag=check+(f'-{stance}-{position}' if check=='wheel' else '')
    out=ROUTE/scene['name']/'prechecks'/scene['attempt']/tag
    if (out/'result.json').exists():return str((out/'result.json').relative_to(ROOT))
    record=out/'process.json'
    if record.exists():
        old=json.loads(record.read_text())
        if old.get('status')=='运行中':
            try:os.kill(old['pid'],0)
            except ProcessLookupError:pass
            else:raise RuntimeError(f'Precheck {tag} still running as PID {old["pid"]}; do not duplicate')
    command=[sys.executable,'ops/crossing_route_precheck.py','--near',str(scene['near_x_m']),
        '--seed',str(scene['threshold_seed']),'--base',scene['base_scene'],'--check',check]
    if stance:command+=['--stance',stance,'--position',position]
    log=Path('/root/3d/.memory/live')/f'route-{scene["name"]}-{scene["attempt"]}-{tag}.log'
    with log.open('a') as stream:
        child=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        code=child.wait()
    if code:raise RuntimeError(f'{tag} exited {code}; preserve {log} and fix the program')
    return str((out/'result.json').relative_to(ROOT))

def aggregate(scene):
    base=ROUTE/scene['name']/'prechecks'/scene['attempt']
    checks={}
    for tag in ['contour','leg','detour',*[f'wheel-{s}-{p}' for s in ['fixed','high'] for p in ['center','left','right']]]:
        p=base/tag/'result.json'
        checks[tag]={'step_status':'终态','path':str(p.relative_to(ROOT)),**json.loads(p.read_text())} if p.exists() else {'step_status':'未开始','path':str(p.relative_to(ROOT))}
    done=all(r['step_status']=='终态' for r in checks.values())
    report={'schema':'beforestep-crossing-route-precheck/v1','scene':scene['name'],'attempt':scene['attempt'],
        'checks':checks,'all_terminal':done,'all_four_passed':done and all(r.get('passed',False) for r in checks.values()),
        'new_lux_tasks':0,'scene_definition':f'evidence/crossing/route/scene-{scene["name"]}.json'}
    write(EVIDENCE/f'precheck-{scene["name"]}.json',report)
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--near',type=float,default=9.);ap.add_argument('--seed',type=int,default=22001);ap.add_argument('--aggregate-only',action='store_true')
    ap.add_argument('--base',default='stress_v8');a=ap.parse_args();scene=build(a.near,a.seed,a.base)
    if not a.aggregate_only:
        tasks=[('wheel',s,p) for s in ['fixed','high'] for p in ['center','left','right']]+[('leg',None,None)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(run_one,scene,*task) for task in tasks]
            for future in concurrent.futures.as_completed(futures):
                result=future.result();report=aggregate(scene)
                print(json.dumps({'completed':result,'all_four_passed':report['all_four_passed']},ensure_ascii=False),flush=True)
    report=aggregate(scene)
    print(json.dumps({'all_terminal':report['all_terminal'],'all_four_passed':report['all_four_passed']},ensure_ascii=False),flush=True)
