"""Offline initialization-only geometry survey; never a physical pass result."""
import itertools
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental.crossing.action import ik
from experimental.crossing.runtime import *

def survey(h, d):
    env = env_for([box_object(h, d)])
    monitor = Record(env)
    model = env.model
    data = mujoco.MjData(model)
    legs = [[env.J[leg+'_'+part+'_joint'] for part in ['hip','thigh','calf']] for leg in LEG]
    wheel_ids = [min(env._body_geoms(leg+'_wheel_link')) for leg in LEG]
    rows = []
    rejects = {'joint_range': 0, 'stone_contact': 0, 'support_polygon': 0}
    for x, y, z, rear, front in itertools.product(
            np.arange(.10,.241,.02), [-.08,-.04,0.,.04],
            np.arange(h+.23,h+.311,.01), [.111,.13,.15,.18,.20], [.23,.28,.32]):
        base = np.array([d+x,y,z])
        feet = np.array([[d+front,-.142,.086],[d+front,.142,.086],
                         [d+rear,.015,.086],[-.091,-.04,.086]])
        data.qpos[:] = env.data.qpos
        data.qpos[:3] = base
        data.qpos[3:7] = [1,0,0,0]
        valid = True
        joint_margin = 10.
        for j in range(4):
            point = feet[j].copy()
            try:
                q = ik(point-base,j)
                for _ in range(5):
                    axis = np.sin(q[0]);side = -1 if j in [0,2] else 1
                    radius = WHEEL_R*np.sqrt(max(0.,1-axis*axis))+.02630213*abs(axis)
                    point[2] = feet[j,2]+radius-side*.0503699327*axis-WHEEL_R
                    q = ik(point-base,j)
                for k, part in enumerate(['hip','thigh','calf']):
                    jid = mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_JOINT,LEG[j]+'_'+part+'_joint')
                    lo,hi = model.jnt_range[jid]
                    joint_margin = min(joint_margin,q[k]-lo,hi-q[k])
                    if not lo<=q[k]<=hi:
                        valid = False
                    data.qpos[legs[j][k]['qadr']] = q[k]
            except ValueError:
                valid = False
        if not valid:
            rejects['joint_range'] += 1
            continue
        mujoco.mj_forward(model,data)
        if any((int(c.geom1) in monitor.stones and int(c.geom2) in monitor.robot) or
               (int(c.geom2) in monitor.stones and int(c.geom1) in monitor.robot) for c in data.contact):
            rejects['stone_contact'] += 1
            continue
        points = data.geom_xpos[wheel_ids,:2]
        com = data.subtree_com[1,:2]
        # Last RL is the only wheel to be lifted next. This is only a static
        # projection of geometry, with no claimed normal load or physical stability.
        weights = np.linalg.solve(np.vstack([np.ones(3),points[:3].T]),np.r_[1.,com])
        if weights.min()<.04:
            rejects['support_polygon'] += 1
            continue
        rows.append({'base':base.tolist(),'feet':feet.tolist(),'joint_margin_rad':float(joint_margin),
                     'last_support_weights':weights.tolist(),'qpos':data.qpos.tolist()})
    rows.sort(key=lambda row: min(row['last_support_weights']), reverse=True)
    return {'h_m':h,'d_m':d,'kind':'offline initialization geometry; not simulation outcome',
            'rejects':rejects,'feasible_initializations':len(rows),'candidates':rows}

if __name__ == '__main__':
    folder = OUT/'calibration/kinematic-v1'
    folder.mkdir(parents=True,exist_ok=True)
    source = folder/'source'
    source.mkdir(exist_ok=True)
    for path in [Path(__file__),ROOT/'experimental/crossing/action.py',ROOT/'experimental/crossing/runtime.py']:
        target = source/path.name
        if target.exists():
            assert target.read_bytes()==path.read_bytes()
        else:
            shutil.copy2(path,target)
    for h,d in [(.12,.20),(.15,.15)]:
        target = folder/f'h{h:.3f}-d{d:.3f}.json'
        value = json.loads(target.read_text()) if target.exists() else survey(h,d)
        if not target.exists():write(target,value)
        print(json.dumps({key:value[key] for key in ['h_m','d_m','rejects','feasible_initializations']}),flush=True)
        print(json.dumps(value['candidates'][:2]),flush=True)
