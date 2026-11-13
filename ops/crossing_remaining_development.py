"""Resume remaining screened v9 scenes; obey SPEC stopping conditions."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import write
from experimental.crossing.budget import CrossingBudget
from ops.crossing_probe import event
SEEDS=[22001,22003,22004,22005];REVISION='scene-dev-v9'

def run(args):subprocess.run([sys.executable,*args],cwd=ROOT,check=True)
def stop(reason,seed):
    budget=CrossingBudget()
    with budget.locked() as data:
        record={'schema':'beforestep-crossing-development-stop/v1','criterion':'SPEC §12.2','reason':reason,
                'revision':REVISION,'seed':seed,'new_creation_stopped':True,'observed_at_unix':time.time(),
                'cumulative_created':data['created'],'formal_test_scenes':0}
        data.setdefault('stop_history',[]).append(record);data.update(stop=record,status='development_spec12_stopped')
    write(ROOT/'evidence/crossing/development-stop-scene-dev-v9.json',record)
    with Path('/root/3d/MEMORY.md').open('a') as f:f.write('\n剩余v9开发命中SPEC12.2：'+reason+'；种子'+str(seed)+'；新增已关闭，stop证据和预算落账，正式0。\n')
    event('remaining-development-v9',status='spec12_stopped',stop=record)
    print(json.dumps(record),flush=True)

if __name__=='__main__':
    event('remaining-development-v9',status='running',pid=os.getpid(),source='ops/crossing_remaining_development.py',seeds=SEEDS)
    for seed in SEEDS:
        report=ROOT/f'evidence/crossing/development-lux-{REVISION}-{seed}.json'
        if not report.exists():run(['ops/crossing_lux.py','--revision',REVISION,'--seed',str(seed),'--first','B1'])
        result=json.loads(report.read_text())
        destination=ROOT/f'outputs/crossing/development/{REVISION}/seed-{seed}/method-D-v1/result.json'
        if not destination.exists():run(['ops/crossing_method_development.py','--revision',REVISION,'--seed',str(seed),'--method','D'])
    decisions=[json.loads((ROOT/f'outputs/crossing/development/{REVISION}/seed-{seed}/method-D-v1/result.json').read_text()) for seed in SEEDS]
    total_admitted=sum(json.loads((ROOT/f'evidence/crossing/development-lux-{REVISION}-{seed}.json').read_text())['admitted'] for seed in SEEDS)
    if total_admitted==0:stop('No generated model admitted across four valid development scenes',SEEDS[-1]);sys.exit(0)
    if not any(row['decision']=='cross' for row in decisions):stop('None of four valid development scenes produced a cross decision',SEEDS[-1]);sys.exit(0)
    event('remaining-development-v9',status='complete',cross_decisions=sum(r['decision']=='cross' for r in decisions))
