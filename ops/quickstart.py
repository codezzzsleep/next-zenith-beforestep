"""Run the complete frozen anchor with existing Lux bytes, then open the site."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1];ANCHOR='evidence/reviews/beforestep_r1/lux/original_b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reuse-lux',nargs='?',const=ANCHOR,required=True);p.add_argument('--out');p.add_argument('--serve',action='store_true');p.add_argument('--port',type=int,default=8080);a=p.parse_args()
 source=(ROOT/a.reuse_lux).resolve();assert source==(ROOT/ANCHOR).resolve(),'This zero-paid entry reuses the preserved anchor only'
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=Path(a.out).resolve() if a.out else ROOT/'outputs/quickstart'/stamp;assert not out.exists(),'Choose a new output; preserved results are never overwritten';out.mkdir(parents=True)
 started=time.monotonic();fixture=out/'reuse-fixture';shutil.copytree(source,fixture)
 # Recreate declared input aliases from exact preserved upload bytes. Original
 # request paths/identities are not edited, and need no other checkout.
 restored=[];task_paths={}
 for target in ['T1','T2']:
  folder=source/'looks/look1'/target;result=json.loads((folder/'lux_result.json').read_text())
  for task in result['tasks']:
   if task['status']=='ok':
    model=(ROOT/task['glb']).resolve();assert model.is_relative_to(ROOT) and sha(model)==task['glb_sha256'];task_paths[task['id']]=model
   for relative,digest in zip(task['inputs'],task['input_sha256']):
    destination=(ROOT/relative).resolve();assert destination.is_relative_to(ROOT)
    if not destination.exists():
     matches=[f for f in (folder/'gen/variants').glob('*') if f.is_file() and sha(f)==digest];assert matches,'Missing preserved upload bytes';destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(matches[0],destination);restored.append(relative)
    assert sha(destination)==digest
  decision=fixture/'looks/look1'/target/'decide/target_decision.json';d=json.loads(decision.read_text())
  for candidate in d['candidates']:candidate['glb']=str((ROOT/'assets/candidates'/Path(candidate['glb']).parent.name/'tex_mesh.glb').resolve())
  decision.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 # Only a disposable copied cache changes filesystem bindings. Observation,
 # input, GLB, frozen thresholds and original production decisions stay intact.
 env={**os.environ,'MUJOCO_GL':os.environ.get('MUJOCO_GL','egl')};env.pop('AHOLO_API_KEY',None);env.pop('BEFORESTEP_ROOT',None)
 subprocess.run([sys.executable,'-m','beforestep','resources'],cwd=ROOT,env=env,check=True)
 command=[sys.executable,'-m','beforestep','run','--scene','stress_v8','--controller-model','rules','--policy','imagination','--imagine','lux','--reuse-lux',str(fixture),'--out',str(out/'run')]
 (out/'job.json').write_text(json.dumps({'status':'running','pid':os.getpid(),'command':command,'new_paid_tasks':0,'started_at':datetime.now(timezone.utc).isoformat()},indent=2)+'\n')
 print('Running the actual observation → reused Lux → check → all rehearsals → independent execution chain. No API key or new generation.',flush=True)
 subprocess.run(command,cwd=ROOT,env=env,check=True)
 run=out/'run/imagination';summary=json.loads((run/'summary.json').read_text());assert not (run/'NEED_LUX3D.json').exists()
 import numpy as np
 with np.load(source/'traj.npz') as expected,np.load(run/'traj.npz') as actual:arrays={key:bool(np.array_equal(expected[key],actual[key])) for key in ['t','qpos','phase','control_sources','control_actions']}
 report={'passed':all(arrays.values()) and summary['result']=='arrived','status':'complete','root':str(ROOT),'run':str(run),'summary':summary,'zero_paid_tasks':True,'new_paid_tasks':0,'reused_source':ANCHOR,'recreated_input_aliases':restored,'trajectory_arrays_exact':arrays,'wall_s':time.monotonic()-started,'completed_at':datetime.now(timezone.utc).isoformat(),'source_sha256':json.loads((run/'run_identity.json').read_text())['source_sha256'],'browser_url':f'http://127.0.0.1:{a.port}/'}
 (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(out/'job.json').write_text(json.dumps({'status':'complete','result':str(out/'result.json')},indent=2)+'\n');assert report['passed'],report
 print(json.dumps({'passed':True,'wall_s':report['wall_s'],'result':summary['result'],'new_paid_tasks':0,'url':report['browser_url']}),flush=True)
 if a.serve:subprocess.run([sys.executable,'-m','beforestep','serve','--port',str(a.port)],cwd=ROOT,env=env,check=True)
if __name__=='__main__':main()
