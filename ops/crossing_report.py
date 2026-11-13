"""Write calibration prose and tables directly from a measured capability file."""
import argparse
import json
from pathlib import Path
import shutil
ROOT = Path(__file__).resolve().parents[1]
LABELS = {'fixed': '固定常规轮行', 'high': '高姿态轮行', 'gait': '逐轮跨越'}
STATUS = {'clean_pass': '干净通过', 'wheel_contact_pass': '带轮触石通过',
          'body_collision': '机身触石', 'unstable': '失稳', 'stuck': '卡住'}


def cm(value):
    return f'{value*100:g}' if value is not None else '尚无'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    source = ROOT / args.data
    d = json.loads(source.read_text())
    assert d['status'] == 'complete'
    canonical = ROOT / 'evidence/crossing/calibration/capability.json'
    shutil.copy2(source, canonical)
    lines = ['# 轮腿跨越：完整能力标定', '',
             f"状态：{d['trial_count']}格记录完成；物理闸门{'通过' if d['physical_gate_passed'] else '尚未通过'}。真实Lux3D开发与预注册测试尚未开始。", '',
             f"固定常规轮行最高有一次通过为{cm(d['maximum']['fixed']['any_pass_height_m'])}厘米，同格三个接近角全过最高{cm(d['maximum']['fixed']['three_of_three_height_m'])}厘米；高姿态两项分别为{cm(d['maximum']['high']['any_pass_height_m'])}、{cm(d['maximum']['high']['three_of_three_height_m'])}厘米。", '',
             f"逐轮动作按任务接触定义最高有一次通过{cm(d['maximum']['gait']['any_pass_height_m'])}厘米；满足实际三支撑约束且同格3/3通过的最高高度为{cm(d['maximum']['gait']['three_of_three_height_m'])}。任务干净通过与动作支撑约束分别记录，不把短时两轮支撑当作合格的逐轮动作。", '',
             f"本表含{d['required_matrix_trial_count']}个必需格、{d['supplemental_d15_trial_count']}个15厘米进深补充格和{d['rock_trial_count']}个真石格。总时限{d['common_total_time_limit_s']:g}秒，近石轮速对应上限{d['speed_cap_m_s']:g}米/秒。固定姿态同样允许轮触石，机身触石、非轮触地或倾角超过60度则失败。", '',
             '支撑审计每2毫秒记录一次法向载荷，以1e-5牛为承重阈值。指令轮实际不承重时，另外三轮必须同时承重；卸载、落地时指令轮仍承重的转换另列。原来按整个指令阶段要求另外三轮始终承重的更严格审计仍保留，终态不被改写。', '',
             '表中逐轮列为满足支撑约束的通过数；括号内另列仅按任务接触定义的通过数。每个深度三个接近角均有独立终态，不从离散采样推断连续能力。', '',
             '| 高度(cm) | 方法 | 深10cm | 深15cm（补充） | 深20cm | 深30cm | 深40cm |',
             '|---|---|---|---|---|---|---|']
    for h in d['heights_m']:
        for method, label in LABELS.items():
            cells = []
            for depth in [.10, .15, .20, .30, .40]:
                g = next((g for g in d['groups'] if g['method'] == method and g['height_m'] == h and g['depth_m'] == depth), None)
                if g is None:
                    cells.append('未测')
                elif method == 'gait':
                    cells.append(f"{g['support_compliant_passed']}/3（任务{g['passed']}/3）")
                else:
                    cells.append(f"{g['passed']}/3")
            lines.append(f'| {cm(h)} | {label} | ' + ' | '.join(cells) + ' |')
    lines += ['', '## 必要带与真石', '']
    band = d['best_sampled_necessary_span']
    if band:
        lines.append(f"采样必要带端点{cm(band['low_m'])}–{cm(band['high_m'])}厘米，跨度{cm(band['width_m'])}厘米；带内各实测高度的最大合格进深至少{cm(band['minimum_d_max_m'])}厘米。只验证列出的采样高度，中间连续高度尚未逐一验证。")
    else:
        lines.append('尚未形成满足三支撑约束的3/3必要带。物理闸门未通过，不能据此启动真实Lux3D测试。')
    lines += ['', '| 真石素材 | 固定常规 | 高姿态 | 逐轮 |', '|---|---|---|---|']
    for rock in sorted({r['rock'] for r in d['rocks']}):
        cells = []
        for method in LABELS:
            row = next(r for r in d['rocks'] if r['rock'] == rock and r['method'] == method)
            text = STATUS[row['status']]
            if method == 'gait':
                text += '；实际三支撑' + ('符合' if row['support_compliant'] else '不符合')
            cells.append(text)
        lines.append('| ' + rock + ' | ' + ' | '.join(cells) + ' |')
    lines += ['', '真石为三个保留扫描素材的同尺寸仿射缩放变体，物理碰撞使用MuJoCo网格凸包。它们最高点相同，轮迹上的局部形状不同；不把方坎的轮行上限套用为所有真石的上限。', '',
              '## 失败与保全', '',
              f"逐格结果、接触、支撑审计和源码身份：[能力数据](../{args.data})；完整轨迹/接触包与SHA：[清单](../evidence/crossing/calibration/{args.tag}-manifest.json)。", '',
              '旧40秒、120秒轮行矩阵和所有开发动作失败原样保留。240秒对照只延长原卡住格，早终态继承；逐轮同源码已完成探针也继承原件，不重复物理执行。开发与能力标定不计入今后的预注册测试统计。', '',
              '## 已核对事实', '']
    refs = json.loads((ROOT / 'evidence/crossing/references.json').read_text())
    for ref in refs['verified']:
        lines.append(f"- {ref['verified_claim']} [原文]({ref['url']})")
    lines += ['', '石门缺口为本项目的简化任务；所引LROC原文不证明所有坑沿都有无缝环形石带。VIPER和ATHLETE作为设计、原型依据。当前结果来自月面重力的MuJoCo仿真，不是实机或任意月面泛化结论。', '']
    (ROOT / 'docs/crossing.md').write_text('\n'.join(lines))
    print(json.dumps({'report': 'docs/crossing.md', 'canonical_data': str(canonical.relative_to(ROOT)),
                      'gate': d['physical_gate_passed']}))


if __name__ == '__main__':
    main()
