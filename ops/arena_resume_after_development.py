"""Take over the existing precheck, then run a new immutable development identity."""
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experimental.arena.common import OUT,read,write,sha


def checkpoint(event):
    p=Path('/root/3d/MEMORY.md')
    with p.open('a') as f:
        f.write(f'\n- Arena takeover checkpoint {datetime.now(timezone.utc).isoformat()}: {event}; ledger evidence/learning/arena_v2/jobs.json.\n')


def main():
    old=OUT/'prechecks/development-production-5'
    ledger=OUT/'jobs.json'
    checkpoint('Waiting on existing development5 PID1371911; parameters remain unchanged until its terminal summary')
    while not (old/'summary.json').exists():
        if not Path('/proc/1371911').exists():raise RuntimeError('Existing development5 disappeared without terminal summary; preserve partial files and inspect')
        time.sleep(10)
    jobs=read(ledger);jobs['jobs']['development-production-5']['status']='complete';write(ledger,jobs)
    checkpoint('Original development5 terminal summary retained; starting new local-view fallback identity with common finite 12-look budget')
    parameters=ROOT/'experimental/arena/parameters.json'
    config=read(parameters)
    if config['revision']=='development_5':
        backup=OUT/'history/parameters-development5-before-budget12.json'
        if not backup.exists():backup.write_bytes(parameters.read_bytes())
        config={**config,'revision':'development_6','max_looks':12};write(parameters,config)
    assert config['revision']=='development_6' and config['max_looks']==12
    # Only the common observation budget changed. Reuse the already completed
    # first-eye fidelity measurements after checking the exact 30 world identities.
    from experimental.arena.world import World
    comparisons=[]
    for result in sorted((OUT/'prechecks/transplant-fidelity-final').glob('*/result.json')):
        record=read(result);w=World(record['seed'],'fidelity',cfg=config)
        try:assert w.manifest()==record['world'],'Fidelity world changed; new imaging check required'
        finally:w.close()
        comparisons.append({'seed':record['seed'],'prior_result_sha256':sha(result)})
    assert len(comparisons)==30
    write(OUT/'prechecks/transplant-fidelity-final/budget12-world-parity.json',{'passed':True,'new_parameters_sha256':sha(parameters),'reason':'Only observation budget changed; all 30 first-eye world/camera/sun/candidate identities exact. Existing completed image and admission checks retained without repeat.','checks':comparisons})
    name='development-production-6';folder=OUT/'prechecks'/name
    log=OUT/'logs'/f'{name}.log';log.parent.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-m','experimental.arena.prechecks','development','--out',str(folder),'--workers','2']
    with log.open('a') as f:
        process=subprocess.Popen(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'MUJOCO_GL':'egl','OPENBLAS_NUM_THREADS':'1'})
        jobs=read(ledger);jobs['jobs'][name]={'status':'running','pid':process.pid,'command':command,'log':str(log.relative_to(ROOT)),'identity':str((folder/'identity.json').relative_to(ROOT))};write(ledger,jobs)
        checkpoint(f'New development6 started PID{process.pid}; parameters SHA{sha(parameters)}, 300 development worlds, no validation/train/sealed/LLM yet')
        code=process.wait()
    jobs=read(ledger);jobs['jobs'][name].update(status='complete' if code==0 else 'failed',exit_code=code);write(ledger,jobs)
    checkpoint(f'Development6 terminal exit{code}; inspect its full summary before interpreting')
    if code:raise RuntimeError('Development6 failed; inspect retained log')
    if not read(folder/'summary.json')['passed']:raise RuntimeError('Development gate still failed; no protocol or training started')
    checkpoint('Final development gate passed; proceeding to commit protocol and resume-safe complete training/evaluation')
    subprocess.run([sys.executable,str(ROOT/'ops/arena_pipeline.py'),'--memory','/root/3d/MEMORY.md','--development-check',name],cwd=ROOT,check=True)


if __name__=='__main__':main()
