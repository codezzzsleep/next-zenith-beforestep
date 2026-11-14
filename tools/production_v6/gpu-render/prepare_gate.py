"""Select actual terminal A/D states for new gate and optional backup shots."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import ROOT,OUT,save,sha,status
import numpy as np

DIRECTORY=OUT/'gpu-render'
NAME='suite_r2_v4_F3_002_gate'

def prepare():
    summary=ROOT/'evidence/crossing/route'/f'summary-{NAME}.json'
    final=json.loads(summary.read_text());assert final['all_terminal']
    inputs=set();plans=json.loads((DIRECTORY/'shot-plan.json').read_text());new=[];unavailable=[]
    def source(path):
        path=Path(path);assert path.is_file(),path
        z=np.load(path);assert z['qpos'].shape[1]==23
        inputs.add(path)
        return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}
    def poses(rows):
        times=[];qpos=[]
        for row in rows:
            z=np.load(ROOT/row['path']);t=z['t'];q=z['qpos'];keep=np.ones(len(t),dtype=bool) if not times else t>times[-1][-1]+1e-8
            if keep.any():times.append(t[keep]);qpos.append(q[keep])
        t=np.concatenate(times);q=np.concatenate(qpos);assert np.all(np.diff(t)>0);return t,q
    def rows(route,vehicle):
        root=ROOT/'outputs/crossing/route'/route/vehicle
        result=json.loads((root/'result.json').read_text())
        items=[source(root/'segment1/full-record/trajectory.npz')]
        if vehicle=='D':parts=[root/'segment2/trajectory.npz']
        else:parts=[root/'segment2/fixed/trajectory.npz',root/'segment2/high/trajectory.npz']
        for p in parts:
            if p.exists():items.append(source(p))
        return items,result
    def add(name,rows,route,duration,camera,start=None,end=None,**extra):
        t,q=poses(rows)
        item={'id':name,'sources':rows,'scene':route,'route':route,'duration_s':duration,'speed':None,'sim_start':float(t[0] if start is None else max(start,t[0])),'sim_end':float(t[-1] if end is None else min(end,t[-1])),'camera':camera,**extra}
        if camera=='overview':item['camera_spec']={'kind':'gate_overview','azimuth':-40,'elevation':-55,'distance':3.6,'x_offset':.35,'y_offset':0,'z_scale':.5}
        new.append(item)
    def definition(route):
        path=ROOT/'evidence/crossing/route'/f'scene-{route}.json';d=json.loads(path.read_text());inputs.add(path);inputs.add(ROOT/'config/scenes'/f'{d["base_scene"]}.json');return d
    def approach(name,src,route,seconds):
        d=definition(route);t,q=poses(src[:1]);x=float(next(iter(d['rocks'].values()))['x']);indices=np.flatnonzero((q[:,0]>=x-1.3)&(q[:,0]<=x+.5))
        if len(indices):a,b=t[indices[0]],t[indices[-1]]
        else:a,b=max(t[0],t[-1]-12),t[-1]
        if b-a<.5:a=max(t[0],b-8)
        add(name,src[:1],route,seconds,'low',a,b,selection='Actual saved states near the first high rock; range bounded by observed progress')
    def crossing(name,src,route,seconds):
        second=[r for r in src if '/segment2/trajectory.npz' in r['path']]
        if not second:
            unavailable.append({'id':name,'status':'not_applicable','reason':'Formal D did not execute a leg crossing; no saved segment2 trajectory exists'});return
        d=definition(route);t,q=poses(second);near=float(d['near_x_m']);indices=np.flatnonzero((q[:,0]>=near-.45)&(q[:,0]<=near+.9))
        a,b=(t[indices[0]],t[indices[-1]]) if len(indices) else (t[0],t[-1])
        add(name,second,route,seconds,'low',a,b,selection='Recorded leg segment while body is near threshold; no generated actions')
    drows,dresult=rows(NAME,'D');arows,aresult=rows(NAME,'A');definition(NAME)
    add('s09-gate-overview',drows,NAME,18,'overview',formal_total_result=dresult['total_result'])
    approach('s09-gate-approach',drows,NAME,8)
    crossing('s09-gate-crossing',drows,NAME,10)
    at,aq=poses(arows);add('s09-gate-A',arows,NAME,8,'low',max(at[0],at[-1]-20),at[-1],formal_total_result=aresult['total_result'],selection='Last20 saved simulation seconds; position/outcome may be before high rock if A never reached threshold')
    # In story version B, supply original backup D closeups and A comparison.
    if dresult['total_result']!='arrived':
        for route in ['suite_r2_v4_F1_003_gate','suite_r2_v4_F2_001_gate']:
            suffix=route.removeprefix('suite_r2_v4_').removesuffix('_gate');dr,_=rows(route,'D');ar,result=rows(route,'A');definition(route)
            approach('s09-backup-'+suffix+'-approach-v2',dr,route,10)
            crossing('s09-backup-'+suffix+'-crossing-v2',dr,route,10)
            t,q=poses(ar);add('s09-backup-'+suffix+'-A-v2',ar,route,8,'low',max(t[0],t[-1]-20),t[-1],formal_total_result=result['total_result'])
    existing={x['id']:x for x in plans['shots']}
    for row in new:existing[row['id']]=row
    plans['shots']=list(existing.values());plans['pending']=[];plans['not_applicable']=unavailable;plans['gate_summary']={'path':str(summary.relative_to(ROOT)),'sha256':sha(summary),'D_result':dresult['total_result'],'A_result':aresult['total_result']};save(DIRECTORY/'shot-plan.json',plans)
    files=[{'path':str(p.relative_to(ROOT.parent)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(inputs)]
    files.append({'path':'final-v6/gpu-render/shot-plan.json','sha256':sha(DIRECTORY/'shot-plan.json'),'bytes':(DIRECTORY/'shot-plan.json').stat().st_size})
    save(DIRECTORY/'gate-input-manifest.json',{'files':files,'shots':new,'not_applicable':unavailable,'source_summary':plans['gate_summary'],'physics_runs':0,'generation_tasks':0})
    (DIRECTORY/'gate-rsync-files.txt').write_text('\n'.join(row['path'] for row in files)+'\n')
    status('GPU F3终态镜头选材',DIRECTORY/'gate-input-manifest.json',f'D={dresult["total_result"]} / A={aresult["total_result"]}；{len(new)}镜头；未发生项目{len(unavailable)}项明确NA；只读保存状态')
    return [x['id'] for x in new]

if __name__=='__main__':print(json.dumps(prepare(),ensure_ascii=False))
