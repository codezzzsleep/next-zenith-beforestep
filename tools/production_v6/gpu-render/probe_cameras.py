"""Measure robot screen height; no images or physical steps are saved."""
import json
from bootstrap import *

plans=json.loads((OUT/'gpu-render/shot-plan.json').read_text())['shots']
vm=build_model('stress_v8',width=1920,height=1080)
robot=[]
base=mujoco.mj_name2id(vm.m,mujoco.mjtObj.mjOBJ_BODY,'base_link')
for g in range(vm.m.ngeom):
    b=int(vm.m.geom_bodyid[g])
    while b and b!=base:b=int(vm.m.body_parentid[b])
    if b==base:robot.append(g)
cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
rows=[]
for distance in [1.3,1.5,1.7]:
    for name in ['s03-optimistic','s03-conservative','s03-imagination']:
        plan=next(p for p in plans if p['id']==name);z=np.load(ROOT/plan['sources'][0]['path'])
        for part in [.15,.5,.85]:
            stamp=plan['sim_start']+(plan['sim_end']-plan['sim_start'])*part;j=int(np.argmin(abs(z['t']-stamp)));q=z['qpos'][j].copy()
            display_sync(vm,q);vm.m.stat.center[:]=q[:3]
            cam.azimuth=-40;cam.elevation=-17;cam.distance=distance;cam.lookat[:]=[q[0]+.08,q[1],q[2]*.65]
            vm.r.enable_segmentation_rendering();vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt);seg=vm.r.render();vm.r.disable_segmentation_rendering()
            mask=np.isin(seg[:,:,0],robot)&(seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM));yy,xx=np.nonzero(mask)
            rows.append({'distance':distance,'shot':name,'fraction':part,'source_row':j,'robot_height_fraction':float((yy.max()-yy.min()+1)/1080),'bbox':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]})
print(json.dumps({'rows':rows,'physics_advanced':False,'quality_parameters_changed':False},ensure_ascii=False))
VZ.release(vm)
