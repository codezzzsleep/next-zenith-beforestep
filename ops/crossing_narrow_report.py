"""Publish narrowed-generator development measurements directly from evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):return json.loads((ROOT/path).read_text())

if __name__=='__main__':
    revision='scene-dev-v9';validity=load('evidence/crossing/development-validity-'+revision+'.json')
    observations=load('evidence/crossing/development-blindness-'+revision+'.json')['scenes']
    extra=ROOT/'evidence/crossing/development-blindness-scene-dev-v9-extra.json'
    if extra.exists():observations+=json.loads(extra.read_text())['scenes']
    truthfile=ROOT/'evidence/crossing/development-truth-scene-dev-v9-truth-v72-v1.json'
    truth=json.loads(truthfile.read_text())['scenes'] if truthfile.exists() else []
    luxfile=ROOT/'evidence/crossing/development-lux-scene-dev-v9-22001.json'
    lux=json.loads(luxfile.read_text()) if luxfile.exists() else None
    budget=load('outputs/generation/crossing-budget.json');rows=[]
    for record in validity['scenes']:
        seed=record['seed'];obs=next((r for r in observations if r['seed']==seed),None)
        diagnostic=next((r for r in truth if r['seed']==seed),None)
        folder=ROOT/'outputs/crossing/development'/revision/f'seed-{seed}'
        methods={}
        for method in ['B','D']:
            resultfile=folder/('method-'+method+'-v1/result.json')
            methods[method]=json.loads(resultfile.read_text()) if resultfile.exists() else None
        rows.append({'seed':seed,'methods':methods,'valid':record['valid'],'wheel_statuses':[r['status'] for r in record['trials']],
                     'unseen_far_m':[r['unseen_far_m'] for r in obs['tracks']] if obs else None,
                     'unseen_height_m':[r['unseen_height_m'] for r in obs['tracks']] if obs else None,
                     'E_diagnostic':{'status':diagnostic['status'],'sim_seconds':diagnostic['sim_seconds']} if diagnostic else None})
    summary={'schema':'beforestep-crossing-narrow-generator-summary/v1','revision':revision,
             'candidate_count':validity['candidate_count'],'invalid_wheel_passable':validity['wheel_passable_candidates'],
             'valid_count':sum(r['valid'] for r in rows),'scenes':rows,'lux':lux,'formal_test_scenes':0,
             'preregistered':False,'cumulative_created':budget['created'],'cumulative_glb_successes':sum(r['status']=='ok' for r in budget['tasks'])}
    (ROOT/'evidence/crossing/development-narrow-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    text='# 窄门槛生成器标定\n\n开发数据，不计入正式统计。动作仍为冻结的 v72，现有五项自检门槛不变。\n\n'
    text+=f'共生成 {summary["candidate_count"]} 个候选，{summary["invalid_wheel_passable"]} 个被轮子滚过而作废，{summary["valid_count"]} 个有效。每场六次轮行使用相同 240 秒时限；A 引用常规中线原件，不重复运行。\n\n'
    text+='|种子|有效性|未知远缘（两轮迹，厘米）|E 真值诊断|B 可见部分|D 真实生成|\n|---|---|---|---|---|---|\n'
    for r in rows:
        far=' / '.join(f'{x*100:.2f}' for x in r['unseen_far_m']) if r['unseen_far_m'] else '未观察'
        e=r['E_diagnostic'];status=f'{e["status"]}，{e["sim_seconds"]:.2f} 秒' if e else '未执行'
        text+=f'|{r["seed"]}|{"有效" if r["valid"] else "作废"}|{far}|{status}|{r["methods"]["B"]["status"] if r["methods"]["B"] else "未执行"}|{r["methods"]["D"]["status"] if r["methods"]["D"] else "未执行"}|\n'
    text+='\nE 是动作的真值诊断，不能当作 Lux3D 成绩。最高点差异和观察距离、腿姿、太阳方位见原始观察表。\n\n'
    if lux:
        text+=f'首个有效场景 {lux["seed"]} 的真实 Lux3D：创建 {lux["generated"]} 份，GLB 成功 {lux["glb_successes"]} 份，准入 {lux["admitted"]} 份。任务号：'+', '.join(map(str,lux['task_ids']))+'。\n\n'
    text+='首场 D 依照所有准入模型的包络决定；完整横向位置、高度、进深限制及理由见汇总。尚无可跨位置时不进行物理预演或真实跨越。\n\n'
    text+=f'本轮累计创建 {summary["cumulative_created"]} 个任务，GLB 成功 {summary["cumulative_glb_successes"]} 个。未预注册，正式测试 0 场，尚无 Lux3D 跨越锚点。\n\n'
    text+='[有效性原件](../../evidence/crossing/development-validity-scene-dev-v9.json) · [观察表](../../evidence/crossing/development-blindness-scene-dev-v9.json) · [完整汇总](../../evidence/crossing/development-narrow-summary.json)\n'
    (ROOT/'docs/reviews/RESULT_CROSSING_NARROW_GENERATOR.md').write_text(text)
    for relative in ['docs/crossing.md','docs/reviews/RESULT_WHEELLEG_CROSSING.md']:
        path=ROOT/relative;existing=path.read_text();marker='\n## 窄门槛开发最新\n'
        if marker in existing:existing=existing.split(marker)[0]
        if relative=='docs/crossing.md':
            for heading in ['\n## 最新续行开发\n','\n## v5 续行记录（历史）\n','\n## 输入诊断与当前进展\n']:
                existing=existing.split(heading)[0]
            existing=existing.replace('## 停因与未完成项','## 首轮停因与未完成项（历史）')
            old=(ROOT/'docs/reviews/RESULT_CROSSING_RESUMPTION.md').read_text().replace('../../','../').replace('当前停因：','v5 停因（历史）：').replace('[当前完整数据]','[v5 完整数据]')
            diagnostic=(ROOT/'docs/reviews/RESULT_CROSSING_DIAGNOSIS.md').read_text().replace('../../','../')
            existing+='\n## v5 续行记录（历史）\n\n'+old.replace('# 石门槛续行开发结果','### 石门槛续行开发结果',1)+'\n## 输入诊断与当前进展\n\n'+diagnostic.replace('# 轮腿输入与生成链路诊断','### 轮腿输入与生成链路诊断',1)
        update=f'\n窄门槛候选 {summary["candidate_count"]} 个，轮行可过而作废 {summary["invalid_wheel_passable"]} 个，有效 {summary["valid_count"]} 个。四有效 E/B 的逐场结果、首场真实 Lux 准入与 D 决定见窄门槛报告；本轮累计创建 {summary["cumulative_created"]}、GLB 成功 {summary["cumulative_glb_successes"]}，正式测试 0，未预注册。\n'
        link='[窄门槛标定](reviews/RESULT_CROSSING_NARROW_GENERATOR.md)' if relative=='docs/crossing.md' else '[窄门槛标定](RESULT_CROSSING_NARROW_GENERATOR.md)'
        path.write_text(existing+marker+update+link+'。\n')
    print(json.dumps({k:summary[k] for k in ['candidate_count','valid_count','cumulative_created','formal_test_scenes']}))
