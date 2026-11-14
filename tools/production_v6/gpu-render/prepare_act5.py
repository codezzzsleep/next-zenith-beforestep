"""Prepare only the already completed ACT5 diagnostic and A/B runs."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import ROOT,OUT,save,sha,status
import numpy as np
p=OUT/'gpu-render';base=ROOT/'outputs/crossing/route/stress_v8_gate'
paths=[base/'prechecks/x9.00-seed22001/detour/segment1/full-record/trajectory.npz',base/'connection-precheck/observed-leg-segment/trajectory.npz',ROOT/'outputs/crossing/route/suite_r2_v4_F3_002_gate/A/segment1/full-record/trajectory.npz',ROOT/'outputs/crossing/route/suite_r2_v4_F3_002_gate/B/segment1/full-record/trajectory.npz']
z=[np.load(path) for path in paths]
for a in z:assert a['qpos'].shape[1]==23
handoff=json.loads((base/'connection-precheck/handoff.json').read_text());assert handoff['equal'] and handoff['before']==handoff['after']
assert np.array_equal(z[0]['qpos'][-1],z[1]['qpos'][0]) and np.array_equal(z[0]['qvel'][-1],z[1]['qvel'][0])
refs=[{'path':str(path.relative_to(ROOT)),'sha256':sha(path)} for path in paths]
close={'kind':'follow','azimuth':-40,'elevation':-17,'distance':1.7,'x_offset':.08,'y_offset':0,'z_scale':.65}
first,last=float(z[0]['t'][0]),float(z[1]['t'][-1]);join=(float(z[0]['t'][-1])-first)/(last-first)*18
phase=z[1]['phase'];mask=np.isin(phase,['front-right-lift','front-right-swing','front-right-land']);times=z[1]['t'][mask];assert len(times)>0
def row(name,source,route,seconds,camera,spec,start,end,**extras):
 return {'id':name,'sources':source,'scene':route,'route':route,'duration_s':seconds,'speed':None,'camera':camera,'camera_spec':spec,'sim_start':start,'sim_end':end,'act5_authority':'NOTE_FOR_CODEX_ACT5.md',**extras}
rows=[
 row('s09-connect-overview-v2',refs[:2],'stress_v8_gate',18,'overhead-close-v2',{'kind':'follow','azimuth':-90,'elevation':-55,'distance':2.4,'x_offset':.15,'y_offset':0,'z_scale':.5},first,last,handoff=handoff,source_classification='Truth-geometry route diagnostic plus observed-threshold connection precheck; not formalD or a Lux3D success',transition_annotation={'start_s':max(0,join-.4),'end_s':join+.9,'text':'转场：保存状态交接 · 门槛跨越'},source_join_sim_s=float(z[0]['t'][-1])),
 row('s09-connect-close-v2',[refs[1]],'stress_v8_gate',8,'low-v2',{'kind':'follow','azimuth':25,'elevation':-12,'distance':1.7,'x_offset':.12,'y_offset':0,'z_scale':.6},float(times[0]),float(times[-1]),source_classification='Observed-threshold leg detail from completed connection precheck; no new physics'),
 row('s09-F3002-A-stop-v2',[refs[2]],'suite_r2_v4_F3_002_gate',14,'follow-v2',close,float(z[2]['t'][0]),float(z[2]['t'][-1]),terminal_hold_s=2,source_classification='Formal A stopped;57.7 execution simulation seconds/2looks/imagined_blocked; no gate crossing'),
 row('s09-F3002-B-stop-v2',[refs[3]],'suite_r2_v4_F3_002_gate',10,'follow-v2',close,float(z[3]['t'][0]),float(z[3]['t'][-1]),terminal_hold_s=1,source_classification='Formal B79.82s/1look; wheel contact triggered monitor; body did not hit rock')]
plan=json.loads((p/'shot-plan.json').read_text());items={r['id']:r for r in plan['shots']}
for r in rows:items[r['id']]=r
plan.update(shots=list(items.values()),pending=['s09-F3002-D-v2 only if terminal first segment matches A'],act5_replaces_old_gate_wait=True);save(p/'shot-plan.json',plan)
files=paths+[p/'shot-plan.json']
manifest={'files':[{'path':str(f.relative_to(ROOT.parent)),'sha256':sha(f),'bytes':f.stat().st_size} for f in files],'shots':rows,'handoff':handoff,'handoff_qpos_qvel_equal':True,'physics_runs':0,'new_generation_tasks':0}
save(p/'act5-input-manifest.json',manifest);(p/'act5-rsync-files.txt').write_text('\n'.join(r['path'] for r in manifest['files'])+'\n')
save(p/'act5-plan.json',{'shots':rows,'authority':'NOTE_FOR_CODEX_ACT5.md','no_wait_for_D':True,'gpu_shutdown':False})
status('ACT5既有终态选材与交接核验',p/'act5-input-manifest.json','4镜头：真值诊断连接全程18s/腿8s、A14s/B10s；原qpos/qvel前后逐字节相等；输入均<20M，零物理/Lux')
print(json.dumps({'shots':[r['id'] for r in rows],'total_input_bytes':sum(r['bytes'] for r in manifest['files']),'maximum_file_bytes':max(r['bytes'] for r in manifest['files']),'transition_output_s':join},ensure_ascii=False))
