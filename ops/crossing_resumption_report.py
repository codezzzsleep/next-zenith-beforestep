"""Publish measured resumption status without counting development as tests."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


if __name__ == '__main__':
    validity = load('evidence/crossing/development-validity-scene-dev-v5.json')
    blindness = load('evidence/crossing/development-blindness-scene-dev-v5.json')
    truths = load('evidence/crossing/development-truth-scene-dev-v5-truth-v72-v2.json')
    budget = load('outputs/generation/crossing-budget.json')
    lux_path = ROOT / 'evidence/crossing/development-lux-scene-dev-v5-11002.json'
    lux = json.loads(lux_path.read_text()) if lux_path.exists() else None
    rows = []
    for scene in validity['scenes']:
        seed = scene['seed']
        observation = next(s for s in blindness['scenes'] if s['seed'] == seed)
        truth = next(s for s in truths['scenes'] if s['seed'] == seed)
        folder = ROOT / 'outputs/crossing/development/scene-dev-v5' / f'seed-{seed}'
        row = {'seed': seed, 'valid': scene['valid'], 'A_reference': scene['A_reference'],
               'E_diagnostic_status': truth['status'], 'E_seconds': truth['sim_seconds'],
               'far_blindness_m': [t['unseen_far_m'] for t in observation['tracks']],
               'height_blindness_m': [t['unseen_height_m'] for t in observation['tracks']]}
        for method in ['B', 'D']:
            path = folder / ('method-' + method + '-v1/result.json')
            row[method] = json.loads(path.read_text())['status'] if path.exists() else None
        rows.append(row)
    result = {'schema': 'beforestep-crossing-resumption-status/v1', 'revision': validity['revision'],
              'physical_gate_passed': True, 'action_version': 'v72', 'formal_test_scenes': 0,
              'candidate_count': validity['candidate_count'],
              'wheel_passable_discarded': validity['wheel_passable_candidates'],
              'validity_trials': sum(len(s['trials']) for s in validity['scenes']),
              'scenes': rows, 'latest_lux': lux,
              'cumulative_lux_created': budget['created'],
              'cumulative_glb_successes': sum(r['status'] == 'ok' for r in budget['tasks']),
              'cumulative_generation_failures': sum(r['status'] == 'failed' for r in budget['tasks']),
              'preregistered': False, 'spec_complete': False,
              'excluded_from_formal_statistics': True,
              'stop': budget.get('stop') if budget.get('stop', {}).get('new_creation_stopped') else None}
    target = ROOT / 'evidence/crossing/development-resumption.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    labels = {'clean_pass': '干净通过', 'wheel_contact_pass': '带轮触石通过', 'stuck': '停止/卡住',
              'body_collision': '机身触石', 'unstable': '失稳', 'stopped': '停下', None: '未执行'}
    text = '# 石门槛续行开发结果\n\n项目与SPEC尚未全部完成。以下为开发证据，不计入正式统计。\n\n'
    text += f'本轮{result["candidate_count"]}个候选，{result["wheel_passable_discarded"]}个被轮行滚过而作废，完成{result["validity_trials"]}场有效性检查；正式测试{result["formal_test_scenes"]}场，未预注册。\n\n'
    text += '| 种子 | 场景有效性 | E真值诊断 | B只信可见部分 | D真实Lux | 双轨远缘盲区(cm) |\n|---|---|---|---|---|---|\n'
    for row in rows:
        far = ' / '.join('无观测' if x is None else f'{x*100:.2f}' for x in row['far_blindness_m'])
        text += f'| {row["seed"]} | {"有效" if row["valid"] else "作废"} | {labels[row["E_diagnostic_status"]]} | {labels[row["B"]]} | {labels[row["D"]]} | {far} |\n'
    text += '\nE是真值诊断，不是Lux3D成绩。两个深坎的E失败记录也保留，但这两场被轮行滚过而作废，不能用它们证明有效测试场景的深坎类别。两个有效浅坎的B也干净通过；没有预设B必须出事。\n\n'
    text += f'本轮Lux累计创建{result["cumulative_lux_created"]}，GLB成功{result["cumulative_glb_successes"]}，已创建生成失败{result["cumulative_generation_failures"]}。'
    if lux:
        text += f'新观察种子{lux["seed"]}生成{lux["generated"]}份，GLB成功{lux["glb_successes"]}份，冻结自检准入{lux["admitted"]}份。\n\n'
        text += '| 任务号 | 准入 | 轮廓IoU | 尺度比 | 隐藏比例 | 自由空间侵入 | 远缘误差左/右(cm) | 最高点误差左/右(cm) |\n|---|---|---|---|---|---|---|---|\n'
        for candidate in lux['candidates']:
            def pair(values):
                return ' / '.join('未覆盖轮迹' if x is None else f'{x*100:+.2f}' for x in values)
            metrics = candidate['metrics']
            text += f'| {candidate["task_id"]} | {"准入" if candidate["admitted"] else "拒绝"} | {metrics["contour_iou"]:.4f} | {metrics["scale_ratio"]:.4f} | {metrics["hidden_frac"]:.4f} | {metrics["free_intrusion_frac"]:.5f} | {pair(candidate["far_error_m"])} | {pair(candidate["height_error_m"])} |\n'
    else:
        text += '新观察真实Lux自检尚未终态。\n'
    text += '\n最高点基本已见。仍需补足有效开发场景、完成真实Lux决定与预演、预注册及正式测试，再交付锚点、素材、帧和最终PDF。Arena保留2747/4000数据及失败记录，不恢复。\n\n'
    if result['stop']:
        text += f'当前停因：{result["stop"]["criterion"]}。新观察的六份模型全部未通过冻结的多项自检，D按无准入规则停下；一份轮廓IoU虽超过阈值，尺度等指标仍不合格。此结论限于已测输入，不代表所有低矮石头都不能生成。其余三个有效开发链路、预注册和正式测试没有完成。\n\n'
    text += '[当前完整数据](../../evidence/crossing/development-resumption.json) · [零付费原件与SHA](../../evidence/crossing/development/resume-20261113-zero-paid-manifest.json)\n'
    (ROOT / 'docs/reviews/RESULT_CROSSING_RESUMPTION.md').write_text(text)
    print(json.dumps({k: result[k] for k in ['formal_test_scenes', 'cumulative_lux_created', 'spec_complete']}))
