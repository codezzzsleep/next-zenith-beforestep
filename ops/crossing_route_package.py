"""Immutable route archives with every member checksum and no credentials."""
import argparse,hashlib,json,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import ROUTE,EVIDENCE
from ops.crossing_route_summary import build

def package(tag,files):
    path=EVIDENCE/(tag+'.tar.gz');manifest=EVIDENCE/(tag+'-manifest.json')
    if manifest.exists():return json.loads(manifest.read_text())
    if path.exists():raise RuntimeError('Unfinished archive retained; recover under a new artifact identity')
    files=sorted(set(files));members=[]
    for p in files:members.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
    with tarfile.open(path,'w:gz',compresslevel=1) as archive:
        for p in files:archive.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    expected={r['path']:r for r in members};count=0
    with tarfile.open(path,'r:gz') as archive:
        for member in archive:
            f=archive.extractfile(member);h=hashlib.sha256()
            for block in iter(lambda:f.read(1<<20),b''):h.update(block)
            assert h.hexdigest()==expected[member.name]['sha256'];count+=1
    assert count==len(members)
    result={'schema':'beforestep-route-archive/v1','path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,
        'sha256':sha(path),'members':members,'member_sha_check':'passed',
        'download':'https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/'+str(path.relative_to(ROOT))}
    write(manifest,result);return result

def handoff_partial():
    summary=build();output=ROUTE/'handoff';output.mkdir(parents=True,exist_ok=True)
    write(output/'summary.json',summary)
    for v in ['A','B','C','D']:
        source=EVIDENCE/f'trajectory-{v}.json'
        if source.exists():(output/f'{v}-trajectory.json').write_bytes(source.read_bytes())
    readme='# 同路两种石头 · 首页与视频素材\n\n'
    readme+='当前结果来自 stress_v8_gate。所有 JSON 轨迹来自真实保存状态，25 Hz，位置以米、关节以弧度；四元数顺序 w,x,y,z，16 关节顺序按每条腿的 hip/thigh/calf/wheel（FL、FR、RL、RR）。\n\n'
    readme+='轨迹与原始 OBJ 使用 MuJoCo Z 向上；展示 GLB 使用标准 Y 向上，坐标转换为 [x,z,-y]，完整矩阵在 models.json。这是显示转换，物理和生成原件没有移动。\n\n'
    readme+='scene.glb：真实地形、高石、石门、门槛的显示模型，合计低于 2 MB；models.json 记录原始扫描 SHA、地形显示采样与碰撞凸包。D-imagination.glb 若存在，包含 D 用到的准入假设，合计低于 2 MB，原始模型另行保留。\n\n'
    readme+='A/B/C/D-trajectory.json：对应四个正式一次运行；未终态的轨迹文件不会伪造。summary.json 含结果、两段交接、仿真用时与原因。\n\n'
    readme+='frames/：1280×720、30 fps JPG，仅渲染保存状态，不推进物理；成片另由 ffmpeg 按分镜合成。每段 index.json 逐帧记录相机、原物理时间、SHA；side_follow 与 overhead 两机位。B-actual 是轮触高石后停下的真实末段，不是机身碰撞。其他片段以最终索引列出的实际来源为准。\n'
    (output/'README.md').write_text(readme)
    return output

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['B-handoff','first-raw','final-handoff'],required=True);a=ap.parse_args()
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    if a.stage=='B-handoff':
        output=handoff_partial();files=[p for p in output.rglob('*') if p.is_file()]
        archive=package('handoff-B-first',files)
        write(EVIDENCE/'handoff-index.json',{'schema':'beforestep-route-handoff-index/v1','complete':False,'archives':[archive],
            'pending':['A and D terminal trajectories','D admitted models','A/D actual and D rehearsal/threshold closeup frames']})
    elif a.stage=='first-raw':
        summary=build();assert summary['all_terminal'],'Do not archive an active formal scene as terminal'
        archives=[]
        for v in ['A','B','C','D']:
            files=[p for p in (ROUTE/'stress_v8_gate'/v).rglob('*') if p.is_file()]
            archives.append(package('first-scene-'+v,files))
        files=[p for part in ['scene-attempts','prechecks','connection-precheck','input-probe'] for p in (ROUTE/'stress_v8_gate'/part).rglob('*') if p.is_file()]
        archives.append(package('first-scene-definition-and-gates',files))
        write(EVIDENCE/'first-scene-archive-index.json',{'schema':'beforestep-route-complete-records/v1','scene':'stress_v8_gate','archives':archives,
            'all_raw_fields_retained':['RGB/depth','uploaded images','task IDs and admission','qpos/qvel and 16 joints','500Hz contacts','every rehearsal','complete physical handoff','program/cloud wait attempts']})
    else:
        output=handoff_partial();archives=[]
        core=[p for p in output.rglob('*') if p.is_file() and 'frames' not in p.relative_to(output).parts]
        archives.append(package('handoff-final-core',core))
        for folder in sorted((output/'frames').iterdir()):
            if not folder.is_dir():continue
            chunks=[];part=[];size=0
            for file in sorted(p for p in folder.rglob('*') if p.is_file() and p.suffix!='.tmp'):
                if part and size+file.stat().st_size>900_000_000:chunks.append(part);part=[];size=0
                part.append(file);size+=file.stat().st_size
            if part:chunks.append(part)
            for number,files in enumerate(chunks,1):archives.append(package(f'handoff-final-{folder.name}-{number:02d}',files))
        pending=[];not_applicable=[]
        for v in ['A','B','C','D']:
            if not (output/f'{v}-trajectory.json').exists():pending.append(v+' trajectory absent; no terminal physical recording')
        for label in ['wheel-stuck','leg-cross','sill-close','connect','A-actual','B-actual','D-actual','D-rehearsal','D-closeup']:
            p=output/'frames'/label/'index.json'
            data=json.loads(p.read_text()) if p.exists() else {}
            if data.get('status')=='not_applicable':not_applicable.append({'clip':label,'reason':data['reason'],'source':data.get('formal_result_source')})
            elif data.get('status')!='complete':pending.append(label+' frames absent; see actual run outcome')
        write(EVIDENCE/'handoff-index.json',{'schema':'beforestep-route-handoff-index/v1','complete':not pending,'archives':archives,'pending':pending,
            'not_applicable':not_applicable,'archive_partition':'Core plus frame clips, with each raw partition capped at 900 MB; every member verified by SHA'})
    print(json.dumps({'stage':a.stage,'archive':archive['path'] if a.stage=='B-handoff' else [r['path'] for r in archives]},ensure_ascii=False),flush=True)
