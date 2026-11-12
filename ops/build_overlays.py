"""Export registered truth/imagined overlays; measure rather than tune back errors."""
import hashlib
import io
import json
from pathlib import Path
import numpy as np
import trimesh
from beforestep import scene as S
from beforestep.navigation import map as N
from scipy.spatial import ConvexHull
from matplotlib.path import Path as MPath
from web_glb import parse,encode
ROOT=S.ROOT;OUT=ROOT/'evidence/web-assets/overlays'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cluster(mesh,pitch):
 if pitch is None:return mesh.copy()
 # Display simplification only. Neither original meshes nor measured results change.
 keys=np.round(mesh.vertices/pitch).astype(np.int64);unique,inverse=np.unique(keys,axis=0,return_inverse=True);counts=np.bincount(inverse);vertices=np.column_stack([np.bincount(inverse,weights=mesh.vertices[:,i])/counts for i in range(3)]);faces=inverse[mesh.faces];valid=(faces[:,0]!=faces[:,1])&(faces[:,1]!=faces[:,2])&(faces[:,0]!=faces[:,2]);return trimesh.Trimesh(vertices,faces[valid],process=False)
def material(mesh,color,alpha):
 from trimesh.visual.material import PBRMaterial
 mesh.visual=trimesh.visual.texture.TextureVisuals(material=PBRMaterial(baseColorFactor=[*color,alpha],alphaMode='BLEND' if alpha<255 else 'OPAQUE',doubleSided=True,metallicFactor=0,roughnessFactor=1));return mesh

def main():
 OUT.mkdir(parents=True,exist_ok=True);stats=ROOT/'evidence/reviews/beforestep_r3/back-error/stats.json';rows=[]
 for r in read(stats)['rows']:
  if r['scene']=='stress_v8' and r['target']=='T2' and r['candidate'] in ['A2','C1'] or r['scene']=='suite_r2_v4_F3_004':rows.append({**r,'sample':r['candidate'],'stats_source':str(stats.relative_to(ROOT))})
 holdouts=ROOT/'evidence/award/holdout-collisions.json'
 for scene in read(holdouts)['rows']:
  for r in scene['all_admitted_candidates']:rows.append({**r,'scene':scene['scene'],'stats_source':str(holdouts.relative_to(ROOT))})
 contexts=read(ROOT/'evidence/web-assets/registrations.json')['contexts'];records=[]
 UP=trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0])
 for row in rows:
  name=row['scene'];S.configure(name);context=next(c for c in contexts if c['task_id']==row['task_id'] and c['scene']==name and c['source_decision_sha256']==row['decision_sha256']);assert context['admitted']
  generated=ROOT/f'evidence/web-assets/models/{row["task_id"]}.glb';mesh=trimesh.load(generated,force='mesh',process=False);mesh.apply_transform(np.asarray(context['viewer_y_up_from_generated']))
  truths=[];source_truth=[]
  for rock_name in row['associated_true_rocks']:
   rock=S.ROCKS[rock_name];obj,_=S.rock_asset_uniform(rock['rock'],rock['height']);obj=Path(obj);truth=trimesh.load(obj,force='mesh',process=False);truth.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rock['yaw']),[0,0,1]));truth.apply_translation([rock['x'],rock['y'],0]);truth.apply_transform(UP);truths.append(truth);source_truth.append({'rock':rock_name,'path':str(obj.relative_to(ROOT)),'sha256':sha(obj),'placement':rock})
  truth=trimesh.util.concatenate(truths)
  frame=context['local_frame'];axis=np.array([np.cos(frame['yaw0']),np.sin(frame['yaw0'])]);viewer_axis=np.array([axis[0],0,-axis[1]])
  original_end=float((mesh.vertices@viewer_axis).max())
  original_truth_end=float((truth.vertices@viewer_axis).max());raw_error=original_end-original_truth_end
  short=name.removeprefix('suite_r2_v4_');path=OUT/f'{short}-{row["target"]}-{row["sample"]}.glb'
  for pitch in [None,.0025,.005,.01,.02,.035]:
   imagined=material(cluster(mesh,pitch),[143,163,184],255);actual=material(cluster(truth,pitch),[242,166,59],89);scene=trimesh.Scene();scene.add_geometry(actual,geom_name='truth_amber_035',node_name='truth');scene.add_geometry(imagined,geom_name='imagined_greyblue',node_name='imagination');binary=scene.export(file_type='glb',include_normals=False)
   document,buffer=parse(binary)
   for mat in document['materials']:
    if mat.get('alphaMode')=='BLEND':mat['pbrMetallicRoughness']['baseColorFactor'][3]=.35
   binary=encode(document,buffer)
   if len(binary)<=2_000_000:break
  assert len(binary)<=2_000_000;path.write_bytes(binary)
  loaded=trimesh.load(io.BytesIO(binary),file_type='glb',force='scene',process=False)
  actual_after=loaded.geometry['truth_amber_035'];imagined_after=loaded.geometry['imagined_greyblue']
  error=float((imagined_after.vertices@viewer_axis).max()-(actual_after.vertices@viewer_axis).max());continuous_difference=abs(error-row['back_error_m'])
  # stats.json measures asymmetric frozen 5 cm discretizations: candidate
  # volume mapped into navigation cells; truth convex hull contains cell centres.
  # Reproject the exported meshes on those fixed cells as an independent check.
  iv=imagined_after.vertices;world=np.column_stack([iv[:,0],-iv[:,2],iv[:,1]]);world=world[world[:,2]>=.04]
  i=((world[:,0]-N.X0)/N.RES).astype(int);j=((world[:,1]-N.Y0)/N.RES).astype(int);valid=(i>=0)&(i<N.NX)&(j>=0)&(j<N.NY)
  projected_candidate=float((N.GX[i[valid],j[valid]]*axis[0]+N.GY[i[valid],j[valid]]*axis[1]).max())
  tv=actual_after.vertices;truthxy=np.column_stack([tv[:,0],-tv[:,2]]);hull=ConvexHull(truthxy);inside=MPath(truthxy[hull.vertices]).contains_points(np.c_[N.GX.ravel(),N.GY.ravel()]).reshape(N.GX.shape)
  projected_truth=float((N.GX[inside]*axis[0]+N.GY[inside]*axis[1]).max());grid_error=projected_candidate-projected_truth;difference=abs(grid_error-row['back_error_m'])
  records.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':len(binary),'scene':name,'target':row['target'],'sample':row['sample'],'task_id':row['task_id'],'viewer_y_up_from_generated':context['viewer_y_up_from_generated'],'matrix_source':'evidence/web-assets/registrations.json','matrix_source_sha256':sha(ROOT/'evidence/web-assets/registrations.json'),'source_glb':str(generated.relative_to(ROOT)),'source_glb_sha256':sha(generated),'source_truth':source_truth,'decision_source':row['decision'],'decision_sha256':row['decision_sha256'],'back_error_source':row['stats_source'],'back_error_source_sha256':sha(ROOT/row['stats_source']),'stored_back_error_m':row['back_error_m'],'continuous_original_back_error_m':raw_error,'exported_projection_back_error_m':error,'continuous_difference_m':continuous_difference,'continuous_within_5cm':continuous_difference<=.05,'grid_projected_back_error_m':grid_error,'projection_method':'Frozen 5 cm candidate-cell mapping and truth hull cell-centre containment; continuous vertex projection retained separately','difference_m':difference,'within_5cm':difference<=.05,'display_clustering_pitch_m':pitch,'coordinate_frame':'world Y-up, original placements unchanged','truth_color':'#F2A63B','truth_opacity':.35,'imagined_color':'#8FA3B8'})
  print(json.dumps({'overlay':path.name,'bytes':len(binary),'stored':row['back_error_m'],'continuous':error,'grid_projection':grid_error,'difference':difference,'passed':difference<=.05}),flush=True)
 result={'schema':'beforestep-truth-imagination-overlays/v1','scope':'Post-result visualization; no truth is supplied to the production controller','models':records,'passed':all(r['within_5cm'] for r in records),'limit_bytes':2_000_000,'projection_tolerance_m':.05,'continuous_outside_tolerance':[r['path'] for r in records if not r['continuous_within_5cm']],'unmatched':[r['path'] for r in records if not r['within_5cm']]};(OUT/'index.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'models':len(records),'passed':result['passed'],'unmatched':result['unmatched']}))
if __name__=='__main__':main()
