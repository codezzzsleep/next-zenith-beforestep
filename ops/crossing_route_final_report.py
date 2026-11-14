"""Produce the required nine-part closure from completed, retained evidence."""
import collections
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from experimental.crossing.runtime import sha, write
from ops.crossing_route_text import table

EVIDENCE = ROOT / 'evidence/crossing/route'
PUBLIC = 'https://codezzzsleep.github.io/next-zenith-beforestep/'


def read(relative):
    return json.loads((ROOT / relative).read_text())


def generate():
    summary = read('evidence/crossing/route/summary.json')
    plan = read('evidence/crossing/route/additional-scenes.json')
    assert summary['all_terminal'] and plan.get('selection_complete')
    assert all(row['status'] == '终态' for row in plan['scenes'])
    pdf = read('evidence/crossing/route/pdf-addendum3.json')
    assert pdf['status'] == 'complete' and sha(ROOT / 'site/media/report.pdf') == pdf['sha256']
    video = read('evidence/crossing/route/video-v2.json')
    assert sha(ROOT / video['path']) == video['sha256']
    final_video = read('evidence/crossing/route/video-v2-final.json')
    assert final_video['status'] == 'complete' and final_video['sha256'] == video['sha256']
    handoff = read('evidence/crossing/route/handoff-index.json')
    assert handoff['complete']
    budget = read('outputs/generation/crossing-budget.json')
    tasks = [task for task in budget['tasks'] if task.get('task_id')]
    assert all(task['status'] in ('ok', 'failed') for task in tasks)
    assert len(tasks) == budget['created']
    usage = read('evidence/crossing/route/lux-usage.json')
    gate = read('evidence/crossing/calibration/gate.json')
    capability = read('evidence/crossing/calibration/capability-v72.json')
    scenes = [{'scene': summary['scene'], 'rows': summary['rows']}]
    excluded = []
    for item in plan['scenes']:
        if item.get('result') and (ROOT / item['result']).is_file():
            data = json.loads((ROOT / item['result']).read_text())
            assert data['all_terminal'] and len(data['rows']) == 4
            scenes.append(data)
        else:
            excluded.append({'scene': item['scene'], 'reason': item.get('result')})
    counts = {vehicle: collections.Counter(row['total_result'] for scene in scenes for row in scene['rows']
                                          if row['vehicle'] == vehicle) for vehicle in 'ABCD'}
    clean = {vehicle: sum(row['second_segment_result'] == 'clean_pass' and row['total_result'] == 'arrived'
                         for scene in scenes for row in scene['rows'] if row['vehicle'] == vehicle) for vehicle in 'ABCD'}
    accidents = [{'scene': scene['scene'], **row} for scene in scenes for row in scene['rows']
                 if row['total_result'] in ('collision', 'body_collision', 'unstable')]
    checks = [counts['A']['arrived'] == 0, not any(row['vehicle'] == 'D' for row in accidents),
              clean['D'] * 2 >= len(scenes),
              counts['D']['collision'] < counts['B']['collision'] or counts['D']['arrived'] > counts['C']['arrived']]
    statuses = collections.Counter(task['status'] for task in tasks)
    route_tasks = sum(task['scene'].startswith('route/') for task in tasks)
    band = gate['best_sampled_necessary_span']
    wheel = max(group['height_m'] for group in capability['groups'] if group['method'] in ('fixed', 'high') and group['passed'])
    depths = '、'.join(f'{round(item["height_m"] * 100)} 厘米高 / {round(item["d_max_m"] * 100)} 厘米深'
                      for item in gate['necessary_by_height'] if item['height_m'] in band['sampled_heights_m'])
    text = '# 轮腿与想象 · 结束报告\n\n'
    text += f'证据快照：{datetime.now(timezone.utc).isoformat()}。按主 SPEC §13 与补充说明 2、3 生成；原十二场门槛测试已经取消，下面统计同路两种石头的示例，不混作原预注册测试。\n\n'
    text += f'1. 轮行最高曾通过 {round(wheel * 100)} 厘米。逐轮已验 {depths}；必要带仅验证 {"、".join(str(round(h * 100)) for h in band["sampled_heights_m"])} 厘米三个离散高度：轮行 {gate["wheel_passes_at_band_heights"]}/{gate["wheel_trials_at_band_heights"]}，跨越 {gate["band_gait_clean_trials"]}/{gate["band_gait_trials"]} 干净通过，真石 {gate["conditions"][2]["count"]}/3。采样点之间未连续验证。\n\n'
    text += f'2. 同路两种石头完成 {len(scenes)} 场，每场四项预检查通过；正式运行 {len(scenes) * 4} 次。原十二场门槛测试取消，“本来跨不过”的正式组没有运行。\n\n'
    text += '3. 四种方法的结果见下表；卡住与机身事故分开记录。\n\n| 车 | 到达 | 干净跨过 | 停下 | 卡住 | 机身事故 |\n| --- | --- | --- | --- | --- | --- |\n'
    for vehicle in 'ABCD':
        count = counts[vehicle]
        text += f'| {vehicle} | {count["arrived"]} | {clean[vehicle]} | {count["stopped"]} | {count["stuck"]} | {sum(row["vehicle"] == vehicle for row in accidents)} |\n'
    text += '\n4. 原 §7.4 四条说法在这组同路示例中的数值检查依次为：'+ '；'.join(('达到' if passed else '没达到') for passed in checks)+'。原十二场的预注册验收未执行，这些数值不替代它。\n\n'
    text += f'5. 同路正式运行机身事故 {len(accidents)} 次。首场 B 轮触高石后被冻结的接触监视器停下，原始 collision 字段保留，但按本轮轮触石不算机身事故。\n\n'
    for row in accidents:
        text += f'   - {row["scene"]} / {row["vehicle"]}：{json.dumps(row["reason"], ensure_ascii=False)}。\n'
    text += '历史原方法四次碰撞均保留：F1_020 未观测到 C；F3_004、F0_003、F3_006 低估 B 背面。原输入、预演和事故复盘在完整报告中。\n\n'
    text += f'6. 同路高石新建 {route_tasks} 个 Lux3D 任务；本轮累计 {len(tasks)} 个，其中 {statuses["ok"]} 份 GLB、{statuses["failed"]} 份服务端失败。全部历史累计 {usage["generated_task_creates"]} 个真实任务；上传和轮询不重复算新任务，未成功创建的并发拒绝不计入。\n\n'
    text += '7. 门槛石 Lux3D 后续开发、原十二场正式测试与对应预注册已按补充说明 2 取消；矮石用实拍几何。首场 D 未走完高石段，D 预演帧和跨越特写没有实际来源，索引明确写 not_applicable；视频用真实几何接通预检查，明示来源。配音与配乐未制作，成片由 Agent 合成，待负责人看片。\n\n'
    for item in excluded:
        text += f'未运行追加场景 {item["scene"]}：{item["reason"]}。\n\n'
    gallery = EVIDENCE / 'official-viewer.json'
    if gallery.exists():
        result = json.loads(gallery.read_text())
        text += '官方陈列室查看器：'+str(result.get('result'))+'。\n\n'
    text += f'8. [页面]({PUBLIC}crossing.html) · [完整报告]({PUBLIC}report.html) · [PDF]({PUBLIC}media/report.pdf) · [视频]({PUBLIC}media/demo-v2.mp4) · [素材包及帧索引]({PUBLIC}evidence/crossing/route/handoff-index.json) · [真实任务号]({PUBLIC}evidence/crossing/route/lux-usage.json)。所有分包附逐成员 SHA，原 PDF 留档。发布提交号以最终 main 与 gh-pages 远端为准。\n\n'
    text += '9. Arena v2 停在 2747/4000，未完成；原失败状态与数据保留，没有重新启动训练。\n\n'
    text += '首场四车结果原表：\n\n'+table(summary)+'\n'
    for scene in scenes[1:]:
        text += scene['scene']+'：\n\n'+table(scene)+'\n'
    path = ROOT / 'docs/reviews/RESULT_WHEELLEG_CROSSING_FINAL.md'
    path.write_text(text)
    progress = ROOT / 'docs/reviews/RESULT_WHEELLEG_CROSSING.md'
    link = '\n[九条结束报告与全部终态表](RESULT_WHEELLEG_CROSSING_FINAL.md)。\n'
    if link not in progress.read_text():
        progress.write_text(progress.read_text() + link)
    write(EVIDENCE / 'final-report.json', {
        'schema': 'beforestep-crossing-final-report/v1', 'formal_route_scenes': len(scenes),
        'formal_route_runs': len(scenes) * 4, 'counts': {key: dict(value) for key, value in counts.items()},
        'clean_passes': clean, 'original_twelve_tests_cancelled': True,
        'original_claims_checked_on_route_examples_only': checks, 'accidents': accidents,
        'new_route_tasks': route_tasks, 'crossing_created': len(tasks), 'crossing_statuses': dict(statuses),
        'historical_created': usage['generated_task_creates'], 'excluded_scenes': excluded,
        'report': str(path.relative_to(ROOT)), 'report_sha256': sha(path),
        'video_sha256': video['sha256'], 'pdf_sha256': pdf['sha256'],
        'evidence_snapshot_main': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    })
    print(json.dumps({'report': str(path.relative_to(ROOT)), 'scenes': len(scenes), 'tasks': len(tasks)}, ensure_ascii=False))


if __name__ == '__main__':
    generate()
