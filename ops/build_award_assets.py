"""Curate six real version assets, their inputs and frozen configurations."""
import hashlib
import html
import json
from pathlib import Path
import shutil

import trimesh

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'evidence/award/asset-iterations'
    out.mkdir(parents=True, exist_ok=True)
    media = ROOT / 'site/media/award'
    media.mkdir(parents=True, exist_ok=True)
    old = Path('/root/3d/lunar-wheelleg-testbench/runs/unseen/recovery_r3/obs_R03')
    for name in ['rgb.png', 'crop_white.png', 'mask.png', 'depth.npy', 'visible_points.npy', 'observation.json']:
        target = out / 'v6-input' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(old / name, target)
    v6 = ROOT / 'assets/geometry/reference_v6/observation_fused.stl'
    derived = media / 'v6-observation-fused.glb'
    if not derived.exists():
        mesh = trimesh.load(v6, force='mesh')
        mesh.apply_transform(trimesh.transformations.rotation_matrix(-3.141592653589793 / 2, [1, 0, 0]))
        mesh.export(derived)
    versions = [
        ('V6', str(v6.relative_to(ROOT)), str(derived.relative_to(ROOT)),
         'evidence/award/asset-iterations/v6-input/crop_white.png',
         ['evidence/milestones/v6/config/unseen_v6_1_fusion.json', 'evidence/milestones/v6/config/unseen_v6_protocol.json'],
         '真实融合结果；可见区域受观测约束，未知背面没有被证明。'),
        ('V7', 'assets/candidates/reference_v7/A_naive1.glb', 'assets/candidates/reference_v7/A_naive1.glb',
         'assets/inputs/reference_v7/A_naive1.png', ['evidence/milestones/v7/config/v5_admission.json', 'evidence/milestones/v7/config/unseen_v7_protocol.json'],
         '原真实候选；阴影深度与多视角比较仍有失败。'),
        ('V8', 'assets/candidates/reference_v8/look1/T1/B2.glb', 'assets/candidates/reference_v8/look1/T1/B2.glb',
         'assets/observations/reference_v8/looks/look1/T1/gen/variants/B2.png', ['evidence/milestones/v8/config/v5_admission.json', 'evidence/milestones/v8/config/v5_protocol.json'],
         '原窄道第一块采纳候选；第二块全拒，原任务停车。'),
        ('v0.1', 'site/media/look1_T1_B2.glb', 'site/media/look1_T1_B2.glb',
         'site/media/look1_T1_B2.jpg', ['evidence/milestones/v8/config/v5_admission.json', 'evidence/milestones/v8/config/v5_protocol.json'],
         '复用 V8 真实资产，重构工程与完整停止规则；不是一份新增生成。'),
        ('v0.2', 'assets/candidates/5027323/tex_mesh.glb', 'assets/candidates/5027323/tex_mesh.glb',
         'assets/observations/gate_passage_001/looks/look1/T1/gen/variants/A1.png', ['config/admission.json', 'config/protocol.json'],
         '实际关口任务 5027323；通过原自检，参与完整预演与执行。'),
        ('v0.3', 'assets/candidates/5125347/tex_mesh.glb', 'assets/candidates/5125347/tex_mesh.glb',
         'assets/observations/trained_live_gate_001/looks/look1/T1/gen/variants/A1.png', ['config/admission.json', 'config/protocol.json'],
         '实际任务 5125347，被拒；学习控制版本保留坏例，未放宽门槛。')]
    sha = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    rows = []
    def url(p):
        return p.removeprefix('site/')
    cards = []
    for version, model, viewer, input_path, config, note in versions:
        rows.append({'version': version, 'model': {'path': model, 'sha256': sha(model)},
                     'viewer': {'path': viewer, 'sha256': sha(viewer)},
                     'input': {'path': input_path, 'sha256': sha(input_path)},
                     'frozen_config': [{'path': p, 'sha256': sha(p)} for p in config], 'note': note})
        cards.append(f'<article><h2>{version}</h2><model-viewer src="{url(viewer)}" camera-controls interaction-prompt="none" camera-orbit="35deg 65deg auto" shadow-intensity=".4" environment-image="neutral" alt="{version} 的真实资产"></model-viewer><img src="{url(input_path)}" alt="{version} 原始输入或注明的历史预览"><p>{html.escape(note)}</p></article>')
    (out / 'manifest.json').write_text(json.dumps({'schema': 'beforestep-award-asset-iterations/v1',
        'scope': 'Real asset renders, not redrawn shapes; V8 and v0.1 share the historical asset. v0.1 input is an existing JPEG preview; other PNG inputs are original bytes.',
        'v6_source': 'Historical observation copied byte-for-byte; parent and fused STL remain in assets/geometry/reference_v6.',
        'versions': rows}, ensure_ascii=False, indent=2) + '\n')
    page = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="favicon.svg"><title>真实关键资产迭代</title><style>body{margin:0;padding:28px;background:#101820;color:#e2edeb;font:15px/1.6 sans-serif}a{color:#70dbb2}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}article{background:#17242c;border:1px solid #34474c;border-radius:8px;padding:18px}h2{margin:0 0 8px;font-size:20px}model-viewer{height:210px;width:100%;background:#1c2b35}img{width:100%;height:120px;object-fit:contain;background:white}p{font-size:12px;margin-bottom:0}@media(max-width:620px){.grid{grid-template-columns:1fr}}</style></head><body><h1>六个版本，真实资产与真实输入</h1><p>模型可旋转；下方是原输入或明确标注的历史预览。候选变化并不自动意味着质量变好。<a href="evidence/award/asset-iterations/manifest.json">完整模型、输入与冻结配置 SHA</a> · <a href="index.html">返回作品</a></p><div class="grid">' + ''.join(cards) + '</div><script type="module" src="vendor/model-viewer.min.js"></script></body></html>'
    (ROOT / 'site/award-assets.html').write_text(page)
    print(json.dumps({'versions': len(rows), 'all_paths_and_sha_verified': True}))


if __name__ == '__main__':
    main()
