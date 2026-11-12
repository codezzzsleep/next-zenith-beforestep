import argparse
from pathlib import Path
from .world import ROOT,make_library,read


def main():
    parser=argparse.ArgumentParser(description='Independent learned-navigation experiment')
    parser.add_argument('--config',default=str(ROOT/'config/training/navigation_v1.json'))
    parser.add_argument('--library',default=str(ROOT/'assets/training/navigation_v1/shape-library.json'))
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('library')
    train=sub.add_parser('train');train.add_argument('--out',required=True);train.add_argument('--resume',action='store_true')
    evaluate=sub.add_parser('evaluate');evaluate.add_argument('--training',required=True);evaluate.add_argument('--out',required=True)
    evaluate.add_argument('--split',action='append',choices=['validation','test','ood'])
    physics=sub.add_parser('physics');physics.add_argument('--training',required=True);physics.add_argument('--out',required=True)
    args=parser.parse_args()
    if args.command=='library':
        library=make_library(args.library);print({'pairs':len(library['pairs']),'output':args.library})
    elif args.command=='train':
        from .train import train
        train(args.config,args.library,args.out,args.resume)
    elif args.command=='evaluate':
        from .evaluate import evaluate
        print(evaluate(args.config,args.library,args.training,args.out,args.split))
    elif args.command=='physics':
        from .physics import evaluate_physics
        evaluate_physics(args.config,args.library,args.training,args.out)
