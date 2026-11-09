"""Column occupancy and known-free-space intrusion measurements."""
import numpy as np
import trimesh

def drop_small_fragments(mesh, min_face_frac=0.02):
    """丢掉面数少于总数 min_face_frac 的孤立碎片（Lux3D 常带漂浮小块）。"""
    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        return mesh
    n = len(mesh.faces)
    keep = [p for p in parts if len(p.faces) >= min_face_frac * n]
    return trimesh.util.concatenate(keep) if keep else mesh


def column_fill_top(mesh, g, z_floor=0.0, z_ray=-1.0):
    """每列从地面 z_floor 填到该列最高交点。

    不做奇偶配对，不要求水密；开口外壳、重复壳、多碎片都得到同一个实心。
    对轮式机器人的通行判断，悬空部分按实心处理是保守的。
    """
    dims = tuple(int(x) for x in g['dims'])
    X, Y = np.meshgrid(np.asarray(g['xs']), np.asarray(g['ys']), indexing='ij')
    o = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z_ray)], 1)
    d = np.tile([0.0, 0.0, 1.0], (len(o), 1))
    loc, ri, _ = trimesh.ray.ray_triangle.RayMeshIntersector(mesh).intersects_location(
        o, d, multiple_hits=True)
    top = np.full(X.size, -np.inf)
    if len(ri):
        np.maximum.at(top, ri, loc[:, 2])
    top = top.reshape(dims[:2])
    zc = np.asarray(g['zs'])
    return (zc[None, None, :] >= z_floor) & (zc[None, None, :] <= top[:, :, None])


def free_intrusion(P, space, g, z_min=0.02):
    """侵入比 = P 落进已知空地（space==2）的体素 ÷ P 的实心体素；另报侵入深度 P95（mm）。"""
    zs = np.asarray(g['zs'])
    above = zs[None, None, :] > z_min
    Pa = P & above
    bad = Pa & (space == 2)
    n = int(Pa.sum())
    out = {'voxels': n, 'free_voxels': int(bad.sum()),
           'free_intrusion_frac': round(int(bad.sum()) / max(n, 1), 5), 'intrusion_depth_p95_mm': 0.0}
    if bad.any():
        from scipy import ndimage
        pitch = float(np.median(np.diff(zs)))
        # 侵入深度：侵入体素到最近"非空地"体素的距离
        dist = ndimage.distance_transform_edt(space == 2) * pitch
        out['intrusion_depth_p95_mm'] = round(float(np.percentile(dist[bad], 95) * 1000), 2)
    return out
