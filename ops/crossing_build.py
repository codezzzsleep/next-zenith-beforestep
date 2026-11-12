"""Build result-derived crossing calibration data, report and first public page."""
import sys,json,hashlib,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import OUT,write,sha

HEIGHTS=[.04,.06,.08,.10,.12,.15,.18,.22];DEPTHS=[.10,.20,.30,.40]
PASS={'clean_pass','wheel_contact_pass'}

def main():
    raw=OUT/'calibration/baseline-v1';rows=json.loads((raw/'summary.json').read_text())['results'];assert len(rows)==192
    rows.sort(key=lambda r:(r['method'],r['h_m'],r['d_m'],r['angle_deg']))
    groups=[]
    for method in ['fixed','high']:
        for h in HEIGHTS:
            for d in DEPTHS:
                trials=[r for r in rows if r['method']==method and r['h_m']==h and r['d_m']==d];assert len(trials)==3
                groups.append({'method':method,'height_m':h,'depth_m':d,'passed':sum(r['status'] in PASS for r in trials),'clean':sum(r['status']=='clean_pass' for r in trials),'trials':trials})
    maximum={m:{'any_pass_height_m':max(r['h_m'] for r in rows if r['method']==m and r['status'] in PASS),'three_of_three_height_m':max(g['height_m'] for g in groups if g['method']==m and g['passed']==3)} for m in ['fixed','high']}
    data={'schema':'beforestep-crossing-baseline/v1','status':'wheel_baselines_complete_gait_developing','trial_count':192,'angles_deg':[0,-5,5],'heights_m':HEIGHTS,'depths_m':DEPTHS,'maximum':maximum,'groups':groups,'new_lux_tasks':0,'speed_target_m_s':.12,'driving_speed_cap_m_s':.15,'time_limit_after_stance_s':40,'tip_threshold_deg':60,'contact_definition':'Wheel-stone contact is permitted and separately recorded; non-wheel stone/ground contact or tilt over threshold fails.','source_job':json.loads((OUT/'jobs.json').read_text())['jobs']['baselines']}
    public=ROOT/'evidence/crossing/calibration';public.mkdir(parents=True,exist_ok=True)
    write(public/'baseline.json',data)
    archive_rows=[]
    for h in HEIGHTS:
        archive=public/f'wheel-baselines-h{int(round(h*100)):02d}cm.tar.gz'
        trials=[r for r in rows if r['h_m']==h]
        if not archive.exists():
            with tarfile.open(archive,'w:gz',compresslevel=1) as bundle:
                for trial in trials:
                    folder=raw/f"{trial['method']}-h{h:.3f}-d{trial['d_m']:.3f}-a{trial['angle_deg']:+.1f}"
                    bundle.add(folder,arcname='trials/'+folder.name)
                bundle.add(raw/'source',arcname='source-first-attempt')
        archive_rows.append({'path':str(archive.relative_to(ROOT)),'bytes':archive.stat().st_size,'sha256':sha(archive),'trials':len(trials),'download':'https://media.githubusercontent.com/media/codezzzsleep/next-zenith-beforestep/main/'+str(archive.relative_to(ROOT))})
    write(public/'manifest.json',{'stage':'wheel_baselines_complete','trial_count':len(rows),'archive_count':len(archive_rows),'archives':archive_rows,'geometry_recovery':'baseline-geometry-recovery.json','frozen_source':'4d53214','model_manifest':'config/robot-assets.json','raw_runs':[{'id':f"{r['method']}-h{r['h_m']:.3f}-d{r['d_m']:.3f}-a{r['angle_deg']:+.1f}",'trajectory_sha256':r['trajectory_sha256'],'contacts_sha256':r['contacts_sha256']} for r in rows]})
    lines=['# 轮腿跨越：轮行能力标定','', '状态：两种轮行矩阵完成；逐轮动作与物理闸门尚未完成。尚未创建Lux3D任务。','',f"常规姿态最高有一次通过的高度为{maximum['fixed']['any_pass_height_m']*100:g}厘米；同一高度、进深下三个接近角全部通过的最高高度为{maximum['fixed']['three_of_three_height_m']*100:g}厘米。高姿态这两个值分别为{maximum['high']['any_pass_height_m']*100:g}、{maximum['high']['three_of_three_height_m']*100:g}厘米。",'', '进深上的结果不单调；这些值只描述本矩阵，不能推断连续能力或实机结果。','', '| 高度(cm) | 方法 | 深10cm | 深20cm | 深30cm | 深40cm |','|---|---|---|---|---|---|']
    for h in HEIGHTS:
        for m,label in [('fixed','固定常规'),('high','固定高姿')]:
            cells=[f"{next(g for g in groups if g['method']==m and g['height_m']==h and g['depth_m']==d)['passed']} / 3" for d in DEPTHS]
            lines.append(f'| {h*100:g} | {label} | '+' | '.join(cells)+' |')
    lines+=['','全部通过均发生过轮触石；不称为干净通过。原始判定含全部机身触石、失稳与卡住，逐试验接触/轨迹SHA和完整包见[清单](../evidence/crossing/calibration/manifest.json)。','', '原协调器发生共享临时文件竞态；190完成试验全部接触点符合请求尺寸，保留原件，只补未完成2试验。控制参数和物理模型保持相同。','', '实验调用冻结MuJoCo3.17.0模型与env.step_command，新判定在独立physics_monitor中实现。既有R1/R2/R3结果和src不改。']
    (ROOT/'docs/crossing.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'trial_count':len(rows),'maximum':maximum,'archive_bytes':sum(a['bytes'] for a in archive_rows)}))

if __name__=='__main__':main()
