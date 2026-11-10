"""Build the R1 viewer payload, figures and report from preserved experiments."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from beforestep import scene as S
from beforestep.navigation import map as N, controller as F
from beforestep import evaluation as E

BASE = ROOT/'evidence/reviews/beforestep_r1'
MEDIA = ROOT/'site/media'
FONT = Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
if FONT.exists():
    font_manager.fontManager.addfont(str(FONT))
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = '#101820'
plt.rcParams['axes.facecolor'] = '#101820'
plt.rcParams['text.color'] = '#e5edf0'
plt.rcParams['axes.labelcolor'] = '#a9b7bf'
plt.rcParams['xtick.color'] = '#a9b7bf'
plt.rcParams['ytick.color'] = '#a9b7bf'
plt.rcParams['axes.edgecolor'] = '#34424c'


def read(path):
    return json.loads(Path(path).read_text())


def preserve(source, destination):
    if not destination.exists():
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)


def preview(source, name, size=(1200,1200)):
    image = Image.open(source).convert('RGB')
    image.thumbnail(size)
    image.save(MEDIA/name,quality=92)
    return 'media/'+name


def trajectory(path, count=900):
    z=np.load(path);q=z['qpos'];indices=np.unique(np.r_[np.arange(0,len(q),max(1,len(q)//count)),len(q)-1])
    return [[round(float(z['t'][i]),4),round(float(q[i,0]),5),round(float(q[i,1]),5),
             round(float(F.yaw_of(q[i])),6)] for i in indices]


def main():
    S.configure('stress_v8');MEDIA.mkdir(parents=True,exist_ok=True)
    preserve(ROOT/'site/data/demo.json',ROOT/'site/data/history/trained_gate_v03.json')
    preserve(ROOT/'docs/report.md',ROOT/'docs/history/report_v03.md')
    preserve(ROOT/'site/report.html',ROOT/'site/media/history/trained_gate_v03/report.html')
    preserve(MEDIA/'report.pdf',MEDIA/'history/trained_gate_v03/report.pdf')
    runs={key:BASE/'section25_final_base'/key for key in ('conservative','optimistic','see_dark','truth')}
    runs['imagination']=BASE/'lux/original_b';runs['replay']=BASE/'lux/replay'
    runs.update({'trust_'+cid:BASE/'counterfactuals'/cid for cid in ('A1','B1','C2')})
    original=runs['imagination'];validation=read(BASE/'replay_validation.json')
    assert validation['all_trajectory_arrays_equal'] and validation['counterfactual_collisions']==0
    descriptions={
        'optimistic':'把太阳黑影与视线遮挡当作空地。原计划压入真实 B 21.9 cm，实际发生碰撞。',
        'conservative':'未知空间保持不可通行。五次实际观察后仍没有路线，安全停车。',
        'imagination':'真实 Lux3D 的八份准入几何支持路线；十二个组合完整预演后，在独立物理世界一眼到达。',
        'see_dark':'只让相机在太阳黑影中也有深度，其余条件相同；三眼到达，说明黑影是保守车的关键障碍。',
        'truth':'检验用真实形状替身，一眼到达。真实形状没有提供给生产规划器。',
        'replay':'复用同一观测与生成资产，重新规划、十二格预演和独立执行；全部轨迹数组及摘要与原运行一致。',
        **{'trust_'+cid:'只信 B/'+cid+' 这份被拒候选，其他条件保持。本次仍到达；本批自检偏保守，未证明它防止了碰撞。' for cid in ('A1','B1','C2')}}
    labels={'optimistic':'直接走','conservative':'看清再走','imagination':'想一想再走',
            'see_dark':'黑影测深对照','truth':'真实形状检验','replay':'完整重放',
            **{'trust_'+cid:'反事实 B/'+cid for cid in ('A1','B1','C2')}}
    data={'schema':'beforestep-r1-site/v1','review_id':'R1','scene_id':'stress_v8',
          'title':'R1 · 极地窄道 A+B','goal':list(S.GOAL),'robot_envelope':S.ROBOT,
          'runs':{},'candidates':[],'rocks':[], 'descriptions':descriptions,'labels':labels,
          'video':'media/demo.mp4','poster':'media/demo-poster.jpg','video_is_historical':True,
          'scope':'Recorded experiments; scan geometry is post-run review only.'}
    for key,path in runs.items():
        summary=read(path/'summary.json');identity=read(path/'run_identity.json')
        events=[json.loads(line) for line in (path/'events.jsonl').read_text().splitlines()]
        panes=[p for e in events if e['kind']=='rehearsal' for p in e['panes']]
        data['runs'][key]={**summary,'trajectory':trajectory(path/'traj.npz'),
                          'run_id':identity['run_id'],'rehearsals':len(panes),
                          'rehearsals_passed':sum(p['completed'] and not p['collided'] for p in panes),
                          'evidence':'evidence/reviews/beforestep_r1/'+str(path.relative_to(BASE))}
    from scipy.spatial import ConvexHull
    for key,rock in S.ROCKS.items():
        obj,_=S.rock_asset_uniform(rock['rock'],rock['height'])
        vertices=np.array([[float(v) for v in l.split()[1:3]] for l in Path(obj).read_text().splitlines() if l.startswith('v ')])
        yaw=np.radians(rock['yaw']);vertices=vertices @ np.array([[np.cos(yaw),-np.sin(yaw)],[np.sin(yaw),np.cos(yaw)]]).T+[rock['x'],rock['y']]
        data['rocks'].append({'id':key,'x':rock['x'],'y':rock['y'],'polygon':vertices[ConvexHull(vertices).vertices].tolist()})
    data['rille_edge']=[[float(x),float(S.rille_edge(x))] for x in np.linspace(-1,13,240)]
    data['wall_y']=S.WALL['y_inner']
    candidates={};admitted=0;failed=[];total=0;union=np.zeros_like(N.GX,dtype=bool)
    true=E.truth_footprints(original)
    for target in ('T2','T1'):
        directory=original/'looks/look1'/target;result=read(directory/'lux_result.json')
        decision=read(directory/'decide/target_decision.json');by_id={c['id']:c for c in decision['candidates']}
        state=read(directory/'state.json')
        for task in result['tasks']:
            total+=1
            if task['status']!='ok':
                failed.append({'target':target,'sample':task['id'],'task_id':task['task_id'],'status':task['status']});continue
            c=by_id[task['id']];admitted+=c['admitted'];name='r1_'+target+'_'+task['id']+'.jpg'
            fp=np.load(directory/'decide'/('footprint_'+task['id']+'.npy'))
            if c['admitted']:union |= fp
            row={'id':'r1_'+target+'_'+task['id'],'target':target,'sample_id':task['id'],
                 'label':('B' if target=='T2' else 'A')+'/'+task['id']+' · '+('通过' if c['admitted'] else '拒绝'),
                 'admitted':c['admitted'],'glb':task['glb'],
                 'input':preview(ROOT/task['inputs'][0],name),'task_id':task['task_id'],
                 'contour_iou':c['contour_iou'],'scale_ratio':c['scale_ratio'],
                 'thresholds':decision['thresholds'],
                 'rejection_reason':None if c['admitted'] else '轮廓 IoU 低于 '+str(decision['thresholds']['contour_iou_min']),
                 'native_px':state['crop_native_px'],'native_ok':state['native_ok'],
                 'back_error_m':float(N.GX[fp].max()-N.GX[true['B' if target=='T2' else 'A']].max()),
                 'verdict':'轮廓 IoU '+str(c['contour_iou'])+' · 尺度比 '+str(c['scale_ratio'])+' · '+('符合本次观测约束' if c['admitted'] else '未通过冻结自检')}
            data['candidates'].append(row);candidates[(target,task['id'])]=row
    data['target_states']={t:read(original/'looks/look1'/t/'state.json') for t in ('T1','T2')}
    data['generation']={'tasks':total,'succeeded':len(data['candidates']),'failed':len(failed),'admitted':admitted,'failed_tasks':failed}
    data['imagined_footprint']=np.c_[N.GX[union],N.GY[union]].tolist()
    state=np.load(original/'decision/look1_state.npy')
    events=[json.loads(l) for l in (original/'events.jsonl').read_text().splitlines()]
    comparison=next(e for e in events if e['kind']=='decision_comparison')
    rehearsal=next(e for e in events if e['kind']=='rehearsal')
    data['decision']={**comparison,'execution_rehearsals':rehearsal['panes'],
                     'reference_rehearsals':[],'observed_cells':{'shape':list(state.shape),
                     'values':state.ravel().tolist(),'resolution':N.RES,'origin':[N.X0,N.Y0]}}
    data['gallery']=[{'pane':p['pane'],'label':'A/'+Path(p['objects'][0]).stem.removeprefix('world_')+' + B/'+Path(p['objects'][1]).stem.removeprefix('world_'),
                     'completed':p['completed'],'collided':p['collided'],
                     'trajectory':trajectory(original/'rehearsal/look1'/('pane'+str(p['pane']))/'traj.npz',count=100),
                     'evidence':'https://github.com/codezzzsleep/next-zenith-beforestep/blob/main/evidence/reviews/beforestep_r1/lux/original_b/rehearsal/look1/pane'+str(p['pane'])+'/traj.npz'} for p in rehearsal['panes']]
    xy_audit=read(original/'eval.json')['actual_clearance_by_rock']['B']
    data['audit']={'xy_center_minus_half_width_B_m':xy_audit['min_center_minus_half_width_m'],
                   'cold_wall_s':read(original/'summary.json')['wall_s'],
                   'optimistic_intrusion_m':read(runs['optimistic']/'eval.json')['first_departure_plan_by_rock']['B']['planned_envelope_intrusion_proxy_m'],
                   'physical_clearance_B_m':validation['physical_clearance_B_m'],
                   'xy_envelope_clearance_B_m':xy_audit['min_xy_rectangle_envelope_gap_m'],'counterfactual_collisions':0,
                   'replay_trajectory_sha256':validation['replay_trajectory_sha256']}
    (ROOT/'site/data/demo.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    scenes={'default':'stress_v8_r1','scenes':[
        {'id':'stress_v8_r1','label':'主线 R1 · A+B 极地窄道','data':'data/demo.json'},
        {'id':'trained_gate_v03','label':'迭代附录 · v0.3 训练模型关口','data':'data/history/trained_gate_v03.json'},
        {'id':'gate_passage_v02','label':'迭代附录 · v0.2 规则关口','data':'data/history/gate_passage_v02.json'},
        {'id':'stress_v8_history','label':'历史边界 · 旧 V8 拒绝停车','data':'data/history/stress_v8.json'}]}
    (ROOT/'site/data/scenes.json').write_text(json.dumps(scenes,ensure_ascii=False))

    # Figures show saved observations and execution, never invented footage.
    rgb=np.asarray(Image.open(original/'looks/look1_rgb.png').convert('RGB'))
    preview(original/'looks/look1_rgb.png','r1-camera.jpg')
    fig,axes=plt.subplots(1,2,figsize=(13,5),gridspec_kw={'width_ratios':[1.3,1]})
    axes[0].imshow(rgb);axes[0].axis('off');axes[0].set_title('第一眼：机器人实际画面')
    from matplotlib.colors import ListedColormap
    colors=['#264c42','#8a8d88','#6f4eb0','#bd8251','#15202a','#56616a']
    axes[1].imshow(state.T,origin='lower',extent=[N.X0,N.X1,N.Y0,N.Y1],cmap=ListedColormap(colors),vmin=0,vmax=5,interpolation='nearest')
    axes[1].set(xlim=(2,9),ylim=(-1.55,1.55),title='截至第一眼的观测地图',xlabel='前进方向 x / m',ylabel='y / m')
    from matplotlib.patches import Patch
    axes[1].legend(handles=[Patch(color=colors[2],label='太阳黑影：没有深度'),Patch(color=colors[3],label='视线遮挡：被挡住')],loc='lower right',fontsize=9)
    fig.tight_layout();fig.savefig(MEDIA/'r1-shadows.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,4))
    x=np.linspace(1.8,11,300);ax.fill_between(x,S.rille_edge(x)-.05,1.5,color='#243945',label='月溪禁行');ax.axhspan(-1.5,S.WALL['y_inner'],color='#243945')
    for rock in data['rocks']:
        polygon=np.asarray(rock['polygon']);ax.fill(polygon[:,0],polygon[:,1],color='#818887',alpha=.75);ax.text(rock['x'],rock['y'],rock['id'],ha='center',va='center',color='#101820')
    for key,color in [('conservative','#ccad69'),('optimistic','#ff8d7e'),('imagination','#70dbb2')]:
        t=np.asarray(data['runs'][key]['trajectory']);ax.plot(t[:,1],t[:,2],color=color,lw=2,label=labels[key]+' · '+{'arrived':'到达','stuck':'停车','collision':'碰撞'}[data['runs'][key]['result']]);ax.scatter(t[-1,1],t[-1,2],color=color,s=25)
    ax.set(xlim=(1.8,11),ylim=(-1.5,1.5),xlabel='x / m',ylabel='y / m',title='同一 A+B 窄道、同一规则控制器：三种选择的实际轨迹')
    ax.legend(loc='upper left',fontsize=9);fig.tight_layout();fig.savefig(MEDIA/'r1-routes.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,3.4));brows=[candidates[('T2',i)] for i in ('A1','A2','B1','C1','C2')]
    ax.bar([c['sample_id'] for c in brows],[c['contour_iou'] for c in brows],color=['#70dbb2' if c['admitted'] else '#ff8d7e' for c in brows])
    ax.axhline(.7068,color='#dce3e5',ls='--',label='冻结轮廓门槛 0.7068');ax.set(ylim=(0,1),ylabel='轮廓 IoU',title='B 第一眼：两份准入，三份拒绝（另有 B2 生成失败）');ax.legend(fontsize=9)
    fig.tight_layout();fig.savefig(MEDIA/'r1-self-check.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,source,title in zip(axes,[original/'looks/look1/T2/gen/variants/A1.png',BASE/'standins/registration_fixed/looks/look2/T2/gen/variants/A1.png'],['真实主线第一眼：原图高度 251 px','独立替身第二眼：原图高度 506 px']):
        ax.imshow(Image.open(source));ax.axis('off');ax.set_title(title)
    fig.suptitle('第二眼是需要补看时的分支；本次真实主线一眼有路，未触发');fig.tight_layout();fig.savefig(MEDIA/'r1-observation.png',dpi=160);plt.close(fig)

    physical=read(original/'physical_clearance.json');fig,ax=plt.subplots(figsize=(9,3))
    values=[physical['rocks'][k]['minimum_signed_collision_geometry_distance_m']*1000 for k in ('A','B')]
    ax.barh(['岩石 A','岩石 B'],values,color=['#70dbb2','#70dbb2'])
    for y,v in enumerate(values):ax.text(v+4,y,f'{v:.3f} mm',va='center')
    ax.set(xlim=(0,max(values)*1.35),xlabel='全部保存状态中的最小三维碰撞几何距离 / mm',title='赛后复盘：实际碰撞几何有间隙，执行没有接触')
    fig.tight_layout();fig.savefig(MEDIA/'r1-clearance.png',dpi=160);plt.close(fig)

    result_table='\n'.join('| '+labels[k]+' | '+{'stuck':'无路线、停车','arrived':'到达','collision':'碰撞'}[data['runs'][k]['result']]+' | '+str(data['runs'][k]['looks'])+' | '+str(data['runs'][k]['sim_time_s'])+' s | [原始身份](../'+data['runs'][k]['evidence']+'/run_identity.json) |' for k in ('conservative','see_dark','optimistic','imagination','truth'))
    cf_table='\n'.join('| B/'+cid+' | 到达、无碰撞 | '+str(data['runs']['trust_'+cid]['sim_time_s'])+' s | [原始身份](../'+data['runs']['trust_'+cid]['evidence']+'/run_identity.json) |' for cid in ('A1','B1','C2'))
    candidate_table='\n'.join('| B/'+c['sample_id']+' | '+str(c['task_id'])+' | '+str(c['contour_iou'])+' | '+str(c['scale_ratio'])+' | '+('准入' if c['admitted'] else c['rejection_reason'])+' |' for c in brows)
    report=f'''# 先见一步：看不见的那一面，先走一遍

Next Zenith · 负责人 R1 主线复核 · Aholo Lux3D。主实验源码 `2147b2f`；完整结果与逐次原始 summary 见 [R1 执行记录](reviews/RESULT_BEFORESTEP_R1.md)。

## 两种影子，一个行动问题

太阳照不到的地方没有可靠深度；岩石挡住的地方也看不见。机器人沿月溪和大石堆之间的窄道前进，A 挡在前面，B 的一部分藏在盲区。第二次观察能改变视线遮挡，却不能照亮太阳黑影。系统让 Lux3D 提出符合可见观测的几何假设，检验路线后再行动。

![第一眼画面与两种未知](../site/media/r1-shadows.png)

## 窄道的约束

月溪与大石堆构成禁行边界，A遮住前方空间，B后半截凸进必须换道的通路。

## 三台车的实际结果

主场景保留 stress_v8 的 A+B、太阳、起点、第一眼和终点 `(10.5,0)`；所有主对比统一规则控制。保守车看五眼仍没有路线；只让相机在黑影里也有深度，三眼到达。乐观车碰撞，其出发前原计划车身压入真实 B {data['audit']['optimistic_intrusion_m']*100:.3f} cm，满足原要求的至少 10 cm。真实 Lux3D 分支一眼到达，12 个候选组合预演全部完成且无碰撞，独立执行也无碰撞。

| 运行 | 结果 | 观察次数 | 仿真总时长 | 证据 |
| --- | --- | --- | --- | --- |
{result_table}

![三种策略的实际轨迹](../site/media/r1-routes.png)

这些结果支持在本次冻结场景中生成几何对行动判断的作用；不宣称对任意石头或场景都可靠。地图上的扫描轮廓只用于赛后复盘，生产规划器不读取隐藏真值。

## 真实生成、自检与被拒候选

首眼共提交 12 个独立真实任务，获得 11 个 GLB、1 个服务端失败。A 的六份全部准入；B 的五个可用模型中两份准入、三份拒绝。B2 任务 `5958893` 失败，无 GLB；不能将它计为自检拒绝。所有原始输入、实际上传字节、任务身份、模型、矩阵和占据保留在 [完整实验数据](../evidence/reviews/beforestep_r1/lux/original_b)。

| 候选 | 真实 task ID | 轮廓 IoU | 尺度比 | 冻结自检 |
| --- | --- | --- | --- | --- |
{candidate_table}

![B 的冻结轮廓检查](../site/media/r1-self-check.png)

轮廓门槛 {decision['thresholds']['contour_iou_min']}、尺度比 {decision['thresholds']['scale_ratio']['min']}–{decision['thresholds']['scale_ratio']['max']}、壳层接触、已知自由空间侵入和未知比例等原门槛保持。准入表示符合当前可见观测，生成背面仍可能错误：两份准入 B 的后缘相对真实占据分别偏短 {abs(candidates[('T2','A2')]['back_error_m']):.2f} m、{abs(candidates[('T2','C1')]['back_error_m']):.2f} m。此次行动结果通过，不把它说成生成背面已准确。

## 第二眼的条件分支与配准修复

需要补看时，用目标可见高度、相机到最近观测格的距离和原图焦距估计像素高度；排除过近点，优先可达的 ≥512 px 点。两眼 native_ok 同时为真才调用两图三份，否则单用新视角六份；第二眼零准入仅追加同字节六份，合计十二仍零则停车，不看第三眼。

![真实首眼与独立替身的第二眼输入](../site/media/r1-observation.png)

本次真实B首眼251 px、native_ok=false，仍有A2和C1两份准入。独立完整替身验证中，第二眼预计513.388 px，实际506 px，仍按单图分支。发现局部配准优化的稀疏点评分变好、最终可见面评分反而退化；修复只保留最终评分更好的矩阵。原自检与余量没有放宽，B替身修复后IoU为0.9673，完整两眼预演与执行到达。40 项单测通过。本次真实主线首眼已有准入和路线，第二眼、追加与 B 替换均未触发；不冒称做了新的多轮 Lux 生成。

## 在想象中预演，然后在独立世界执行

规划使用全部八份准入几何的占据；执行前，在 A 六份 × B 两份共十二种物理场景中完整运行同一规则控制器。十二格均完成、无碰撞，其全部轨迹与原配置在仓库。之后在独立扫描几何世界执行，实际到达。完整 `--reuse-lux` 重放再次完成十二格与独立执行，t、qpos、阶段和动作来源等全部数组逐字节相同，轨迹 SHA256 为 `{validation['replay_trajectory_sha256']}`。

## 赛后真值与间隙复盘

按每一个保存 qpos 重建原 MuJoCo 可碰撞几何，其最小有符号距离为 A 256.109 mm、B 47.541 mm，均为正，与执行无碰撞相容。XY 的 0.76×0.66 m 矩形包络对 B 间隙为零，中心距离减半车宽最小为 -62.778 mm；这是平面包络指标，同时公开（中心减半宽=-0.062778 m），不当作三维接触。原规划始终遵循冻结的 5 cm 占据扩张规则；不将 47.541 mm 向上写成真实 5 cm。

![真实可碰撞几何的最小距离](../site/media/r1-clearance.png)

原运行墙钟 {data['audit']['cold_wall_s']} s，含冷配准和完整物理预演，不含此前云端排队，不能称为端到端延迟；仿真总时长与执行时间分别记录在summary。

原始 [eval](../evidence/reviews/beforestep_r1/lux/original_b/eval.json)、[三维最近点和时刻](../evidence/reviews/beforestep_r1/lux/original_b/physical_clearance.json) 与 [完整重放核验](../evidence/reviews/beforestep_r1/replay_validation.json) 可独立检查。

## 全部反事实：本批自检偏保守

按预注册逐一只信 B 第一眼被拒的 A1、B1、C2，不挑选，不补看，不重新调用 Lux3D。三次均到达、无碰撞，碰撞数 0/3。因此此次不能说“自检挡住了会撞的想象”；结论是本批自检偏保守。

| 只信的被拒 B | 实际终态 | 仿真总时长 | 证据 |
| --- | --- | --- | --- |
{cf_table}

## 迭代、训练与相关工作

V6/V7/V8 的源码、输入、生成资产、融合几何和失败结果保留。旧 gate_passage_001、终点 `(5.7,-0.5)` 的实验及训练控制移到附录：它们证明了工程闭环与网络运动，但对照同样能到达，没有证明 Lux3D 的必要性。固定 v4 实际训练 115490 行物理示教，部署权重与独立任务 15/16 评估均保留；新姿态网络、四眼实测和失败也保留，不继续训练迭代。

[训练附录](training.md) · [主动观察控制附录](observation-control.md) · [版本证据](milestones.md) · [旧 v0.3 报告](history/report_v03.md)。PSSNet、PVD、Robust Grasp Planning、Uncertain Regions 与 NBV-SC 为多候选形状、动作评价及补看提供研究依据；本项目贡献是受观测自检约束、同控制器完整预演与独立执行的轮腿导航实证，不主张全球首次或科学上只有 Lux3D 能实现。[相关工作](related-work.md)。

首页提供实际轨迹、全部候选与十二格预演的交互查看。当前是受控仿真实验，不是实机或月球部署。R1 新 Demo 由负责人使用完整保存数据制作；网页保留视频位置，现有 v0.3 视频明确作为历史，冻结发布不改。完整可运行源码、原资产、失败和恢复输入见 [仓库](../README.md)、[R1 数据说明](../evidence/reviews/beforestep_r1/README.md)。
'''
    (ROOT/'docs/report.md').write_text(report)
    import markdown
    html=markdown.markdown(report,extensions=['tables','fenced_code'])
    html=html.replace('../site/media/','media/').replace('href="../evidence/','href="evidence/')
    html=html.replace('href="../README.md"','href="https://github.com/codezzzsleep/next-zenith-beforestep"')
    for name in ('reviews/RESULT_BEFORESTEP_R1.md','training.md','observation-control.md','milestones.md','history/report_v03.md','related-work.md'):
        html=html.replace('href="'+name+'"','href="docs/'+name+'"')
    style='@page{size:A4;margin:16mm}body{max-width:860px;margin:35px auto;padding:0 16px;overflow-wrap:anywhere;color:#1d2730;font:14px/1.8 "WenQuanYi Zen Hei",sans-serif}h1{font-size:29px}h2{margin-top:28px;break-after:avoid}img{width:100%;height:auto;break-inside:avoid}a{color:#27644e}table{border-collapse:collapse;width:100%;break-inside:avoid}td,th{border:1px solid #bbb;padding:7px;overflow-wrap:anywhere}table{font-size:12px}code{font-size:11px;overflow-wrap:anywhere}'
    (ROOT/'site/report.html').write_text('<!doctype html><html lang="zh-CN"><head><link rel="icon" href="favicon.svg"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>先见一步 · R1 项目报告</title><style>'+style+'</style></head><body>'+html+'</body></html>')
    print(json.dumps({'runs':len(data['runs']),'candidates':len(data['candidates']),'panes':len(data['gallery']),
                      'main_result':data['runs']['imagination']['result'],'physical_clearance_B_mm':data['audit']['physical_clearance_B_m']*1000},indent=2))


if __name__=='__main__':main()
