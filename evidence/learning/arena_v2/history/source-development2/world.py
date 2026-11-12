"""Seeded finite-observation arenas; all Lux candidates retain their original rig."""
import numpy as np
from beforestep import scene as S
from beforestep.navigation import map as N
from .common import ROOT,OUT,read
from .capsules import transplant
from .geometry import scene_height,apply_scene,geometric_observation,camera_at


class World:
    def __init__(self,seed,split='development',cfg=None,library=None):
        self.seed=int(seed);self.split=split;self.cfg=cfg or read(ROOT/'experimental/arena/parameters.json')
        library=library or read(OUT/'capsules.json');rng=np.random.default_rng(seed)
        side='heldout' if split in ('sealed','ood') else 'training_side'
        pool=[c for c in library['capsules'] if c['eligible'] and c['split']==side and c.get('source_look') in self.cfg.get('source_looks',['look1','look2','look3','look4'])]
        source=pool[int(rng.integers(len(pool)))];yaw=float(rng.uniform(*self.cfg['capsule_rotation_deg']))
        shift=[float(rng.uniform(*self.cfg['capsule_translation_x_m'])),float(rng.uniform(*self.cfg['capsule_translation_y_m']))]
        self.capsule=transplant(source,yaw,shift)
        c=self.capsule;frame=c['local_frame'];self.start=np.array([frame['x0'],frame['y0']]);self.heading=frame['yaw0']
        family=list(self.cfg['families'])[int(rng.integers(len(self.cfg['families'])))];self.family=family
        rocks={f'capsule_{k}':dict(p) for k,p in c['truth_rocks'].items()}
        rocks.update({f'background_{k}':dict(p) for k,p in c.get('background_rocks',{}).items()})
        extras=self.cfg['ood_extra_rocks'] if split=='ood' else self.cfg['families'][family]
        count=int(rng.integers(extras[0],extras[1]+1))
        assets=[p.name for p in (ROOT/'assets/rocks').iterdir() if p.is_dir()]
        for i in range(count):
            p={'rock':assets[int(rng.integers(len(assets)))],
               'height':float(rng.uniform(*self.cfg['extra_rock_height_m'])),
               'x':float(rng.uniform(*self.cfg['extra_rock_x_m'])),
               'y':float(rng.uniform(*self.cfg['extra_rock_y_m'])),
               'yaw':float(rng.uniform(*self.cfg['extra_rock_yaw_deg']))}
            if np.hypot(p['x']-self.start[0],p['y']-self.start[1])>.95:rocks[f'unimagined_{i}']=p
        goal=[float(rng.uniform(*self.cfg['goal_x_m'])),float(rng.uniform(*self.cfg['goal_y_m']))]
        craters=[]
        if family=='crater' or split=='ood':
            craters=[{'center':[float(rng.uniform(5.0,8.0)),float(rng.choice([-1.4,1.7]))],
                      'radius':float(rng.uniform(*self.cfg['crater_radius_m'])),
                      'depth':float(rng.uniform(*self.cfg['crater_depth_m']))}]
        source_terrain=S.terrain_settings(c['source_scene'])
        from .common import transform_points
        old_craters=[{**p,'center':transform_points([[*p['center'],0]],c['transplant_world_from_source'])[0,:2].tolist()} for p in source_terrain['craters']]
        self.definition={'id':f'arena_{split}_{seed}','rocks':rocks,'start':self.start.tolist(),
                         'first_stop':self.start.tolist(),'goal':goal,
                         'terrain':{'type':source_terrain['type'],'right_wall':source_terrain['right_wall'],'craters':old_craters+craters},
                         'sun':c['sun'],'asset_cache_precision':c['source_scene'].get('asset_cache_precision','legacy_mm'),'rehearse_reference':False}
        self.goal=np.array(goal);self.height,self.ground=scene_height(self.definition)
        self.raw=self.height>=N.ROCK_Z;self.nogo=N.prior_nogo()
        self.first_camera=c['camera_world'];self.look_count=0
        self._sensor=None;self._sensor_cache={}
        # Truth is used for simulator collision/reachability, never in the policy card.
        self.truth_occ=self.raw|self.nogo
        self.launch_clear=not (self.raw&N.swept([self.start],r=self.cfg.get('known_launch_radius_m',N.R_DRIVE))).any()

    def manifest(self):
        return {'schema':'beforestep-arena-world/v2','seed':self.seed,'split':self.split,'family':self.family,
                'definition':self.definition,'capsule_id':self.capsule['id'],
                'capsule_scene':self.capsule['scene'],'transplant':self.capsule['transplant_world_from_source'],
                'deviations':self.capsule['deviations'],
                'unimagined_rocks':sum(k.startswith('unimagined') for k in self.definition['rocks']),
                'real_task_ids':[c['task_id'] for c in self.capsule['candidates']],
                'known_launch_radius_m':self.cfg.get('known_launch_radius_m',N.R_DRIVE),'launch_clear':bool(self.launch_clear)}

    def observe(self,position,yaw,see_dark=False):
        apply_scene(self.definition)
        camera=self.first_camera if self.look_count==0 else camera_at(position,yaw)
        first=self.look_count==0
        self.look_count+=1
        if self.cfg.get('sensor')=='production_rgbd':
            key=('first' if first else (tuple(np.round(position,6)),round(float(yaw),6)),see_dark)
            if key not in self._sensor_cache:
                from .sensor import ProductionSensor,transplanted_qpos
                import os,tempfile
                if self._sensor is None:
                    self._sensor=ProductionSensor(self.definition, __import__('pathlib').Path(tempfile.gettempdir())/f'beforestep-arena-sensor-{os.getpid()}')
                ob=self._sensor.at(position,yaw,qpos=transplanted_qpos(self.capsule) if first else None,see_dark=see_dark)
                self._sensor_cache[key]={k:ob[k] for k in ['state','zmax','cam_pos','cam_mat','fovy']}
            return self._sensor_cache[key]
        return geometric_observation(self.height,self.ground,camera,self.definition['sun'],see_dark)

    def reset_sensor(self):self.look_count=0

    def close(self):
        if self._sensor is not None:self._sensor.close();self._sensor=None

    def imagination(self):
        candidates=[]
        for row in self.capsule['candidates']:
            if not row['registration_available']:continue
            xy=np.asarray(row['footprint_world_xy']).reshape(-1,2);mask=np.zeros((N.NX,N.NY),bool)
            ij=np.floor((xy-[N.X0,N.Y0])/N.RES).astype(int)
            valid=(ij[:,0]>=0)&(ij[:,0]<N.NX)&(ij[:,1]>=0)&(ij[:,1]<N.NY)
            mask[tuple(ij[valid].T)]=True
            candidates.append({'mask':mask,'admitted':row['frozen_admitted'],'metrics':row['metrics'],
                               'task_id':row['task_id'],'world_from_generated':row['world_from_generated'],'glb':row['glb']})
        return candidates
