"""Generate the stopped development report from evidence, without claiming tests."""
import json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(name):return json.loads((ROOT/name).read_text())

if __name__=='__main__':
    gate=load('evidence/crossing/calibration/gate.json')
    blind=load('evidence/crossing/development-blindness.json')
    matched=load('evidence/crossing/development-blindness-matched-height.json')
    valid=load('evidence/crossing/development-validity.json')
    lux=load('evidence/crossing/development-lux-first.json')
    stop=load('evidence/crossing/generation-stop.json')
    arena=load('evidence/learning/arena_v2/closure.json')
    passing=[s['seed'] for s in valid['scenes'] if s['valid']]
    invalid=[s['seed'] for s in valid['scenes'] if not s['valid']]
    final={'schema':'beforestep-crossing-stopped-status/v1','physical_gate_passed':gate['physical_gate_passed'],
        'action_version':'v72','development_candidate_count':valid['candidate_count'],
        'wheel_passable_candidates_discarded':valid['wheel_passable_candidates'],
        'valid_development_seeds':passing,'invalid_development_seeds':invalid,
        'development_validity_trials':sum(len(s['trials']) for s in valid['scenes']),
        'formal_test_scenes':0,'oracle_E_tested_scenes':0,'formal_method_results':None,
        'new_lux_tasks':lux['generated'],'successful_glbs':lux['glb_successes'],
        'failed_created_generations':lux['generated']-lux['glb_successes'],'admitted':lux['admitted'],
        'create_rejections':lux['create_rejections'],'stop':stop,
        'uncompleted':['other three Lux development chains','crossing rehearsal and real execution','preregistration and formal tests','anchor and anchor asset package','720p30fps JPG frame sequences','final PDF regeneration'],
        'arena_status':arena['status'],'arena_completed_worlds':arena['completed_training_world_entries'],
        'claim_7_4_status':['validity condition implemented in development; formal tests not reached',
            'not reached: no formal D execution','not reached: no E-labelled formal scenes',
            'not reached: no formal B/D comparisons']}
    (ROOT/'evidence/crossing/final-development-status.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
    subprocess.run([sys.executable,str(ROOT/'ops/crossing_report.py'),'--data','evidence/crossing/calibration/capability-v72.json','--tag','capability-v72'],cwd=ROOT,check=True)
    report=ROOT/'docs/crossing.md';text=report.read_text()
    text=text.replace('真实Lux3D开发与预注册测试尚未开始。',f'首个真实Lux开发生成{lux["generated"]}份、准入{lux["admitted"]}份；因平台并发拒绝按§12.4停止新增请求，尚无预注册测试。')
    text+='\n## 开发场景的盲区与有效性\n\n'
    text+=f'生成器scene-dev-v3先生成{valid["candidate_count"]}个候选，轮行检查{final["development_validity_trials"]}次，每次时限{valid["time_limit_s"]:g}秒。候选{invalid}能够被轮行滚过而作废；{passing}在两姿态和中线/左右极限位置均未通过。A失败是场景定义，不是新发现；正式测试尚未开始。\n\n'
    text+='| 开发种子 | 轮行有效性 | 相机距近缘(cm) | 左轮迹远缘盲区(cm) | 右轮迹远缘盲区(cm) |\n|---|---|---|---|---|\n'
    for row in blind['scenes']:
        screen=next(s for s in valid['scenes'] if s['seed']==row['seed'])
        text+=f'| {row["seed"]} | {"有效" if screen["valid"] else "轮行可过，作废"} | {row["camera_to_near_m"]*100:.2f} | {row["tracks"][0]["unseen_far_m"]*100:.2f} | {row["tracks"][1]["unseen_far_m"]*100:.2f} |\n'
    for seed in passing:
        row=next(s for s in matched['scenes'] if s['seed']==seed)
        text+=f'\n种子{seed}在同为4厘米高度过滤后，左右轮迹仍有{row["tracks"][0]["unseen_far_above_4cm_m"]*100:.2f}、{row["tracks"][1]["unseen_far_above_4cm_m"]*100:.2f}厘米背面远缘未见。'
    maxheight=max(abs(t['unseen_height_m']) for s in blind['scenes'] for t in s['tracks'])
    text+=f'\n\n最高点基本已见，双轮迹最大绝对高度差{maxheight*100:.3f}厘米。当前数据支持背面进深盲区存在，尚不支持隐藏最高点或完整三维优于二维轮廓的效果结论。太阳高度10°，方位和真实位姿逐场保留。观测使用与原管线相同的亮度<0.10无深度和4厘米石头过滤，并使用理想目标分割；真值低裙边另以同4厘米阈值诊断。[原量测](../evidence/crossing/development-blindness.json)、[匹配高度诊断](../evidence/crossing/development-blindness-matched-height.json)。\n'
    text+='\n## 首个真实Lux开发（不计入正式统计）\n\n'
    text+=f'种子{lux["seed"]}，真实创建{lux["generated"]}份，GLB成功{lux["glb_successes"]}份，原阈值准入{lux["admitted"]}份。第六份创建被并发上限拒绝；拒绝不计为已创建任务失败。准入阈值0.7068及其他冻结指标未改。\n\n'
    text+='| 任务号 | 准入 | 左/右远缘误差(cm) | 左/右最高点误差(cm) |\n|---|---|---|---|\n'
    def pair(values):return ' / '.join('未覆盖轮迹' if v is None else f'{v*100:+.2f}' for v in values)
    for c in lux['candidates']:
        text+=f'| {c["task_id"]} | {"准入" if c["admitted"] else "拒绝"} | {pair(c["far_error_m"])} | {pair(c["height_error_m"])} |\n'
    text+='\n误差为想象减真值；远缘负值表示想象背面更短。各项原始指标、配准和所有生成模型继续保留。[首轮记录](../evidence/crossing/development-lux-first.json)。\n'
    shape=load('evidence/crossing/development-lux-shape-diagnostic.json')
    text+='\n五份模型都未覆盖两条预定轮迹，轮迹远缘/最高点误差保持“未覆盖”。轮廓IoU均低于冻结0.7068；下列整块模型的包围盒远缘与最高点误差仅供诊断。[原诊断](../evidence/crossing/development-lux-shape-diagnostic.json)。\n\n'
    text+='| 任务号 | 轮廓IoU | 整体远缘误差(cm) | 整体最高点误差(cm) |\n|---|---|---|---|\n'
    for c in shape['rows']:
        text+=f'| {c["task_id"]} | {c["contour_iou"]:.4f} | {c["whole_mesh_far_error_m"]*100:+.2f} | {c["whole_mesh_high_error_m"]*100:+.2f} |\n'
    text+='\n## 停因与未完成项\n\n'
    text+=f'平台以{stop["code"]}拒绝第六份任务。主文件§12.4将平台拒绝创建列为停因，因此停止新增请求，已创建{lux["generated"]}份全部收齐并自检。[停因](../evidence/crossing/generation-stop.json)。\n\n'
    text+='正式测试0场，E真值诊断0场；A/B/C/D尚无正式结果，不用0/0宣称达标。§7.4四条状态：场景有效性条件在开发中已实施，正式测试未达到；D安全、可跨场至少一半通过、D优于B或C三条均未达到（尚未执行对应实验）。\n\n'
    text+='余三Lux开发、跨越预演执行、预注册、正式测试、锚点素材、JPG帧及最终一次PDF未完成。旧PDF保留，本次未消耗最终重生授权。首页第二版READY未到件，未集成。开发场景与能力标定都不冒充正式统计。\n\n'
    text+=f'Arena v2未完成，训练世界{arena["completed_training_world_entries"]}/{arena["planned_training_worlds"]}条；失败记录和数据保留，按补充说明1不再恢复。\n'
    text+='\n完整开发与新增末批动作原件：[打包索引](../evidence/crossing/development/addendum1-index.json)。全部实际状态：[终态表](../evidence/crossing/final-development-status.json)。\n'
    report.write_text(text)
    result=ROOT/'docs/reviews/RESULT_WHEELLEG_CROSSING.md'
    with result.open('a') as f:f.write(f'\n## 当前终态（§12.4停止后收齐已创建结果）\n\n5份真实Lux全部终态：{lux["glb_successes"]}份GLB成功、{lux["admitted"]}份准入，另1次创建拒绝，正式测试0/E诊断0，四方法无正式结果。余三开发/预演执行/预注册/锚点/帧/最终PDF未完成。能力闸门按v72通过；Arena{arena["completed_training_world_entries"]}/4000未完成且不恢复。原始表与停因见[终态](../../evidence/crossing/final-development-status.json)，完整数据报告由ops/crossing_final_status.py从证据生成。\n')
    print(json.dumps({k:final[k] for k in ['new_lux_tasks','successful_glbs','admitted','formal_test_scenes','wheel_passable_candidates_discarded']}))
