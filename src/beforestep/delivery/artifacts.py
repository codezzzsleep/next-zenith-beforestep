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


def comparisons():
    MEDIA.mkdir(parents=True,exist_ok=True)
    source=ROOT/'assets/observations/reference_v8/looks'
    canvas=Image.new('RGB',(1600,680),'#0b0e13');draw=ImageDraw.Draw(canvas)
    draw.text((35,25),'Lux3D 资产链：真实输入 → 原始候选 → 冻结自检',font=font(30),fill='#e9edf1')
    items=[('look1/T1/gen/variants/B2.png','assets/candidates/reference_v8/look1/T1/B2.glb','第一块石头 · B2 · 采纳'),
           ('look1/T2/gen/variants/A2.png','assets/candidates/reference_v8/look1/T2/A2.glb','第二块石头 · A2 · 拒绝')]
    for row,(input_path,glb,label) in enumerate(items):
        y=105+row*275
        for x,image in [(35,Image.open(source/input_path).convert('RGB')),(400,mesh_image(ROOT/glb))]:
            image.thumbnail((330,235));canvas.paste(image,(x,y))
        draw.text((780,y+30),label,font=font(26),fill='#70dbb2')
        message='满足冻结门槛，进入候选几何。' if row==0 else '轮廓 IoU 0.6972 < 0.7068，不能降低门槛。'
        draw.text((780,y+85),message,font=font(21),fill='#a2adbb')
        draw.text((780,y+145),'保留真实 GLB、输入 SHA、任务身份和准入结果。',font=font(18),fill='#83919f')
    canvas.save(MEDIA/'asset-comparison.jpg',quality=93)
    version=Image.new('RGB',(1600,760),'#0b0e13');draw=ImageDraw.Draw(version)
    draw.text((35,25),'核心迭代：观测约束 → 阴影与两图 → 窄道决策 → 完整终态',font=font(29),fill='#e9edf1')
    for index,(path,label) in enumerate([('assets/geometry/reference_v6/generated_parent.stl','V6 / 生成原型'),('assets/geometry/reference_v6/observation_fused.stl','V6 / 观测融合')]):
        image=mesh_image(ROOT/path);image.thumbnail((380,330));version.paste(image,(35+index*400,100));draw.text((45+index*400,410),label,font=font(22),fill='#70dbb2')
    image=Image.open(source/'look2/T2/gen/variants/A1.png').convert('RGB');image.thumbnail((330,330));version.paste(image,(855,105));draw.text((855,410),'V7 → V8 / 第二次观察',font=font(22),fill='#70dbb2')
    draw.text((1220,125),'BEFORESTEP',font=font(24),fill='#70dbb2')
    for i,label in enumerate(['全程接触监测','预演必须完成','最多两次观察','任务安全续跑']):draw.text((1220,190+i*52),label,font=font(22),fill='#d2dae2')
    draw.text((45,535),'保留关键版本源码与冻结结果，解释改动为什么发生。',font=font(28),fill='#e9edf1')
    draw.text((45,605),'候选拒绝和真实失败也保留；真值替身只标为诊断。',font=font(23),fill='#a2adbb')
    version.save(MEDIA/'version-comparison.jpg',quality=93)


def build_data(paths):
    data={'schema':'beforestep-demo/v1','runs':{},'candidates':[],'rocks':[]}
    from beforestep import scene
    from scipy.spatial import ConvexHull
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
        data['runs'][policy]=summary
        evidence=ROOT/'evidence/delivery'/policy;evidence.mkdir(parents=True,exist_ok=True)
        for name in ('summary.json','events.jsonl','traj.npz','run_identity.json','map_final.png'):
            if (path/name).exists():shutil.copy2(path/name,evidence/name)
    for label,look,target,sample in [('采纳 / 第一块 B2','look1','T1','B2'),('拒绝 / 第二块 A2','look1','T2','A2'),('两图 / 第二块 M1','look2','T2','M1')]:
        directory=ROOT/f'assets/observations/reference_v8/looks/{look}/{target}'
        result=json.loads((directory/'lux_result.json').read_text());task=next(t for t in result['tasks'] if t['id']==sample)
        glb=ROOT/task['glb'];filename=f'{look}_{target}_{sample}.glb';shutil.copy2(glb,MEDIA/filename)
        input_path=directory/f'gen/variants/{sample if sample[0]!="M" else "A1"}.png';input_name=filename.replace('.glb','.jpg')
        image=Image.open(input_path).convert('RGB');image.thumbnail((1200,1200));image.save(MEDIA/input_name,quality=92)
        data['candidates'].append({'id':filename,'label':label,'glb':f'media/{filename}','input':f'media/{input_name}','task_id':task['task_id'],
                                   'verdict':'通过冻结自检' if target=='T1' else '未通过冻结自检'})
    retry=ROOT/'experiments/polar_retry_001/admission.json'
    if retry.exists():
        admission=json.loads(retry.read_text())
        best=max(admission['candidates'],key=lambda c:c.get('contour_iou') or 0)
        generated=json.loads((ROOT/'experiments/polar_retry_001/lux_result.json').read_text())
        task=next(t for t in generated['tasks'] if t['id']==best['id'])
        filename=f'retry_{best["id"]}.glb';shutil.copy2(ROOT/task['glb'],MEDIA/filename)
        image=Image.open(ROOT/task['inputs'][1]).convert('RGB');image.thumbnail((1200,1200));image.save(MEDIA/'retry-input.jpg',quality=92)
        data['candidates'].append({'id':filename,'label':f'新增两图 / {best["id"]}','glb':f'media/{filename}','input':'media/retry-input.jpg','task_id':task['task_id'],
                                  'verdict':f'本批轮廓 IoU 最高 {best["contour_iou"]}，仍被拒绝；完整12份结果已保留'})
    shutil.copy2(MEDIA/data['candidates'][0]['glb'].split('/')[-1],MEDIA/'candidate.glb')
    shutil.copy2(MEDIA/data['candidates'][0]['input'].split('/')[-1],MEDIA/'input.jpg')
    (ROOT/'site/data').mkdir(parents=True,exist_ok=True)
    (ROOT/'site/data/demo.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    (ROOT/'evidence/delivery/results.json').write_text(json.dumps({k:{x:v for x,v in s.items() if x!='trajectory'} for k,s in data['runs'].items()},ensure_ascii=False,indent=2)+'\n')
    return data


def build_report():
    import markdown
    text=(ROOT/'docs/report.md').read_text()
    html=markdown.markdown(text,extensions=['tables','fenced_code'])
    html=html.replace('../site/media/','media/').replace('href="milestones.md"','href="docs/milestones.md"').replace('href="credits.md"','href="docs/credits.md"')
    html=html.replace('href="../README.md"','href="https://github.com/codezzzsleep/next-zenith-beforestep"')
    style='@page{size:A4;margin:18mm}body{max-width:860px;margin:40px auto;color:#1d2730;font:15px/1.8 sans-serif}h1{font-size:30px}h2{margin-top:35px;break-after:avoid}img{width:100%;height:auto;break-inside:avoid}a{color:#27644e}table{border-collapse:collapse;width:100%;break-inside:avoid}td,th{border:1px solid #bbb;padding:8px}code{font-size:12px}pre{white-space:pre-wrap}'
    (ROOT/'site/report.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>先见一步 · 项目报告</title><style>'+style+'</style></head><body>'+html+'</body></html>')


def main(argv=None):
    parser=argparse.ArgumentParser(prog='beforestep build')
    parser.add_argument('--conservative',default='outputs/validation/conservative')
    parser.add_argument('--optimistic',default='outputs/final-validation/optimistic')
    parser.add_argument('--imagination',default='outputs/delivery/imagination')
    parser.add_argument('--comparisons-only',action='store_true');parser.add_argument('--video',action='store_true')
    parser.add_argument('--report',action='store_true')
    args=parser.parse_args(argv);comparisons()
    if args.comparisons_only:return
    paths={p:ROOT/getattr(args,p) for p in ('conservative','optimistic','imagination')}
    build_data(paths)
    if args.report:build_report()
    if args.video:
        from .video import render, outcome_cards
        render(paths)
        outcome_cards(paths)
    print('Built showcase data, comparisons and evidence.')
