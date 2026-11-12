"""Execute entire planned segments without observation, score against independent truth."""
import time
import numpy as np
from beforestep.navigation import map as N
from .geometry import apply_scene
from .numerical import plan
from .policies import evidence,decide
from .common import finite


def execute_geometric(path,position,truth_occ):
    field=N.clearance(truth_occ);trace=[np.asarray(position).tolist()];collision=None
    for k,(a,b) in enumerate(zip([position,*path[:-1]],path)):
        a,b=np.asarray(a),np.asarray(b)
        # A turn sweeps the frozen robot turn radius, except the declared initial pose.
        if k>0:
            i,j=N.cell_of(*a)
            if field[i,j]<N.R_TURN:return trace,{'kind':'turn','position':a.tolist()}
        points=a+np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/.025)))[:,None]*(b-a)
        for q in points[1:]:
            i,j=N.cell_of(*q);trace.append(q.tolist())
            if not (0<=i<N.NX and 0<=j<N.NY) or field[i,j]<N.R_DRIVE:
                return trace,{'kind':'drive','position':q.tolist()}
    return trace,collision


def run(world,method,model=None,threshold=.1):
    apply_scene(world.definition);world.reset_sensor();position=world.start.copy();yaw=world.heading
    launch_ok=getattr(world,'launch_clear',True)
    known=N.swept([position],r=world.cfg.get('known_launch_radius_m',N.R_DRIVE) if launch_ok else N.R_DRIVE);maps=[];zmaps=[];looks=[];trace=[position.tolist()]
    started=time.monotonic();status='stopped';collision=None;probabilities=[]
    candidates=world.imagination() if method not in ('conservative','optimistic','see_dark') else [];elapsed=0.
    reachable=plan(world.truth_occ,world.start,world.goal) is not None
    for k in range(world.cfg['max_looks']):
        ob=world.observe(position,yaw,see_dark=method=='see_dark');maps.append(ob['state']);zmaps.append(ob['zmax'])
        state=N.fuse(maps);zmax=np.max(np.stack(zmaps),axis=0)
        card=evidence(state,zmax,candidates,known,position,yaw,world.definition['sun'],world.ground)
        card['look_history']=[(np.asarray(l['position']),l['yaw']) for l in looks]
        action,probability,occ=decide(card,method,world.goal,world.cfg['max_looks']-k-1,model,threshold)
        if probability is not None:probabilities.append(probability.astype(np.float16))
        looks.append({'position':position.tolist(),'yaw':float(yaw),'action':finite(action),
                      'state_counts':np.bincount(state.ravel(),minlength=6).tolist()})
        elapsed+=world.cfg['look_seconds']
        if action['kind']=='stop':break
        segment,collision=execute_geometric(action['path'],position,world.truth_occ)
        length=float(np.linalg.norm(np.diff(segment,axis=0),axis=1).sum()) if len(segment)>1 else 0.
        elapsed+=length/world.cfg['speed_m_s'];trace.extend(segment[1:]);position=np.array(trace[-1])
        if collision:status='collision';break
        known|=N.swept(segment,r=N.R_DRIVE)
        if action['kind']=='go':status='arrived';break
        yaw=action['yaw']
    row={'seed':world.seed,'split':world.split,'capsule_id':world.capsule['id'],'method':method,
         'launch_clear':bool(launch_ok),
         'reachable':reachable,'status':status,'collision':collision,'looks':len(looks),
         'elapsed_seconds':elapsed,'wall_seconds':time.monotonic()-started,
         'path_length_m':float(np.linalg.norm(np.diff(trace,axis=0),axis=1).sum()) if len(trace)>1 else 0.,
         'trace':trace,'observations':looks,'goal_error_m':float(np.linalg.norm(position-world.goal)),
         'sensor':world.cfg.get('sensor','5cm geometric height-ray sensor')+'; only explicit looks, no observations in motion'}
    return row,{'state':state,'zmax':zmax,'risk':probabilities,'truth':world.raw}


def summarize(rows):
    out={}
    for method in sorted({r['method'] for r in rows}):
        group=[r for r in rows if r['method']==method]
        for scope in ['all','reachable']:
            g=group if scope=='all' else [r for r in group if r['reachable']];n=len(g)
            out.setdefault(method,{})[scope]={'worlds':n,'arrived':sum(r['status']=='arrived' for r in g),
                'collision':sum(r['status']=='collision' for r in g),'stopped':sum(r['status']=='stopped' for r in g),
                'arrival_rate':sum(r['status']=='arrived' for r in g)/n if n else None,
                'collision_rate':sum(r['status']=='collision' for r in g)/n if n else None,
                'mean_looks':np.mean([r['looks'] for r in g]) if n else None,
                'mean_elapsed_seconds':np.mean([r['elapsed_seconds'] for r in g]) if n else None,
                'mean_path_length_m':np.mean([r['path_length_m'] for r in g]) if n else None}
    return finite(out)
