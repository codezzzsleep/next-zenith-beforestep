"""Observed-only pose inputs to the unchanged registration and admission code."""
import argparse,json,sys,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,trimesh
from beforestep.geometry import imagination as IM,registration as REG,metrics as MET,admission as ADM
from experimental.crossing.runtime import write,sha


def diagnose(task_id,revision):
    folder=ROOT/'outputs/crossing/development'/revision/'seed-11002';obsdir=folder/'observation'
    destination=ROOT/'outputs/crossing/diagnosis/observed-pose-v1'/revision/str(task_id)
    if (destination/'result.json').exists():return json.loads((destination/'result.json').read_text())
    asset=ROOT/'assets/candidates'/str(task_id)/'tex_mesh.glb';mesh=REG.load_mesh(asset)
    obs=IM.load_observation(obsdir);points=obs['points'];sample=trimesh.sample.sample_surface(mesh,20000,seed=0)[0]
    _,axes=np.linalg.eigh(np.cov(sample.T));model=np.column_stack([axes[:,1],axes[:,2],axes[:,0]])
    if np.linalg.det(model)<0:model[:,0]*=-1
    _,observed_axes=np.linalg.eigh(np.cov(points[:,:2].T));long=observed_axes[:,-1]
    if long[1]<0:long=-long
    y=np.array([long[0],long[1],0.]);z=np.array([0.,0.,1.]);x=np.cross(y,z);target=np.column_stack([x,y,z])
    V,g,_,_=IM.build_volume(obsdir);rows=[]
    for index,signs in enumerate([(1,1,1),(-1,-1,1),(1,-1,-1),(-1,1,-1)]):
        rotation=target@np.diag(signs)@model.T
        q=mesh.vertices@rotation.T;span=np.ptp(q,axis=0)
        projected_span=np.ptp(q@y);visible_span=np.ptp(points@y)
        scales={'visible_long_span':float(visible_span/projected_span),'visible_top_height':float(points[:,2].max()/span[2])}
        for label,scale in scales.items():
            placed=q*scale;matrix=np.eye(4);matrix[:3,:3]=rotation*scale
            matrix[:3,3]=[points[:,0].min()-placed[:,0].min(),
                            (points[:,1].min()+points[:,1].max()-placed[:,1].min()-placed[:,1].max())/2,
                            -placed[:,2].min()]
            out=destination/f'{index}-{label}'
            if (out/'metrics.json').exists():rows.append(json.loads((out/'metrics.json').read_text()));continue
            registration=REG.register(asset,obsdir,IM.PROTO,out,coarse=matrix,
                    observation_loader=IM.load_observation,evaluator=IM.evaluate_matrix,scorer=IM.observation_score)
            m=MET.admission_metrics(mesh,np.asarray(registration['M']),V,g,registration['diagnostics'])
            m['scale_ratio']=ADM.scale_ratio_ground(m['P'],V,g);m.pop('P')
            result={'signs':signs,'scale_input':label,'matrix':registration['M'],'metrics':m,
                    'admitted_diagnostic':ADM.admitted(m),'registration_quality':registration['best']['quality']}
            write(out/'metrics.json',result);rows.append(result)
    result={'task_id':task_id,'revision':revision,'diagnostic_only':True,'source':'Observed point cloud and raw generated geometry; no truth used',
            'src_and_thresholds_unchanged':True,'new_lux_tasks':0,'raw_glb_sha256':sha(asset),
            'initialization_source_sha256':sha(Path(__file__)),'placements':rows,'any_admitted':any(r['admitted_diagnostic'] for r in rows)}
    write(destination/'result.json',result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True);parser.add_argument('--task',type=int,nargs='+',required=True);parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(diagnose,task,args.revision) for task in args.task];rows=[]
        for f in concurrent.futures.as_completed(futures):
            row=f.result();rows.append(row);print(json.dumps({'task_id':row['task_id'],'any_admitted':row['any_admitted']}),flush=True)
    write(ROOT/'evidence/crossing'/f'diagnosis-observed-pose-{args.revision}.json',{'diagnostic_only':True,'new_lux_tasks':0,'results':rows})
