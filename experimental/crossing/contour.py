"""Truth-contour diagnostic using the unchanged 2-D production planner."""
import json
from pathlib import Path
import numpy as np
import trimesh
from beforestep.navigation import map as N
from .runtime import write,sha


def contour_check(scene,destination):
    destination=Path(destination);saved=destination/'result.json'
    if saved.exists():return json.loads(saved.read_text())
    occupancy=np.zeros_like(N.GX,dtype=bool);sources=[]
    for item in scene['spec']['objects']:
        mesh_path=Path(item['posed_dir'])/'truth.obj'
        mesh=trimesh.load(mesh_path,force='mesh',process=False)
        faces=mesh.triangles[:,:,:2]
        area=(faces[:,1,0]-faces[:,0,0])*(faces[:,2,1]-faces[:,0,1])-(faces[:,1,1]-faces[:,0,1])*(faces[:,2,0]-faces[:,0,0])
        for t,a in zip(faces,area):
            if abs(a)<=1e-12:continue
            lo=np.maximum(np.ceil((t.min(axis=0)-[N.X0,N.Y0])/N.RES-.5).astype(int),0)
            hi=np.minimum(np.floor((t.max(axis=0)-[N.X0,N.Y0])/N.RES-.5).astype(int),[N.NX-1,N.NY-1])
            if (lo>hi).any():continue
            sl=(slice(lo[0],hi[0]+1),slice(lo[1],hi[1]+1));x=N.GX[sl];y=N.GY[sl]
            inside=np.ones(x.shape,dtype=bool)
            for u,v in [(0,1),(1,2),(2,0)]:
                cross=(t[v,0]-t[u,0])*(y-t[u,1])-(t[v,1]-t[u,1])*(x-t[u,0])
                inside &= cross*np.sign(a)>=-1e-12
            occupancy[sl]|=inside
        sources.append({'path':str(mesh_path),'sha256':sha(mesh_path)})
    # The declared channel is known terrain context; no generated geometry is used.
    channel=scene['spec']['channel'];occupancy|=np.abs(N.GY-channel['center_y'])>channel['half_width']
    start=scene['observation_stop'];goal=scene['goal']
    path=N.plan(occupancy,start,goal)
    destination.mkdir(parents=True,exist_ok=True);np.save(destination/'occupancy.npy',occupancy)
    result={'schema':'beforestep-crossing-contour-diagnostic/v1','seed':scene['seed'],'revision':scene['revision'],
            'planner':'beforestep.navigation.map.plan; unchanged default parameters','has_path':path is not None,
            'path':path,'start':start,'goal':goal,'grid_resolution_m':N.RES,'sources':sources,
            'projection':'Union of original scan triangles projected into XY, sampled at production grid centers; no convex approximation',
            'occupancy_sha256':sha(destination/'occupancy.npy'),'diagnostic_only':True,'new_lux_tasks':0}
    write(saved,result);return result
