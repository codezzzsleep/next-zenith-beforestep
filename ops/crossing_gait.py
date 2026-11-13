"""Run one independent calibration attempt; completed trials are immutable."""
import argparse,json,sys,time,os,uuid,importlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import *
from experimental.crossing.action import crossing

def run_gait(h,d,angle,attempt,variant='default',control_hz=100):
    folder=OUT/'calibration'/attempt/f'gait-h{h:.3f}-d{d:.3f}-a{angle:+.1f}'
    if (folder/'result.json').exists():return json.loads((folder/'result.json').read_text())
    source=OUT/'calibration'/attempt/'source';source.mkdir(parents=True,exist_ok=True)
    action_path=ROOT/'experimental/crossing'/('action.py' if variant=='default' else 'action_'+variant+'.py')
    action=crossing if variant=='default' else importlib.import_module('experimental.crossing.action_'+variant).crossing
    for path in [action_path,ROOT/'experimental/crossing/runtime.py']:
        target=source/('action.py' if path==action_path else path.name)
        payload=path.read_bytes()
        if target.exists():assert target.read_bytes()==payload,'Changed source in one calibration identity'
        else:
            temporary=source/(path.name+'.'+uuid.uuid4().hex+'.tmp')
            temporary.write_bytes(payload)
            try:
                try:os.link(temporary,target)
                except FileExistsError:assert target.read_bytes()==payload,'Changed source in one calibration identity'
            finally:temporary.unlink()
    e=env_for([box_object(h,d)],angle=angle,control_hz=control_hz);rec=Record(e);rec.frame('start');t0=time.monotonic()
    ok,stages=action(rec,{'near':[0.,0.],'far':[d,d],'high':[h,h],'lateral':0.})
    status='clean_pass' if ok and rec.summary()['steps_with_wheel_stone']==0 else 'wheel_contact_pass' if ok else 'body_collision' if rec.failure and rec.failure['kind']=='body_collision' else 'unstable' if rec.failure else 'stuck'
    rec.save(folder)
    row={'method':'gait','h_m':h,'d_m':d,'angle_deg':angle,'attempt':attempt,'control_hz':control_hz,'status':status,'sim_seconds':e.t,'wall_seconds':time.monotonic()-t0,'final_base':e.data.qpos[:7].tolist(),'final_wheel_centres':wheel_positions(e).tolist(),'contact':rec.summary(),'stages':stages,'last_phase':rec.phase[-1],'scene':e.spec,'object_bounds':e.obj_bounds,'trajectory_sha256':sha(folder/'trajectory.npz'),'contacts_sha256':sha(folder/'contacts.npz'),'source_sha256':{p.name:sha(p) for p in source.glob('*.py')},'new_lux_tasks':0}
    write(folder/'result.json',row);return row

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--height',type=float,required=True);a.add_argument('--depth',type=float,required=True);a.add_argument('--angle',type=float,default=0);a.add_argument('--attempt',required=True);a.add_argument('--variant',choices=['default','force','fullframe','heading'],default='default');a.add_argument('--control-hz',type=int,choices=[50,100,250,500],default=100);v=a.parse_args();r=run_gait(v.height,v.depth,v.angle,v.attempt,v.variant,v.control_hz);print(json.dumps({k:r[k] for k in ['status','sim_seconds','contact','last_phase','final_base']}))
