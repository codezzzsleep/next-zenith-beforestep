"""Real-world wheel-only validity checks, retained even when seeds are invalid."""
import argparse, json, sys, os, time, concurrent.futures, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import *
from experimental.crossing.scene import generate, DEVELOPMENT_SEEDS
from ops.crossing_probe import event


def run_case(seed, revision, method, position):
    scene=generate(seed,revision);folder=Path(scene['truth_mesh']).parents[1]/'validity'/f'{method}-{position}'
    if (folder/'result.json').exists():return json.loads((folder/'result.json').read_text())
    lateral={'center':0.,'left':scene['gap_m']/2-.25,'right':-scene['gap_m']/2+.25}[position]
    spec=scene['spec'];e=WheelLegEnv(spec,control_hz=50,max_seconds=240,nav_base=False,tip_deg=60)
    q=e.data.qpos.copy();q[:2]=[scene['observation_stop'][0],lateral];e.data.qpos[:]=q;e.data.qvel[:]=0;mujoco.mj_forward(e.model,e.data)
    rec=Record(e);rec.frame('initial');write(folder/'process.json',{'pid':os.getpid(),'seed':seed,'method':method,'position':position})
    pose=stance_array(STANCE if method=='fixed' else STANCE_HIGH)
    ok=transition(rec,pose,2.,'settle' if method=='fixed' else 'raise');started=time.monotonic()
    goal=scene['goal'][0]
    arrived=False
    while ok and e.t<240.:
        if min(wheel_positions(e)[:,0])>=goal:arrived=True;break
        w,x,y,z=e.data.qpos[3:7];yaw=np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z))
        turn=float(np.clip(-.8*yaw+.6*(lateral-e.data.qpos[1]),-.20,.20));v=min(.12,.03+e.t*.08)
        omega=np.array([(v+(-1 if leg in ['FL','RL'] else 1)*turn*.192)/WHEEL_R for leg in LEG])
        ok=rec.command(pose,np.clip(omega,-.15/WHEEL_R,.15/WHEEL_R),phase='wheel-validity')
    summary=rec.summary();status=('clean_pass' if arrived and not summary['steps_with_wheel_stone'] else 'wheel_contact_pass' if arrived else
        'body_collision' if rec.failure and rec.failure['kind']=='body_collision' else 'unstable' if rec.failure else 'stuck')
    rec.save(folder)
    result={'schema':'beforestep-crossing-validity-trial/v1','seed':seed,'revision':revision,'method':method,'position':position,
        'lateral_m':lateral,'status':status,'sim_seconds':e.t,'wall_seconds':time.monotonic()-started,'contact':summary,
        'scene':str(Path(scene['truth_mesh']).parents[1]/'scene.json'),'time_limit_s':240.,'speed_cap_m_s':.15,
        'trajectory_sha256':sha(folder/'trajectory.npz'),'contacts_sha256':sha(folder/'contacts.npz'),
        'raw_path':str(folder.relative_to(ROOT)),'final_base':e.data.qpos[:7].tolist(),'new_lux_tasks':0}
    write(folder/'result.json',result);return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',default='scene-dev-v3');parser.add_argument('--workers',type=int,default=3);args=parser.parse_args()
    attempt='validity-'+args.revision;tasks=[]
    for seed in DEVELOPMENT_SEEDS:
        scene=generate(seed,args.revision);folder=Path(scene['truth_mesh']).parents[1];source=folder/'source';source.mkdir(exist_ok=True)
        for p in [ROOT/'experimental/crossing/scene.py',Path(__file__),ROOT/'experimental/crossing/runtime.py']:
            target=source/p.name
            if target.exists():assert target.read_bytes()==p.read_bytes()
            else:shutil.copyfile(p,target)
        tasks.extend((seed,args.revision,m,p) for m in ['fixed','high'] for p in ['center','left','right'])
    event(attempt,status='running',pid=os.getpid(),trials=len(tasks),workers=args.workers,output='outputs/crossing/development/'+args.revision,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'experimental/crossing/scene.py',ROOT/'experimental/crossing/runtime.py']})
    rows=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run_case,*task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            r=future.result();rows.append(r);print(json.dumps({k:r[k] for k in ['seed','method','position','status','sim_seconds']}),flush=True)
            event(attempt,completed=len(rows))
    scenes=[]
    for seed in DEVELOPMENT_SEEDS:
        trials=[r for r in rows if r['seed']==seed];assert len(trials)==6
        record={'seed':seed,'valid':not any(r['status'] in ('clean_pass','wheel_contact_pass') for r in trials),
                'trials':trials,'A_reference':next(r['raw_path'] for r in trials if r['method']=='fixed' and r['position']=='center')}
        write(OUT/'development'/args.revision/f'seed-{seed}'/'validity.json',record);scenes.append(record)
    report={'schema':'beforestep-crossing-validity/v1','revision':args.revision,'candidate_count':4,
            'wheel_passable_candidates':sum(not s['valid'] for s in scenes),'time_limit_s':240.,'scenes':scenes}
    write(ROOT/'evidence/crossing/development-validity.json',report);event(attempt,status='complete',results=report)
if __name__=='__main__':main()
