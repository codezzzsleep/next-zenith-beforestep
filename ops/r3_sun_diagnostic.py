"""Check the fixed rendered solar convention against the original first view."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mujoco
import numpy as np
import trimesh

from beforestep import scene as S
from beforestep.navigation import map as N, shadows as SH

ROOT = S.ROOT


def main():
    S.configure('stress_v8')
    original = ROOT / 'evidence/reviews/beforestep_r1/lux/original_b'
    out = ROOT / 'evidence/reviews/beforestep_r3/sun-diagnostic'
    out.mkdir(parents=True, exist_ok=True)
    world = ROOT / 'outputs/qa/r3/S2/sun-world'
    spec, _, meta = S.scene_spec(world)
    environment = S.make_env(spec)
    meshes = []
    for key, rock in meta['rocks'].items():
        mesh = trimesh.load(rock['obj'], force='mesh', process=False)
        matrix = trimesh.transformations.rotation_matrix(np.radians(rock['yaw']), [0,0,1])
        body = mujoco.mj_name2id(environment.model, mujoco.mjtObj.mjOBJ_BODY, rock['body'])
        matrix[:3, 3] = environment.data.xpos[body]
        mesh.apply_transform(matrix)
        path = world / (key + '.obj'); mesh.export(path); meshes.append(path)
    state = np.load(original / 'decision/look1_state.npy')
    zmax = np.load(original / 'looks/look1_zmax.npy')
    predicted, height, ground = SH.predict(zmax, meshes, spec['terrain']['custom_height_file'])
    dark = state == N.DARK
    domain = (state != N.UNSEEN) & (state != N.ROCK) & (state != N.NOGO) & ~N.prior_nogo()
    def iou(a,b):
        return float((a & b).sum() / (a | b).sum()) if (a | b).any() else 1.
    toward, tangent = SH.toward_sun()
    opposite = SH.shadow_from_height(height, ground, -toward, tangent, SH.PADDING)
    # Diagnose the original map's z=0 image projection without changing it.
    # A DARK pixel can hit a dark rock face before the projected floor point.
    camera = json.loads((original / 'looks/look1/T1/camera_world.json').read_text())
    depth = np.load(original / 'looks/look1_depth.npy')
    matrix = np.asarray(camera['R_world_from_camera'])
    pc = (np.stack([N.GX, N.GY, np.zeros_like(N.GX)], -1) - camera['world_pos']) @ matrix
    zc = -pc[..., 2]
    f = (depth.shape[0] / 2) / np.tan(np.radians(camera['intrinsics']['fovy_deg']) / 2) if 'fovy_deg' in camera['intrinsics'] else camera['intrinsics']['fy']
    with np.errstate(divide='ignore', invalid='ignore'):
        u = pc[..., 0] / zc * f + depth.shape[1] / 2
        v = -pc[..., 1] / zc * f + depth.shape[0] / 2
    ui = np.clip(u.astype(int), 0, depth.shape[1] - 1)
    vi = np.clip(v.astype(int), 0, depth.shape[0] - 1)
    # Reuse the frozen map.py HIDDEN-depth offset, not a fitted new threshold.
    nearer = depth[vi, ui] < zc - .10
    floor_domain = domain & ~nearer
    report = {'schema':'beforestep-r3-sun-diagnostic/v1', 'post_run_truth_only':True,
        'rendered_light_propagation':S.sun_dir().tolist(), 'toward_sun_xy':toward.tolist(),
        'tan_elevation':tangent, 'raw_whole_map_iou':iou(predicted,dark),
        'observed_ground_iou':iou(predicted & domain,dark & domain),
        'opposite_direction_observed_ground_iou':iou(opposite & domain,dark & domain),
        'original_map_dark_domain_cells':int((dark & domain).sum()),
        'dark_on_nearer_surface_cells':int((dark & domain & nearer).sum()),
        'depth_consistent_ground_iou':iou(predicted & floor_domain,dark & floor_domain),
        'direction_check':'Shared scene.sun_dir(), negated toward the sun; fixed-height block unit test confirms length and direction. Opposite-direction diagnostic is also retained.',
        'map_projection_note':'The frozen map projects z=0 floor cells into RGB. DARK is assigned without the depth-occlusion test used for HIDDEN, so dark foreground rock faces label floor cells behind them. Luminance DARK also includes terrain/texture effects. The raster shadow predicts physical heightfield occlusion, not that complete luminance classification. No camera, sensor, sun or map threshold changed.',
        'fixed_ray_distances_m':[.05,5.], 'resolution_m':N.RES,
        'scope':'Fixed 5cm, 5m ray test from the rendered light function. Raw and observed-ground comparisons both reported; no fitted threshold.'}
    (out / 'diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for name, value in [('predicted.npy',predicted),('observed-dark.npy',dark),('domain.npy',domain)]:np.save(out/name,value)
    diff=np.zeros_like(state);diff[predicted & domain]=1;diff[dark & domain]=2;diff[predicted & dark & domain]=3
    fig,axes=plt.subplots(1,3,figsize=(12,3),constrained_layout=True)
    for ax,value,title in zip(axes,[dark,predicted,diff],['Observed DARK','Fixed predicted shadow','Difference: predicted / observed / overlap']):
        ax.imshow(value.T,origin='lower',extent=[N.X0,N.X1,N.Y0,N.Y1],aspect='equal');ax.set_title(title);ax.set_xlabel('x (m)')
    fig.savefig(out/'difference.png',dpi=180)
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
