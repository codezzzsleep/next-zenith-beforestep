"""CPU training with immutable data identity and resumable epoch checkpoints."""
import json
import os
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch.nn import functional as F

from .model import NavigationNet
from .world import ROOT, World, read, sha, write


def snapshots(cfg, library, split):
    X, Y, A, G, manifests = [],[],[],[],[]
    spec = cfg[split]
    for seed in range(spec['seed_start'],spec['seed_start']+spec['count']):
        world = World(cfg,library,split,seed)
        manifests.append(world.manifest())
        free = np.argwhere(np.isfinite(world.teacher_distance))
        if not len(free):
            continue
        for snapshot in range(cfg['training']['snapshots_per_world']):
            position = free[int(world.rng.integers(len(free)))]
            known = None
            for _ in range(int(world.rng.integers(1,5))):
                view = free[int(world.rng.integers(len(free)))]
                features,known = world.observe(view,world.rng.uniform(-np.pi,np.pi),known,panorama=True)
            features,known = world.observe(position,world.rng.uniform(-np.pi,np.pi),known)
            if snapshot == 1 and world.rng.random() < .5:
                features,_ = world.observe(position,0.,np.ones(world.shape,bool),panorama=True)
            marker = np.zeros(world.shape,np.float32)
            marker[tuple(world.goal)] = 1.
            X.append(features);Y.append(world.blocked.astype(np.float32))
            A.append(world.teacher_action.copy());G.append(marker)
    return (np.stack(X),np.stack(Y),np.stack(A),np.stack(G)),manifests


def save_checkpoint(path, data):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    torch.save(data,temporary)
    temporary.replace(path)


def train(cfg_path, library_path, out, resume=False):
    cfg,library = read(cfg_path),read(library_path)
    out = Path(out)
    identity = {'schema':'beforestep-navigation-training/v1','config_sha256':sha(cfg_path),
                'library_sha256':sha(library_path),
                'source':{str(p.relative_to(ROOT)):sha(p) for p in
                          [Path(__file__),Path(__file__).with_name('model.py'),Path(__file__).with_name('world.py')]},
                'seed':cfg['seed'],'new_paid_tasks':0,'torch_version':torch.__version__,
                'pid':os.getpid(),'stage':'training','started_at_unix':time.time()}
    if out.exists() and any(out.iterdir()) and not resume:
        raise ValueError('Preserve existing training output; use --resume or a new directory')
    out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(3)
    torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);random.seed(cfg['seed'])
    model = NavigationNet(cfg['value_iterations'])
    optimizer = torch.optim.Adam(model.parameters(),lr=cfg['training']['learning_rate'])
    start,best,history = 0,float('inf'),[]
    if resume:
        old = read(out/'identity.json')
        if any(old[k] != identity[k] for k in ('config_sha256','library_sha256','source')):
            raise ValueError('Resume configuration, library or source identity mismatch')
        checkpoint = torch.load(out/'latest.pt',weights_only=True,map_location='cpu')
        model.load_state_dict(checkpoint['model']);optimizer.load_state_dict(checkpoint['optimizer'])
        torch.set_rng_state(checkpoint['torch_rng']);start=checkpoint['epoch'];best=checkpoint['best']
        history=read(out/'history.json');identity['original_started_at_unix']=old['started_at_unix']
    else:
        save_checkpoint(out/'untrained.pt',{'model':model.state_dict(),'epoch':0})
    write(out/'identity.json',identity)
    if not (out/'data.npz').exists():
        data,manifest = snapshots(cfg,library,'train')
        val,valmanifest = snapshots(cfg,library,'validation')
        np.savez_compressed(out/'data.npz',**{f'train_{k}':v for k,v in zip('XYAG',data)},
                            **{f'val_{k}':v for k,v in zip('XYAG',val)})
        write(out/'train-scenes.json',manifest);write(out/'validation-scenes.json',valmanifest)
    with np.load(out/'data.npz',allow_pickle=False) as file:
        data=[torch.from_numpy(file['train_'+k]) for k in 'XYAG']
        val=[torch.from_numpy(file['val_'+k]) for k in 'XYAG']
    identity.update(samples=len(data[0]),validation_samples=len(val[0]),data_sha256=sha(out/'data.npz'))
    write(out/'identity.json',identity)
    # Supervised occupancy risk + imitation of offline shortest-path directions.
    # Teacher has training truth; the network only receives the observation contract.
    def loss(batch):
        x,y,a,g = batch
        q,logits = model(x,g)
        bce=F.binary_cross_entropy_with_logits(logits,y,pos_weight=torch.tensor(3.))
        action=F.cross_entropy(q*35.,a,ignore_index=-1)
        return bce+.10*action,bce,action
    for epoch in range(start,cfg['training']['epochs']):
        started=time.monotonic();model.train();sums=np.zeros(3);batches=0
        order=torch.randperm(len(data[0]))
        for indices in order.split(cfg['training']['batch_size']):
            optimizer.zero_grad();values=loss([a[indices] for a in data])
            values[0].backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.)
            optimizer.step();sums += [v.item() for v in values];batches+=1
        model.eval();vsums=np.zeros(3);vbatches=0
        with torch.no_grad():
            for indices in torch.arange(len(val[0])).split(cfg['training']['batch_size']):
                values=loss([a[indices] for a in val]);vsums += [v.item() for v in values];vbatches+=1
        row={'epoch':epoch+1,'train_loss':float(sums[0]/batches),'validation_loss':float(vsums[0]/vbatches),
             'train_occupancy_loss':float(sums[1]/batches),'validation_occupancy_loss':float(vsums[1]/vbatches),
             'validation_action_loss':float(vsums[2]/vbatches),'wall_seconds':time.monotonic()-started}
        if row['validation_loss'] < best:
            best=row['validation_loss'];save_checkpoint(out/'best.pt',{'model':model.state_dict(),'epoch':epoch+1})
        history.append(row);write(out/'history.json',history)
        save_checkpoint(out/'latest.pt',{'model':model.state_dict(),'optimizer':optimizer.state_dict(),
                                        'torch_rng':torch.get_rng_state(),'epoch':epoch+1,'best':best})
        print(json.dumps(row),flush=True)
    identity.update(stage='complete',completed_at_unix=time.time(),epochs=cfg['training']['epochs'],
                    best_sha256=sha(out/'best.pt'),best_validation_loss=best)
    write(out/'identity.json',identity)
