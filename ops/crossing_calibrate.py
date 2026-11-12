"""Zero-paid crossing calibration. Every attempt gets an immutable output folder."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from experimental.crossing.runtime import *

def run_fixed(h,d,angle,method,out):
    out=Path(out)
    if (out/'result.json').exists():return json.loads((out/'result.json').read_text())
    obj=box_object(h,d);e=env_for([obj],angle=angle);rec=Record(e);rec.frame('start');t0=time.monotonic()
    pose=stance_array(STANCE if method=='fixed' else STANCE_HIGH)
    ok=transition(rec,pose,2,'raise' if method=='high' else 'settle')
    if ok:ok=drive(rec,pose,d+.35,heading=np.deg2rad(angle),timeout=40.)
    status='clean_pass' if ok and not rec.summary()['steps_with_wheel_stone'] else 'wheel_contact_pass' if ok else 'body_collision' if rec.failure and rec.failure['kind']=='body_collision' else 'unstable' if rec.failure else 'stuck'
    rec.save(out)
    result={'method':method,'h_m':h,'d_m':d,'angle_deg':angle,'status':status,'sim_seconds':e.t,'wall_seconds':time.monotonic()-t0,'final_base':e.data.qpos[:7].tolist(),'final_wheels':wheel_positions(e).tolist(),'contact':rec.summary(),'scene':e.spec,'trajectory_sha256':sha(out/'trajectory.npz'),'contacts_sha256':sha(out/'contacts.npz'),'new_lux_tasks':0}
    write(out/'result.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--method',choices=['fixed','high'],required=True);ap.add_argument('--height',type=float,required=True);ap.add_argument('--depth',type=float,required=True);ap.add_argument('--angle',type=float,default=0);ap.add_argument('--attempt',default='baseline-v1');a=ap.parse_args()
    folder=OUT/'calibration'/a.attempt/f'{a.method}-h{a.height:.3f}-d{a.depth:.3f}-a{a.angle:+.1f}'
    r=run_fixed(a.height,a.depth,a.angle,a.method,folder);print(json.dumps({k:r[k] for k in ['method','h_m','d_m','angle_deg','status','sim_seconds','wall_seconds','final_base','contact']}))
