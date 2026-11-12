"""5cm height maps rasterized from original scan triangles; geometric visibility."""
from functools import lru_cache
import numpy as np
from scipy import ndimage
from beforestep import scene as S
from beforestep.navigation import map as N, shadows as SH
from .common import OUT,sha,rigid,transform_points


def apply_scene(definition):
    S.ROCKS=definition['rocks'];S.START=tuple(definition['start']);S.STOP1=tuple(definition['first_stop']);S.GOAL=tuple(definition['goal'])
    S.SCENE_ID=definition['id'];S.TERRAIN=S.terrain_settings(definition)
    sun=S.sun_settings(definition);S.SUN_EL_DEG=sun['elevation_deg'];S.SUN_AZ_DEG=sun['azimuth_deg']
    S.ASSET_CACHE_PRECISION=definition.get('asset_cache_precision','exact');S.REHEARSE_REFERENCE=False


@lru_cache(maxsize=48)
def canonical_mesh(rock,height,precision='exact'):
    import trimesh
    S.ASSET_CACHE_PRECISION=precision
    from .runtime_cache import use
    with use():path,_=S.rock_asset_uniform(rock,height)
    return trimesh.load(path,force='mesh',process=False)


def world_mesh(p,precision='exact'):
    mesh=canonical_mesh(p['rock'],float(p['height']),precision).copy()
    mesh.apply_transform(rigid(p['yaw'],[p['x'],p['y']]))
    return mesh


def surface_height(mesh,shape=(N.NX,N.NY),origin=(N.X0,N.Y0)):
    """Maximum triangle surface intersecting a cell, using frozen rasterizer."""
    from .numerical import triangle_height
    return triangle_height(np.asarray(mesh.vertices),np.asarray(mesh.faces),shape,np.array(origin),N.RES)


def scene_height(definition,include_walls=False):
    apply_scene(definition)
    ground=S.height_at(N.GX,N.GY);height=ground.copy()
    for p in definition['rocks'].values():
        key=sha_text(p,definition.get('asset_cache_precision','exact'))
        cache=OUT/'geometry'/f'{key}.npy'
        if cache.exists():z=np.load(cache)
        else:
            z=surface_height(world_mesh(p,definition.get('asset_cache_precision','exact')))
            cache.parent.mkdir(parents=True,exist_ok=True);np.save(cache,z.astype(np.float32))
        height=np.maximum(height,z)
    if include_walls and S.TERRAIN['right_wall']:
        height[N.GY<S.WALL['y_inner']]=1.0
    return height,ground


def sha_text(p,precision):
    import hashlib,json
    return hashlib.sha256(json.dumps([p,precision],sort_keys=True).encode()).hexdigest()


def solar_dark(height,ground,sun):
    el,az=np.radians([sun['elevation_deg'],sun['azimuth_deg']]);toward=np.array([-np.cos(az),np.sin(az)])
    shadow=SH.shadow_from_height(height,ground,toward,np.tan(el))
    # Sloped backlit surfaces have no valid passive depth even at a closer pose.
    gx,gy=np.gradient(height,N.RES);normal=np.stack([-gx,-gy,np.ones_like(height)],-1)
    light=np.array([toward[0]*np.cos(el),toward[1]*np.cos(el),np.sin(el)])
    cosine=(normal@light)/np.linalg.norm(normal,axis=-1)
    backlit=(height>=N.ROCK_Z)&(cosine<=.05)
    return shadow|backlit


def geometric_observation(height,ground,camera,sun,see_dark=False):
    """Finite camera frustum; height rays distinguish occlusion from illumination.

    No close-range visibility override. True geometry is confined to this sensor.
    """
    cam=np.asarray(camera['world_pos']);R=np.asarray(camera['R_world_from_camera'])
    dark=solar_dark(height,ground,sun)
    targets=np.stack([N.GX,N.GY,height],-1)
    pc=(targets-cam)@R;zc=-pc[...,2]
    fovy=camera.get('fovy_deg',camera.get('fovy',70.))
    K=camera.get('intrinsics',{});ratio=K.get('width',512)/K.get('height',512)
    tan=np.tan(np.radians(fovy)/2)
    inview=(zc>.05)&(abs(pc[...,0])<=zc*tan*ratio)&(abs(pc[...,1])<=zc*tan)
    distance=np.linalg.norm(targets-cam,axis=-1);inview &= distance<9.
    ix,iy=np.nonzero(inview);state=np.full((N.NX,N.NY),N.UNSEEN,np.int8);zmax=np.full(state.shape,-np.inf)
    if len(ix):
        end=targets[ix,iy];delta=end-cam
        raylen=np.linalg.norm(delta[:,:2],axis=1)
        steps=int(9/N.RES)+1;t=np.arange(1,steps)/steps
        xyz=cam[None,None,:]+delta[:,None,:]*t[None,:,None]
        si=np.floor((xyz[:,:,0]-N.X0)/N.RES).astype(int);sj=np.floor((xyz[:,:,1]-N.Y0)/N.RES).astype(int)
        inside=(si>=0)&(si<N.NX)&(sj>=0)&(sj<N.NY)
        si=si.clip(0,N.NX-1);sj=sj.clip(0,N.NY-1)
        # Ignore the endpoint cell because rays terminate on its surface.
        endpoint=(si==ix[:,None])&(sj==iy[:,None])
        occluded=inside&~endpoint&(height[si,sj]>xyz[:,:,2]+.06)
        hidden=occluded.any(1)
        first=occluded.argmax(1);firstdark=dark[si[np.arange(len(ix)),first],sj[np.arange(len(ix)),first]]
        state[ix,iy]=np.where(hidden,N.HIDDEN,np.where(height[ix,iy]>=N.ROCK_Z,N.ROCK,N.FREE))
        if not see_dark:
            state[ix,iy]=np.where((~hidden&dark[ix,iy])|(hidden&firstdark),N.DARK,state[ix,iy])
        seen=(state[ix,iy]==N.ROCK)|(state[ix,iy]==N.FREE)
        zmax[ix[seen],iy[seen]]=height[ix[seen],iy[seen]]
        state[(state==N.FREE)&(height<-.08)]=N.NOGO
    return {'state':state,'zmax':zmax,'cam_pos':cam.tolist(),'cam_mat':R.ravel().tolist(),'fovy':fovy}


def camera_at(position,yaw,z=.3832):
    pitch=np.radians(S.CAM['pitch_deg']);c,s=np.cos(yaw),np.sin(yaw)
    # Camera right, up, backwards; yaw0 sees along positive world x.
    R=np.array([[0,-np.sin(pitch),-np.cos(pitch)],[-1,0,0],[0,np.cos(pitch),-np.sin(pitch)]])
    turn=rigid(np.degrees(yaw),[0,0])[:3,:3];R=turn@R
    return {'world_pos':[position[0]+.42*c,position[1]+.42*s,z],
            'R_world_from_camera':R.tolist(),'fovy_deg':70.,'intrinsics':{'width':512,'height':512}}
