"""Seeded scanned-rock thresholds; development ranges precede preregistration."""
import io
import json
import tarfile
from pathlib import Path
import numpy as np
import trimesh
from .runtime import ROOT, OUT, write, sha

DEVELOPMENT_SEEDS = [11001, 11002, 11005, 11006]
SOURCE_ROCKS = ['rock_07', 'moon_rock_03', 'moon_rock_04']
GENERATOR = {'revision': 'scene-dev-v5', 'height_m': [.14, .15],
             'shallow_depth_m': [.11, .15], 'deep_depth_m': [.22, .30],
             'width_m': [1.4, 1.6], 'yaw_deg': [-8., 8.], 'lateral_m': [-.035, .035],
             'gap_m': [.9, 1.1], 'sun_azimuth_deg': [-8., 8.],
             'camera_to_near_m': [.58, .62], 'threshold_pitch_deg': 90., 'observation_yaw_deg': -45., 'sun_elevation_deg': 10.,
             'shallow_probability': .65, 'ridge_floor_target_m': .10, 'wheel_time_limit_s': 240.,
             'speed_cap_m_s': .15, 'observation_stance': 'STANCE', 'goal_x_m': 4.0, 'goal_lateral_tolerance_m': .4}


def source_mesh(name):
    archive = ROOT / 'assets/runtime-rocks.tar.gz'
    with tarfile.open(archive, 'r:gz') as f:
        info = json.load(f.extractfile(name + '/rock.json'))
        member = name + '/h1/body_vis.obj'; payload = f.extractfile(member).read()
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    assert digest == next(r for r in info['levels'] if r['level'] == 1)['vis_obj_sha256']
    return trimesh.load(io.BytesIO(payload), file_type='obj', force='mesh', process=False), {
        'archive': 'assets/runtime-rocks.tar.gz', 'member': member, 'member_sha256': digest,
        'rock': name, 'url': info['source_url'], 'license': info['license'], 'authors': info['authors']}


def transformed(name, height, depth, width, near, lateral, yaw, pitch=0.):
    mesh, origin = source_mesh(name)
    th = np.deg2rad(yaw); rot = np.eye(4)
    rot[:2, :2] = [[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]
    pr=np.deg2rad(pitch); tilted=np.eye(4);tilted[:3,:3]=[[np.cos(pr),0,np.sin(pr)],[0,1,0],[-np.sin(pr),0,np.cos(pr)]]
    rot=rot@tilted
    mesh.apply_transform(rot); lo, hi = mesh.bounds
    scale = np.array([depth, width, height]) / (hi - lo)
    affine = np.eye(4); affine[:3, :3] = np.diag(scale)
    affine[:3, 3] = [near - lo[0]*scale[0], lateral - (lo[1]+hi[1])*.5*scale[1], -lo[2]*scale[2]]
    mesh.apply_transform(affine)
    return mesh, {**origin, 'world_from_source': (affine @ rot).tolist()}


def profile(mesh, y, minimum_z=.004):
    tri = mesh.triangles
    hit = (tri[:, :, 1].min(axis=1) <= y) & (tri[:, :, 1].max(axis=1) >= y)
    tri = tri[hit]; points = []
    for a, b in [(0,1),(1,2),(2,0)]:
        p, q = tri[:, a], tri[:, b]; dy = q[:,1] - p[:,1]
        good = (np.abs(dy) > 1e-12) & ((p[:,1]-y)*(q[:,1]-y) <= 0)
        u = (y-p[good,1]) / dy[good]
        points.append(p[good] + u[:,None]*(q[good]-p[good]))
    points = np.concatenate(points) if points else np.empty((0,3))
    points = points[points[:,2] >= minimum_z]
    if not len(points): return {'near': None, 'far': None, 'high': None}
    return {'near': float(points[:,0].min()), 'far': float(points[:,0].max()), 'high': float(points[:,2].max())}


def track_geometry(mesh, lateral=0., band_halfwidth=.025, minimum_z=.004):
    rows = []
    for sign in (-1, 1):
        ys = lateral + sign*.192 + np.linspace(-band_halfwidth, band_halfwidth, 11)
        profiles = [profile(mesh, float(y), minimum_z) for y in ys]
        profiles = [p for p in profiles if p['near'] is not None]
        rows.append({'near': min((p['near'] for p in profiles), default=None),
                     'far': max((p['far'] for p in profiles), default=None),
                     'high': max((p['high'] for p in profiles), default=None),
                     'track_y_m': lateral + sign*.192, 'band_halfwidth_m': band_halfwidth})
    return {'near': [r['near'] for r in rows], 'far': [r['far'] for r in rows],
            'high': [r['high'] for r in rows], 'lateral': lateral, 'tracks': rows,
            'minimum_stone_z_m': minimum_z}


def save_mesh(folder, mesh, provenance):
    folder.mkdir(parents=True, exist_ok=True)
    mesh.export(folder/'truth.obj'); mesh.export(folder/'truth.glb')
    write(folder/'manifest.json', {'coordinate_frame': 'world', 'parts': ['truth.obj'],
        'parts_sha256': {'truth.obj': sha(folder/'truth.obj')}, 'source': provenance,
        'bounds_m': mesh.bounds.tolist(), 'collision': 'MuJoCo mesh convex hull; observation uses original scan surface'})
    return {'posed_dir': str(folder)}


def generate(seed, revision=None):
    revision = revision or GENERATOR['revision']; folder = OUT/'development'/revision/f'seed-{seed}'
    if (folder/'scene.json').exists(): return json.loads((folder/'scene.json').read_text())
    rng = np.random.default_rng(seed); shallow = rng.random() < GENERATOR['shallow_probability']; name = str(rng.choice(SOURCE_ROCKS))
    h = float(rng.uniform(*GENERATOR['height_m']))
    depth_range = GENERATOR['shallow_depth_m'] if shallow else GENERATOR['deep_depth_m']
    depth = float(rng.uniform(*depth_range)); width = float(rng.uniform(*GENERATOR['width_m']))
    yaw = float(rng.uniform(*GENERATOR['yaw_deg'])); lateral = float(rng.uniform(*GENERATOR['lateral_m']))
    gap = float(rng.uniform(*GENERATOR['gap_m'])); near = 3.
    mesh, provenance = transformed(name,h,depth,width,near,lateral,yaw,GENERATOR['threshold_pitch_deg'])
    objects = [save_mesh(folder/'threshold',mesh,provenance)]
    bodies = {'obstacle0': name}
    for index, side in enumerate((-1,1), start=1):
        gate, origin = transformed('rock_07' if side < 0 else 'moon_rock_03',.75,.95,3.5,
                                   near-.3,side*(gap/2+1.75),0.)
        objects.append(save_mesh(folder/f'gate-{index}',gate,origin)); bodies[f'obstacle{index}']=origin['rock']
    distance = float(rng.uniform(*GENERATOR['camera_to_near_m']))
    obsyaw=np.deg2rad(GENERATOR['observation_yaw_deg'])
    stop = [near-distance-.42*np.cos(obsyaw),distance-.42*np.sin(obsyaw)]
    az = float(rng.uniform(*GENERATOR['sun_azimuth_deg']))
    spec = {'name': f'crossing-{revision}-{seed}', 'seed': seed, 'start': stop, 'goal_x': GENERATOR['goal_x_m'],
        'front_cam': {'pos': [.42,0.,-.00125], 'pitch_deg': -24.83, 'fovy': 70.},
        'terrain': {'kind': 'flat', 'span': 16, 'field_x_max': 15.95},
        '_hfield_dir': str(OUT/'runtime/heightfields'), 'objects': objects,
        'channel': {'center_y': 0., 'half_width': 2.}, 'skill_cfg': {'task': 'M'},
        'init_perturbation': {'lateral_m': 0., 'yaw_rad': 0.}}
    ridge = [profile(mesh,float(y))['high'] for y in np.linspace(-gap/2,gap/2,51)]
    scene = {'schema': 'beforestep-crossing-scene/v1', 'seed': seed, 'revision': revision, 'generator': GENERATOR,
        'dimensions_m': {'height': h, 'depth': depth, 'width': width}, 'gap_m': gap,
        'lateral_m': lateral, 'yaw_deg': yaw, 'sun': {'elevation_deg':10.,'azimuth_deg':az},
        'camera_nominal_distance_m': distance, 'observation_stop': stop, 'observation_yaw_deg': GENERATOR['observation_yaw_deg'], 'threshold_pitch_deg': GENERATOR['threshold_pitch_deg'], 'goal':[GENERATOR['goal_x_m'],0.],
        'ridge_min_high_m': min(ridge), 'ridge_meets_target': min(ridge)>=.10,
        'spec':spec,'rock_bodies':bodies,'truth_geometry':track_geometry(mesh),
        'truth_mesh':str(folder/'threshold/truth.obj'), 'development_excluded_from_statistics': True}
    write(folder/'scene.json',scene)
    return scene
