import argparse
from pathlib import Path
from .world import ROOT,make_library,read


def main():
    parser=argparse.ArgumentParser(description='Independent learned-navigation experiment')
    parser.add_argument('--config',default=str(ROOT/'config/training/navigation_v1.json'))
    parser.add_argument('--library',default=str(ROOT/'assets/training/navigation_v1/shape-library.json'))
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('library')
    generate=sub.add_parser('generate');generate.add_argument('--seed',type=int,required=True)
    generate.add_argument('--distribution',choices=['train','test','ood'],default='test')
    generate.add_argument('--out',required=True);generate.add_argument('--mujoco',action='store_true')
    train=sub.add_parser('train');train.add_argument('--out',required=True);train.add_argument('--resume',action='store_true')
    evaluate=sub.add_parser('evaluate');evaluate.add_argument('--training',required=True);evaluate.add_argument('--out',required=True)
    evaluate.add_argument('--resume',action='store_true')
    evaluate.add_argument('--split',action='append',choices=['validation','test','ood'])
    physics=sub.add_parser('physics');physics.add_argument('--training',required=True);physics.add_argument('--out',required=True)
    physics.add_argument('--resume',action='store_true')
    llm=sub.add_parser('llm');llm.add_argument('--env-file',required=True);llm.add_argument('--out',required=True)
    llm.add_argument('--seed-start',type=int,default=6100000);llm.add_argument('--count',type=int,default=8)
    llm.add_argument('--max-calls',type=int,default=32)
    llm.add_argument('--prior-calls',action='append',default=[],help='Prior request ledgers counted against the same total budget')
    args=parser.parse_args()
    if args.command=='library':
        library=make_library(args.library);print({'pairs':len(library['pairs']),'output':args.library})
    elif args.command=='generate':
        from .world import World,write
        world=World(read(args.config),read(args.library),args.distribution,args.seed)
        out=Path(args.out)
        if out.exists() and any(out.iterdir()):raise ValueError('Preserve existing generated scene')
        write(out/'world.json',world.manifest())
        if args.mujoco:
            from .physics import scene_spec
            write(out/'mujoco-scene.json',scene_spec(world,out))
        print({'seed':args.seed,'output':str(out),'rocks':len(world.rocks),'oracle_reachable':bool(world.reachable)})
    elif args.command=='train':
        from .train import train
        train(args.config,args.library,args.out,args.resume)
    elif args.command=='evaluate':
        from .evaluate import evaluate
        print(evaluate(args.config,args.library,args.training,args.out,args.split,args.resume))
    elif args.command=='physics':
        from .physics import evaluate_physics
        evaluate_physics(args.config,args.library,args.training,args.out,args.resume)
    elif args.command=='llm':
        from .evaluate import evaluate_llm
        evaluate_llm(args.config,args.library,args.env_file,args.out,args.seed_start,args.count,args.max_calls,args.prior_calls)
