"""Curate real learned-controller trials, figures and a rendered trajectory video."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from beforestep.paths import ROOT
from beforestep import scene
from .artifacts import font


def public(value, replacements=None):
    replacements = replacements or {}
    if isinstance(value, str):
        return replacements.get(value,value).replace(str(ROOT)+'/', '')
    if isinstance(value, list):
        return [public(item,replacements) for item in value]
    if isinstance(value, dict):
        return {key: public(item,replacements) for key,item in value.items()}
    return value


def write_json(path, value, replacements=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(public(value,replacements), ensure_ascii=False, indent=2)+'\n')


def preserve(source, destination, replacements=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == '.json':
        write_json(destination, json.loads(source.read_text()),replacements)
    elif source.suffix == '.jsonl':
        destination.write_text(''.join(json.dumps(public(json.loads(line),replacements), ensure_ascii=False)+'\n'
                                      for line in source.read_text().splitlines() if line.strip()))
    else:
        shutil.copy2(source, destination)


def polygons(definition):
    from scipy.spatial import ConvexHull
    scene.configure(definition['id'])
    scene.GOAL = tuple(definition['goal'])
    result = []
    for rock in scene.ROCKS.values():
        obj, _ = scene.rock_asset_uniform(rock['rock'], rock['height'])
        vertices = np.array([[float(v) for v in line.split()[1:3]] for line in Path(obj).read_text().splitlines() if line.startswith('v ')])
        angle = np.radians(rock['yaw'])
        rotation = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        points = vertices @ rotation.T + [rock['x'],rock['y']]
        result.append({**rock, 'polygon': points[ConvexHull(points).vertices].tolist()})
    return result


def run_data(label, source):
    definition = json.loads((source/'scene.json').read_text())
    summary = json.loads((source/'summary.json').read_text())
    events = [json.loads(line) for line in (source/'events.jsonl').read_text().splitlines() if line.strip()]
    identity = json.loads((source/'run_identity.json').read_text())
    with np.load(source/'traj.npz', allow_pickle=False) as archive:
        trace = {k: archive[k].copy() for k in archive.files}
    panes = [pane for event in events if event['kind']=='rehearsal' and event.get('role','execution')=='execution' for pane in event['panes']]
    indices = np.unique(np.r_[np.arange(0,len(trace['t']),6),len(trace['t'])-1])
    q = trace['qpos'];w,x,y,z = q[:,3:7].T
    yaw = np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))
    frames = [{'elapsed': float(trace['t'][i]-trace['t'][0]), 'x': float(q[i,0]), 'y': float(q[i,1]),
               'yaw': float(yaw[i]), 'action': trace['control_actions'][i].tolist(),
               'source': str(trace['control_sources'][i])} for i in indices]
    destination = ROOT/'evidence/learning'/label
    provenance=destination/'provenance.json'
    if provenance.exists() and json.loads(provenance.read_text())['source_identity_sha256']!=hashlib.sha256((source/'run_identity.json').read_bytes()).hexdigest():
        raise ValueError('A different completed trial already uses this evidence label: '+label)
    geometry_refs=[];replacements={}
    for target in (source/'looks').glob('look*/T*'):
        decision=target/'decide/target_decision.json'
        if not decision.exists():continue
        record=json.loads(decision.read_text());cache_id=record['cache_identity']
        shared=ROOT/'evidence/learning/geometry'/cache_id/target.name
        for path in (target/'decide').rglob('*'):
            if not path.is_file():continue
            if path.name=='target_decision.json' or path.name.startswith(('footprint_','world_')) or path.name=='align.json':
                preserve(path,shared/path.relative_to(target/'decide'))
                if path.name.startswith('world_'):
                    replacements[str(path)]=str((shared/path.relative_to(target/'decide')).relative_to(ROOT))
        geometry_refs.append({'target':target.name,'cache_identity':cache_id,'path':str(shared.relative_to(ROOT))})
    write_json(destination/'geometry.json',{'qualified_geometry':geometry_refs,
               'note':'Byte-identical candidate geometry is shared by input/GLB/protocol identity; each trial retains its own physical rehearsal and execution.'})
    for name in ('scene.json','summary.json','events.jsonl','run_identity.json','traj.npz','map_final.png'):
        if (source/name).exists():preserve(source/name,destination/name,replacements)
    for pane in (source/'rehearsal').glob('*/pane*'):
        for name in ('pane.json','traj.npz'):
            if (pane/name).exists():preserve(pane/name,destination/'rehearsal'/pane.relative_to(source/'rehearsal')/name,replacements)
    proof = {'source_identity_sha256': hashlib.sha256((source/'run_identity.json').read_bytes()).hexdigest(),
             'source_events_sha256': hashlib.sha256((source/'events.jsonl').read_bytes()).hexdigest(),
             'public_events_sha256': hashlib.sha256((destination/'events.jsonl').read_bytes()).hexdigest(),
             'trajectory_sha256': hashlib.sha256((destination/'traj.npz').read_bytes()).hexdigest(),
             'path_transform': 'Workspace paths made repository-relative; candidate mesh paths point to shared qualified geometry. Numerical results and mesh bytes unchanged.'}
    write_json(destination/'provenance.json', proof)
    comparison = next((event for event in reversed(events) if event['kind']=='decision_comparison'),{})
    names = {'dual_ppo_v2':'PPO v2 · 双岩石通行', 'gate_lux_v2':'PPO v2 + Lux3D · 关口通行',
             'gate_lux_v2_repeat':'PPO v2 + Lux3D · 独立复跑',
             'goal_variant_v2_failed':'PPO v2 + Lux3D · 大转向失败',
             'goal_variant_v4':'训练模型 v4 + Lux3D · 目标变体',
             'goal_variant_v4_repeat':'训练模型 v4 + Lux3D · 独立复跑',
             'goal_variant_v4_reference':'同一训练模型 · 去掉生成几何',
             'gate_live_v4':'训练模型 v4 · 关口实时通行', 'dual_live_v4':'训练模型 v4 · 双岩石实时通行',
             'v1_gate_collision':'模型 v1 · 关口碰撞失败',
             'trained_detour_live_v4':'v4 + Lux3D · 实时观测改路与到达',
             'trained_detour_live_v4_repeat':'v4 + Lux3D · 改路独立复跑',
             'trained_detour_reference_v4':'同一 v4 模型 · 去掉生成几何',
             'trained_detour_conservative_v4_failed':'同一 v4 模型 · 主动观察姿态失败',
             'trained_gate_lux_live_v4':'v4 + Lux3D · 原关口实时到达',
             'trained_gate_lux_live_v4_repeat':'v4 + Lux3D · 原关口独立复跑',
             'trained_near_goal_v4_rejected':'v4 + Lux3D · 近岩石任务无路，拒绝执行',
             'v5_observation_failed':'v5 · 主动观察失败',
             'v6_observation_failed':'v6 · 主动观察失败',
             'v6_staged_observation_failed':'v6 · 姿态分步实验仍未通过'}
    recorded = summary.get('start_mode')=='recorded_observation_state'
    return {'id':label, 'title':names.get(label,label), 'result':summary['result'],
            'goal':definition['goal'], 'start': q[0,:2].tolist(), 'rocks':polygons(definition),
            'frames':frames, 'duration':float(trace['t'][-1]-trace['t'][0]),
            'panes':len(panes), 'panes_passed':sum(p['completed'] and not p['collided'] for p in panes),
            'reference_path':comparison.get('reference_path'), 'selected_path':comparison.get('selected_path'),
            'controller_sha256':summary.get('controller_sha256'),
            'note':('从保存的真实观测状态开始，使用记录 RGB-D 和真实 Lux3D 资产；接近观察点的运动不计入本次模型执行。' if recorded else '从场景起点实际运行；实时仿真观测，移动和转向由固定神经网络控制。'),
            'evidence':f'evidence/learning/{label}/summary.json'}


def evaluation_data(label, source):
    summary = json.loads((source/'summary.json').read_text())
    destination = ROOT/'evidence/learning'/label
    for path in source.glob('*.json*'):preserve(path,destination/path.name)
    names = {'ppo':'PPO v2','bc':'BC v2','untrained':'未训练','rules':'规则专家','v4':'训练模型 v4','v2':'PPO v2'}
    rows = [{'label':names.get(name,name), **value} for name,value in summary['controllers'].items()]
    identity = json.loads((source/'run_identity.json').read_text())
    terrain = identity['terrain']
    note = f"种子 {identity['tasks'][0]['seed']} 起；同一任务清单，每回合最多 {identity['max_seconds_per_episode']:.0f}s；坡度 {terrain['slope_degrees']}°、粗糙度 {terrain['roughness_m']*1000:.0f}mm。"
    return {'id':label,'title':{'held_out_v2_flat':'v2 · 新种子平地目标','held_out_v2_slope':'v2 · 新种子坡地目标','held_out_v4':'大角度与近目标测试'}.get(label,label), 'controllers':rows,'note':note}


def figures(data, trainings):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    media = ROOT/'site/media';media.mkdir(parents=True,exist_ok=True)
    figure, axes = plt.subplots(1,len(data['evaluations']),figsize=(max(6,5*len(data['evaluations'])),4),squeeze=False)
    colors=['#278b75','#5d82bc','#ac6659','#8a7bad']
    for ax,evaluation in zip(axes[0],data['evaluations']):
        rows=evaluation['controllers'];labels=[row['label'].replace('训练模型 ','Model ').replace('未训练','Untrained').replace('规则专家','Rules') for row in rows]
        ax.bar(range(len(rows)),[r['success_rate']*100 for r in rows],color=colors[:len(rows)])
        ax.set_xticks(range(len(rows)),labels);ax.set_ylim(0,110);ax.set_ylabel('Success rate (%)');ax.set_title(evaluation['id'])
        for i,row in enumerate(rows):ax.text(i,row['success_rate']*100+2,f"{row['successes']}/{row['episodes']}",ha='center')
    figure.tight_layout();figure.savefig(media/'controller-evaluation.png',dpi=180);plt.close(figure)
    if trainings:
        figure,axes=plt.subplots(1,2,figsize=(12,4))
        for label,path in trainings:
            bc=json.loads((path/'behavior_cloning.json').read_text())
            records=[json.loads(line) for line in (path/'ppo.jsonl').read_text().splitlines()]
            axes[0].plot([r['epoch'] for r in bc],[r['loss'] for r in bc],label=label)
            axes[1].plot([r['control_steps'] for r in records],[r['reward_mean'] for r in records],label=label)
        axes[0].set(xlabel='BC epoch',ylabel='Weighted action loss',yscale='log');axes[1].set(xlabel='Real PPO control steps',ylabel='Mean rollout reward')
        for ax in axes:ax.legend();ax.grid(alpha=.2)
        figure.tight_layout();figure.savefig(media/'controller-training.png',dpi=180);plt.close(figure)


def render_video(runs, output=None):
    import mujoco
    from beforestep.visualization import camera
    output=Path(output) if output is not None else ROOT/'site/media/learning-demo.mp4'
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','12','-i','-',
                              '-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],stdin=subprocess.PIPE)
    for label,path in runs:
        definition=json.loads((path/'scene.json').read_text());scene.configure(definition['id']);scene.GOAL=tuple(definition['goal'])
        spec,rocks,_=scene.scene_spec(ROOT/'outputs/video-learning'/label)
        env=scene.make_env(spec);vm=camera.video_model(env,rocks,width=960,height=540,off=(960,540))
        vm.m.vis.quality.shadowsize=1024;vm.m.vis.quality.offsamples=1
        for group in range(6):vm.opt.geomgroup[group]=1 if group in (0,1,2) else 0
        trace=np.load(path/'traj.npz',allow_pickle=False);summary=json.loads((path/'summary.json').read_text())
        cam=mujoco.MjvCamera();cam.lookat[:]=[(trace['qpos'][0,0]+definition['goal'][0])/2,0.,.1];cam.distance=max(7.,definition['goal'][0]+1);cam.azimuth=90;cam.elevation=-70
        duration=float(trace['t'][-1]-trace['t'][0]);frames=int((duration/6+3)*12)
        for i in range(frames):
            elapsed=max(0.,min(duration,(i/12-1)*6));index=min(int(np.searchsorted(trace['t'],trace['t'][0]+elapsed)),len(trace['t'])-1)
            vm.sync(trace['qpos'][index]);vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt)
            image=Image.new('RGB',(1280,720),'#0b1018');image.paste(Image.fromarray(vm.r.render()),(160,95));draw=ImageDraw.Draw(image)
            draw.text((45,20),'NEXT ZENITH / 训练模型实际月面执行',font=font(28),fill='#e8eef2')
            mode='记录观测状态起步' if summary.get('start_mode')=='recorded_observation_state' else '场景起点 / 实时观测'
            draw.text((45,665),f'{label} · {mode} · {elapsed:.1f}/{duration:.1f}s · 真实轨迹 6×回放',font=font(19),fill='#70dbb2')
            if elapsed>=duration:draw.text((880,24),{'arrived':'到达 / 无碰撞','stuck':'预演拒绝 / 停下','collision':'碰撞停止'}.get(summary['result'],summary['result']),font=font(23),fill='#70dbb2')
            if label==runs[0][0] and i==12:image.save(ROOT/'site/media/learning-demo-poster.jpg',quality=92)
            process.stdin.write(image.tobytes())
        camera.release(vm)
    process.stdin.close()
    if process.wait()!=0:raise RuntimeError('Learned trajectory video encoding failed')


def main(argv=None):
    parser=argparse.ArgumentParser(prog='beforestep learning-artifacts')
    parser.add_argument('--run',action='append',required=True,help='LABEL=completed run directory')
    parser.add_argument('--evaluation',action='append',default=[],help='LABEL=completed controller evaluation')
    parser.add_argument('--training',action='append',default=[],help='LABEL=completed training directory for figures')
    parser.add_argument('--video',action='store_true')
    args=parser.parse_args(argv)
    parse=lambda values:[(value.split('=',1)[0],ROOT/value.split('=',1)[1]) for value in values]
    runs=parse(args.run);evaluations=parse(args.evaluation);trainings=parse(args.training)
    data={'schema':'beforestep-learned-demo/v1','runs':[run_data(label,path) for label,path in runs],
          'evaluations':[evaluation_data(label,path) for label,path in evaluations]}
    write_json(ROOT/'site/data/learning.json',data);figures(data,trainings)
    if args.video:render_video(runs)
    print(json.dumps({'runs':len(runs),'evaluations':len(evaluations),'video':args.video}),flush=True)
