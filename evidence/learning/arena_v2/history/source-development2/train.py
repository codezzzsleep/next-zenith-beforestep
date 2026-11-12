"""CPU CNN training; dataset generation is guarded by passed development checks."""
import argparse
from pathlib import Path
import random,time,os
import numpy as np
import torch
from torch.utils.data import Dataset,DataLoader
from beforestep.navigation import map as N
from .common import ROOT,OUT,read,write,sha
from .world import World
from .policies import evidence
from .model import HiddenOccupancy,features,LUX_CHANNELS


def make_sample(seed,split,out):
    w=World(seed,split)
    try:
        ob=w.observe(w.start,w.heading)
        card=evidence(ob['state'],ob['zmax'],w.imagination(),N.swept([w.start],r=w.cfg['known_launch_radius_m']),w.start,w.heading,w.definition['sun'],w.ground)
        x=features(card);unknown=(ob['state']==N.DARK)|(ob['state']==N.HIDDEN)|(ob['state']==N.UNSEEN)
        path=Path(out)/'samples'/f'{seed}.npz';path.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(path,x=x.astype(np.float16),target=w.raw,unknown=unknown)
        return {'seed':seed,'split':split,'world':w.manifest(),'sample':str(path.relative_to(ROOT)),'sha256':sha(path),'unknown_cells':int(unknown.sum()),'teacher_only_target':'True scan occupancy; not included in x'}
    finally:w.close()


def generate(out,split='train',workers=2):
    from concurrent.futures import ProcessPoolExecutor
    out=Path(out);out.mkdir(parents=True,exist_ok=True);cfg=read(ROOT/'experimental/arena/parameters.json')
    assert cfg['sensor']=='production_rgbd'
    assert read(OUT/'prechecks/final.json')['passed'],'Prechecks must pass before training data'
    assert (ROOT/'docs/arena-protocol.md').exists(),'Commit preregistration before validation data'
    r=cfg[split];seeds=range(r['seed_start'],r['seed_start']+r['count'])
    write(out/'identity.json',{'status':'running','pid':os.getpid(),'split':split,'parameters_sha256':sha(ROOT/'experimental/arena/parameters.json'),'capsules_sha256':sha(OUT/'capsules.json'),'protocol_sha256':sha(ROOT/'docs/arena-protocol.md')})
    rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={}
        for seed in seeds:
            entry=out/'entries'/f'{seed}.json'
            if entry.exists():
                row=read(entry);assert sha(ROOT/row['sample'])==row['sha256'];rows.append(row)
            else:futures[seed]=pool.submit(make_sample,seed,split,out)
        for seed,f in futures.items():
            row=f.result();write(out/'entries'/f'{seed}.json',row);rows.append(row)
            if len(rows)%20==0:print(split,len(rows),flush=True)
    rows.sort(key=lambda r:r['seed']);write(out/'manifest.json',rows)
    identity=read(out/'identity.json');identity.update(status='complete',worlds=len(rows),manifest_sha256=sha(out/'manifest.json'));write(out/'identity.json',identity)


class Samples(Dataset):
    def __init__(self,folder,no_lux=False):self.rows=read(Path(folder)/'manifest.json');self.no_lux=no_lux
    def __len__(self):return len(self.rows)
    def __getitem__(self,i):
        a=np.load(ROOT/self.rows[i]['sample']);x=a['x'].astype(np.float32)
        if self.no_lux:x[LUX_CHANNELS]=0
        return torch.from_numpy(x),torch.from_numpy(a['target'].astype(np.float32)),torch.from_numpy(a['unknown'].astype(np.float32))


def train(data,out,epochs=15,no_lux=False,seed=20261112):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.set_num_threads(4)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not (out/'best.pt').exists(),'Preserve previous weights; use a distinct training identity'
    ds=Samples(data,no_lux);assert len(ds)>=4000
    loader=DataLoader(ds,batch_size=8,shuffle=True,num_workers=2,generator=torch.Generator().manual_seed(seed))
    model=HiddenOccupancy();opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001);history=[];best=float('inf');started=time.monotonic()
    identity={'status':'running','pid':os.getpid(),'seed':seed,'no_lux':no_lux,'epochs':epochs,'parameters':sum(p.numel() for p in model.parameters()),'manifest_sha256':sha(Path(data)/'manifest.json'),'model_source_sha256':sha(ROOT/'experimental/arena/model.py'),'train_source_sha256':sha(__file__),'torch':torch.__version__,'teacher':'Binary true occupancy at unknown cells; unweighted BCE for probability calibration','decision_head':False}
    write(out/'identity.json',identity)
    for epoch in range(epochs):
        model.train();loss_sum=0.;cells=0.
        for x,y,unknown in loader:
            logits=model(x);lossmap=torch.nn.functional.binary_cross_entropy_with_logits(logits,y,reduction='none')
            loss=(lossmap*unknown).sum()/unknown.sum().clamp_min(1)
            opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.);opt.step()
            loss_sum+=float(loss.detach())*float(unknown.sum());cells+=float(unknown.sum())
        avg=loss_sum/cells;history.append({'epoch':epoch+1,'train_loss':avg,'wall_seconds':time.monotonic()-started})
        payload={'state_dict':model.state_dict(),'optimizer':opt.state_dict(),'epoch':epoch+1,'seed':seed,'no_lux':no_lux,'torch_rng':torch.get_rng_state(),'numpy_rng':np.random.get_state(),'manifest_sha256':identity['manifest_sha256']}
        torch.save(payload,out/'latest.pt')
        if avg<best:best=avg;torch.save(payload,out/'best.pt')
        write(out/'curve.json',history);print(no_lux,history[-1],flush=True)
    identity.update(status='complete',best_train_loss=best,wall_seconds=time.monotonic()-started,best_sha256=sha(out/'best.pt'));write(out/'identity.json',identity)


def calibration(data,model,out,no_lux=False):
    from .model import load
    model=load(model);torch.set_num_threads(2);bins=np.linspace(0,1,11);counts=np.zeros(10,int);sum_p=np.zeros(10);sum_y=np.zeros(10)
    ds=Samples(data,no_lux)
    with torch.inference_mode():
        for x,y,u in DataLoader(ds,batch_size=8):
            p=torch.sigmoid(model(x)).numpy();y=y.numpy();u=u.numpy()>0;p=p[u];y=y[u]
            idx=np.minimum((p*10).astype(int),9);counts+=np.bincount(idx,minlength=10);sum_p+=np.bincount(idx,weights=p,minlength=10);sum_y+=np.bincount(idx,weights=y,minlength=10)
    mean=sum_p/np.maximum(counts,1);actual=sum_y/np.maximum(counts,1)
    write(out,{'bins':bins.tolist(),'counts':counts.tolist(),'mean_probability':mean.tolist(),'actual_fraction':actual.tolist(),'ece':float((abs(mean-actual)*counts).sum()/counts.sum()),'unknown_cells':int(counts.sum()),'no_lux':no_lux})


if __name__=='__main__':
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    g=sub.add_parser('generate');g.add_argument('--out',required=True);g.add_argument('--split',default='train',choices=['train','validation']);g.add_argument('--workers',type=int,default=2)
    t=sub.add_parser('train');t.add_argument('--data',required=True);t.add_argument('--out',required=True);t.add_argument('--epochs',type=int,default=15);t.add_argument('--no-lux',action='store_true')
    a=ap.parse_args()
    if a.cmd=='generate':generate(a.out,a.split,a.workers)
    else:train(a.data,a.out,a.epochs,a.no_lux)
