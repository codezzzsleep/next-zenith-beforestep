"""Frozen production RGB-D renderer, isolated scene output and correct initialization."""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.visualization import camera as VZ
from .geometry import apply_scene


class ProductionSensor:
    def __init__(self,definition,out):
        from .runtime_cache import use
        with use():self._initialize(definition,out)

    def _initialize(self,definition,out):
        import mujoco
        self.mj=mujoco;self.definition=definition;apply_scene(definition)
        spec,rb,self.meta=S.scene_spec(Path(out))
        spec['start']=list(definition['start'])
        spec['_hfield_dir']=str((Path(out)/'heightfield').resolve())
        self.env=S.make_env(spec)
        S.place(self.env,*definition['start']);S.settle(self.env)
        # Runtime render mesh is reproducible from the saved scene definition.
        # A per-process scratch slot avoids retaining thousands of identical
        # or one-use terrain meshes; existing evidence and caches are untouched.
        import tempfile,os
        scratch=Path(tempfile.gettempdir())/f'beforestep-arena-render-{os.getpid()}'
        scratch.mkdir(exist_ok=True);mesh=scratch/'terrain.obj'
        if mesh.exists():mesh.unlink()
        original=S.terrain_visual_obj
        S.terrain_visual_obj=lambda path,**kw: original(mesh,**kw)
        try:self.vm=VZ.video_model(self.env,rb,width=1600,height=1200,off=VZ.HI)
        finally:S.terrain_visual_obj=original
        self.vm.hi_sensor=True

    def set_qpos(self,qpos):
        self.env.data.qpos[:]=qpos;self.env.data.qvel[:]=0
        self.mj.mj_forward(self.env.model,self.env.data)

    def at(self,position,yaw,qpos=None,see_dark=False):
        apply_scene(self.definition)
        if qpos is not None:self.set_qpos(qpos)
        else:S.place(self.env,*position,yaw=yaw)
        return N.observe(self.vm,self.env,dark_thr=0. if see_dark else .10)

    def close(self):VZ.release(self.vm)


def transplanted_qpos(capsule):
    q=np.array(capsule['robot_qpos_world'],float);T=np.asarray(capsule['transplant_world_from_source'])
    q[:3]=q[:3]@T[:3,:3].T+T[:3,3]
    rot=Rotation.from_quat(q[[4,5,6,3]])
    quat=(Rotation.from_matrix(T[:3,:3])*rot).as_quat();q[3:7]=quat[[3,0,1,2]]
    return q
