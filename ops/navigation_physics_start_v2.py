"""Independent start-initialization repair; v1 results and model stay intact."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experimental.navigation.world import ROOT,World,read,write
from experimental.navigation.model import load_model
from experimental.navigation_physics_start_v2 import run,evaluate_physics


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',default=str(ROOT/'config/training/navigation_physics_start_v2.json'))
    p.add_argument('--training',default=str(ROOT/'outputs/learning/navigation_v1'))
    p.add_argument('--out',required=True);p.add_argument('--validation-seed',type=int)
    p.add_argument('--resume',action='store_true');a=p.parse_args()
    library=ROOT/'assets/training/navigation_v1/shape-library.json'
    if a.validation_seed is None:
        evaluate_physics(a.config,library,a.training,a.out,a.resume)
    else:
        import torch
        torch.set_num_threads(1)
        cfg=read(a.config);world=World(cfg,read(library),'validation',a.validation_seed)
        out=Path(a.out)
        if out.exists():raise ValueError('Preserve existing validation')
        write(out/'world.json',world.manifest())
        model=load_model(Path(a.training)/'best.pt',cfg['value_iterations'])
        for method in ['rules_cached_prior','learned']:
            result=run(world,method,model,out/method)
            print({k:result[k] for k in ['method','status','goal_error_m','sim_seconds']},flush=True)


if __name__=='__main__':main()
