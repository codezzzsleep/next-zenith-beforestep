"""Frozen nominal, low-traction and high-drag profiles."""
import hashlib, json
from . import soil as SOIL

CONFIGS = {
    'nominal': dict(n=1.0, kc=1400.0, kphi=820000.0, cohesion_pa=170.0,
                    phi_deg=35.0, k_shear=0.018),
    'low_traction': dict(n=1.0, kc=1400.0, kphi=820000.0, cohesion_pa=100.0,
                         phi_deg=30.0, k_shear=0.018),
    'high_drag': dict(n=1.0, kc=700.0, kphi=410000.0, cohesion_pa=170.0,
                      phi_deg=35.0, k_shear=0.018),
}


NOTE = ('纲领范围内的实验配置（同轮载同轮宽扫描），不是实测月壤统计分布；'
        'n 固定为 1，kc/kphi 单位分别为 N/m²、N/m³。')


def resolve(mode):
    """mode -> {'mode','params','params_sha'}；rigid 不调用土壤力。"""
    if mode == 'rigid':
        return {'mode': 'rigid', 'params': None, 'params_sha': None}
    if mode not in CONFIGS:
        raise SystemExit(f'未知土壤配置 {mode}（可用：rigid, {", ".join(CONFIGS)}）')
    p = CONFIGS[mode]
    sha = hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:32]
    return {'mode': 'soil', 'label': mode, 'params': p, 'params_sha': sha}


def specimen(load_n=120.0, width_m=0.045, radius_m=0.08595, contact_area_m2=0.0012):
    """判别量：同轮载、同轮宽下的牵引上限 H_cap 与压实阻力 Rc。

    Rc 必须先用**同一**下陷 z 计算，否则比较的是不同工况。这里两种方式都报：
      · 各自按自己参数求下陷后的 Rc（真实工况）
      · 固定同一 z=5 mm 的 Rc（只看参数本身）
    """
    out = {}
    for name in CONFIGS:
        sp = SOIL.SoilParams(**CONFIGS[name])
        h = float(sp.traction_limit(load_n, contact_area_m2))
        z = float(sp.sinkage(load_n, width_m, wheel_radius_m=radius_m))
        rc = float(sp.compaction_resistance(z, width_m))
        rc_fixed = float(sp.compaction_resistance(0.005, width_m))
        out[name] = {'H_cap_n': round(h, 3), 'sinkage_mm': round(z * 1000, 4),
                     'Rc_n_at_own_z': round(rc, 4),
                     'Rc_n_at_5mm': round(rc_fixed, 4),
                     'params_sha': resolve(name)['params_sha']}
    return out
