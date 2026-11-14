"""Relocate copied sources and build display geometry without simulation steps."""
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get('BEFORESTEP_ROOT', str(Path(__file__).resolve().parents[3]))).resolve()
BASE = ROOT.parent
OUT = Path(os.environ.get('BEFORESTEP_PRODUCTION_OUT', str(ROOT / 'evidence/production-v6'))).resolve()
TOOLS = ROOT / 'tools/production_v6'
os.environ['BEFORESTEP_ROOT'] = str(ROOT)
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(TOOLS), str(OUT)]

import mujoco
import numpy as np
from beforestep import scene as S
from beforestep.visualization import camera as VZ
from ops import crossing_real_footage_capture as footage
from ops.crossing_showcase_capture import display_sync
import photography

footage.ROOT = ROOT
photography.ROOT = ROOT

def forbidden_step(*args, **kwargs):
    raise RuntimeError('B2 display-only guard: physics integration is forbidden')

mujoco.mj_step = forbidden_step
mujoco.mj_step1 = forbidden_step
mujoco.mj_step2 = forbidden_step
# The existing constructor/reset settles for 0.6s. A display model needs only
# its compiled XML and geometry; saved qpos supplies all rendered state.
S.wheelleg_env.WheelLegEnv._reset_state = lambda *args, **kwargs: None

def display_env(spec):
    S.terrain.SPAN, S.terrain.N = S.SPAN, S.NGRID
    spec['_hfield_dir'] = str(OUT / 'gpu-render' / 'runtime-hfield')
    return S.wheelleg_env.WheelLegEnv(spec, max_seconds=900)

S.make_env = display_env

def build_model(scene='stress_v8', *, route=None, objects=None, width=1920, height=1080):
    folder = OUT / 'gpu-render' / 'models' / (route or scene)
    # Reuse the transferred original height field. NumPy version differences
    # must not regenerate slightly different terrain on the GPU host.
    height_file = folder / 'scene' / 'height.npy'
    original_height_map = S.height_map
    saved_height = np.load(height_file) if height_file.exists() else None
    def scene_spec():
        if saved_height is not None:
            S.height_map = lambda: saved_height.copy()
        try:
            return S.scene_spec(folder)
        finally:
            S.height_map = original_height_map
    if route:
        import json
        d = json.loads((ROOT / 'evidence/crossing/route' / f'scene-{route}.json').read_text())
        def relocate(value):
            if isinstance(value, dict):
                return {key: relocate(item) for key, item in value.items()}
            if isinstance(value, list):
                return [relocate(item) for item in value]
            if isinstance(value, str) and value.startswith('/root/3d/next-zenith-beforestep/'):
                return str(ROOT / value.removeprefix('/root/3d/next-zenith-beforestep/'))
            return value
        d = relocate(d)
        S.configure(d['base_scene'])
        spec, rb, _ = scene_spec()
        for item, provenance in zip(d['objects'], d['provenance']):
            rb[f'obstacle{len(spec["objects"])}'] = provenance['rock']
            spec['objects'].append(item)
        spec['goal_x'] = d['goal'][0]
        vm = VZ.video_model(S.make_env(spec), rb, width=width, height=height, off=(width, height))
        for g in range(6):
            vm.opt.geomgroup[g] = int(g in (0, 1, 2))
    else:
        S.configure(scene)
        spec, rb, _ = scene_spec()
        if objects is not None:
            spec = footage.IM.rehearsal_spec(spec, objects, folder / 'imagined-world')
            rb = {}
        vm = VZ.video_model(S.make_env(spec), rb, width=width, height=height, off=(width, height))
        for g in range(6):
            vm.opt.geomgroup[g] = int(g in (0, 1, 2))
        if objects:
            for gi in range(vm.m.ngeom):
                name = mujoco.mj_id2name(vm.m, mujoco.mjtObj.mjOBJ_BODY, int(vm.m.geom_bodyid[gi])) or ''
                if name.startswith('obstacle'):
                    vm.m.geom_rgba[gi] = [.43, .46, .48, 1]
    photography.original_actor(vm)
    photography.quality(vm, exposure=True)
    vm.m.vis.quality.shadowsize = 8192
    vm.m.vis.quality.offsamples = 4
    vm.m.vis.map.shadowclip = 3
    vm.m.vis.map.znear = .001
    return vm
