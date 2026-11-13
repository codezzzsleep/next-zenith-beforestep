"""Measure four development RGB-D blind regions before any paid generation."""
import argparse, json, sys, time, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import *
from experimental.crossing.scene import generate, DEVELOPMENT_SEEDS
from beforestep import scene as S
from beforestep.visualization import camera as VZ
from beforestep.geometry import camera as camera_io
from beforestep.observation import images as inputs
from PIL import Image


def configure(scene):
    S.SCENE_ID=scene['spec']['name']; S.TERRAIN={'type':'plain','craters':[],'right_wall':False}
    S.SUN_EL_DEG=10.; S.SUN_AZ_DEG=scene['sun']['azimuth_deg']


def observe(seed, revision=None):
    scene=generate(seed,revision);folder=Path(scene['truth_mesh']).parents[1]
    out=folder/'observation'; result=out/'blindness.json'
    if result.exists(): return json.loads(result.read_text())
    configure(scene);out.mkdir(parents=True,exist_ok=True)
    identity={'seed':seed,'revision':scene['revision'],'pid':os.getpid(),
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'experimental/crossing/scene.py',ROOT/'experimental/crossing/runtime.py']},
        'stage':'zero-paid RGB-D blind-region measurement'}
    write(out/'identity.json',identity)
    e=WheelLegEnv(scene['spec'],control_hz=50,max_seconds=240,nav_base=False,tip_deg=60)
    q=e.data.qpos.copy();q[:2]=scene['observation_stop'];e.data.qpos[:]=q;e.data.qvel[:]=0;mujoco.mj_forward(e.model,e.data)
    rec=Record(e);rec.frame('initial');assert transition(rec,stance_array(STANCE),2.,'park-and-observe')
    rec.save(out/'parking');write(out/'parking/result.json',{'contact':rec.summary(),'scene':scene,'phase':'parking'})
    vm=VZ.video_model(e,scene['rock_bodies'],width=1600,height=1200,off=(4040,3030));vm.hi_sensor=True;vm.sync(e.data.qpos)
    try:
        hi,dh=VZ.render_cam(vm,hi=True)
        dark_hi=VZ.dark_mask(hi,.10)
        cid=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_CAMERA,'front_cam')
        r=VZ.hi_renderer(vm);r.enable_segmentation_rendering();r.update_scene(vm.d,camera=cid,scene_option=vm.opt)
        seg=r.render().copy();r.disable_segmentation_rendering()
        gids=vm.rock_geoms['obstacle0'];segmask=np.isin(seg[:,:,0],gids)&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
        rgb=np.asarray(Image.fromarray(hi).resize((1600,1200),Image.LANCZOS))
        depth=np.asarray(Image.fromarray(dh.astype(np.float32),mode='F').resize((1600,1200),Image.NEAREST))
        target=np.asarray(Image.fromarray(segmask.astype(np.uint8)*255).resize((1600,1200),Image.NEAREST))>127
        dark=VZ.dark_mask(rgb,.10)
        snap=camera_io.capture(vm.m,vm.d,cid,1600,1200);snap_hi=camera_io.capture(vm.m,vm.d,cid,4040,3030)
        depth_valid=np.where(dark,np.nan,depth).astype(np.float32)
        p,ys,xs=camera_io.unproject_depth(depth_valid,snap)
        keep=target[ys,xs]&(p[:,2]>=.04)
        points=p[keep];assert len(points)>2000,'Insufficient target lit pixels; retain this input attempt'
        mask=np.zeros(depth.shape,bool);mask[ys[keep],xs[keep]]=True
        mask_hi=segmask&~dark_hi
        # Same >=4cm stone observation threshold as the frozen pipeline.
        for y0 in range(0,3030,192):
            blk=np.where(dark_hi[y0:y0+192],np.nan,dh[y0:y0+192]).astype(float)
            pts,yy,xx=camera_io.unproject_depth(blk,dict(snap_hi,intrinsics=dict(snap_hi['intrinsics'],cy=snap_hi['intrinsics']['cy']-y0)))
            zmask=np.zeros(blk.shape,bool);zmask[yy,xx]=pts[:,2]>=.04
            mask_hi[y0:y0+192]&=zmask
        x0,y0=map(float,e.data.qpos[:2]);local=points-np.array([x0,y0,0.])
        sl=dict(snap);sl['world_pos']=(np.array(snap['world_pos'])-np.array([x0,y0,0.])).tolist()
        sl['frame']='local';sl['local_frame']={'x0':x0,'y0':y0,'yaw0':0.}
        Image.fromarray(rgb).save(out/'rgb.png');Image.fromarray(hi).save(out/'rgb_gen.png')
        Image.fromarray(mask.astype(np.uint8)*255).save(out/'mask.png');Image.fromarray(dark.astype(np.uint8)*255).save(out/'dark.png')
        np.save(out/'depth.npy',depth_valid);np.save(out/'visible_points.npy',local);np.save(out/'visible_points_world.npy',points)
        box=inputs._pixel_box(mask_hi);native=box[3]-box[1]+1
        proto=json.loads((ROOT/'config/protocol.json').read_text());variants=inputs._variants(hi,mask_hi,box,out/'gen',native,proto)
        st={'schema':'v8-target-state/v1','target':'T','look':'look1','visible':{
            'x_front':float(local[:,0].min()),'y_center':float((local[:,1].min()+local[:,1].max())/2),
            'W_vis':float(np.ptp(local[:,1])),'H_vis':float(local[:,2].max())},
            'local_frame':{'x0':x0,'y0':y0,'yaw0':0.},'robot_qpos_world':e.data.qpos.tolist(),'t_sim':e.t,
            'crop_native_px':native,'native_ok':variants['native_ok'],'crops':variants['variants'],
            'observation_sha256':{name:sha(out/name) for name in ['rgb.png','depth.npy','mask.png','dark.png']}}
        write(out/'state.json',st);write(out/'camera_world.json',snap)
        write(out/'observation.json',{'schema':'observation/v8','label':f'crossing_{scene["revision"]}_{seed}',
            'camera':sl,'intrinsics':sl['intrinsics'],'image':'rgb.png','target':'T','mask_px':int(mask.sum()),
            'mask_source':'ideal simulated target segmentation from visible RGB-D pixels only; lit and >=4cm; no hidden geometry passed to admission',
            'dark_rule':'luminance < 0.10: no depth, same frozen passive camera rule'})
        tracks=[]
        for truth in scene['truth_geometry']['tracks']:
            y=truth['track_y_m'];p=points[np.abs(points[:,1]-y)<=truth['band_halfwidth_m']]
            observed={'near':float(p[:,0].min()),'far':float(p[:,0].max()),'high':float(p[:,2].max()),'points':len(p)} if len(p) else None
            tracks.append({'track_y_m':y,'truth':truth,'observed':observed,
                'unseen_far_m':truth['far']-observed['far'] if observed else None,
                'unseen_height_m':truth['high']-observed['high'] if observed else None})
        report={'schema':'beforestep-crossing-blindness/v1','seed':seed,'revision':scene['revision'],
            'camera_world':snap,'camera_to_near_m':float(min(scene['truth_geometry']['near'])-snap['world_pos'][0]),
            'leg_stance':'STANCE; reached through env.step_command, 50Hz control/500Hz physics',
            'sun':scene['sun'],'tracks':tracks,'crop_native_height_px':native,
            'native_ok':variants['native_ok'],'visible_points':len(points),'new_lux_tasks':0,
            'source_identity':identity,'input_sha256':st['observation_sha256'],
            'limitations':['Ideal target segmentation; passive-dark depth suppressed.',
                'True far edges include the low >=4mm rear skirt; observed stone filter is >=4cm, as in the frozen pipeline.']}
        write(result,report)
        return report
    finally:VZ.release(vm)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int);parser.add_argument('--revision');args=parser.parse_args()
    rows=[]
    for seed in [args.seed] if args.seed else DEVELOPMENT_SEEDS:
        row=observe(seed,args.revision);rows.append(row)
        print(json.dumps({k:row[k] for k in ['seed','camera_to_near_m','tracks','crop_native_height_px','native_ok']}),flush=True)
    write(ROOT/'evidence/crossing/development-blindness.json',{'stage':'zero-paid development; excluded from statistics','scenes':rows})
