"""Run v72 on four development truth worlds; source and failures are retained."""
import argparse,json,os,sys,concurrent.futures,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import OUT,write,sha
from experimental.crossing.scene import generate,DEVELOPMENT_SEEDS
from experimental.crossing.execution import execute,geometry_for
from ops.crossing_probe import event
import trimesh


def trial(seed,revision,attempt):
    scene=generate(seed,revision);folder=Path(scene['truth_mesh']).parents[1];g=geometry_for(trimesh.load(scene['truth_mesh'],force='mesh',process=False));return execute(scene,folder/'observation',g,folder/attempt,'E')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',default='scene-dev-v5');p.add_argument('--workers',type=int,default=3);p.add_argument('--attempt',default='truth-v72-v2');a=p.parse_args();name='truth-'+a.revision+'-'+a.attempt
    files=[ROOT/'experimental/crossing'/n for n in ['action.py','runtime.py','scene.py','execution.py']]+[Path(__file__)]
    source=OUT/'development'/a.revision/(a.attempt+'-source');source.mkdir(exist_ok=True)
    for file in files:
        target=source/file.name
        if target.exists():assert target.read_bytes()==file.read_bytes()
        else:shutil.copyfile(file,target)
    event(name,status='running',pid=os.getpid(),source_sha256={str(f.relative_to(ROOT)):sha(f) for f in files},cases=DEVELOPMENT_SEEDS,workers=a.workers)
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
        rows=[]
        for f in concurrent.futures.as_completed([pool.submit(trial,seed,a.revision,a.attempt) for seed in DEVELOPMENT_SEEDS]):
            r=f.result();rows.append(r);print(json.dumps({k:r[k] for k in ['seed','status','sim_seconds','preparation_end_s','last_phase']}),flush=True)
    write(ROOT/'evidence/crossing'/('development-truth-'+a.revision+'-'+a.attempt+'.json'),{'diagnostic_only':True,'action_version':'v72','scenes':rows});event(name,status='complete',results=[{k:r[k] for k in ['seed','status','raw_path']} for r in rows])
