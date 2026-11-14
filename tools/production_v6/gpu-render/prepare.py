"""Validate all available shot sources and trace their display dependencies."""
import gc
import json
import sys
from pathlib import Path
from bootstrap import *
from common import save, sha

metadata = json.loads((ROOT / 'site/data/footage.json').read_text())['clips']
required = set()
plans = []
def use(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    assert p.is_file(), p
    identity = sha(p)
    if expected:
        assert identity == expected, (p, identity, expected)
    required.add(p)
    return {'path': str(p.relative_to(ROOT)), 'sha256': identity}

def clip(name):
    d = metadata[name]
    return use(d['source'], d['source_sha256'])

def plan(name, sources, scene, start=None, end=None, duration=None, speed=None, camera='follow', **extra):
    for source in sources:
        z = np.load(ROOT / source['path'])
        assert z['qpos'].shape[1] == 23
    plans.append(dict(id=name, sources=sources, scene=scene, sim_start=start, sim_end=end,
                      duration_s=duration, speed=speed, camera=camera, **extra))

r1 = clip('stress_v8-imagination')
for policy, end, speed, hold in [('optimistic',80.87,6,2),('conservative',142.2,12,0),('imagination',112.84,6,2)]:
    plan('s03-'+policy,[clip('stress_v8-'+policy)],'stress_v8',0,end,speed=speed,terminal_hold_s=hold)
base = ROOT / 'outputs/crossing/route/stress_v8_gate/prechecks/x9.00-seed22001'
for name, source, start, end, duration in [('wheel','wheel-fixed-center',6.654,11.654,5),('lift','leg',50.14,64.14,14),('depart','leg',167.08,173.08,6)]:
    plan('s08-'+name,[use(base/source/'trajectory.npz')],'stress_v8',start,end,duration,camera='low',route='stress_v8_gate')
plan('s01-open',[r1],'stress_v8',1.2,16.08,15,camera='opening')
eye = ROOT / 'evidence/reviews/beforestep_r1/lux/original_b/looks/look1/T1'
plan('s02-eye',[r1],'stress_v8',14.08,16.08,3,camera='front_cam',original_rgb=use(eye/'rgb.png'),original_camera=use(eye/'camera_world.json'))
plan('s06-failure',[clip('suite_r2_v4_F3_004-imagination')],'suite_r2_v4_F3_004',70.14,82.14,24,speed=.5,camera='failure',timing_note='12 simulation seconds at0.5x require24 video seconds; editor can trim')
worlds=[]
for i in range(12):
    d=metadata[f'world-{i:02d}']
    source=clip(f'world-{i:02d}')
    pane=use(d['world_source']['pane'],d['world_source']['sha256'])
    data=json.loads((ROOT/pane['path']).read_text())
    assert data['completed'] and not data['collided']
    objects=[use(p) for p in data['objects']]
    worlds.append({'source':source,'pane':pane,'objects':objects})
plan('s05-world-1',[worlds[0]['source']],'stress_v8',0,96.18,8,objects=worlds[0]['objects'],pane=worlds[0]['pane'])
plans.append({'id':'s05-world-grid','scene':'stress_v8','duration_s':6,'worlds':worlds,'camera':'follow','sim_start':25,'sim_end':41})
for route in ['suite_r2_v4_F1_003_gate','suite_r2_v4_F2_001_gate']:
    d=metadata[route+'-D']
    sources=[use(x['path'],x['sha256']) for x in d['source_files']]
    plan('s09-backup-'+route.removeprefix('suite_r2_v4_').removesuffix('_gate'),sources,route,duration=10,camera='overview',route=route)

for scene, route in [('stress_v8',None),('stress_v8','stress_v8_gate'),('suite_r2_v4_F3_004',None),('suite_r2_v4_F1_003','suite_r2_v4_F1_003_gate'),('suite_r2_v4_F2_001','suite_r2_v4_F2_001_gate'),('suite_r2_v4_F3_002','suite_r2_v4_F3_002_gate')]:
    use(ROOT/'config/scenes'/f'{scene}.json')
    if route:
        d=use(ROOT/'evidence/crossing/route'/f'scene-{route}.json')
        definition=json.loads((ROOT/d['path']).read_text())
        for obj in definition['objects']:
            if 'mesh_file' in obj:
                use(obj['mesh_file'])
    vm=build_model(scene,route=route)
    assert vm.m.nq==23
    VZ.release(vm);del vm;gc.collect()
    print('dependency model',route or scene,flush=True)
for w in worlds:
    paths=[str(ROOT/x['path']) for x in w['objects']]
    vm=build_model(objects=paths)
    VZ.release(vm);del vm;gc.collect()
    print('dependency world',w['pane']['path'],flush=True)

save(OUT/'gpu-render/shot-plan.json',{'shots':plans,'pending':['s09-gate-overview','s09-gate-approach','s09-gate-crossing','s09-gate-A'],'pending_reason':'F3_002 formal A/D not terminal/available; no physics started here','screen_recordings':['r01-reveal','r02-glb-A','r03-glb-B','r04-photo-to-glb']})
for p in [OUT/'render-ab/leg-h-center-clean.png',OUT/'render-ab/index.json',TOOLS/'render_ab.py',TOOLS/'common.py',TOOLS/'photography.py',TOOLS/'capture.py',ROOT/'ops/crossing_real_footage_capture.py',ROOT/'ops/crossing_showcase_capture.py']:
    required.add(p)
for p in (ROOT/'src/beforestep/visualization').glob('*.py'):
    required.add(p)
for module in tuple(sys.modules.values()):
    name=getattr(module,'__file__',None)
    if name:
        p=Path(name).resolve()
        if p.is_relative_to(ROOT) and p.suffix=='.py':
            required.add(p)
save(OUT/'gpu-render/explicit-files.json',[str(p) for p in sorted(required)])
print('Explicit files',len(required),flush=True)
