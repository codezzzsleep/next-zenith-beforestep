"""Write B7/B8 tables and bounded conclusions directly from preserved evidence."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'decisive': '决定性', 'ordinary': '普通', 'arrived': '到达',
          'collision': '碰撞', 'stuck': '安全停车', 'stopped_short': '未完成'}


def read(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', default='evidence/suite/summary.json')
    parser.add_argument('--out', default='docs/suite.md')
    args = parser.parse_args()
    data = read(ROOT / args.summary)
    frozen = read(ROOT / data['freeze'])
    pools = {}
    for source in frozen['pool_sources']:
        for scene, row in read(ROOT / source['path'])['scenes'].items():
            pools[scene] = row
    lines = ['# 预注册月面场景组', '',
        '场景组在任何本轮 Lux3D 结果之前冻结。选择只依据保守、see-dark、乐观和真实形状检验四次非 Lux 运行；各类别按种子从小到大取决定性与普通场景，stress_v8 直接使用已完成的 R1 锚点。冻结后不换场景、不放宽门槛、不迭代控制器。', '',
        f"原冻结 {data['frozen_scene_count']} 个场景，完成 {data['completed_scene_count']} 个。未完成：" + ('、'.join(data['incomplete_scenes']) or '无') + '。', '',
        '[冻结名单与预期](../' + data['freeze'] + ') · [原始结果总表](../' + args.summary + ')', '',
        '## 候选池分布', '', '| 类别 | 候选数 | 决定性 | 普通 | 无解 | 未归类 | 执行错误 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for family in frozen['families']:
        rows = [r for r in pools.values() if r['family'] == family]
        counts = [sum(r['classification'] == k for r in rows)
                  for k in ('decisive', 'ordinary', 'unsolvable', 'unclassified', 'incomplete')]
        lines.append('| ' + ' | '.join(map(str, [family, len(rows), *counts])) + ' |')
    lines.extend(['', '决定性：真实形状检验到达，乐观碰撞，保守停车或用满五眼。普通：真实形状与乐观均到达。无解：真实形状检验不到达。执行错误不会算成无解或被隐藏。此前错误池与参数调整理由保留在[决策记录](decisions.md)与[R2结果](reviews/RESULT_BEFORESTEP_R2.md)。', '',
        '## 五次运行', '', '| 场景 / 类别 / 分类 / 种子 | 保守 | see-dark | 乐观 | 真实形状检验 | 真实 Lux3D |',
        '| --- | --- | --- | --- | --- | --- |'] )
    for row in data['scenes']:
        title = f"{row['scene']} / {row['family']} / {LABELS[row['classification']]} / {row['seed'] if row['seed'] is not None else 'R1锚点'}"
        values = [title]
        for key in ('conservative', 'see_dark', 'optimistic', 'truth', 'imagination'):
            run = row['runs'][key]; s = run['summary']
            identity = (run['run'] + '/run_identity.json') if row.get('anchor') else ('evidence/suite/scenes/' + row['scene'] + '/runs/' + key + '/run_identity.json')
            values.append(f"{LABELS.get(s['result'], s['result'])} · {s['looks']}眼 · {s['sim_time_s']}s · [身份](../{identity})")
        lines.append('| ' + ' | '.join(values) + ' |')
    lines.extend(['', '每项时间为原始 summary 的仿真总时长，包含该运行的接近与观察，不包含云端排队。自检计算与预演计算墙钟另在原运行中保留，不作为端到端速度优势。所有运行使用 rules，传感器、机器人、5cm规则、准入门槛与两眼上限相同。真实形状是独立检验，未提供给生产规划器。', '',
        '## 候选与补看', '', '| 场景 | 真实岩石 | 任务 / 成功 / 准入 | 原视角高度与方式 | 第二眼 | 6b |',
        '| --- | --- | --- | --- | --- | --- |'])
    for row in data['scenes']:
        for rock, target in row['targets'].items():
            views = '; '.join(f"{v['look']}/{v['target']}: {v['native_px']}px, native_ok={v['native_ok']}, {v['mode']}" for v in target['views'])
            lines.append(f"| {row['scene']} | {rock} | {target['tasks']} / {target['succeeded']} / {target['admitted']} | {views} | {'是' if row['second_eye'] else '否'} | {'是' if target['six_b'] else '否'} |")
    lines.extend(['', '每份成功、失败与被拒候选均保留；第二眼单图首次零准入时只追加同字节 6b 一批，仍零准入就停止。两眼都 native_ok 的两图分支按原协议三份执行。', '',
        '## 赛后真值与全部拒绝反事实', '', '| 场景 | 3D最小间隙mm | XY包络间隙mm | 乐观原路线压入mm | 反事实碰撞 / 可执行 | 不能执行的拒绝候选 |',
        '| --- | ---: | ---: | ---: | --- | ---: |'])
    for row in data['scenes']:
        review, cf = row['review'], row['counterfactuals']
        lines.append(f"| {row['scene']} | {review['minimum_3d_clearance_m']*1000:.3f} | {review['minimum_xy_envelope_clearance_m']*1000:.3f} | {review['optimistic_max_intrusion_m']*1000:.3f} | {cf['collisions']} / {cf['executed']} | {cf['unexecutable']} |")
    lines.extend(['', '3D量来自每个保存姿态的原 MuJoCo 可碰撞几何；XY矩形与真实扫描平面包络是单独的复盘近似。二者同时报告，XY相交不等于真实3D接触。反事实枚举每一眼每份被拒候选，不挑选；第二眼候选在原第一眼与移动前缀重放之后干预，不在第一眼泄露未来观测。不能形成可执行反事实的失败另列，不能当作“不会撞”。', '', '## 预先约定的结论', ''])
    d, o, cf = data['decisive'], data['ordinary'], data['counterfactuals']
    if data['imagination_collision_scenes']:
        lines.append('**想象策略实际发生碰撞：' + '、'.join(data['imagination_collision_scenes']) + '。这是最重要的安全边界，首页与总表同时公开。**')
    lines.append(f"决定性完成 {d['completed']} 个：想象到达 {d['arrived']}，安全终止 {d['safe_stop']}，碰撞 {d['collisions']}。")
    lines.append('在预注册场景组的多数决定性场景中有效，且本组未观察到想象执行碰撞。' if data['majority_effectiveness_supported'] else '没有满足“决定性场景到达至少2/3且无碰撞”的预注册条件，结论限于逐项实测的有效范围。')
    lines.append(f"普通场景完成 {o['completed']}、想象到达 {o['arrived']}；相对乐观额外眼数与仿真时间分别为 {o['extra_eyes']}、{o['extra_sim_time_s']}s。")
    lines.append(f"被拒候选反事实碰撞 {cf['collisions']}/{cf['executed']}，另 {cf['unexecutable']} 份不能执行。" + ('自检拒绝的候选中出现过会碰撞的想象，比例和场景逐项公开。' if data['selfcheck_collision_evidence'] else '本批未证明自检挡住碰撞，继续报告自检偏保守。'))
    lines.append('第二眼真实触发：' + ('、'.join(data['second_eye_scenes']) or '无') + '；6b：' + ('、'.join(data['six_b_scenes']) or '无') + '。')
    failed = [r for r in data['scenes'] if r.get('failure_reason')]
    if failed:
        lines.extend(['', '## 未到达与碰撞的原因', '', '| 场景 / 类别 | 原始判断 | 事件或物理接触 |', '| --- | --- | --- |'])
        labels = {'physical_collision': '真实物理接触', 'zero_admission_after_retry': '追加后仍零准入',
                  'approach_or_observation_control': '接近或观察点控制未完成', 'no_accepted_route': '没有可执行准入路线'}
        for row in failed:
            failure = row['failure_reason']
            lines.append(f"| {row['scene']} / {row['family']} | {labels[failure['category']]} | {json.dumps(failure['detail'], ensure_ascii=False)} |")
    lines.extend(['', '这是有限扫描岩石、有限摆放和极区低太阳角下的受控仿真实验，不支持“对任何场景都有效”或“通用”的结论。每个数字均能追溯到原始运行身份、任务与保全清单。', ''])
    (ROOT / args.out).write_text('\n'.join(lines))
    print(json.dumps({'document': args.out, 'scenes': len(data['scenes'])}))


if __name__ == '__main__':
    main()
