"""Classify observed free space, surface bands and unknown space."""
import json, pathlib
import numpy as np
from . import camera as camera_io

def _slice_centers(g, axis, i):
    """返回该切片所有体素中心 (N,3)，避免整块 meshgrid 的内存峰值。"""
    if axis == 0:
        a, b = np.meshgrid(g['ys'], g['zs'], indexing='ij')
        return np.stack([np.full(a.size, g['xs'][i]), a.ravel(), b.ravel()], axis=1)
    raise ValueError(axis)


def observe_volume(obs_dir, grid, proto, *, with_shell=True):
    """F/B/U 分类 + 公共观测壳层 V。只读观测，不读任何真值。"""
    obs_dir = pathlib.Path(obs_dir)
    obs = json.loads((obs_dir / 'observation.json').read_text())
    depth = np.load(obs_dir / 'depth.npy').astype(np.float64)
    from PIL import Image
    mask = np.array(Image.open(obs_dir / 'mask.png').convert('L')) > 127
    H, W = depth.shape
    v = proto['visibility']
    eps = float(v['free_epsilon_m'])
    band = float(v['band_m'])
    off = float(v['shell_offset_voxels']) * float(grid['pitch'])
    dims = tuple(int(x) for x in grid['dims'])
    space = np.zeros(dims, dtype=np.uint8)
    shell = np.zeros(dims, dtype=bool)
    cam = obs['camera']
    valid_depth = np.isfinite(depth) & (depth > 0) & (depth < 100.0)
    stats_n = {'free': 0, 'band': 0, 'unknown': 0, 'in_fov': 0, 'masked_fov': 0}
    for i in range(dims[0]):
        pts = _slice_centers(grid, 0, i)
        u, vv, z = camera_io.project(pts, cam)
        finite = np.isfinite(u) & np.isfinite(vv) & np.isfinite(z)
        in_fov = finite & (u >= 0) & (u <= W - 1) & (vv >= 0) & (vv <= H - 1) & (z > 0)
        ui = np.clip(np.nan_to_num(u, nan=-1), 0, W - 1).astype(np.int64)
        vi = np.clip(np.nan_to_num(vv, nan=-1), 0, H - 1).astype(np.int64)
        d = depth[vi, ui]
        d_ok = in_fov & np.isfinite(d) & (d > 0) & (d < 100.0)
        cls = np.zeros(len(pts), dtype=np.uint8)
        # 已知自由：到测量面之前（测量带外）
        cls[d_ok & (z < d - eps)] = 2
        # 测量带：只在掩码内（掩码外没有目标表面，不能当已知）
        m = mask[vi, ui]
        band_v = d_ok & m & (z >= d - eps + off) & (z <= d + band + off)
        cls[band_v] = 1
        sl = (slice(i, i + 1), slice(None), slice(None))
        space[sl] = cls.reshape(1, dims[1], dims[2])
        if with_shell:
            shell[sl] = band_v.reshape(1, dims[1], dims[2])
        stats_n['free'] += int((cls == 2).sum())
        stats_n['band'] += int((cls == 1).sum())
        stats_n['unknown'] += int((cls == 0).sum())
        stats_n['in_fov'] += int(in_fov.sum())
        stats_n['masked_fov'] += int((in_fov & m).sum())
    stats = {'n_voxels': int(np.prod(dims)), 'n_free': stats_n['free'],
             'n_band': stats_n['band'], 'n_unknown': stats_n['unknown'],
             'n_in_fov': stats_n['in_fov'], 'n_masked_fov': stats_n['masked_fov'],
             'n_shell': int(shell.sum()),
             'valid_depth_frac': round(float(valid_depth.mean()), 6),
             'free_eps_m': eps, 'band_m': band, 'shell_offset_m': off,
             'pitch_m': float(grid['pitch']),
             'depth_convention': 'positive_camera_minus_z'}
    return space, shell, stats, obs
