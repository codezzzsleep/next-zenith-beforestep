"""Build reproducible showcase data and comparisons from retained real assets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from beforestep.paths import ROOT

MEDIA=ROOT/'site/media'


@lru_cache(maxsize=16)
def font(size):
    for path in ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(path).exists():return ImageFont.truetype(path,size)
    return ImageFont.load_default(size=size)


def mesh_image(path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import trimesh
    mesh=trimesh.load(path,force='mesh',process=False)
    vertices=np.asarray(mesh.vertices);faces=np.asarray(mesh.faces)
    if Path(path).suffix.lower()=='.glb':vertices=vertices[:,[0,2,1]]
    fig=plt.figure(figsize=(4,3.3),facecolor='#131b24')
    ax=fig.add_subplot(111,projection='3d',facecolor='#131b24')
    subset=faces[::max(1,len(faces)//6000)]
    ax.add_collection3d(Poly3DCollection(vertices[subset],facecolor='#8ec8b4',edgecolor='#36544b',linewidths=.12))
    mid=(vertices.min(0)+vertices.max(0))/2;radius=float(np.ptp(vertices,axis=0).max())*.55
    ax.set_xlim(mid[0]-radius,mid[0]+radius);ax.set_ylim(mid[1]-radius,mid[1]+radius);ax.set_zlim(mid[2]-radius,mid[2]+radius)
    ax.view_init(25,-55);ax.set_box_aspect((1,1,1));ax.axis('off')
    temp=MEDIA/f'_mesh_{hashlib.sha256(str(path).encode()).hexdigest()[:8]}.png'
    fig.savefig(temp,dpi=150,bbox_inches='tight',facecolor=fig.get_facecolor());plt.close(fig)
    result=Image.open(temp).convert('RGB');temp.unlink();return result


def comparisons(scene_id='gate_passage_001'):
    MEDIA.mkdir(parents=True,exist_ok=True)
    source=ROOT/'assets/observations/reference_v8/looks'
    current=ROOT/f'assets/observations/{scene_id}/looks/look1/T1'
    generated=json.loads((current/'lux_result.json').read_text())
    admission=json.loads((ROOT/f'experiments/{scene_id}/admission.json').read_text())
    rows=admission['candidates']
    accepted=[r for r in rows if r['admitted']]
    rejected=[r for r in rows if not r['admitted']]
    if not accepted:raise ValueError('Comparison needs an admitted real candidate')
    representatives=[accepted[0],(rejected or accepted)[-1]]
    canvas=Image.new('RGB',(1600,680),'#0b0e13');draw=ImageDraw.Draw(canvas)
    draw.text((35,25),'真实输入 → Lux3D 几何 → 冻结自检 → 路线预演',font=font(30),fill='#e9edf1')
    for index,row in enumerate(representatives):
        sample=row['id']
        task=next(t for t in generated['tasks'] if t['id']==sample)
        y=105+index*275
        for x,image in [(35,Image.open(ROOT/task['inputs'][0]).convert('RGB')),(400,mesh_image(ROOT/task['glb']))]:
            image.thumbnail((330,235));canvas.paste(image,(x,y))
        draw.text((780,y+30),sample+' / '+('通过并参与实际预演' if row['admitted'] else '拒绝并保留原始资产'),font=font(26),fill='#70dbb2')
        from beforestep.geometry.admission import ADM
        message=f'轮廓 IoU {row["contour_iou"]}；冻结门槛 {ADM["contour_iou_min"]}。'
        draw.text((780,y+85),message,font=font(21),fill='#a2adbb')
        draw.text((780,y+145),f'全部 {len(generated["tasks"])} 个真实任务与输入 SHA 保留。',font=font(18),fill='#83919f')
    canvas.save(MEDIA/'asset-comparison.jpg',quality=93)
    version=Image.new('RGB',(1600,760),'#0b0e13');draw=ImageDraw.Draw(version)
    draw.text((35,25),'核心迭代：观测约束 → 阴影与两图 → 窄道决策 → 完整终态',font=font(29),fill='#e9edf1')
    for index,(path,label) in enumerate([('assets/geometry/reference_v6/generated_parent.stl','V6 / 生成原型'),('assets/geometry/reference_v6/observation_fused.stl','V6 / 观测融合')]):
        image=mesh_image(ROOT/path);image.thumbnail((380,330));version.paste(image,(35+index*400,100));draw.text((45+index*400,410),label,font=font(22),fill='#70dbb2')
    image=Image.open(source/'look2/T2/gen/variants/A1.png').convert('RGB');image.thumbnail((330,330));version.paste(image,(855,105));draw.text((855,410),'V7 → V8 / 第二次观察',font=font(22),fill='#70dbb2')
    draw.text((1220,125),'有效主场景',font=font(24),fill='#70dbb2')
    for i,label in enumerate(['新输入 / 真实生成','三候选预演通过','一眼 / 实际到达','旧压力案例保留']):draw.text((1220,190+i*52),label,font=font(22),fill='#d2dae2')
    draw.text((45,535),'旧双盲区停下 → 有效关口通行，冻结门槛不变。',font=font(28),fill='#e9edf1')
    draw.text((45,605),'候选拒绝和真实失败也保留；真值替身只标为诊断。',font=font(23),fill='#a2adbb')
    version.save(MEDIA/'version-comparison.jpg',quality=93)


def configure_from_runs(paths):
    from beforestep import scene
    definitions=[]
    for path in paths.values():
        file=Path(path)/'scene.json'
        definitions.append(json.loads(file.read_text()) if file.exists() else json.loads((ROOT/'config/scenes/stress_v8.json').read_text()))
    first=scene.physical_identity(definitions[0])
    if any(scene.physical_identity(d)!=first for d in definitions[1:]):
        raise ValueError('All comparison runs must use the same physical scene')
    scene.configure(definitions[0]['id'])
    return definitions[0]


def build_data(paths):
    from beforestep import scene
    from scipy.spatial import ConvexHull
    definition=configure_from_runs(paths)
    data={'schema':'beforestep-demo/v2','scene_id':definition['id'],'title':definition.get('label',definition['id']),
          'goal':definition['goal'],'video':'media/demo.mp4','poster':'media/demo-poster.jpg',
          'runs':{},'candidates':[],'rocks':[]}
    for rock in scene.ROCKS.values():
        obj,_=scene.rock_asset_uniform(rock['rock'],rock['height'])
        vertices=np.array([[float(v) for v in line.split()[1:3]] for line in Path(obj).read_text().splitlines() if line.startswith('v ')])
        angle=np.radians(rock['yaw']);rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        points=vertices@rotation.T+[rock['x'],rock['y']]
        data['rocks'].append({**rock,'polygon':points[ConvexHull(points).vertices].tolist()})
    for policy,path in paths.items():
        path=Path(path);summary=json.loads((path/'summary.json').read_text())
        trace=np.load(path/'traj.npz');t,q=trace['t'],trace['qpos']
        indices=np.unique(np.r_[np.arange(0,len(t),10),len(t)-1])
        w,x,y,z=q[:,3:7].T;yaw=np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))
        summary['trajectory']=[[round(float(t[i]),2),round(float(q[i,0]),4),round(float(q[i,1]),4),round(float(yaw[i]),5)] for i in indices]
        events=[json.loads(line) for line in (path/'events.jsonl').read_text().splitlines() if line.strip()]
        panes=[pane for e in events if e['kind']=='rehearsal' and e.get('role','execution')=='execution' for pane in e['panes']]
        summary['rehearsals']=len(panes);summary['rehearsals_passed']=sum(p['completed'] and not p['collided'] for p in panes)
        plans=[e for e in events if e['kind']=='plan' and e.get('path')]
        if plans:summary['route_margin_m']=min(e['margin_vs_truth']['drive_margin_m'] for e in plans if e.get('margin_vs_truth'))
        comparisons=[e for e in events if e['kind']=='decision_comparison']
        if comparisons:
            decision=dict(comparisons[-1]);look=decision['look']
            reference=[pane for e in events if e['kind']=='rehearsal' and e.get('role')=='reference_without_generated_occupancy' and e['look']==look for pane in e['panes']]
            execution=[pane for e in events if e['kind']=='rehearsal' and e.get('role','execution')=='execution' and e['look']==look for pane in e['panes']]
            decision['reference_rehearsals']=reference;decision['execution_rehearsals']=execution
            snapshot=path/'decision'/f'look{look}_state.npy'
            if snapshot.exists():
                from beforestep.navigation import map as nav
                state=np.load(snapshot)
                decision['observed_cells']={'shape':list(state.shape),'values':state.ravel().tolist(),'resolution':nav.RES,'origin':[nav.X0,nav.Y0]}
            data['decision']=decision
        data['runs'][policy]=summary
        evidence=ROOT/'evidence/delivery'/policy;evidence.mkdir(parents=True,exist_ok=True)
        for name in ('summary.json','events.jsonl','traj.npz','run_identity.json','scene.json','map_final.png'):
            if (path/name).exists():shutil.copy2(path/name,evidence/name)
    directory=ROOT/f'assets/observations/{definition["id"]}/looks/look1/T1'
    result=json.loads((directory/'lux_result.json').read_text())
    admission=json.loads((ROOT/f'experiments/{definition["id"]}/admission.json').read_text())
    rows={c['id']:c for c in admission['candidates']}
    for task in result['tasks']:
        if task['status']!='ok':continue
        sample=task['id'];filename=f'{definition["id"]}_{sample}.glb'
        shutil.copy2(ROOT/task['glb'],MEDIA/filename)
        image=Image.open(ROOT/task['inputs'][0]).convert('RGB');image.thumbnail((1200,1200))
        image_name=filename.replace('.glb','.jpg');image.save(MEDIA/image_name,quality=92)
        row=rows[sample]
        data['candidates'].append({'id':filename,'label':f'{sample} / '+('自检采纳' if row['admitted'] else '自检拒绝'),
            'glb':f'media/{filename}','input':f'media/{image_name}','task_id':task['task_id'],
            'verdict':f'轮廓 IoU {row["contour_iou"]} · '+('通过冻结门槛，参与实际预演' if row['admitted'] else '低于冻结门槛，保留作为拒绝对比')})
    data['generation']={'tasks':len(result['tasks']),'succeeded':len(rows),'failed':sum(t['status']=='failed' for t in result['tasks']),
                        'admitted':len(admission['admitted_ids'])}
    footprint=Path(paths['imagination'])/'looks/look1/T1/decide/footprint_union.npy'
    if footprint.exists():
        from beforestep.navigation import map as nav
        mask=np.load(footprint);data['imagined_footprint']=[[round(float(nav.GX[i,j]),3),round(float(nav.GY[i,j]),3)] for i,j in zip(*np.nonzero(mask))]
    (ROOT/'site/data').mkdir(parents=True,exist_ok=True)
    (ROOT/'site/data/demo.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    scenes=[{'id':definition['id'],'label':data['title'],'data':'data/demo.json'}]
    for sid,label in [('gate_passage_001','关口通行 · 前一版本'),('stress_v8','双盲区压力测试 · 历史反例')]:
        if sid!=definition['id'] and (ROOT/f'site/data/history/{sid}.json').exists():
            scenes.append({'id':sid,'label':label,'data':f'data/history/{sid}.json'})
    (ROOT/'site/data/scenes.json').write_text(json.dumps({'default':definition['id'],'scenes':scenes},ensure_ascii=False))
    (ROOT/'evidence/delivery/results.json').write_text(json.dumps({k:{x:v for x,v in s.items() if x!='trajectory'} for k,s in data['runs'].items()},ensure_ascii=False,indent=2)+'\n')
    return data


def build_report():
    import markdown
    text=(ROOT/'docs/report.md').read_text()
    html=markdown.markdown(text,extensions=['tables','fenced_code'])
    html=html.replace('../site/media/','media/').replace('href="milestones.md"','href="docs/milestones.md"').replace('href="credits.md"','href="docs/credits.md"')
    html=html.replace('href="../README.md"','href="https://github.com/codezzzsleep/next-zenith-beforestep"')
    for document in ('project.md', 'effective-scene.md'):
        html=html.replace(f'href="{document}"',f'href="docs/{document}"')
    style='@page{size:A4;margin:18mm}body{max-width:860px;margin:40px auto;color:#1d2730;font:15px/1.8 sans-serif}h1{font-size:30px}h2{margin-top:35px;break-after:avoid}img{width:100%;height:auto;break-inside:avoid}a{color:#27644e}table{border-collapse:collapse;width:100%;break-inside:avoid}td,th{border:1px solid #bbb;padding:8px}code{font-size:12px}pre{white-space:pre-wrap}'
    (ROOT/'site/report.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>先见一步 · 项目报告</title><style>'+style+'</style></head><body>'+html+'</body></html>')


def main(argv=None):
    parser=argparse.ArgumentParser(prog='beforestep build')
    parser.add_argument('--conservative',default='outputs/effective/conservative')
    parser.add_argument('--optimistic',default='outputs/effective/optimistic')
    parser.add_argument('--imagination',default='outputs/effective/imagination')
    parser.add_argument('--comparisons-only',action='store_true');parser.add_argument('--video',action='store_true')
    parser.add_argument('--report',action='store_true')
    parser.add_argument('--scene',default='gate_passage_001',help='Asset comparison scene; run identities select the Demo scene')
    args=parser.parse_args(argv)
    if args.comparisons_only:
        comparisons(args.scene);return
    paths={p:ROOT/getattr(args,p) for p in ('conservative','optimistic','imagination')}
    definition=configure_from_runs(paths)
    comparisons(definition['id'])
    build_data(paths)
    if args.report:build_report()
    if args.video:
        from .video import render, outcome_cards
        render(paths)
        outcome_cards(paths)
    print('Built showcase data, comparisons and evidence.')
