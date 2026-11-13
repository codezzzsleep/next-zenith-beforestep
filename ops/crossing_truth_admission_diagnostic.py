"""Input feasibility diagnostic with exact truth transform; never a Lux result."""
import json,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,trimesh
from experimental.crossing.scene import generate
from experimental.crossing.runtime import write
from beforestep.geometry import imagination as IM,metrics as C,admission as VE

if __name__=='__main__':
    seed=11002;scene=generate(seed,'scene-dev-v5');folder=Path(scene['truth_mesh']).parents[1];obsdir=folder/'observation'
    V,g,st,stats=IM.build_volume(obsdir);obs=IM.load_observation(obsdir);mesh=trimesh.load(scene['truth_mesh'],force='mesh',process=False)
    frame=st['local_frame'];c,s=np.cos(-frame['yaw0']),np.sin(-frame['yaw0']);M=np.eye(4);M[:3,:3]=[[c,-s,0],[s,c,0],[0,0,1]];M[:3,3]=-M[:3,:3]@np.array([frame['x0'],frame['y0'],0])
    ev=IM.evaluate_matrix(mesh,obs,M);metrics=C.admission_metrics(mesh,M,V,g,ev);metrics['scale_ratio']=VE.scale_ratio_ground(metrics['P'],V,g);metrics.pop('P')
    result={'diagnostic_only':True,'not_a_lux_result':True,'seed':seed,'exact_truth_transform':M.tolist(),'metrics':metrics,'admitted_diagnostic':VE.admitted(metrics),'new_lux_tasks':0}
    write(ROOT/'evidence/crossing/development-truth-admission-v5.json',result);print(json.dumps(result))
