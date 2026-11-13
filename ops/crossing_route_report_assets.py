"""Derive the report's API ledger and input/model/check comparisons."""
import argparse,collections,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image
from experimental.crossing.runtime import write,sha

OUT=ROOT/'evidence/crossing/route/report-assets'
font_manager.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
plt.rcParams['font.family']='WenQuanYi Zen Hei';plt.rcParams['axes.unicode_minus']=False

def usage():
    ledger=ROOT/'outputs/generation/tasks';rows={}
    for path in ledger.glob('*.json'):
        data=json.loads(path.read_text())
        if not data.get('task_id'):continue
        tid=data['task_id']
        safe={key:data.get(key) for key in ['task_id','status','api_field','n_images','id','identity','input_sha256','glb_sha256']}
        safe.update(client_record_sha256=sha(path))
        if tid in rows:assert rows[tid]['identity']==safe['identity']
        rows[tid]=safe
    counts=collections.Counter(row['status'] for row in rows.values());budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    document={'schema':'beforestep-public-lux-usage/v1','generated_task_creates':len(rows),'status_counts':dict(counts),
        'scope':'All accepted task IDs in the authoritative client ledger, including historical and crossing runs. HTTP uploads/polls are not counted as new generation tasks.',
        'interfaces':['POST /lux3d/v1/generate/img-to-3d/task/create','GET /lux3d/v1/generate/task/get','Signed upload preparation, block upload, and upload completion'],
        'input_modes':dict(collections.Counter(r['api_field'] for r in rows.values())),
        'crossing_budget_created':budget['created'],'crossing_limit':400,'tasks':[rows[k] for k in sorted(rows)]}
    write(ROOT/'evidence/crossing/route/lux-usage.json',document)
    return document

def mesh_panel(ax,path):
    obj=trimesh.load(path,process=False)
    mesh=obj.to_geometry() if isinstance(obj,trimesh.Scene) else obj
    vertices=np.asarray(mesh.vertices);vertices=vertices[:,[0,2,1]]*np.array([1,-1,1])
    ax.plot_trisurf(vertices[:,0],vertices[:,1],vertices[:,2],triangles=mesh.faces,color='#b6bfc7',linewidth=0,antialiased=False,shade=True)
    midpoint=(vertices.min(0)+vertices.max(0))/2;radius=max(np.ptp(vertices,axis=0))/2*1.08
    ax.set(xlim=(midpoint[0]-radius,midpoint[0]+radius),ylim=(midpoint[1]-radius,midpoint[1]+radius),zlim=(midpoint[2]-radius,midpoint[2]+radius))
    ax.set_box_aspect([1,1,1]);ax.view_init(elev=24,azim=-55);ax.set_axis_off()

def figure(examples,path,title):
    fig=plt.figure(figsize=(12,3.4*len(examples)),layout='constrained',facecolor='#111416')
    for i,row in enumerate(examples):
        ax=fig.add_subplot(len(examples),3,i*3+1);ax.imshow(Image.open(ROOT/row['input']));ax.set_axis_off();ax.set_title(row['label']+'\n实际上传图像',color='white',fontsize=11)
        ax=fig.add_subplot(len(examples),3,i*3+2,projection='3d',facecolor='#111416');mesh_panel(ax,ROOT/row['glb']);ax.set_title('原生成几何（省略纹理）',color='white',fontsize=11)
        ax=fig.add_subplot(len(examples),3,i*3+3,facecolor='#111416');ax.set_axis_off()
        metrics=row['metrics'];detail='\n'.join(f'{k}: {v:.4f}' for k,v in metrics.items() if isinstance(v,(int,float)))
        ax.text(0,.95,f'真实任务 {row["task_id"]}\n代表例：'+('准入' if row['admitted'] else '拒绝')+'\n\n'+detail+'\n\n'+row.get('round_totals',''),color='white',va='top',fontsize=10)
    fig.suptitle(title+'\n每行是一份明确标注的代表例；全部任务与拒绝结果保留在账本',color='white',fontsize=14)
    fig.savefig(path,dpi=140,facecolor=fig.get_facecolor());plt.close(fig)

def iterations():
    OUT.mkdir(parents=True,exist_ok=True)
    low=json.loads((ROOT/'evidence/crossing/route/low-stone.json').read_text());budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    records={r['task_id']:r for r in budget['tasks'] if r.get('task_id')}
    decisions={c['task_id']:c for p in (ROOT/'evidence/crossing').glob('development-lux-*.json') for c in json.loads(p.read_text()).get('candidates',[]) if c.get('task_id')}
    examples=[]
    for round in low['six_input_rounds']:
        candidates=[tid for tid in round['task_ids'] if tid in decisions]
        tid=next((tid for tid in candidates if decisions[tid]['admitted']),candidates[0]);record=records[tid];candidate=decisions[tid]
        source=ROOT/record['inputs'][0];destination=OUT/f'low-{round["revision"]}-input{source.suffix}';shutil.copy2(source,destination)
        examples.append({'label':round['revision'],'task_id':tid,'input':str(destination.relative_to(ROOT)),'input_original':record['inputs'][0],'input_sha256':sha(source),
            'glb':record['glb'],'glb_sha256':record['glb_sha256'],'metrics':candidate['metrics'],'admitted':candidate['admitted'],
            'round_totals':f'本轮全部：生成 {round["created"]}，准入 {round["admitted"]}'})
    figure(examples,OUT/'low-six-inputs.png','门槛石：六轮输入 → 真实生成结果 → 冻结自检')
    for i in range(3):figure(examples[i*2:i*2+2],OUT/f'low-inputs-{i+1}.png',f'门槛石输入迭代 · 第 {i*2+1} / {i*2+2} 轮')
    high=[];base=ROOT/'outputs/crossing/route/stress_v8_gate/A/segment1/looks'
    for look in ['look1','look2']:
        target=base/look/'T2';request=json.loads((target/'lux_request.json').read_text());results=json.loads((target/'lux_result.json').read_text())['tasks']
        decision=json.loads((target/'decide/target_decision.json').read_text());by={x['id']:x for x in results}
        candidates=[c for c in decision['candidates'] if c['id'] in by and by[c['id']]['status']=='ok']
        if not candidates:continue
        candidate=next((c for c in candidates if c['admitted']),candidates[0]);record=by[candidate['id']];item=next(x for x in request['items'] if x['id']==candidate['id'])
        source=(item.get('paths') or [item['path']])[0];p=ROOT/source;destination=OUT/f'high-{look}-input{p.suffix}';shutil.copy2(p,destination)
        metrics={k:candidate.get(k) for k in ['contour_iou','scale_ratio','hidden_frac','shell_contact','free_intrusion_frac']}
        state=json.loads((target/'state.json').read_text())
        high.append({'label':'高石 B · '+look,'task_id':record['task_id'],'input':str(destination.relative_to(ROOT)),'input_original':source,'input_sha256':sha(p),
            'glb':record['glb'],'glb_sha256':record['glb_sha256'],'metrics':metrics,'admitted':candidate['admitted'],
            'round_totals':f'目标原生像素高 {state["crop_native_px"]}\n当前该眼准入 {sum(c["admitted"] for c in decision["candidates"])} / {len(decision["candidates"])}\n同一 B 石；机器人走到新观察点再拍'})
    if high:figure(high,OUT/'high-two-looks.png','高石头：第一眼被挡住 → 第二眼实际移动后补看')
    record={'schema':'beforestep-report-key-asset-iterations/v1','low_stone':examples,'high_stone':high,
        'model_display':'Original GLB triangles, uniform camera framing, coordinate display conversion [x,-z,y], textures omitted. No new generation or physics run.',
        'source_figures':['evidence/crossing/route/report-assets/low-six-inputs.png','evidence/crossing/route/report-assets/high-two-looks.png']}
    write(OUT/'manifest.json',record);return record

def update_report(data,assets):
    path=ROOT/'docs/report.md';text=path.read_text()
    start='<!-- ADDENDUM3-LUX-USAGE-START -->';end='<!-- ADDENDUM3-LUX-USAGE-END -->'
    block=f'''{start}
Lux3D 使用：本项目调用图像转三维任务创建接口（单图 `img` / 多图 `imgs`）、任务查询接口以及官方上传流程。客户端账本有 **{data['generated_task_creates']} 个真实已创建任务**，其中 {data['status_counts'].get('ok',0)} 份返回 GLB、{data['status_counts'].get('failed',0)} 份服务端失败；逐项任务号与输入 SHA 见 [公开调用账本](../evidence/crossing/route/lux-usage.json)。这是生成任务数，上传与轮询 HTTP 请求不重复计数。本轮跨越独立预算 {data['crossing_budget_created']}/{data['crossing_limit']}。

生成结果是高石头看不见部分的三维假设：先与可见观测核对，准入后进入各个完整物理预演世界，全部安全才实走。门槛石的跨越用实拍几何，Lux3D 在门槛石上的开发没有被记为跨越成功。
{end}
'''
    if start in text:text=re.sub(re.escape(start)+'.*?'+re.escape(end),block.strip(),text,flags=re.S)
    else:
        head,tail=text.split('\n',1);text=head+'\n\n'+block+'\n'+tail
    start='<!-- ADDENDUM3-ASSET-ITERATIONS-START -->';end='<!-- ADDENDUM3-ASSET-ITERATIONS-END -->'
    section=f'''{start}
## 关键资产迭代：输入、生成结果与自检

门槛石六轮输入全部计数，下面每行是一份标明任务号的代表例。没有通过的轮次照实显示拒绝；第六轮展示一份准入例，全部 {sum(r['created'] for r in json.loads((ROOT/'evidence/crossing/route/low-stone.json').read_text())['six_input_rounds'])} 个任务仍在原账本。图中三维使用原 GLB 三角面，只省略纹理，不改变形状。

![门槛石第一、二轮输入与自检](../evidence/crossing/route/report-assets/low-inputs-1.png)

![门槛石第三、四轮输入与自检](../evidence/crossing/route/report-assets/low-inputs-2.png)

![门槛石第五、六轮输入与自检](../evidence/crossing/route/report-assets/low-inputs-3.png)

高石 B 保持同一块原石头和同一场景。第二眼来自机器人实际移动后的新观测，输入图、生成任务与自检结论分别记录；不会把第一眼的任务号当成第二眼的新调用。

![高石 B 的两次真实输入、模型和自检结论](../evidence/crossing/route/report-assets/high-two-looks.png)

[每张输入、原模型 SHA 与准入指标](../evidence/crossing/route/report-assets/manifest.json) · [六轮全部结果](../evidence/crossing/route/low-stone.json) · [核心历史版本与资产迭代](../evidence/award/asset-iterations/manifest.json)。
{end}
'''
    if start in text:text=re.sub(re.escape(start)+'.*?'+re.escape(end),section.strip(),text,flags=re.S)
    else:text=text.replace('\n## 轮腿与想象\n','\n'+section+'\n## 轮腿与想象\n')
    path.write_text(text)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--usage-only',action='store_true');a=parser.parse_args()
    data=usage();assets=json.loads((OUT/'manifest.json').read_text()) if a.usage_only else iterations();update_report(data,assets)
    print(json.dumps({'real_created_tasks':data['generated_task_creates'],'low_input_rounds':len(assets['low_stone']),'high_looks':len(assets['high_stone'])}),flush=True)
