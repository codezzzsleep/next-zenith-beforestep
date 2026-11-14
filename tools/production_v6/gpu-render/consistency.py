"""Reproduce the selected h-center frame before authorizing batch rendering."""
import argparse
import hashlib
import time
from bootstrap import *
from common import save, sha
from PIL import Image
from OpenGL import GL

parser=argparse.ArgumentParser()
parser.add_argument('--label',choices=['local','gpu'],required=True)
args=parser.parse_args()
directory=OUT/'render-ab'
directory.mkdir(exist_ok=True)
source=ROOT/'outputs/crossing/route/stress_v8_gate/prechecks/x9.00-seed22001/leg/trajectory.npz'
z=np.load(source)
q=z['qpos'][2857].copy()
assert q.shape==(23,)
assert hashlib.sha256(q.tobytes()).hexdigest()=='312a87076a5a4944283ffcee82262ad0909b546e0d6c9617d0d79b9f7e8b4ec7'
start=time.monotonic()
vm=build_model(route='stress_v8_gate')
vm.m.stat.center[:]=q[:3]
display_sync(vm,q)
cam=mujoco.MjvCamera()
cam.type=mujoco.mjtCamera.mjCAMERA_FREE
cam.azimuth=25
cam.elevation=-12
cam.distance=1.9
cam.lookat[:]=[q[0]+.12,q[1],q[2]*.6]
solar=vm.m.light_dir.copy()
vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt)
rgb=vm.r.render().copy()
assert np.array_equal(q,vm.d.qpos) and np.array_equal(solar,vm.m.light_dir)
renderer=GL.glGetString(GL.GL_RENDERER).decode()
vendor=GL.glGetString(GL.GL_VENDOR).decode()
if args.label=='gpu':
    assert 'RTX 4090 D' in renderer and 'NVIDIA' in vendor,(renderer,vendor)
output=directory/f'leg-{args.label}-h-center-clean.png'
Image.fromarray(rgb).save(output)
reference=directory/'leg-h-center-clean.png'
expected=np.asarray(Image.open(reference).convert('RGB'))
assert rgb.shape==expected.shape==(1080,1920,3)
diff=np.abs(rgb.astype(np.int16)-expected.astype(np.int16))
row={'label':args.label,'status':'passed' if diff.max()<=8 else 'stopped_consistency_gate',
     'maximum_channel_difference':int(diff.max()),'mean_absolute_channel_difference':float(diff.mean()),
     'different_pixel_fraction':float(np.any(diff>0,axis=2).mean()),
     'pixels_exceeding_8_fraction':float(np.any(diff>8,axis=2).mean()),
     'GL_RENDERER':renderer,'GL_VENDOR':vendor,'mujoco_version':mujoco.__version__,
     'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'source_row':2857,
     'qpos_sha256':hashlib.sha256(q.tobytes()).hexdigest(),'saved_sim_s':float(z['t'][2857]),
     'reference_sha256':sha(reference),'output_sha256':sha(output),'elapsed_s':time.monotonic()-start,
     'render_resolution':[1920,1080],'shadowsize':int(vm.m.vis.quality.shadowsize),
     'offsamples':int(vm.m.vis.quality.offsamples),'shadowclip':float(vm.m.vis.map.shadowclip),
     'znear':float(vm.m.vis.map.znear),'extent':float(vm.m.stat.extent),'center':vm.m.stat.center.tolist(),
     'solar_directions':solar.tolist(),'physics_advanced':False,'physics_step_guard_active':True,
     'additional_fill':False,'supersampling':False,'sharpening':False}
if diff.max()>8:
    destination=directory/('gpu-diff.png' if args.label=='gpu' else 'local-diff.png')
    Image.fromarray(np.minimum(diff*4,255).astype(np.uint8)).save(destination)
    row['difference_image']=str(destination)
    row['difference_image_gain']=4
save(OUT/'gpu-render'/f'{args.label}-consistency.json',row)
print(__import__('json').dumps(row,ensure_ascii=False),flush=True)
VZ.release(vm)
