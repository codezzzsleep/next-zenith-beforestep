"""Register an appended stone gate at runtime; preserve all frozen scene bytes."""
import copy, hashlib, json
from pathlib import Path
import numpy as np
import trimesh
from matplotlib.path import Path as Polygon
from scipy.spatial import ConvexHull
from beforestep import scene as S
from beforestep.navigation import map as N
from experimental.crossing.runtime import ROOT, OUT, write, sha
from experimental.crossing.scene import save_mesh, track_geometry

ROUTE = OUT/'route'
EVIDENCE = ROOT/'evidence/crossing/route'
BASE = ROOT/'config/scenes/stress_v8.json'

def footprint(mesh):
    """Convex collision footprint at the production grid centers."""
    xy=mesh.vertices[:,:2]
    hull=ConvexHull(xy)
    return Polygon(xy[hull.vertices]).contains_points(np.c_[N.GX.ravel(),N.GY.ravel()]).reshape(N.GX.shape)

def build(near=9., seed=22001, base_id='stress_v8'):
    name=base_id+'_gate'
    attempt=f'x{near:.2f}-seed{seed}'
    folder=ROUTE/name/'scene-attempts'/attempt
    saved=folder/'route-scene.json'
    if saved.exists():return json.loads(saved.read_text())
    original=json.loads((ROOT/f'config/scenes/{base_id}.json').read_text())
    old=ROOT/f'outputs/crossing/development/scene-dev-v9/seed-{seed}'
    source=json.loads((old/'scene.json').read_text())
    delta=np.array([near-3.,0.,0.])
    objects=[];paths=[];origins=[]
    for part in ['threshold','gate-1','gate-2']:
        p=old/part/'truth.obj'
        mesh=trimesh.load(p,force='mesh',process=False)
        mesh.apply_translation(delta)
        provenance={'source_scene':str((old/'scene.json').relative_to(ROOT)),
            'source_mesh':str(p.relative_to(ROOT)), 'source_sha256':sha(p),
            'translation_m':delta.tolist(), 'shape_size_orientation_unchanged':True,
            'rock':json.loads((old/part/'manifest.json').read_text())['source']['rock']}
        objects.append(save_mesh(folder/part,mesh,provenance))
        paths.append(str((folder/part/'truth.obj').relative_to(ROOT)));origins.append(provenance)
    threshold=trimesh.load(ROOT/paths[0],force='mesh',process=False)
    spec={'schema':'beforestep-crossing-route-scene/v1', 'name':name,'base_scene':base_id,
        'base_scene_sha256':sha(ROOT/f'config/scenes/{base_id}.json'),'attempt':attempt,
        'threshold_seed':seed,'near_x_m':near,'gap_m':source['gap_m'],
        'staging_xy':[near-.85,0.], 'goal':[near+1.5,0.],
        'start':original['start'], 'first_stop':original['first_stop'], 'rocks':original['rocks'],
        'objects':objects,'mesh_paths':paths,'provenance':origins,
        'truth_geometry':track_geometry(threshold),'registration':'runtime; original config/scenes and src untouched',
        'gate_treatment':'Known terrain, excluded from generation targets and included in all first-segment planning/rehearsal worlds',
        'formal_order':['C','B','A','D'],'frozen_action_sha256':sha(ROOT/'experimental/crossing/action.py')}
    write(saved,spec);return spec

def select(scene):
    path=EVIDENCE/f'scene-{scene["name"]}.json'
    if path.exists():
        old=json.loads(path.read_text())
        if old.get('formal_runs_started'):
            assert old['attempt']==scene['attempt'],'Scene cannot change after a formal run'
    write(path,{**scene,'formal_runs_started':False})
    return path

def register(scene):
    """Runtime registration changes only the appended known terrain and task goal."""
    original_configure=S.configure
    original_spec=S.scene_spec
    original_exclusion=N.target_exclusion_mask
    known=np.zeros_like(N.GX,dtype=bool)
    for path in scene['mesh_paths']:
        known |= footprint(trimesh.load(ROOT/path,force='mesh',process=False))
    def configure(scene_id):
        if scene_id!=scene['name']:return original_configure(scene_id)
        definition=copy.deepcopy(original_configure(scene['base_scene']))
        S.SCENE_ID=scene['name'];S.GOAL=tuple(scene['staging_xy']);S.REHEARSE_REFERENCE=False
        definition.update(id=scene['name'],goal=list(scene['staging_xy']),rehearse_reference=False,
            appended_known_terrain=scene['mesh_paths'],route_definition=str((EVIDENCE/f'scene-{scene["name"]}.json').relative_to(ROOT)))
        return definition
    def scene_spec(run):
        spec,rb,meta=original_spec(run)
        for item,origin in zip(scene['objects'],scene['provenance']):
            index=len(spec['objects']);spec['objects'].append(copy.deepcopy(item))
            body=f'obstacle{index}';rb[body]=origin['rock'];meta['walls'].append(body)
        spec['route_threshold_index']=len(spec['objects'])-3
        spec['route_known_objects']=copy.deepcopy(scene['objects'])
        spec['route_rock_bodies']=copy.deepcopy(rb)
        return spec,rb,meta
    S.configure=configure;S.scene_spec=scene_spec
    N.target_exclusion_mask=lambda:original_exclusion()|known
    # prior_nogo calls target_exclusion_mask at runtime: known additions receive
    # exactly the existing planning clearance and no generated geometry.
    return known

def make(scene,staging=False):
    S.configure(scene['base_scene']);S.SCENE_ID=scene['name'];S.GOAL=tuple(scene['goal'])
    spec,rb,meta=S.scene_spec(ROUTE/scene['name']/'world')
    for item,origin in zip(scene['objects'],scene['provenance']):
        i=len(spec['objects']);spec['objects'].append(copy.deepcopy(item));rb[f'obstacle{i}']=origin['rock'];meta['walls'].append(f'obstacle{i}')
    spec['goal_x']=scene['goal'][0]
    e=S.make_env(spec);e.tip_deg=60.;e.nav_base=False
    if staging:S.place(e,*scene['staging_xy'])
    else:S.place(e,*S.START)
    return e,rb,meta,len(spec['objects'])-3
