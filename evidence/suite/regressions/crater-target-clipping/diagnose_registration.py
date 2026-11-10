import json
from pathlib import Path
import numpy as np
import trimesh
from beforestep import scene as S
from beforestep.geometry import imagination as IM, registration as REG, metrics as C, admission as VE
root=S.ROOT;scene='suite_r2_v4_F2_007';definition=S.configure(scene)
obsdir=root/'outputs/suite/standins-wallfix/alternates'/scene/'imagination/looks/look2/T2'
state=json.loads((obsdir/'state.json').read_text());glb=obsdir/'offline_true_shape.glb';mesh=trimesh.load(glb,force='mesh',process=False)
V,g,st,stats=IM.build_volume(obsdir);obs=IM.load_observation(obsdir)
# Exact placement is a post-observation diagnostic only, never an initializer.
rock=definition['rocks']['B'];scan=trimesh.load(S.rock_asset_uniform(rock['rock'],rock['height'])[0],force='mesh',process=False)
scan.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rock['yaw']),[0,0,1]));scan.apply_translation([rock['x'],rock['y'],float(S.height_at(np.array([rock['x']]),np.array([rock['y']]))[0])+.00002])
frame=state['local_frame'];scan.apply_translation([-frame['x0'],-frame['y0'],0]);scan.apply_transform(trimesh.transformations.rotation_matrix(-frame['yaw0'],[0,0,1]))
known=np.eye(4);known[:3,3]=np.median(scan.vertices-mesh.vertices,axis=0)
def evaluate(M):
 ev=IM.evaluate_matrix(mesh,obs,M);metrics=C.admission_metrics(mesh,M,V,g,ev);metrics['scale_ratio_v5']=metrics['scale_ratio'];metrics['scale_ratio']=VE.scale_ratio_ground(metrics['P'],V,g)
 return {'M':M.tolist(),'admitted':IM.admitted(metrics),'metrics':{k:v for k,v in metrics.items() if k!='P'},'visible':ev}
report={'scope':'Offline exact-geometry registration diagnosis, not a Lux/physical result','paid_tasks':0,'known_pose_diagnostic':evaluate(known)}
print(json.dumps({'known_pose_diagnostic':report['known_pose_diagnostic']},ensure_ascii=False),flush=True)
# This alternative uses only the current visible points and native candidate.
points=obs['points'];scale=state['visible']['H_vis']/np.ptp(mesh.vertices[:,2]);initial=np.eye(4);initial[:3,:3]*=scale
initial[:3,3]=[np.median(points[:,0])-scale*np.median(mesh.vertices[:,0]),(points[:,1].min()+points[:,1].max())/2-scale*(mesh.bounds[0,1]+mesh.bounds[1,1])/2,-scale*mesh.bounds[0,2]]
out=root/'outputs/qa/r2/F2-centroid-registration';rec=REG.register(glb,obsdir,IM.PROTO,out,coarse=initial,observation_loader=IM.load_observation,evaluator=IM.evaluate_matrix,scorer=IM.observation_score)
report['visible_centroid_initial']=initial.tolist();report['visible_centroid_registration']=evaluate(np.array(rec['M']))
(out/'diagnosis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False),flush=True)
