"""Generate the public route table and replay data from terminal recordings."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import numpy as np
import trimesh
from scipy.spatial import ConvexHull
from beforestep import scene as S
from experimental.crossing.runtime import write,sha
from experimental.crossing.route.world import EVIDENCE,ROUTE

def labels(value):
    return {'arrived':'到达','clean_pass':'干净跨过','wheel_contact_pass':'带轮触石通过','collision':'出事',
        'body_collision':'出事','unstable':'出事','stopped':'停下','stuck':'卡住','not_run':'未运行'}.get(value,value)

def build(name='stress_v8_gate'):
    scene=json.loads((EVIDENCE/f'scene-{name}.json').read_text())
    results=[];cars={}
    for vehicle in ['A','B','C','D']:
        base=ROUTE/name/vehicle;p=base/'result.json'
        if not p.exists():continue
        r=json.loads(p.read_text());results.append(r)
        arrays=[]
        for file in [base/'segment1/full-record/trajectory.npz',base/'segment2/trajectory.npz'] if vehicle!='A' else [base/'segment1/full-record/trajectory.npz',base/'segment2/fixed/trajectory.npz',base/'segment2/high/trajectory.npz']:
            if file.exists():
                with np.load(file) as data:arrays.append((data['t'].copy(),data['qpos'].copy()))
        if arrays:
            t=np.concatenate([a[0] for a in arrays]);q=np.concatenate([a[1] for a in arrays]);order=np.argsort(t,kind='stable');t=t[order];q=q[order]
            unique=np.r_[True,np.diff(t)>1e-9];t=t[unique];q=q[unique]
            ix=np.unique(np.r_[np.arange(0,len(t),2),len(t)-1]);origin=t[0]
            samples=[]
            for i in ix:
                samples.append({'t':round(float(t[i]-origin),6),'position':np.round(q[i,:3],6).tolist(),
                    'orientation_wxyz':np.round(q[i,3:7],7).tolist(),'joints':np.round(q[i,7:],6).tolist()})
            payload={'schema':'beforestep-route-trajectory/v1','vehicle':vehicle,'nominal_hz':25,'joint_count':16,
                'physics_time_origin_s':float(origin),'samples':samples,'sources':[str(f.relative_to(ROOT)) for f in [base/'segment1/full-record/trajectory.npz',base/'segment2/trajectory.npz'] if f.exists()]}
            write(EVIDENCE/f'trajectory-{vehicle}.json',payload);cars[vehicle]={'path':f'evidence/crossing/route/trajectory-{vehicle}.json','result':r['total_result'],'samples':samples}
    polygons=[]
    detour=ROUTE/name/'prechecks'/scene['attempt']/'detour/segment1/truth_standin'
    for label,path in [('high-A',detour/'A.obj'),('high-B',detour/'B.obj'),*zip(['threshold','gate-left','gate-right'],[ROOT/p for p in scene['mesh_paths']])]:
        if not path.exists():continue
        mesh=trimesh.load(path,force='mesh',process=False);xy=mesh.vertices[:,:2]
        polygons.append({'name':label,'xy':np.round(xy[ConvexHull(xy).vertices],6).tolist()})
    precheck=json.loads((EVIDENCE/f'precheck-{name}.json').read_text()) if (EVIDENCE/f'precheck-{name}.json').exists() else None
    budget=json.loads((ROOT/'outputs/generation/crossing-budget.json').read_text())
    complete=len(results)==4
    by={r['vehicle']:r for r in results}
    legs=('这一场 A 没到、D 到达，支持腿在这条路线上的必要性。' if complete and by['D']['total_result']=='arrived' and by['A']['total_result']!='arrived' else
        '这一场 A 也到达，腿的必要性没有成立。' if complete and by['A']['total_result']=='arrived' else
        'D 尚未到达终点，这一场不能证明腿的必要性。' if complete else '四种车尚未全部终态，腿的必要性待核对。')
    imagination=('这一场不靠想象也到了。' if complete and any(by[v]['total_result']=='arrived' for v in ['B','C']) else
        '这一场 B、C 没到、D 到达，支持想象在这条路线上的必要性。' if complete and by['D']['total_result']=='arrived' else
        'D 尚未到达终点，这一场不能证明想象的必要性。' if complete else '四种车尚未全部终态，想象的必要性待核对。')
    report={'schema':'beforestep-crossing-route-summary/v1','scene':name,'scene_definition':f'evidence/crossing/route/scene-{name}.json',
        'scene_data':{'near_x_m':scene['near_x_m'],'gap_m':scene['gap_m'],'staging_xy':scene['staging_xy'],'goal':scene['goal'],'polygons':polygons},
        'rows':results,'all_terminal':complete,'prechecks_passed':bool(precheck and precheck['all_four_passed']),
        'legs_necessity':legs,'imagination_necessity':imagination,
        'threshold_closed_created':json.loads((EVIDENCE/'threshold-closure.json').read_text())['created'],'route_new_created':sum(r['scene'].startswith('route/') and bool(r.get('task_id')) for r in budget['tasks']),
        'cumulative_created':budget['created'],'first_scene_only':True,'additional_scenes':[],
        'state':'首场四种车全部终态' if complete else '四项预检查和首场运行正在进行',
        'freeze_verification':{'action_sha256':sha(ROOT/'experimental/crossing/action.py'),'base_scene_sha256':sha(ROOT/f'config/scenes/{scene["base_scene"]}.json'),'admission_sha256':sha(ROOT/'config/admission.json')}}
    write(EVIDENCE/'summary.json',report)
    write(EVIDENCE/'replay.json',{'schema':'beforestep-route-replay/v1','scene':report['scene_data'],'cars':cars})
    return report

if __name__=='__main__':
    r=build();print(json.dumps({'all_terminal':r['all_terminal'],'rows':len(r['rows']),'new_route_tasks':r['route_new_created']},ensure_ascii=False))
