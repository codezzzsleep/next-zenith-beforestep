"""Generate any seed, run a fixed policy and save an honest geometric trajectory."""
import argparse
from pathlib import Path
import numpy as np
from .common import ROOT,OUT,read,write


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run');r.add_argument('--seed',type=int,required=True);r.add_argument('--method',choices=['conservative','optimistic','imagination','strict','strict_llm','learned','learned_no_lux','see_dark'],default='learned');r.add_argument('--split',choices=['development','sealed','ood'],default='sealed');r.add_argument('--out',required=True);r.add_argument('--model');r.add_argument('--env-file',default=str(ROOT.parent/'.env'))
    ev=sub.add_parser('evaluate');ev.add_argument('--split',choices=['validation','sealed','ood'],required=True);ev.add_argument('--out',required=True);ev.add_argument('--lux',required=True);ev.add_argument('--no-lux',required=True);ev.add_argument('--workers',type=int,default=2);ev.add_argument('--thresholds',type=float,nargs='+')
    ph=sub.add_parser('real');ph.add_argument('--scene',required=True);ph.add_argument('--model',required=True);ph.add_argument('--out',required=True)
    a=ap.parse_args()
    if a.command=='evaluate':
        from .suite import evaluate
        chosen=read(OUT/'validation/workpoint.json')['chosen'] if a.split!='validation' else None
        evaluate(a.split,a.out,a.lux,a.no_lux,a.thresholds,chosen,a.workers);return
    if a.command=='real':
        from .physics import real_world,run
        from .model import load
        w,source=real_world(a.scene);threshold=read(OUT/'validation/workpoint.json')['chosen']['learned']
        run(w,'learned',load(a.model),threshold,a.out,source);return
    from .world import World
    from .evaluate import run
    from .model import load
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    if (out/'result.json').exists():ap.error('Result already exists; use a new output directory')
    model=None;threshold=.1;advisor=None
    if a.method=='strict_llm':
        from .llm import Advisor
        advisor=Advisor(a.env_file,OUT/'llm/calls',stage='adhoc',stage_limit=3000)
    if a.method.startswith('learned'):
        default=ROOT/'assets/models/arena_v2'/('no_lux' if a.method=='learned_no_lux' else 'lux')/'best.pt'
        model=load(a.model or default);threshold=read(OUT/'validation/workpoint.json')['chosen'][a.method]
    w=World(a.seed,a.split)
    try:
        row,maps=run(w,a.method,model,threshold,advisor);write(out/'world.json',w.manifest());write(out/'result.json',row)
        np.savez_compressed(out/'maps.npz',state=maps['state'],truth=maps['truth'],risk=np.asarray(maps['risk']))
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from beforestep.navigation import map as N
        fig,ax=plt.subplots(figsize=(12,4));ax.imshow(maps['state'].T,origin='lower',extent=[N.X0,N.X1,N.Y0,N.Y1],cmap='tab10',vmin=0,vmax=9)
        ax.contour(N.GX,N.GY,w.raw,levels=[.5],colors='#b68d51',linewidths=1)
        trace=np.array(row['trace']);ax.plot(trace[:,0],trace[:,1],color='#26b39a',label=a.method)
        looks=np.array([o['position'] for o in row['observations']]);ax.scatter(looks[:,0],looks[:,1],marker='o',facecolors='none',edgecolors='#fff',label='explicit looks')
        ax.scatter(*w.goal,marker='*',color='#ffdb7d',s=120);ax.set_title(f"Seed {a.seed}: {a.method} / {row['status']} — production RGB-D, geometric execution")
        ax.set_xlabel('metres');ax.set_ylabel('metres');ax.legend();fig.tight_layout();fig.savefig(out/'trajectory.png',dpi=160);plt.close(fig)
        print({k:row[k] for k in ['seed','method','status','looks','path_length_m']})
    finally:w.close()


if __name__=='__main__':main()
