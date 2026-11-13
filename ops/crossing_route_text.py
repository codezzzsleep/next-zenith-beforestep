"""Write the story opening and four evidence-derived report sections."""
import json,re,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from ops.crossing_route_summary import build,labels

def table(summary):
    text='| 车 | 第一段结果 | 第二段结果 | 总结果 | 用时（仿真秒） | 看了几眼 | 出事位置或停下原因 |\n| --- | --- | --- | --- | --- | --- | --- |\n'
    by={r['vehicle']:r for r in summary['rows']}
    for v in ['A','B','C','D']:
        if v not in by:text+=f'| {v} | 未完成 | 未运行 | 未完成 | — | — | 等待终态 |\n';continue
        r=by[v];reason=json.dumps(r['reason'],ensure_ascii=False) if isinstance(r['reason'],dict) else str(r['reason'] or '—')
        if v in ['B','C'] and not r['legs_used']:reason+='；没有用上腿'
        text+=f'| {v} | {labels(r["first_segment_result"])} | {labels(r["second_segment_result"])} | {labels(r["total_result"])} | {r["sim_seconds"]:.2f} | {r["looks"]} | {reason} |\n'
    return text

if __name__=='__main__':
    summary=build();low=json.loads((ROOT/'evidence/crossing/route/low-stone.json').read_text());gate=json.loads((ROOT/'evidence/crossing/calibration/gate.json').read_text());cap=json.loads((ROOT/'evidence/crossing/calibration/capability.json').read_text())
    opening=re.search(r'^> (机器人只拍到石头的一面。.*)$',(ROOT/'docs/story.md').read_text(),re.M).group(1)
    band=gate['best_sampled_necessary_span'];cm=lambda x:f'{x*100:.2f}'.rstrip('0').rstrip('.')
    wheel=max(g['height_m'] for g in cap['groups'] if g['method'] in ['fixed','high'] and g['passed'])
    chapter='## 轮腿与想象\n\n'+opening+'\n\n'
    chapter+='### 腿的必要性\n\n'
    chapter+=f'轮行实测最高曾通过 {cm(wheel)} 厘米；{cm(band["low_m"])}–{cm(band["high_m"])} 厘米的三个采样高度，常规和高姿态轮行 {gate["wheel_passes_at_band_heights"]}/{gate["wheel_trials_at_band_heights"]} 通过，逐轮跨越 {gate["band_gait_clean_trials"]}/{gate["band_gait_trials"]} 干净通过。各高度最大已验进深：'+ '、'.join(f'{cm(r["height_m"])} 厘米高 / {cm(r["d_max_m"])} 厘米深' for r in gate['necessary_by_height'] if r['height_m']>=band['low_m'] and r['height_m']<=band['high_m'])+f'；真石头 {gate["conditions"][2]["count"]}/{len(cap["rocks"])//3} 干净跨过。采样点之间没有连续高度验证。\n\n'
    chapter+='### 矮石头不需要想象\n\n'
    chapter+=f'有效开发场景中，双轮迹未看见的远缘为 {cm(low["unseen_rear_range_m"][0])}–{cm(low["unseen_rear_range_m"][1])} 厘米。场景 {low["seed"]} 只信看见的 B 用 {low["B"]["sim_seconds"]:.2f} 秒干净跨过；使用想象的 D 停下，原因是 {low["D"]["reason"]}，物理预演 {low["D"]["rehearsal_count"]} 次，没有实走。真实双轮迹进深 '+ ' / '.join(cm(x) for x in low['truth_depth_m'])+' 厘米，准入想象包络 '+ '–'.join(cm(x) for x in low['imagination_envelope_depth_range_m'])+f' 厘米，超过冻结的 {cm(low["frozen_depth_limit_m"])} 厘米能力。\n\n'
    chapter+='| 输入轮次 | 创建 | GLB 成功 | 准入 | 拒绝的主要原因（同份可重复） |\n| --- | --- | --- | --- | --- |\n'
    for r in low['six_input_rounds']:chapter+=f'| {r["revision"]} | {r["created"]} | {r["glb_successes"]} | {r["admitted"]} | '+ '；'.join(f'{k} {v}' for k,v in r['main_rejections'].items())+' |\n'
    chapter+=f'\n累计 {low["threshold_created"]} 份包括补充说明 2 允许收尾的批次；STORY 原字节保留此前 35 份的检查点。全部为开发数据，原十二场正式门槛测试已取消。模型叠合和 B 轨迹见 [开发素材](../evidence/crossing/route/low-stone.json)。\n\n'
    chapter+='### 一条路上两种石头\n\n'+summary['state']+'。石门位置已运行前提交，四项检查和每条终态都有独立证据。\n\n'+table(summary)+'\n'+summary['legs_necessity']+' '+summary['imagination_necessity']+'\n\n'
    chapter+='B、C 若第一段没有到整备点，第二段不运行；这不计作腿失败。到整备点的车保存完整物理状态，使用同一个 MuJoCo 世界继续，qpos/qvel 交接 SHA 必须相等。门槛石只用实拍的可见几何与冻结 v72，未对门槛创建任何 Lux3D。\n\n'
    chapter+='### 事实出处与边界\n\n'
    chapter+='事实出处保留原文核对记录：[来源](../evidence/crossing/references.json)。石门为简化任务，地形和几何限定在这一场；采用月面重力、被动暗区深度规则和理想目标分割，尚未验证实机。两极太阳约束及主动车灯方案的差异见原出处；仿真太阳是已冻结场景条件。\n\n'
    support=gate['support_diagnostic'];chapter+=f'动作按三轮支撑设计，单场两轮承重累计最长 {support["maximum_trial_total_two_loaded_wheels_s"]:.3f} 秒；最长连续片段 {support["longest_two_loaded_wheels_s"]:.3f} 秒。这是保留的支撑诊断，不增加闸门条件。结果不好看也不移动正式场景、不重跑终态、不改包络或准入阈值。原门槛预注册和十二场测试取消；同路两石的未完成项目由进度和结果表明确标出。\n\n'
    chapter+='[交互页面](https://codezzzsleep.github.io/next-zenith-beforestep/crossing.html) · [四车原始结果](../evidence/crossing/route/summary.json) · [负责人故事原文](story.md) · [补充说明 2](reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM2.md)。\n'
    (ROOT/'docs/crossing.md').write_text('# 轮腿与想象\n\n'+chapter+'\n## 附录\n\n学习模型与 Arena 停在 2747/4000，未完成；既有版本和失败证据保留。\n')
    p=ROOT/'docs/report.md';text=p.read_text();marker='<!-- PHOTO-STORY-REPORT-START -->\n';head,tail=text.split(marker,1);_,tail=tail.split('\n\n',1);text=head+marker+opening+'\n\n'+tail
    text=text.replace('不作为泛化证据','不作为样本外证据')
    if '\n## 轮腿跨越\n' in text:text=text.split('\n## 轮腿跨越\n')[0]
    if '\n## 轮腿与想象\n' in text:text=text.split('\n## 轮腿与想象\n')[0]
    text=re.sub(r'固定 v4 实际训练.*?不继续训练迭代。','历史学习模型的独立证据见附录入口。',text)
    p.write_text(text+'\n'+chapter+'\n## 学习附录\n\n学习模型与 Arena 停在 2747/4000，未完成；[历史版本与训练证据](training.md)保留。\n')
    p=ROOT/'README.md';text=p.read_text();marker='<!-- PHOTO-STORY-README-START -->\n';head,tail=text.split(marker,1);_,tail=tail.split('\n\n',1)
    tail=tail.split('<!-- PHOTO-STORY-README-END -->',1)[1]
    links='[自检拦下了什么](docs/report.md#全部反事实本批自检偏保守)\n\n[高石头绕行 R1 到 R3](docs/reviews/RESULT_BEFORESTEP_R1.md)\n\n[腿与想象：同路两种石头](docs/crossing.md)'
    history=ROOT/'docs/history/README-before-addendum2.md'
    if not history.exists():history.write_bytes(subprocess.check_output(['git','show','60644964:README.md'],cwd=ROOT))
    quickstart=tail[tail.index('## 三分钟跑起来'):]
    if '当前主线以' in quickstart:quickstart=quickstart.split('当前主线以')[0]
    elif '## 轮腿与想象' in quickstart:quickstart=quickstart.split('## 轮腿与想象')[0]
    body='\n\n## 轮腿与想象\n\n'+summary['state']+'。原门槛石开发已收尾，四项物理闸门通过；同路两种石头的四车结果按原件公开，结论以 [结果表](docs/crossing.md#一条路上两种石头) 为准。\n\n'
    body+='[交互页面](https://codezzzsleep.github.io/next-zenith-beforestep/crossing.html) · [实验规范](docs/reviews/SPEC_WHEELLEG_CROSSING_ADDENDUM2.md) · [故事](docs/story.md)。\n\n'
    body+='## 源码、资产与版本证据\n\n[代码导览](docs/code-tour.md)、[版本里程碑](docs/milestones.md)和[核心资产迭代](evidence/award/asset-iterations/manifest.json)保留各版本的源码、输入、原生成资产及失败对比；[原 README 与历史复现命令](docs/history/README-before-addendum2.md)原字节留档。\n\n'
    body+='## 附录\n\n学习模型保留历史记录；Arena 停在 2747/4000，未完成，原数据与失败证据保留。\n'
    p.write_text(head+marker+opening+'\n\n'+links+'\n<!-- PHOTO-STORY-README-END -->\n\n'+quickstart.strip()+body)
    p=ROOT/'docs/reviews/RESULT_WHEELLEG_CROSSING.md';text=p.read_text();mark='\n### 补充说明 2 当前结果（由证据生成）\n'
    if mark in text:text=text.split(mark)[0]
    cleanup=json.loads((ROOT/'evidence/crossing/route/cleanup.json').read_text());text+=mark+f'\n§0 已收尾：53 个已创建任务均有原 GLB，0 新创建；门槛后续队列、预注册与十二场测试取消。磁盘空余 {cleanup["free_before_bytes"]/2**30:.2f}→{cleanup["free_after_bytes"]/2**30:.2f} GiB，证据原件与依赖保留。STORY 和补充说明原字节已入库并同步私有恢复。\n\n'+table(summary)+'\n'+summary['legs_necessity']+' '+summary['imagination_necessity']+'\n'
    p.write_text(text)
    print(json.dumps({'opening_from_story':True,'route_rows':len(summary['rows']),'threshold_created':low['threshold_created']},ensure_ascii=False))
