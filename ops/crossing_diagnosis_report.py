"""Summarize actual input diagnostics and retained Lux outcomes, never oracle as Lux."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load(relative):return json.loads((ROOT/relative).read_text())


if __name__=='__main__':
    audit=load('evidence/crossing/diagnosis-input-audit-v1.json')
    truth=load('evidence/crossing/diagnosis-truth-registration-v1.json')
    poses=load('evidence/crossing/diagnosis-cached-poses-v1.json')
    initial=load('evidence/crossing/diagnosis-observed-pose-scene-dev-v8.json')
    budget=load('outputs/generation/crossing-budget.json')
    trials=[]
    for revision in ['scene-dev-v5','scene-dev-v6','scene-dev-v7','scene-dev-v8','scene-dev-v9']:
        for report in sorted((ROOT/'evidence/crossing').glob('development-lux-'+revision+'-*.json')):
            r=json.loads(report.read_text())
            trials.append({'revision':revision+'/'+str(r['seed']),'generated':r['generated'],'glbs':r['glb_successes'],
                           'admitted':r['admitted'],'task_ids':r['task_ids'],'source':str(report.relative_to(ROOT))})
    result={'schema':'beforestep-crossing-diagnosis-summary/v1','status':'narrow_generator_has_admitted_models_four_development_chains_continue',
            'coordinate_checks':{k:audit[k] for k in ['world_local_max_error_m','reprojection_max_error_px','reprojection_depth_max_error_m']},
            'same_pipeline_truth_diagnostic':truth,'original_cached_pose_checks':sum(len(c['poses']) for c in poses['candidates']),
            'cached_pose_admitted':sum(sum(p['admitted_diagnostic'] for p in c['poses']) for c in poses['candidates']),
            'observed_initialization_checks':sum(len(r['placements']) for r in initial['results']),
            'observed_initialization_admitted':sum(sum(p['admitted_diagnostic'] for p in r['placements']) for r in initial['results']),
            'lux_trials':trials,'cumulative_created':budget['created'],'cumulative_glb_successes':sum(r['status']=='ok' for r in budget['tasks']),
            'formal_test_scenes':0,'corrections':['Separate image foreground envelope from reliable passive depth mask.',
                'Preserve real shadow RGB instead of painting it as background.','Rectangular crops retain the whole observed long edge.',
                'Do not impose the old navigation 512px target-height rule as an additional crossing gate.',
                '2-D real-pixel orientation normalization with no padded pixels in uploads.',
                'Use v72 action margins and sampled depth capacity; separate belly clearance from wheel step height.'],
            'frozen_changed':False,'next_step':'Complete the remaining valid v9 development Lux chains; screen every candidate before Lux.'}
    (ROOT/'evidence/crossing/diagnosis-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    text='# 轮腿输入与生成链路诊断\n\n主SPEC未全部完成，正式测试尚未预注册。输入处理的具体错误已修正；窄门槛已出现通过原自检的真实生成模型，继续完成四个有效开发场景。\n\n'
    text+=f'坐标/深度回投一致：世界-局部误差{audit["world_local_max_error_m"]:.3g}米，像素回投{audit["reprojection_max_error_px"]:.3g}像素，深度{audit["reprojection_depth_max_error_m"]:.3g}米。未发现这些变换错位。\n\n'
    m=truth['metrics'];text+=f'真实石头送入同一生产配准得到轮廓IoU {m["contour_iou"]:.4f}、高度比{m["scale_ratio"]:.4f}、自由空间侵入{m["free_intrusion_frac"]:.5f}，通过自检。这是真值诊断，不是Lux成绩。原六份生成模型的{result["original_cached_pose_checks"]}个已缓存备选位置全部不准入；对两个新模型追加{result["observed_initialization_checks"]}个观察派生初值仍没有准入，只改善部分配准质量，不能把它解释为所有可能配准都无解。\n\n'
    text+='输入处理发现：原A/C裁图相同；B图把可见轮廓内原阴影擦成背景；旧高度512像素限制不适合细长门槛。现在三类图分开，B只用已观察二维包络选取原RGB（可能含邻近背景/遮挡），深度/自检掩码不扩张；矩形裁图和长轴归一化保持真实像素，上传区域不含旋转补边。原始RGB、深度、mask、物理状态及来源SHA均保留。旧height检查失败仍如实写False，没有改为通过。所有src、config/admission.json、global config/protocol.json、v72动作、R1/R2/R3不改。\n\n'
    text+='| 开发输入 | 真实创建 | GLB成功 | 原五项准入 |\n|---|---|---|---|\n'
    for r in trials:text+=f'| {r["revision"]} | {r["generated"]} | {r["glbs"]} | {r["admitted"]} |\n'
    text+=f'\n本轮累计真实创建{result["cumulative_created"]}个，GLB成功{result["cumulative_glb_successes"]}个；更早首轮五份也保留，原并发创建拒绝另列。开发数据不计入正式统计。\n\n'
    v6=load('outputs/crossing/development/scene-dev-v6/seed-11002/truth-v72-v1/result.json')
    v7=load('outputs/crossing/development/scene-dev-v7/seed-11002/truth-v72-v1/result.json')
    text+=f'新观察的真值动作仍干净通过：v6为{v6["sim_seconds"]:.1f}秒，v7为{v7["sim_seconds"]:.1f}秒；这些不是Lux的通过。v8沿用v6同一物理状态及几何，B/E和六轮行直接引用原件，零新物理运行，不能重复累计。v6至v8模型在已测配准下仍存在高度、轮廓或自由空间矛盾；v9已有模型准入。没有放宽门槛，没有把真值模型放进Lux列。部分高度比达到栅格顶界，只表示该测量范围内的偏高，不能当整个模型的精确全尺寸比。\n\n'
    text+='v9生成器使用T宽1.10–1.20米、缺口0.90–1.00米，保持高度必要带与浅/深范围。轮行可过的候选作废并保留；当前结果见窄门槛标定报告。旧作废深场不能充当正式负类。还没有四条正式达标证据、锚点、帧或最终PDF。\n\n'
    text+='[诊断完整数据](../../evidence/crossing/diagnosis-summary.json) · [原36配准](../../evidence/crossing/diagnosis-cached-poses-v1.json) · [观察初值诊断](../../evidence/crossing/diagnosis-observed-pose-scene-dev-v8.json)\n'
    (ROOT/'docs/reviews/RESULT_CROSSING_DIAGNOSIS.md').write_text(text)
    print(json.dumps({'created':result['cumulative_created'],'formal':0,'frozen_changed':False}))
