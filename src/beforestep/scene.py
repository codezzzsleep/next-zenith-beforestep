"""The frozen polar corridor, scan assets, starting pose and goal."""
import os, pathlib, sys
import json
import numpy as np
from .paths import ROOT
from .simulation import terrain, environment as wheelleg_env, soil_profiles as v7_soil
from .visualization import textures as LW

LW.ROCKS = pathlib.Path(os.environ.get('BEFORESTEP_ROCK_ROOT', str(ROOT / 'assets/rocks')))
ROCKS = {
    'A': {'rock': 'rock_07', 'height': 0.55, 'x': 4.55, 'y': -0.735, 'yaw': 90.0},
    'B': {'rock': 'moon_rock_04', 'height': 0.42, 'x': 6.86, 'y': 0.22, 'yaw': -26.0},
}


SPAN, NGRID = 16.0, 257


CAM = {'pos': [0.42, 0.0, -0.00125], 'pitch_deg': -24.83, 'fovy': 70.0}


ROBOT = {'half_len': 0.38, 'half_wid': 0.33, 'turn_radius': 0.50}


SUN_EL_DEG, SUN_AZ_DEG = 10.0, 35.0


RILLE = {'edge_y': 1.30, 'width': 4.2, 'wall': 1.15, 'depth': 1.0}


WALL = {'y_inner': -1.35, 'x0': -2.0, 'x1': 13.0}


START = (0.0, -0.50)


STOP1 = (2.30, -0.50)


GOAL = (10.5, 0.00)
SCENE_ID = 'stress_v8'


def configure(scene_id='stress_v8'):
    """Select a documented scene before creating any observation or physics model."""
    global ROCKS, START, STOP1, GOAL, SCENE_ID
    if pathlib.Path(scene_id).name != scene_id:
        raise ValueError('Scene must be a config/scenes name')
    path = ROOT / 'config/scenes' / f'{scene_id}.json'
    definition = json.loads(path.read_text())
    if definition['id'] != scene_id or not definition['rocks']:
        raise ValueError('Scene identity or obstacles missing')
    for key in ('start', 'first_stop', 'goal'):
        if len(definition[key]) != 2 or not np.isfinite(definition[key]).all():
            raise ValueError(f'Invalid {key}')
    for rock in definition['rocks'].values():
        if not all(np.isfinite(rock[k]) for k in ('height','x','y','yaw')) or rock['height'] <= 0:
            raise ValueError('Invalid rock dimensions')
    ROCKS = definition['rocks']
    START, STOP1, GOAL = (tuple(definition[k]) for k in ('start','first_stop','goal'))
    SCENE_ID = scene_id
    return definition


def physical_identity(definition):
    return {k: definition[k] for k in ('id','rocks','start','first_stop','goal')}


WALL_ROCKS = ['rock_09', 'moon_rock_04', 'rock_07', 'moon_rock_03', 'moon_rock_06', 'moon_rock_07']


def sun_dir():
    el, az = np.radians(SUN_EL_DEG), np.radians(SUN_AZ_DEG)
    d = np.array([np.cos(el) * np.cos(az), -np.cos(el) * np.sin(az), -np.sin(el)])
    return d / np.linalg.norm(d)                 # 光线传播方向


def rille_edge(x):
    """月溪右沿（靠窄道一侧）的 y：轻微弯曲，在 B 附近收窄。"""
    x = np.asarray(x, float)
    return RILLE['edge_y'] + 0.12 * np.sin(0.8 * x + 0.4) - 0.20 * np.exp(-((x - 7.4) / 1.3) ** 2)


def height_at(X, Y):
    r = RILLE
    e = rille_edge(X)
    d = Y - e                                   # 进入月溪的横向深度（>0 在溪内）
    w = r['width']
    H = np.zeros_like(X, dtype=float)
    # 右坡：0 -> -depth；溪底；左坡：-depth -> 0
    t1 = np.clip(d / r['wall'], 0, 1); t2 = np.clip((w - d) / r['wall'], 0, 1)
    s1 = t1 * t1 * (3 - 2 * t1); s2 = t2 * t2 * (3 - 2 * t2)
    inside = (d > 0) & (d < w)
    H[inside] = -r['depth'] * np.minimum(s1, s2)[inside]
    H += 0.025 * np.exp(-(d / 0.35) ** 2) * (d < 0)            # 溪沿外侧轻微隆起
    return H


def height_map():
    terrain.SPAN = SPAN; terrain.N = NGRID
    X, Y = terrain.grid_xy(NGRID)
    return height_at(X, Y)


def terrain_visual_obj(path, step=0.08, tile=0.9):
    """成片用的地面网格：比物理高度场细，顶点法线平滑；带贴图坐标。物理仍用高度场。"""
    path = pathlib.Path(path)
    if path.exists():
        return path
    xs = np.arange(-SPAN, SPAN + 1e-9, step); ys = np.arange(-SPAN, SPAN + 1e-9, step)
    X, Y = np.meshgrid(xs, ys); Z = height_at(X, Y)
    ny, nx = X.shape
    with open(path, 'w') as f:
        for x, y, z in zip(X.ravel(), Y.ravel(), Z.ravel()):
            f.write(f'v {x:.4f} {y:.4f} {z:.4f}\n')
        for x, y in zip(X.ravel(), Y.ravel()):
            f.write(f'vt {x / tile:.4f} {y / tile:.4f}\n')
        idx = np.arange(nx * ny).reshape(ny, nx) + 1
        a, b, c, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
        for i in range(len(a)):
            f.write(f'f {a[i]}/{a[i]} {b[i]}/{b[i]} {c[i]}/{c[i]}\nf {a[i]}/{a[i]} {c[i]}/{c[i]} {d[i]}/{d[i]}\n')
    return path


def rock_asset_uniform(rock_id, height, level='h1'):
    """扫描岩石等比缩放到给定高度：水平主轴转到 x，底面落在 z=0，包围盒中心在原点。"""
    src, tex = LW.rock_asset(rock_id, level)
    dst = LW.CACHE / f'{rock_id}_{level}_v8ax_h{int(height * 1000)}_2s.obj'
    if not dst.exists():
        lines = pathlib.Path(src).read_text().splitlines()
        V = np.array([[float(t) for t in l.split()[1:4]] for l in lines if l.startswith('v ')])
        c = V[:, :2].mean(0); w, U = np.linalg.eigh(np.cov((V[:, :2] - c).T)); ax = U[:, np.argmax(w)]
        th = -np.arctan2(ax[1], ax[0]); R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        xy = (V[:, :2] - c) @ R.T
        s = height / np.ptp(V[:, 2]); mid = (xy.min(0) + xy.max(0)) / 2; z0 = V[:, 2].min()
        out, k = [], 0
        for l in lines:
            if l.startswith('v '):
                x, y = xy[k] - mid; z = V[k, 2] - z0; k += 1
                out.append(f'v {x * s:.6f} {y * s:.6f} {z * s:.6f}')
            elif l.startswith('vn '):
                n = np.array([float(v) for v in l.split()[1:4]]); n[:2] = R @ n[:2]
                out.append(f'vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}')
            else:
                out.append(l)
        dst.write_text('\n'.join(out) + '\n')
    return dst, tex


def scene_spec(run):
    H = height_map()
    hf = pathlib.Path(run) / 'scene' / 'height.npy'; hf.parent.mkdir(parents=True, exist_ok=True); np.save(hf, H)
    spec = terrain.make_spec(kind='flat', seed=0, goal_x=GOAL[0], span=SPAN, name=SCENE_ID)
    spec['terrain']['field_x_max'] = SPAN
    spec['terrain']['custom_height_file'] = str(hf)
    spec['channel'] = {'center_y': 0.0, 'half_width': 1.4}
    spec['soil'] = v7_soil.resolve('nominal')
    spec['front_cam'] = dict(CAM)
    objs, rock_bodies, meta = [], {}, {'rocks': {}, 'walls': [], 'scene_id': SCENE_ID}
    for key, p in ROCKS.items():
        obj, _ = rock_asset_uniform(p['rock'], p['height'])
        objs.append({'mesh_file': str(obj), 'x': p['x'], 'y': p['y'], 'yaw_deg': p['yaw'], 'height_m': p['height']})
        b = f'obstacle{len(objs) - 1}'; rock_bodies[b] = p['rock']; meta['rocks'][key] = dict(p, body=b, obj=str(obj))
    rng = np.random.default_rng(18)
    x = WALL['x0']
    while x < WALL['x1']:                         # 右侧大石堆：两排，彼此重叠
        for row in (0, 1):
            Hh = float(rng.uniform(0.6, 1.05)) * (1.0 + 0.25 * row)
            rid = WALL_ROCKS[rng.integers(len(WALL_ROCKS))]
            obj, _ = rock_asset_uniform(rid, Hh)
            V = np.array([[float(t) for t in l.split()[1:3]] for l in pathlib.Path(obj).read_text().splitlines() if l.startswith('v ')])
            yaw = float(rng.uniform(-25, 25)) + (90.0 if row else 0.0)
            th = np.radians(yaw); R2 = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
            ext = (V @ R2.T)
            half_y = float(np.abs(ext[:, 1]).max())
            yc = WALL['y_inner'] - half_y - row * float(rng.uniform(0.6, 1.1)) + float(rng.uniform(-0.05, 0.05))
            objs.append({'mesh_file': str(obj), 'x': x + float(rng.uniform(-0.1, 0.1)), 'y': yc, 'yaw_deg': yaw, 'height_m': Hh})
            b = f'obstacle{len(objs) - 1}'; rock_bodies[b] = rid; meta['walls'].append(b)
        x += float(rng.uniform(0.75, 1.05))
    spec['objects'] = objs
    return spec, rock_bodies, meta


def make_env(spec):
    terrain.SPAN = SPAN; terrain.N = NGRID
    env = wheelleg_env.WheelLegEnv(spec, max_seconds=900); env.reset(seed=0)
    return env


def place(env, x, y, yaw=0.0):
    import mujoco
    q = env.data.qpos
    q[0], q[1] = x, y
    q[3:7] = [np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)]
    env.data.qvel[:] = 0
    mujoco.mj_forward(env.model, env.data)


def settle(env, steps=60):
    for _ in range(steps):
        env.step_command(joint_targets_rad=np.array([[0, 0.85, -1.65]] * 4), wheel_brake=np.ones(4, bool))
