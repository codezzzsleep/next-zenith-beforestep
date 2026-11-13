"""Whole-mesh diagnostics when rejected candidates do not cover wheel tracks."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import trimesh
from experimental.crossing.runtime import write
from experimental.crossing.scene import generate

if __name__=='__main__':
    first=json.loads((ROOT/'evidence/crossing/development-lux-first.json').read_text())
    scene=generate(first['seed'],first['revision']);truth=trimesh.load(scene['truth_mesh'],force='mesh',process=False)
    rows=[]
    for c in first['candidates']:
        mesh=trimesh.load(ROOT/c['world_mesh'],force='mesh',process=False)
        rows.append({'task_id':c['task_id'],'contour_iou':c['metrics']['contour_iou'],'admitted':c['admitted'],
            'world_bounds_m':mesh.bounds.tolist(),'whole_mesh_far_error_m':float(mesh.bounds[1,0]-truth.bounds[1,0]),
            'whole_mesh_high_error_m':float(mesh.bounds[1,2]-truth.bounds[1,2]),
            'covered_wheel_tracks':sum(v is not None for v in c['geometry']['far']),
            'wheel_track_errors_remain_undefined':not any(v is not None for v in c['geometry']['far'])})
    write(ROOT/'evidence/crossing/development-lux-shape-diagnostic.json',{'schema':'beforestep-crossing-lux-shape-diagnostic/v1',
        'purpose':'Whole-mesh far/high diagnostics for rejected models; no substitute for absent wheel-track geometry',
        'truth_world_bounds_m':truth.bounds.tolist(),'frozen_contour_iou_threshold':.7068,'rows':rows})
    print(json.dumps(rows))
