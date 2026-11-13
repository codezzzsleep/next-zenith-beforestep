"""Small, geometry-preserving handoff models; full scans remain in raw evidence."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import mujoco
import numpy as np
import trimesh
from beforestep import scene as S
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import ROUTE,EVIDENCE,make

def material(mesh,rgba):
    mesh.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=rgba,roughnessFactor=.9,doubleSided=True))
    return mesh

if __name__=='__main__':
    scene=json.loads((EVIDENCE/'scene-stress_v8_gate.json').read_text());name=scene['name']
    output=ROUTE/'handoff';output.mkdir(parents=True,exist_ok=True)
    e,rb,meta,index=make(scene)
    display=trimesh.Scene();parts=[]
    # Retain all five original scan surfaces; no geometric transform or decimation.
    detour=ROUTE/name/'prechecks'/scene['attempt']/'detour/segment1/truth_standin'
    for label,p in [('high-A',detour/'A.obj'),('high-B',detour/'B.obj'),*zip(['threshold','gate-left','gate-right'],[ROOT/p for p in scene['mesh_paths']])]:
        mesh=trimesh.load(p,force='mesh',process=False)
        display.add_geometry(material(mesh,[178,163,136,255] if label=='threshold' else [121,128,128,255]),node_name=label)
        parts.append({'name':label,'source':str(p.relative_to(ROOT)),'source_sha256':sha(p),'geometry':'Original scan surface, unchanged world coordinates'})
    # Known stone wall retains every real collision hull; omit unused interior faces.
    for body in meta['walls'][:-3]:
        bid=mujoco.mj_name2id(e.model,mujoco.mjtObj.mjOBJ_BODY,body)
        for gi in e._body_geoms(body):
            if e.model.geom_type[gi]!=mujoco.mjtGeom.mjGEOM_MESH:continue
            mid=int(e.model.geom_dataid[gi]);start=int(e.model.mesh_vertadr[mid]);count=int(e.model.mesh_vertnum[mid])
            v=e.model.mesh_vert[start:start+count]@e.data.geom_xmat[gi].reshape(3,3).T+e.data.geom_xpos[gi]
            hull=trimesh.convex.convex_hull(v)
            display.add_geometry(material(hull,[94,101,100,255]),node_name=body+f'-{gi}')
    xs=np.linspace(-1.,13.,49);ys=np.linspace(-2.,3.5,33);X,Y=np.meshgrid(xs,ys,indexing='ij');z=S.height_at(X,Y)
    vertices=np.c_[X.ravel(),Y.ravel(),z.ravel()];faces=[]
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            a=i*len(ys)+j;b=a+len(ys);faces.extend([[a,b,a+1],[a+1,b,b+1]])
    terrain=trimesh.Trimesh(vertices,faces,process=False)
    display.add_geometry(material(terrain,[78,79,76,255]),node_name='terrain')
    world_to_gltf=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype=float)
    display.apply_transform(world_to_gltf)
    path=output/'scene.glb';display.export(path);assert path.stat().st_size<=2_000_000
    record={'schema':'beforestep-route-model-handoff/v1','scene':name,'scene_model':{'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path)},
        'world_to_gltf':world_to_gltf.tolist(),'gltf_coordinates':'Y up; [x,z,-y] from MuJoCo [x,y,z]',
        'parts':parts,'terrain':'Display sampling of unchanged analytic terrain; original full collision world remains authoritative',
        'stone_wall':'Exact collision hulls for the existing known wall','D_imagination_models':[],'total_scene_bytes':path.stat().st_size}
    # D uses A's verified shared high-rock observation and candidate registration.
    run=ROUTE/name/'D/segment1'
    paths=sorted(run.glob('looks/look*/T*/decide/world_*.obj'))
    imagined=trimesh.Scene();admitted=[]
    for decision_file in sorted(run.glob('looks/look*/T*/decide/target_decision.json')):
        decision=json.loads(decision_file.read_text())
        for c in decision['candidates']:
            if not c['admitted']:continue
            p=decision_file.parent/f'world_{c["id"]}.obj'
            if not p.exists():continue
            mesh=trimesh.load(p,force='mesh',process=False)
            imagined.add_geometry(material(mesh,[78,159,170,180]),node_name=decision_file.parent.parent.name+'-'+c['id'])
            admitted.append({'sample':c['id'],'source':str(p.relative_to(ROOT)),'sha256':sha(p),'metrics':{k:v for k,v in c.items() if k not in ['M','glb']}})
    if admitted:
        imagined.apply_transform(world_to_gltf)
        p=output/'D-imagination.glb';imagined.export(p)
        if p.stat().st_size>2_000_000:
            # An exact convex collision representation preserves the shapes used
            # for physical rehearsal; original visual surfaces remain archived.
            compact=trimesh.Scene()
            for label,mesh in imagined.geometry.items():compact.add_geometry(material(mesh.convex_hull,[78,159,170,180]),node_name=label)
            compact.export(p)
        assert p.stat().st_size<=2_000_000
        record['D_imagination_models']=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p),'candidates':admitted}]
    write(output/'models.json',record)
    print(json.dumps({'scene_model_bytes':path.stat().st_size,'D_models':len(record['D_imagination_models'])}))
