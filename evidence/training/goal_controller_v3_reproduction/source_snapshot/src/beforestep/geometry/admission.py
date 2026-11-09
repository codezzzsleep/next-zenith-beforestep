"""Frozen candidate admission policy; no truth geometry enters this gate."""
import json
import numpy as np
from beforestep.paths import ROOT
ADM = json.loads((ROOT / 'config/admission.json').read_text())

def admitted(m):
    if any(not isinstance(m.get(k), (int, float, np.number)) or not np.isfinite(m[k])
           for k in ('scale_ratio', 'hidden_frac', 'shell_contact', 'free_intrusion_frac', 'contour_iou')):
        return False
    return bool(ADM['scale_ratio']['min'] <= m['scale_ratio'] <= ADM['scale_ratio']['max']
                and m['hidden_frac'] >= ADM['hidden_frac_min'] and m['shell_contact'] >= ADM['shell_contact_min']
                and m['free_intrusion_frac'] <= ADM['free_intrusion_max'] and (m['contour_iou'] or 0) >= ADM['contour_iou_min'])


def scale_ratio_ground(P, V, g):
    """尺寸比（从地面量起）：候选在可见列里的高度 ÷ 观测正面的顶高，两者都以地面为起点。

    v5 的定义用"正面壳层的最低点"做起点。分割掩码时代，壳层一直延伸到地面，两种定义一样；
    V7 改用深度掩码后，离地 1.5 cm 以下的像素分不出石头与地面，壳层从约 1.3 cm 才开始，
    观测高度被低估，比值被抬高（E1 真石头 1.057，E2 真石头 1.113，超过上限 1.09）。
    从地面量起后，两块真石头都是 1.000。门槛数值不变。
    """
    shell = V['shell']; zs = np.asarray(g['zs'])
    vz = (P & shell.any(axis=2)[:, :, None]).any(axis=(0, 1))
    if not vz.any():
        return 0.0
    zg = float(zs[np.searchsorted(zs, 0.0)])
    h = float(zs[vz].max()) - zg
    sh = float(zs[shell.any(axis=(0, 1))].max()) - zg
    return round(h / max(sh, 1e-6), 4)
