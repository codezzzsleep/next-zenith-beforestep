"""Build result-driven report and replay assets from completed, immutable experiments."""
import base64
import gzip
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experimental.arena.common import OUT,read,write,sha,finite
from experimental.arena.evaluate import summarize
from experimental.arena.suite import clustered_comparison

METHODS=['conservative','optimistic','imagination','strict','strict_llm','learned','learned_no_lux','see_dark']
LABELS=dict(zip(METHODS,['保守规则','乐观规则','原想象规则','严格规则','严格+LLM','学习+Lux3D','学习，去掉Lux3D','see_dark参照']))


def percent(value):return f'{100*value:.2f}%'


def status(value):return {'arrived':'到达','collision':'碰撞','stopped':'停车','stuck':'停车','stopped_short':'停车','controller_failed':'控制未完成','execution_error':'执行错误'}.get(value,value)


def paired_comparison(rows,a,b):
    """Keep both overall and per-capsule summaries on the same paired worlds."""
    sides={method:[r for r in rows if r['method']==method] for method in [a,b]}
    for method,group in sides.items():
        assert len(group)==len({r['seed'] for r in group}),f'Duplicate paired row: {method}'
    common=set(r['seed'] for r in sides[a]) & set(r['seed'] for r in sides[b])
    assert common,f'No paired worlds: {a}/{b}'
    paired=[r for method in [a,b] for r in sides[method] if r['seed'] in common]
    return clustered_comparison(paired,a,b)


def report_summary(rows):
    summary=summarize(rows)
    for method,scopes in summary.items():
        for scope,values in scopes.items():
            group=[r for r in rows if r['method']==method and (scope=='all' or r['reachable'])]
            values['stop_rate']=values['stopped']/values['worlds'] if values['worlds'] else None
            values['mean_wall_seconds']=float(np.mean([r['wall_seconds'] for r in group])) if group else None
    return summary


def workpoint_description(workpoint):
    unsafe=[LABELS[m] for m,safe in workpoint['safe_workpoint_exists'].items() if not safe]
    text=f"两模型按验证集共同碰撞上限 {percent(workpoint['collision_limit'])} 选择工作点。"
    if unsafe:text+='、'.join(unsafe)+'没有满足上限的工作点，使用预注册的最低碰撞备选点；该备选点未满足验证安全条件。'
    else:text+='两者均存在满足验证安全条件的工作点。'
    return text


def statistical_report(result):
    lines=['## 可达分母、真实想象组与成对区间','',
        '| 方法 | 真值规划可达世界 | 到达率 | 碰撞率 | 停车率 |',
        '|---|---:|---:|---:|---:|']
    for method in METHODS:
        values=result['summary'][method]['reachable']
        rate=lambda key:percent(values[key]) if values[key] is not None else '—'
        lines.append(f"| {LABELS[method]} | {values['worlds']} | {rate('arrival_rate')} | {rate('collision_rate')} | {rate('stop_rate')} |")
    lines+=['','下表保留每个真实想象组的全部世界，并单列其中真值规划可达的世界。LLM只有前150场；缺席组不补记结果。数字为到达/碰撞/停车的场数。','',
        '| 想象组 | 方法 | 全部世界 | 到达/碰撞/停车 | 可达世界 | 可达组到达/碰撞/停车 |',
        '|---|---|---:|---|---:|---|']
    for capsule,summary in sorted(result['per_capsule'].items()):
        for method in METHODS:
            if method not in summary:continue
            all_values=summary[method]['all'];reachable=summary[method]['reachable']
            counts=lambda v:f"{v['arrived']}/{v['collision']}/{v['stopped']}"
            lines.append(f"| {capsule} | {LABELS[method]} | {all_values['worlds']} | {counts(all_values)} | {reachable['worlds']} | {counts(reachable)} |")
    lines+=['','成对差值均为前一方法减后一方法，单位为百分点。95%区间按真实想象组聚类自助2000次；LLM比较只用双方共同的150场，组内分母同样成对。','',
        '| 成对比较 | 共同世界 | 想象组 | 到达差 [95%CI] | 碰撞差 [95%CI] |',
        '|---|---:|---:|---|---|']
    comparisons=[*result['comparisons'].values(),result['llm']['paired_comparison']]
    for comparison in comparisons:
        ci=comparison['cluster_bootstrap_95ci']
        value=lambda key,i:f"{100*comparison[key]:.2f} [{100*ci[0][i]:.2f}, {100*ci[1][i]:.2f}]"
        lines.append(f"| {LABELS[comparison['a']]} − {LABELS[comparison['b']]} | {comparison['paired_worlds']} | {comparison['real_imagination_groups']} | {value('arrival_delta',0)} | {value('collision_delta',1)} |")
    lines+=['','## 验证集工作点','',workpoint_description(result['validation_workpoint']),'',
        '| 模型 | 所选阈值 | 验证到达率 | 验证碰撞率 | 存在安全工作点 |',
        '|---|---:|---:|---:|---|']
    workpoint=result['validation_workpoint']
    for method in ['learned','learned_no_lux']:
        chosen=next(v for v in workpoint['statistics'][method] if v['threshold']==workpoint['chosen'][method])
        lines.append(f"| {LABELS[method]} | {chosen['threshold']} | {percent(chosen['arrival_rate'])} | {percent(chosen['collision_rate'])} | {'是' if workpoint['safe_workpoint_exists'][method] else '否'} |")
    return lines


def verify_training():
    """Verify saved training artifacts without generating samples or training."""
    import torch
    cfg=read(ROOT/'experimental/arena/parameters.json');folder=OUT/'training-data'
    identity=read(folder/'identity.json');manifest=read(folder/'manifest.json')
    expected=set(range(cfg['train']['seed_start'],cfg['train']['seed_start']+cfg['train']['count']))
    assert identity['status']=='complete' and identity['worlds']==len(expected)==4000
    assert sha(folder/'manifest.json')==identity['manifest_sha256']
    assert len(manifest)==len(expected) and {r['seed'] for r in manifest}==expected
    for row in manifest:
        assert row==read(folder/'entries'/f"{row['seed']}.json")
        assert sha(ROOT/row['sample'])==row['sha256'],f"Training sample differs: {row['seed']}"
    variants={}
    for name,no_lux in [('lux',False),('no_lux',True)]:
        training=OUT/'training'/name;meta=read(training/'identity.json');curve=read(training/'curve.json')
        assert meta['status']=='complete' and meta['no_lux']==no_lux and meta['epochs']==15
        assert meta['manifest_sha256']==identity['manifest_sha256']
        assert meta['train_source_sha256']==sha(ROOT/'experimental/arena/train.py')
        assert meta['model_source_sha256']==sha(ROOT/'experimental/arena/model.py')
        assert meta['protocol_commit']==identity['protocol_commit']
        assert sha(training/'best.pt')==meta['best_sha256']
        assert [r['epoch'] for r in curve]==list(range(1,16))
        best=torch.load(training/'best.pt',map_location='cpu',weights_only=False)
        latest=torch.load(training/'latest.pt',map_location='cpu',weights_only=False)
        assert latest['epoch']==15 and latest['history']==curve
        assert best['best_train_loss']==min(r['train_loss'] for r in curve)==meta['best_train_loss']
        for checkpoint in [best,latest]:
            assert checkpoint['manifest_sha256']==identity['manifest_sha256'] and checkpoint['no_lux']==no_lux
            assert checkpoint['seed']==meta['seed']==20261112
            assert all(k in checkpoint for k in ['state_dict','optimizer','torch_rng','numpy_rng','python_rng','loader_rng'])
        variants[name]={'best_sha256':sha(training/'best.pt'),'latest_sha256':sha(training/'latest.pt'),
            'epochs':15,'optimizer_and_rng_retained':True,'parameters':meta['parameters']}
    proof={'passed':True,'worlds':len(manifest),'manifest_sha256':identity['manifest_sha256'],
        'all_samples_and_entries_verified':True,'variants':variants,'training_or_simulation_rerun':False}
    write(OUT/'acceptance/training-artifacts.json',proof)
    return proof


def final_report(result):
    """The same seven answers are used for RESULT and the final handoff."""
    summary=result['summary'];criteria=result['criteria'];llm=result['llm'];effect=result['lux_effect']
    learned=summary['learned']['all'];strict=summary['strict']['all']
    lines=[f"封存 {learned['worlds']} 个未见月面：学习模型到达 {percent(learned['arrival_rate'])}、碰撞 {percent(learned['collision_rate'])}；严格规则到达 {percent(strict['arrival_rate'])}、碰撞 {percent(strict['collision_rate'])}。",
        '安全'+('通过' if criteria['safety'] else '未通过')+'；到达提升10个百分点'+('通过' if criteria['arrival'] else '未通过')+'；不被规则支配'+('通过' if criteria['nondominated'] else '未通过')+'。','',
        '1. 封存八方法（LLM使用前150场成对子集）：','',
        '| 方法 | 世界数 | 到达率 | 碰撞率 | 停车率 |','|---|---:|---:|---:|---:|']
    for method in METHODS:
        v=summary[method]['all'];lines.append(f"| {LABELS[method]} | {v['worlds']} | {percent(v['arrival_rate'])} | {percent(v['collision_rate'])} | {percent(v['stop_rate'])} |")
    lines+=['',f"2. 去掉Lux3D后，到达率差（带Lux减消融）为 {100*effect['arrival_delta_lux_minus_no_lux']:.2f} 个百分点。{workpoint_description(result['validation_workpoint'])}封存碰撞率分别为 {percent(effect['lux_collision_rate'])}、{percent(effect['no_lux_collision_rate'])}；实测碰撞率不保证相等。",'',
        f"3. v2共发出 {llm['all_v2_requests']} 次请求；封存LLM实际裁决 {llm['actual_decisions']} 步、回退 {llm['fallbacks']} 步。相对同批严格规则，到达差 {100*llm['paired_comparison']['arrival_delta']:.2f} 个百分点、碰撞差 {100*llm['paired_comparison']['collision_delta']:.2f} 个百分点，每场平均多等待 {llm['mean_extra_wait_per_world']:.2f} 秒。完整验证/封存成对结果与等待在result.json/llm。",'',
        '4. 六个真实留出场景（新学习策略的MuJoCo执行与既有记录）：','',
        '| 场景 | 学习模型 | 既有严格 | 既有原想象 | 既有see_dark |','|---|---|---|---|---|']
    for row in result['real_heldouts']:lines.append(f"| {row['scene']} | {row['learned']} | {row['strict']} | {row['imagination']} | {row['see_dark']} |")
    ds=result['final_prechecks']['development']['summary']
    lines+=['',f"5. 最终开发预检：乐观碰撞 {percent(ds['optimistic']['all']['collision_rate'])}；保守未到 {percent(1-ds['conservative']['all']['arrival_rate'])}；see_dark可达组 {ds['see_dark']['reachable']['arrived']}/{ds['see_dark']['reachable']['worlds']}={percent(ds['see_dark']['reachable']['arrival_rate'])}。快速观测17场状态一致77.0465%、三方法33/51=64.7059%，失败后改用正式RGB-D；移植保真30场168候选、1次准入翻转=0.595238%。",'',
        f"6. 学习未到达 {len(result['failed_learned_worlds'])} 场，全部失败种子/轨迹/概率图在evidence/learning/arena_v2/sealed。物理控制与数值失败在physical及real-heldouts；LLM服务、解析与不确定请求在llm/calls；旧失败预检仍在prechecks。未做LLM的OOD评分、未做单独石种留出；评分只使用真实胶囊、没有新增Lux付费。几何与物理一致率逐方法在result.json；达标失败照实保留。",'',
        '7. 发布提交号和实际公网验收记录在本文件末尾的“发布核验”记录；页面：https://codezzzsleep.github.io/next-zenith-beforestep/arena.html。验证命令：','',
        '```bash','python ops/check_arena_integrity.py --out outputs/arena-integrity.json',
        'python ops/check_arena_page.py --base https://codezzzsleep.github.io/next-zenith-beforestep/ --out outputs/arena-public-check',
        'python -m experimental.arena.cli run --seed 9200000 --method learned --out outputs/arena-new-9200000','```']
    return '\n'.join(lines)+'\n'


def packed(array):
    a=np.asarray(array,np.uint8).ravel()
    return base64.b64encode(a.tobytes()).decode()


def replay_timing(row,cfg):
    trace=np.asarray(row['trace']);indices=[];minimum=0
    for eye in row['observations']:
        k=minimum+int(np.argmin(np.linalg.norm(trace[minimum:]-eye['position'],axis=1)))
        assert np.linalg.norm(trace[k]-eye['position'])<1e-6,'Replay eye position missing from saved trace'
        indices.append(k);minimum=k
    distance=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(trace,axis=0),axis=1))]
    eye_times=distance[indices]/cfg['speed_m_s']+np.arange(len(indices))*cfg['look_seconds']
    trace_times=distance/cfg['speed_m_s']+np.searchsorted(indices,np.arange(len(trace)),side='left')*cfg['look_seconds']
    duration=float(distance[-1]/cfg['speed_m_s']+len(indices)*cfg['look_seconds'])
    if 'elapsed_seconds' in row:assert abs(duration-row['elapsed_seconds'])<1e-6,'Replay clock differs from saved episode budget'
    return {'eye_indices':indices,'eye_times':eye_times.tolist(),'trace_times':trace_times.tolist(),'duration_seconds':duration,
        'clock':'Saved path distance / frozen speed plus explicit-look budget; stationary turns retain separate eyes'}


def archive_payload(seed,world,rows):
    from beforestep.navigation import map as N
    from experimental.arena.capsules import transplant
    cfg=read(ROOT/'experimental/arena/parameters.json');lib=read(ROOT/cfg['capsule_library'])
    capsule=next(c for c in lib['capsules'] if c['id']==world['capsule_id'])
    T=np.array(world['transplant']);yaw=np.degrees(np.arctan2(T[1,0],T[0,0]))
    capsule=transplant(capsule,yaw,T[:2,3])
    hypotheses=[{'task_id':c['task_id'],'admitted':c['frozen_admitted'],'cells':c.get('footprint_world_xy',[])} for c in capsule['candidates'] if c['registration_available']]
    payload={'seed':seed,'capsule_id':world['capsule_id'],'shape':[N.NX,N.NY],'bounds':[N.X0,N.X1,N.Y0,N.Y1],'goal':world['definition']['goal'],'reachable':rows[0]['reachable'],'hypotheses':hypotheses,'methods':{}}
    for row in rows:
        method=row['method'];folder=OUT/'llm/sealed'/str(seed) if method=='strict_llm' else OUT/'sealed'/str(seed)
        path=folder/f'{method}-maps.npz'
        with np.load(path) as a:
            # The archive retains each raw eye; decisions use cumulative fusion.
            # Reconstruct that exact view so overlays and model risk agree.
            raw_states=a['state_history'];states=[N.fuse(raw_states[:k+1]) for k in range(len(raw_states))];risks=a['risk']
            assert len(states)==len(row['observations']), f'Observation count differs: {seed}/{method}'
            for state,eye in zip(states,row['observations']):
                assert np.bincount(state.ravel(),minlength=6).tolist()==eye['state_counts'], f'Fused replay differs from decision evidence: {seed}/{method}'
            payload['truth']=packed(a['truth'])
            payload['methods'][method]={**row,'states':[packed(s) for s in states],
                'risks':[packed(np.clip(np.rint(p*255),0,255)) for p in risks],
                **replay_timing(row,cfg),'state_display':'Cumulative frozen N.fuse of recorded explicit looks',
                'evidence':str((folder/f'{method}.json').relative_to(ROOT))}
    return payload


def real_comparison():
    original=read(ROOT/'evidence/reviews/beforestep_r3/summary.json')['holdouts']
    c7=read(ROOT/'evidence/award/demo/result.json')
    historical={r['scene']:r['runs'] for r in original};historical[c7['scene']]=c7['runs']
    rows=[]
    for row in read(OUT/'real-heldouts/results.json'):
        scene=row.get('scene',row.get('identifier'));runs=historical[scene]
        rows.append({'scene':scene,'learned':status(row['status']),
                    'strict':status(runs['imagination_strict']['summary']['result']),
                    'imagination':status(runs['imagination']['summary']['result']),
                    'see_dark':status(runs['see_dark']['summary']['result']),
                    'evidence':str((OUT/'real-heldouts'/scene/'learned/result.json').relative_to(ROOT))})
    return rows


def plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams['svg.hashsalt']='beforestep-arena-v2'
    folder=ROOT/'site/media/arena';folder.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(7,3.5))
    for variant,label in [('lux','With Lux3D'),('no_lux','Without Lux3D')]:
        curve=read(OUT/'training'/variant/'curve.json');ax.plot([r['epoch'] for r in curve],[r['train_loss'] for r in curve],label=label)
    ax.set(xlabel='Epoch',ylabel='Unknown-cell BCE');ax.legend();fig.tight_layout();fig.savefig(folder/'training.svg',metadata={'Date':None});plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,3.5));ax.plot([0,1],[0,1],'--',color='#aaa',label='Ideal')
    for variant,label in [('lux','With Lux3D'),('no_lux','Without Lux3D')]:
        c=read(OUT/'calibration'/f'{variant}.json');good=np.array(c['counts'])>0
        ax.plot(np.array(c['mean_probability'])[good],np.array(c['actual_fraction'])[good],marker='o',label=f"{label}, ECE {c['ece']:.4f}")
    ax.set(xlabel='Predicted occupancy',ylabel='Observed occupancy',xlim=(0,1),ylim=(0,1));ax.legend();fig.tight_layout();fig.savefig(folder/'calibration.svg',metadata={'Date':None});plt.close(fig)


def main():
    from experimental.arena.registration import require_registration
    require_registration()
    training_verification=verify_training()
    for relative in ['sealed','ood','llm/sealed','llm/validation','real-heldouts','physical']:
        assert read(OUT/relative/'identity.json')['status']=='complete',f'Incomplete experiment: {relative}'
    rows=read(OUT/'sealed/results.json')+read(OUT/'llm/sealed/results.json');summary=report_summary(rows)
    cfg=read(ROOT/'experimental/arena/parameters.json')
    expected_seeds=set(range(cfg['sealed']['seed_start'],cfg['sealed']['seed_start']+cfg['sealed']['count']))
    for method in METHODS:
        group=[r for r in rows if r['method']==method]
        expected=set(sorted(expected_seeds)[:150]) if method=='strict_llm' else expected_seeds
        assert len(group)==len(expected) and {r['seed'] for r in group}==expected, f'Incomplete or duplicated sealed method: {method}'
    learned=summary['learned']['all'];strict=summary['strict']['all'];no=summary['learned_no_lux']['all']
    comparisons={m:paired_comparison(rows,'learned',m) for m in ['conservative','optimistic','imagination','strict','strict_llm','learned_no_lux']}
    dominated=[m for m in ['conservative','optimistic','imagination','strict','strict_llm'] if comparisons[m]['arrival_delta']<0 and comparisons[m]['collision_delta']>0]
    verdict={'safety':learned['collision_rate']<=min(.03,strict['collision_rate']+.01)+1e-12,'arrival':learned['arrival_rate']>=strict['arrival_rate']+.10-1e-12,'nondominated':not dominated,'dominating_rules':dominated}
    effects={'arrival_delta_lux_minus_no_lux':learned['arrival_rate']-no['arrival_rate'],'lux_collision_rate':learned['collision_rate'],'no_lux_collision_rate':no['collision_rate'],'validation_collision_limit':read(OUT/'validation/workpoint.json')['collision_limit']}
    llm=read(OUT/'llm/sealed/summary.json');llm_rows=[r for r in rows if r['method']=='strict_llm'];paired=paired_comparison(rows,'strict_llm','strict')
    requests=[read(p) for p in (OUT/'llm/calls').glob('*-*.json')]
    llm_info={**llm,'paired_comparison':paired,'all_v2_requests':len(requests),'successful_requests':sum(r['status']=='ok' for r in requests),'parse_or_service_failures':sum(r['status']!='ok' for r in requests),'mean_extra_wait_per_world':llm['wait_seconds']/len(llm_rows)}
    real=real_comparison();worlds=[];folder=ROOT/'site/data/arena/worlds';folder.mkdir(parents=True,exist_ok=True)
    physical_rows=read(OUT/'physical/results.json');geometric={(r['seed'],r['method']):r for r in rows}
    assert len(real)==6 and len({r['scene'] for r in real})==6,'All six real heldouts must remain in the report'
    assert len(physical_rows)==72,'All first-24 paired physical episodes must remain in the report'
    physical={}
    for method in ['optimistic','strict','learned']:
        group=[r for r in physical_rows if r['method']==method]
        matches=sum(r['status']==geometric[(r.get('seed',r.get('identifier')),method)]['status'] for r in group)
        physical[method]={'worlds':len(group),'matches':matches,'agreement':matches/len(group),'outcomes':dict(Counter(r['status'] for r in group))}
    validation_workpoint=read(OUT/'validation/workpoint.json');workpoint=validation_workpoint['chosen']
    selected_validation=[r for r in read(OUT/'validation/results.json') if not r['method'].startswith('learned') or r['threshold']==workpoint[r['method']]]
    validation_llm=read(OUT/'llm/validation/results.json')
    llm_info['validation_vs_strict']=paired_comparison(selected_validation+validation_llm,'strict_llm','strict')
    llm_info['validation_vs_learned']=paired_comparison(selected_validation+validation_llm,'strict_llm','learned')
    llm_info['sealed_vs_learned']=paired_comparison(rows,'strict_llm','learned')
    final_gate=read(OUT/'prechecks/final.json');development=read(ROOT/final_gate['development'])
    fidelity=read(ROOT/final_gate['fidelity']);ood=read(OUT/'ood/summary.json')
    for seed in sorted({r['seed'] for r in rows}):
        group=[r for r in rows if r['seed']==seed];world=read(OUT/'sealed'/str(seed)/'world.json')
        worlds.append({'seed':seed,'capsule_id':world['capsule_id'],'reachable':group[0]['reachable'],'results':{r['method']:r['status'] for r in group}})
        body=json.dumps(finite(archive_payload(seed,world,group)),ensure_ascii=False,separators=(',',':')).encode()
        (folder/f'{seed}.json.gz').write_bytes(gzip.compress(body,mtime=0))
    failures=[w['seed'] for w in worlds if w['results']['learned']!='arrived']
    representatives=list(dict.fromkeys([*failures[:2],*(w['seed'] for w in worlds)]))[:6]
    groups=len({w['capsule_id'] for w in worlds});methods=[{'id':m,**summary[m]['all']} for m in METHODS]
    per_capsule={capsule:report_summary([r for r in rows if r['capsule_id']==capsule]) for capsule in sorted({r['capsule_id'] for r in rows})}
    result={'schema':'beforestep-arena-results/v2','summary':summary,'per_capsule':per_capsule,'validation_workpoint':validation_workpoint,'training_verification':training_verification,'criteria':verdict,'lux_effect':effects,'llm':llm_info,'comparisons':comparisons,'real_heldouts':real,'physical_confirmation':physical,'ood_summary':ood,'final_prechecks':{'development':development,'fidelity':fidelity},'worlds':worlds,'real_imagination_groups':groups,'representatives':representatives,'failed_learned_worlds':failures,'new_lux_tasks':0}
    write(OUT/'result.json',finite(result))
    (OUT/'final-answer.md').write_text(final_report(result))
    headline=f"{len(worlds)} 个未见随机月面，{groups} 个真实想象组。学习模型到达 {percent(learned['arrival_rate'])}，碰撞 {percent(learned['collision_rate'])}；严格规则到达 {percent(strict['arrival_rate'])}，碰撞 {percent(strict['collision_rate'])}。"
    verdict_text='达标判定：'+ '；'.join(f"{name}{'通过' if verdict[key] else '未通过'}" for key,name in [('safety','安全'),('arrival','到达提升10个百分点'),('nondominated','不被规则支配')])+'。'
    effects_text=workpoint_description(validation_workpoint)+f"带Lux3D的到达率比消融高 {100*effects['arrival_delta_lux_minus_no_lux']:.2f} 个百分点；封存碰撞率分别为 {percent(learned['collision_rate'])}、{percent(no['collision_rate'])}。"
    training_text='4000 个训练世界，300 个开发世界，300 个验证世界；两个相同架构的卷积模型分别完成15轮未知占据监督训练。真值只用于教师标签、独立评分和诊断。'
    llm_text=f"封存成对子集 {len(llm_rows)} 场，LLM实际裁决 {llm['actual_decisions']} 步，回退 {llm['fallbacks']} 步；每场平均额外等待 {llm_info['mean_extra_wait_per_world']:.2f} 秒。相对严格规则到达差 {100*paired['arrival_delta']:.2f} 个百分点，碰撞差 {100*paired['collision_delta']:.2f} 个百分点。"
    write(ROOT/'site/data/arena.json',finite({**result,'methods':methods,'headline':headline,'verdict_text':verdict_text,'effects_text':effects_text,'training_text':training_text,'llm_text':llm_text}))
    for variant in ['lux','no_lux']:
        target=ROOT/'assets/models/arena_v2'/variant;target.mkdir(parents=True,exist_ok=True)
        for name in ['best.pt','latest.pt']:shutil.copy2(OUT/'training'/variant/name,target/name)
    plots()
    lines=['# 随机月面竞技场：Arena v2','',headline,verdict_text,effects_text,'','## 封存结果','', '| 方法 | 世界数 | 到达率 | 碰撞率 | 安全停车率 | 平均眼数 | 平均含观察耗时 | 路径长度 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in methods:lines.append(f"| {LABELS[m['id']]} | {m['worlds']} | {percent(m['arrival_rate'])} | {percent(m['collision_rate'])} | {percent(m['stop_rate'])} | {m['mean_looks']:.2f} | {m['mean_elapsed_seconds']:.2f}s | {m['mean_path_length_m']:.2f}m |")
    lines+=['',llm_text,'',f"共有 {len(worlds)} 个世界、{groups} 个不同真实想象组。完整结果另列真值规划可达的分母；可达性是使用冻结安全余量规划器的诊断，不是物理可达性的完备证明。成对置信区间按胶囊聚类自助2000次，见result.json中的comparisons。",'',*statistical_report(result),'','## 六个真实留出场景','', '| 场景 | 学习模型 | 既有严格 | 既有原想象 | 既有see_dark |','|---|---|---|---|---|']
    for r in real:lines.append(f"| {r['scene']} | {r['learned']} | {r['strict']} | {r['imagination']} | {r['see_dark']} |")
    lines+=['','## 物理确认与更密分布','', '| 方法 | 前24场物理结果 | 与几何终态一致 |','|---|---|---:|']
    for method,metrics in physical.items():lines.append(f"| {LABELS[method]} | {json.dumps(metrics['outcomes'],ensure_ascii=False)} | {metrics['matches']}/{metrics['worlds']} |")
    lines+=['', '| 方法 | OOD世界数 | 到达率 | 碰撞率 |','|---|---:|---:|---:|']
    for method,metrics in ood.items():
        values=metrics['all'];lines.append(f"| {LABELS[method]} | {values['worlds']} | {percent(values['arrival_rate'])} | {percent(values['collision_rate'])} |")
    ds=development['summary'];lines+=['','## 最终开发门卫','',f"乐观碰撞 {ds['optimistic']['all']['collision']}/{ds['optimistic']['all']['worlds']}={percent(ds['optimistic']['all']['collision_rate'])}；保守未到达 {ds['conservative']['all']['stopped']}/{ds['conservative']['all']['worlds']}={percent(1-ds['conservative']['all']['arrival_rate'])}；see_dark真值规划可达组 {ds['see_dark']['reachable']['arrived']}/{ds['see_dark']['reachable']['worlds']}={percent(ds['see_dark']['reachable']['arrival_rate'])}。最终门卫passed={development['passed']}。",'','几何耗时为路径长/0.15m/s加每眼1s的预算估算，实际转向与动力学另见MuJoCo记录。各原始记录保留墙钟耗时，它包含渲染、规划、推理和等待，并受同场观测缓存与并行顺序影响，不据此声称端到端速度收益。']
    lines+=['','真实场景从保留的第一眼状态开始；首次接近段未重跑或计作学习动作。后续使用冻结RGB-D、缓存真实Lux候选与MuJoCo规则控制，观察预算5眼。','', '## 方法与数据','',training_text,'', '竞技场沿用5cm地图与六状态，只在显式停看时观测，途中不更新地图。所有方法预算12眼，数值规划/底层规则控制相同。新Lux付费0；真实GLB、原相机、太阳整体刚体移植，后眼不新增想象。留出布局、摆位、Lux结果，石头种类重叠。初始1m已知空地按生成器核验共同提供。学习模型预测未知占据，找路交给数值代码；去掉6:15全部Lux通道的消融用同数据、架构、种子和轮数。','', '快速近似观测预检17场状态一致77.0465%，三参照终态一致33/51=64.7059%，未通过，已改用正式RGB-D生成。最终开发门卫见prechecks/final.json及development-production-6/summary.json。30场移植保真168候选/1翻转=0.595238%；新12眼预算下30世界的首眼定义完全相同，原检查直接复用。旧第5批300场未通过（see_dark167/205=81.4634%），旧数据完整保留。','', '工作点只在300验证集选，规则和候选阈值见不可改预注册；封存500和更密OOD300均为固定权重的一次性首次运行。概率校准见calibration，两模型ECE为 '+', '.join(f"{v}: {read(OUT/'calibration'/f'{v}.json')['ece']:.6f}" for v in ['lux','no_lux'])+'。','', '## 失败与局限','',f"学习模型未到达 {len(failures)} 场；逐场原件、风险图和轨迹在evidence/learning/arena_v2/sealed/，失败种子见result.json。物理确认取封存前24场三方法，全部原件及控制/数值失败在physical/。源相同但几何代理与实际接触分别报告，不能用二维结果代替物理安全。LLM所有请求、解析/服务失败和不确定请求在llm/calls；回退不算模型裁决。",'', '## 复现','', '```bash','git lfs pull --include="assets/runtime-*.tar.gz,assets/candidates/**" --exclude=""','./setup.sh','.venv/bin/python -m pip install -r requirements-arena.txt','.venv/bin/python -m experimental.arena.cli run --seed 9200000 --method learned --out outputs/arena-new-9200000','.venv/bin/python ops/restore_arena_inputs.py','.venv/bin/python -m experimental.arena.cli real --scene suite_r2_v4_F0_003 --model assets/models/arena_v2/lux/best.pt --out outputs/arena-real-new-F0_003','```','', '独立新种子只复用有限的真实想象库。结果页是记录回放，运行新种子需命令行。完整预注册、训练曲线/权重/数据清单SHA、每场记录和全部失败均在evidence/learning/arena_v2。']
    (ROOT/'docs/arena.md').write_text('\n'.join(lines)+'\n')
    print(headline);print(verdict_text)


if __name__=='__main__':main()
