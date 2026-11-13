"""Generate the low-stone evidence from existing terminal data, without reruns."""
import collections,copy,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import EVIDENCE

def trajectory_json(source,target):
    with np.load(source) as data:
        t=data['t'];q=data['qpos'];indices=np.unique(np.r_[np.arange(0,len(t),2),len(t)-1])
        rows=[{'t':round(float(t[i]),6),'position':np.round(q[i,:3],6).tolist(),
            'orientation_wxyz':np.round(q[i,3:7],7).tolist(),'joints':np.round(q[i,7:],6).tolist()} for i in indices]
    payload={'schema':'beforestep-trajectory/v1','nominal_hz':25,'joint_count':16,
        'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'samples':rows}
    write(target,payload);return {'path':str(target.relative_to(ROOT)),'sha256':sha(target),'samples':len(rows),'nominal_hz':25}

if __name__=='__main__':
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    folder=EVIDENCE/'low-stone';folder.mkdir(exist_ok=True)
    old=ROOT/'outputs/crossing/development/scene-dev-v9/seed-22001'
    scene=json.loads((old/'scene.json').read_text())
    B=json.loads((old/'method-B-v1/result.json').read_text());D=json.loads((old/'method-D-v1/result.json').read_text())
    lux=json.loads((ROOT/'evidence/crossing/development-lux-scene-dev-v9-22001.json').read_text())
    budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    reports=[json.loads(p.read_text()) for p in (ROOT/'evidence/crossing').glob('development-lux-*.json')]
    thresholds=json.loads((ROOT/'config/admission.json').read_text())
    admitted_by_task={c['task_id']:c for r in reports for c in r.get('candidates',[]) if c.get('task_id')}
    groups=collections.defaultdict(list)
    for r in budget['tasks']:
        if r.get('task_id') and not r['scene'].startswith('route/'):groups[r['scene'].split('/')[0]].append(r)
    inputs=[]
    for revision,rows in sorted(groups.items()):
        candidates=[admitted_by_task[r['task_id']] for r in rows if r['task_id'] in admitted_by_task]
        reasons=collections.Counter()
        for c in candidates:
            if c['admitted']:continue
            metrics=c['metrics']
            if metrics.get('contour_iou',1)<thresholds['contour_iou_min']:reasons['轮廓 IoU 不足']+=1
            if not thresholds['scale_ratio']['min']<=metrics.get('scale_ratio',1)<=thresholds['scale_ratio']['max']:reasons['尺度不符']+=1
            if metrics.get('hidden_frac',1)<thresholds['hidden_frac_min']:reasons['隐藏占比不足']+=1
            if metrics.get('shell_contact',1)<thresholds['shell_contact_min']:reasons['可见壳接触不足']+=1
            if metrics.get('free_intrusion_frac',0)>thresholds['free_intrusion_max']:reasons['侵入已知空地']+=1
        inputs.append({'revision':revision,'created':len(rows),'glb_successes':sum(r['status']=='ok' for r in rows),
            'admitted':sum(c['admitted'] for c in candidates),'admission_records_found':len(candidates),
            'main_rejections':dict(reasons),'task_ids':[r['task_id'] for r in rows]})
    true=trimesh.load(scene['truth_mesh'],force='mesh',process=False)
    models=[];fig,axes=plt.subplots(2,2,figsize=(12,7),layout='constrained')
    for ax,c in zip(axes.flat,[c for c in lux['candidates'] if c['admitted']]):
        imagined=trimesh.load(ROOT/c['world_mesh'],force='mesh',process=False)
        actual=true.copy();hypothesis=imagined.copy()
        actual.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[215,161,68,100],alphaMode='BLEND',doubleSided=True))
        hypothesis.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[98,176,203,190],alphaMode='BLEND',doubleSided=True))
        overlay=trimesh.Scene();overlay.add_geometry(actual,node_name='true_scan_amber');overlay.add_geometry(hypothesis,node_name='admitted_hypothesis_blue')
        world_to_gltf=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype=float)
        overlay.apply_transform(world_to_gltf)
        path=folder/f'overlay-{c["task_id"]}.glb';overlay.export(path)
        assert path.stat().st_size<=2_000_000
        models.append({'task_id':c['task_id'],'sample':c['id'],'path':str(path.relative_to(ROOT)),
            'bytes':path.stat().st_size,'sha256':sha(path),'admitted':True,'geometry':c['geometry'],
            'gltf_coordinate_frame':'Y up; position [x,z,-y] from MuJoCo [x,y,z]',
            'world_to_gltf':world_to_gltf.tolist(),
            'source_world_mesh':c['world_mesh'],'source_sha256':sha(ROOT/c['world_mesh'])})
        for mesh,color,label in [(true,'#ba821e','True scan'),(imagined,'#247f9e','Admitted hypothesis')]:
            from scipy.spatial import ConvexHull
            xy=mesh.vertices[:,:2];v=xy[ConvexHull(xy).vertices];v=np.vstack([v,v[0]])
            ax.plot(v[:,0],v[:,1],color=color,label=label,linewidth=2)
        ax.axhline(.192,color='gray',linestyle=':',linewidth=1);ax.axhline(-.192,color='gray',linestyle=':',linewidth=1)
        ax.set_title(f'Task {c["task_id"]}');ax.set_xlabel('Forward x (m)');ax.set_ylabel('Lateral y (m)');ax.set_xlim(2.97,3.24);ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.savefig(folder/'admitted-vs-truth.png',dpi=160);plt.close(fig)
    Btraj=trajectory_json(old/'method-B-v1/trajectory.npz',folder/'B-trajectory.json')
    shutil.copy2(old/'method-D-v1/result.json',folder/'D-decision.json')
    depths=[]
    for position in D['positions']:
        envelope=position.get('envelope') or position.get('geometry')
        if envelope and 'far' in envelope:depths.extend(np.array(envelope['far'])-np.array(envelope['near']))
    # The original decision stores a per-position envelope; use its exact fields.
    if not depths:
        for position in D['positions']:
            near=np.min([c['geometry']['near'] for c in position['candidates']],axis=0)
            far=np.max([c['geometry']['far'] for c in position['candidates']],axis=0)
            depths.extend(far-near)
    truth_depth=np.array(scene['truth_geometry']['far'])-np.array(scene['truth_geometry']['near'])
    narrow=json.loads((ROOT/'evidence/crossing/development-narrow-summary.json').read_text())
    blind=[x for row in narrow['scenes'] if row['valid'] for x in row['unseen_far_m']]
    low={'schema':'beforestep-crossing-low-stone/v1','development_not_formal':True,'seed':22001,
        'B':{'status':B['status'],'sim_seconds':B['sim_seconds'],'trajectory':Btraj,'result':str((old/'method-B-v1/result.json').relative_to(ROOT))},
        'D':{'status':D['status'],'reason':D['reason'],'physical_execution':False,'rehearsal_count':len(D['rehearsals']),
             'decision':str((folder/'D-decision.json').relative_to(ROOT))},
        'models':models,'overlay_image':str((folder/'admitted-vs-truth.png').relative_to(ROOT)),
        'truth_depth_m':truth_depth.tolist(),'imagination_envelope_depth_range_m':[float(min(depths)),float(max(depths))],
        'frozen_depth_limit_m':.15,'unseen_rear_range_m':[min(blind),max(blind)],
        'six_input_rounds':inputs,'threshold_created':sum(r['created'] for r in inputs),
        'threshold_admitted':sum(r['admitted'] for r in inputs),'new_simulations':0,'new_lux_tasks':0,
        'story_count_note':'STORY.md preserves the original 35-task checkpoint; this table includes the authorized closing batch.'}
    write(EVIDENCE/'low-stone.json',low)
    p=ROOT/'outputs/crossing/route/progress.json';data=json.loads(p.read_text());data['steps']['low_stone_assets'].update(status='终态',output=str((EVIDENCE/'low-stone.json').relative_to(ROOT)));write(p,data)
    print(json.dumps({'inputs':inputs,'threshold_created':low['threshold_created'],'threshold_admitted':low['threshold_admitted'],
        'depth_truth':low['truth_depth_m'],'depth_imagined':low['imagination_envelope_depth_range_m']},ensure_ascii=False),flush=True)
