"""Seeded scan/Lux shape-pair worlds and an explicitly planar sensor simulator.

Cached reconstructions are relocated together with scans. This is a shape-prior
experiment, NOT a fresh photo-to-Lux call or an RGB-D sensor reproduction.
Truth is accessible only to simulation, offline teacher labels and scoring.
"""
import hashlib
import heapq
import json
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[2]
DIRECTIONS = np.array([[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1],[0,-1],[1,-1]])


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_library(out):
    import trimesh
    index = ROOT / 'evidence/web-assets/overlays/index.json'
    records = []
    for row in read(index)['models']:
        # Multi-stone targets are kept together as a composite shape prior.
        scene = trimesh.load(ROOT / row['path'], force='scene', process=False)
        a = scene.geometry['truth_amber_035'].vertices
        b = scene.geometry['imagined_greyblue'].vertices
        a = np.column_stack([a[:,0], -a[:,2]])
        b = np.column_stack([b[:,0], -b[:,2]])
        origin = (a.min(0) + a.max(0)) / 2
        truth = a[ConvexHull(a).vertices] - origin
        prior = b[ConvexHull(b).vertices] - origin
        records.append({'task_id':row['task_id'], 'source':row['path'],
                        'source_sha256':sha(ROOT / row['path']),
                        'truth_polygon':truth.tolist(), 'prior_polygon':prior.tolist(),
                        'origin_world_xy':origin.tolist(),
                        'height_m':max(r['placement']['height'] for r in row['source_truth'])})
    result = {'schema':'beforestep-relocated-cached-shape-pairs/v1',
              'scope':'Relocated existing Lux/scan pairs; no new generated task or input-image identity claim',
              'index_source':str(index.relative_to(ROOT)), 'index_sha256':sha(index), 'pairs':records}
    write(out, result)
    return result


def inside(points, polygon):
    # Convex hull vertices have counter-clockwise orientation.
    p = np.asarray(polygon)
    edge = np.roll(p, -1, axis=0) - p
    delta = points[:,None,:] - p[None,:,:]
    return ((edge[None,:,0]*delta[:,:,1] - edge[None,:,1]*delta[:,:,0]) >= -1e-7).all(1)


class World:
    def __init__(self, cfg, library, split, seed):
        self.cfg, self.seed, self.split = cfg, int(seed), split
        self.shape = tuple(cfg['grid'])
        self.res = cfg['resolution_m']
        self.rng = np.random.default_rng(seed)
        n, m = self.shape
        self.points = np.stack(np.meshgrid(np.arange(n), np.arange(m), indexing='ij'), -1)
        self.start = np.array([2, int(self.rng.integers(4, m-4))])
        self.goal = np.array([n-3, int(self.rng.integers(4, m-4))])
        p = cfg[split]
        self.rocks = []
        self.raw = np.zeros(self.shape, bool)
        self.border = np.zeros(self.shape, bool)
        self.border[[0,-1],:] = True
        self.border[:,[0,-1]] = True
        self.shadow = np.zeros(self.shape, bool)
        self.sun_elevation_deg = float(self.rng.uniform(5, 35))
        self.sun_azimuth_deg = float(self.rng.uniform(-180, 180))
        points_m = self.points.reshape(-1,2)*self.res
        for _ in range(int(self.rng.integers(p['rocks'][0], p['rocks'][1]+1))):
            pair = library['pairs'][int(self.rng.integers(len(library['pairs'])))]
            scale = float(self.rng.uniform(*p['scale']))
            yaw = float(self.rng.uniform(-np.pi, np.pi))
            rotation = np.array([[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]])
            center = np.array([self.rng.uniform(5, n-6), self.rng.uniform(3, m-3)])*self.res
            truth = np.asarray(pair['truth_polygon']) @ rotation.T * scale + center
            prior = np.asarray(pair['prior_polygon']) @ rotation.T * scale + center
            mask = inside(points_m, truth).reshape(self.shape)
            # Reject placements on start/goal BEFORE observing policy outcomes.
            if min(np.linalg.norm(truth-self.start*self.res,axis=1).min(),
                   np.linalg.norm(truth-self.goal*self.res,axis=1).min()) < .9:
                continue
            prior_mask = inside(points_m, prior).reshape(self.shape)
            height = pair['height_m']*scale
            shadow_cells = int(min(12, height/np.tan(np.radians(self.sun_elevation_deg))/self.res))
            angle = np.radians(self.sun_azimuth_deg)
            shadow = mask.copy()
            for k in range(1, shadow_cells+1):
                offset = [int(round(k*np.cos(angle))), int(round(k*np.sin(angle)))]
                shadow |= ndimage.shift(mask.astype(np.uint8),offset,order=0,mode='constant') > 0
            self.shadow |= shadow
            self.raw |= mask
            self.rocks.append({'task_id':pair['task_id'], 'source':pair['source'],
                               'source_sha256':pair['source_sha256'], 'scale':scale,
                               'yaw_rad':yaw,'center_m':center.tolist(),'height_m':height,
                               'truth_polygon':truth.tolist(),'prior_polygon':prior.tolist(),
                               'mask':mask,'prior_mask':prior_mask})
        self.raw |= self.border
        self.shadow &= ~self.raw
        self.blocked = ndimage.distance_transform_edt(~self.raw)*self.res <= cfg['robot_radius_m']
        self.teacher_distance, self.teacher_action = shortest_paths(self.blocked, self.goal)
        self.reachable = np.isfinite(self.teacher_distance[tuple(self.start)])

    def manifest(self):
        return {'seed':self.seed,'split':self.split,'start_cell':self.start.tolist(),
                'goal_cell':self.goal.tolist(),'grid':list(self.shape),'resolution_m':self.res,
                'sun_elevation_deg':self.sun_elevation_deg,'sun_azimuth_deg':self.sun_azimuth_deg,
                'oracle_reachable':bool(self.reachable),
                'rocks':[{k:v for k,v in r.items() if k not in ('mask','prior_mask')} for r in self.rocks]}

    def sensor(self, position, heading=0., panorama=False):
        delta = self.points.reshape(-1,2)-position
        distance = np.linalg.norm(delta,axis=1)*self.res
        angle = (np.arctan2(delta[:,1],delta[:,0])-heading+np.pi)%(2*np.pi)-np.pi
        visible = distance <= self.cfg['sensor_range_m']
        if not panorama:
            visible &= abs(angle) <= np.radians(self.cfg['sensor_fov_deg']/2)
        # Each planar ray is checked against actual rocks; endpoints remain visible.
        steps = np.linspace(0, 1, max(self.shape)*2, endpoint=False)[1:]
        samples = np.rint(position[None,None,:]+delta[:,None,:]*steps[None,:,None]).astype(int)
        samples[:,:,0] = samples[:,:,0].clip(0,self.shape[0]-1)
        samples[:,:,1] = samples[:,:,1].clip(0,self.shape[1]-1)
        hit = self.raw[samples[:,:,0],samples[:,:,1]]
        endpoint = np.all(samples == self.points.reshape(-1,2)[:,None,:],axis=-1)
        visible &= ~(hit & ~endpoint).any(1)
        visible = visible.reshape(self.shape) & ~self.shadow
        visible |= np.linalg.norm(self.points-position,axis=-1)*self.res < .65
        return visible

    def observe(self, position, heading, known=None, panorama=False, prior_enabled=True):
        known = np.zeros(self.shape,bool) if known is None else known.copy()
        known |= self.sensor(position,heading,panorama)
        known |= self.border
        prior, available = np.zeros(self.shape,bool), np.zeros(self.shape,bool)
        if prior_enabled:
            for rock in self.rocks:
                if (rock['mask'] & known).any():
                    prior |= rock['prior_mask']
                    # Support is a declared contextual region, NOT true geometry.
                    center = np.array(rock['center_m'])/self.res
                    available |= np.linalg.norm(self.points-center,axis=-1)*self.res < 2.5
        features = np.stack([self.raw & known, known, prior, available]).astype(np.float32)
        return features, known


def shortest_paths(blocked, goal):
    n,m = blocked.shape
    dist = np.full((n,m), np.inf)
    actions = np.full((n,m), -1, np.int64)
    g = tuple(map(int,goal))
    if blocked[g]:
        return dist, actions
    dist[g] = 0.
    queue = [(0.,*g)]
    while queue:
        value,x,y = heapq.heappop(queue)
        if value != dist[x,y]:
            continue
        for a, (dx,dy) in enumerate(DIRECTIONS):
            u,v = x-dx,y-dy
            if not (0<=u<n and 0<=v<m) or blocked[u,v]:
                continue
            if dx and dy and (blocked[x,v] or blocked[u,y]):
                continue
            proposed = value+float(np.hypot(dx,dy))
            if proposed < dist[u,v]:
                dist[u,v],actions[u,v] = proposed,a
                heapq.heappush(queue,(proposed,int(u),int(v)))
    return dist,actions


def known_blocked(features, cfg):
    return ndimage.distance_transform_edt(features[0] < .5)*cfg['resolution_m'] <= cfg['robot_radius_m']


def safe_transition(blocked, position, action):
    next_position = position+DIRECTIONS[action]
    x,y = next_position
    if not (0<=x<blocked.shape[0] and 0<=y<blocked.shape[1]) or blocked[x,y]:
        return False
    dx,dy = DIRECTIONS[action]
    return not (dx and dy and (blocked[position[0]+dx,position[1]] or blocked[position[0],position[1]+dy]))
