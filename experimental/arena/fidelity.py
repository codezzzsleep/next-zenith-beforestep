"""Reimage transplanted training-side rigs and rerun all five frozen admission checks."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from beforestep.geometry import camera as C,imagination as I,metrics as M,admission as A
from beforestep.observation import capture as O
from beforestep.navigation import map as N
from .common import ROOT,OUT,read,write,sha,finite,rigid
from .world import World
from .sensor import ProductionSensor,transplanted_qpos


def check(seed,out,cfg=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);w=World(seed,'fidelity',cfg=cfg)
    write(out/'world.json',w.manifest());sensor=ProductionSensor(w.definition,out/'physical')
    try:
        q=transplanted_qpos(w.capsule);ob=sensor.at(w.start,w.heading,qpos=q)
        np.save(out/'state.npy',ob['state']);np.save(out/'zmax.npy',ob['zmax'])
        xy=np.array(w.capsule['visible_cells_world_xy']);T=np.asarray(w.capsule['transplant_world_from_source'])
        xy=np.column_stack([xy,np.zeros(len(xy))])@T[:3,:3].T+T[:3,3]
        ij=np.floor((xy[:,:2]-[N.X0,N.Y0])/N.RES).astype(int);cells=np.zeros((N.NX,N.NY),bool)
        good=(ij[:,0]>=0)&(ij[:,0]<N.NX)&(ij[:,1]>=0)&(ij[:,1]<N.NY);cells[tuple(ij[good].T)]=True
        grow=O.target_growth(cells)
        cid=sensor.mj.mj_name2id(sensor.vm.m,sensor.mj.mjtObj.mjOBJ_CAMERA,'front_cam')
        snap=C.capture(sensor.vm.m,sensor.vm.d,cid,1600,1200)
        depth=np.where(ob['dark'],np.nan,ob['depth']);points=O.world_points(depth,snap)
        p=points;inside=np.isfinite(p).all(-1)&(p[...,2]>=N.ROCK_Z)&(p[...,0]>N.X0)&(p[...,0]<N.X1)&(p[...,1]>N.Y0)&(p[...,1]<N.Y1)
        ix=np.clip(((np.nan_to_num(p[...,0],nan=-99)-N.X0)/N.RES).astype(int),0,N.NX-1)
        iy=np.clip(((np.nan_to_num(p[...,1],nan=-99)-N.Y0)/N.RES).astype(int),0,N.NY-1)
        mask=inside&grow[ix,iy];target=out/'target';target.mkdir(exist_ok=True)
        if mask.sum()==0:raise ValueError('Transplanted target lost all visible support')
        frame=w.capsule['local_frame'];local=np.linalg.inv(rigid(np.degrees(frame['yaw0']),[frame['x0'],frame['y0']]))
        local_points=p[mask]@local[:3,:3].T+local[:3,3]
        local_camera={**snap,'world_pos':(np.array(snap['world_pos'])@local[:3,:3].T+local[:3,3]).tolist(),'R_world_from_camera':(local[:3,:3]@np.array(snap['R_world_from_camera'])).tolist()}
        Image.fromarray(ob['rgb']).save(target/'rgb.png');Image.fromarray(mask.astype(np.uint8)*255).save(target/'mask.png');Image.fromarray(ob['dark'].astype(np.uint8)*255).save(target/'dark.png')
        np.save(target/'depth.npy',depth.astype(np.float32));np.save(target/'visible_points.npy',local_points);np.save(target/'cells.npy',cells)
        visible={'x_front':float(local_points[:,0].min()),'y_center':float((local_points[:,1].min()+local_points[:,1].max())/2),'W_vis':float(np.ptp(local_points[:,1])),'H_vis':float(local_points[:,2].max())}
        write(target/'observation.json',{'schema':'observation/v8','camera':local_camera,'intrinsics':snap['intrinsics']})
        write(target/'state.json',{'visible':visible,'local_frame':frame,'robot_qpos_world':q.tolist(),'look':'look1','t_sim':float(sensor.env.t)})
        write(target/'camera_world.json',snap)
    finally:sensor.close()
    V,g,st,stats=I.build_volume(target);obs=I.load_observation(target);rows=[]
    for c in w.capsule['candidates']:
        if not c['registration_available']:continue
        mesh=I.REG.load_mesh(ROOT/c['glb']);ev=I.evaluate_matrix(mesh,obs,c['local_from_generated'])
        metrics=M.admission_metrics(mesh,c['local_from_generated'],V,g,ev)
        metrics['scale_ratio']=A.scale_ratio_ground(metrics['P'],V,g);metrics.pop('P')
        after=A.admitted(metrics);rows.append({'task_id':c['task_id'],'before_metrics':c['metrics'],'after_metrics':finite(metrics),
            'metric_deltas':{k:metrics[k]-c['metrics'][k] if c['metrics'][k] is not None else None for k in c['metrics']},
            'before_admitted':c['frozen_admitted'],'after_admitted':after,'flipped':after!=c['frozen_admitted'],
            'glb_sha256':c['glb_sha256'],'registration':'frozen source M, unchanged in jointly transformed observer frame'})
        print(seed,c['task_id'],c['frozen_admitted'],after,flush=True);write(out/'candidate-progress.json',rows)
    result={'seed':seed,'capsule_id':w.capsule['id'],'world':w.manifest(),'candidates':rows,
            'flips':sum(r['flipped'] for r in rows),'candidate_count':len(rows),'observation_state_sha256':sha(out/'state.npy'),
            'sensor':'Frozen production N.observe, 4040x3030 RGB-D downsampled to 1600x1200; no new Lux task'}
    write(out/'result.json',finite(result));return result


def batch(out,count=30,cfg=None):
    import os
    out=Path(out);out.mkdir(parents=True,exist_ok=True);config=cfg or read(ROOT/'experimental/arena/parameters.json')
    write(out/'identity.json',{'status':'running','pid':os.getpid(),'count':count,'parameters':config,'capsule_library':config.get('capsule_library','evidence/learning/arena_v2/capsules.json'),'capsules_sha256':sha(ROOT/config.get('capsule_library','evidence/learning/arena_v2/capsules.json')),'new_lux_tasks':0})
    rows=[];start=config['fidelity']['seed_start']
    for seed in range(start,start+count):
        folder=out/str(seed)
        if (folder/'result.json').exists():r=read(folder/'result.json')
        else:r=check(seed,folder,config)
        rows.append(r);write(out/'progress.json',rows)
    total=sum(r['candidate_count'] for r in rows);flips=sum(r['flips'] for r in rows)
    write(out/'summary.json',{'worlds':len(rows),'candidate_checks':total,'flips':flips,'flip_rate':flips/total,'passed':flips/total<=.2,'scored_split':'training-side development only'})
    identity=read(out/'identity.json');identity['status']='complete';write(out/'identity.json',identity)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--count',type=int,default=30);ap.add_argument('--parameters');a=ap.parse_args()
    batch(a.out,a.count,read(a.parameters) if a.parameters else None)
