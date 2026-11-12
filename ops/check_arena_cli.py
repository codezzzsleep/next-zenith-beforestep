"""Exercise the arbitrary-seed command once, outside all scored datasets."""
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experimental.arena.common import OUT,read,write,sha
from experimental.arena.registration import require_registration

SEED=9210000


def restore_plot(folder,cfg):
    """A terminal episode is preserved if interruption omitted its plot."""
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    row=read(folder/'result.json')
    with np.load(folder/'maps.npz') as maps:
        fig,ax=plt.subplots(figsize=(12,4))
        ax.imshow(maps['state'].T,origin='lower',extent=cfg['bounds'],cmap='tab10',vmin=0,vmax=9)
        trace=np.asarray(row['trace']);ax.plot(trace[:,0],trace[:,1],color='#26b39a')
        eyes=np.asarray([eye['position'] for eye in row['observations']])
        ax.scatter(eyes[:,0],eyes[:,1],facecolors='none',edgecolors='white')
        ax.scatter(*read(folder/'world.json')['definition']['goal'],marker='*',color='#b68d51')
        ax.set(xlabel='metres',ylabel='metres',title=f"Seed {SEED}: learned / {row['status']} — saved geometric record")
        fig.tight_layout();fig.savefig(folder/'trajectory.png',dpi=160);plt.close(fig)


def main():
    from PIL import Image
    registration=require_registration();cfg=read(ROOT/'experimental/arena/parameters.json')
    for key in ['development','train','validation','sealed','ood','fidelity']:
        interval=cfg[key]
        assert not interval['seed_start']<=SEED<interval['seed_start']+interval['count']
    folder=OUT/'acceptance/new-seed-cli';model=ROOT/'assets/models/arena_v2/lux/best.pt'
    command=[sys.executable,'-m','experimental.arena.cli','run','--seed',str(SEED),
        '--method','learned','--out',str(folder)]
    identity={'seed':SEED,'method':'learned','model_sha256':sha(model),
        'protocol_commit':registration['commit'],'threshold':read(OUT/'validation/workpoint.json')['chosen']['learned'],
        'scope':'Command acceptance only; excluded from sealed/OOD scores','new_lux_tasks':0}
    previous=read(folder/'identity.json') if (folder/'identity.json').exists() else None
    if previous:
        assert all(previous[key]==value for key,value in identity.items()),'CLI acceptance identity changed'
        if previous.get('pid')!=os.getpid() and previous.get('status')=='running':
            assert not Path(f"/proc/{previous['pid']}").exists(),'Existing live CLI acceptance; do not duplicate'
    recovered=bool(previous and previous.get('plot_recovered_from_saved_arrays'))
    attempts=list(previous.get('attempts',[])) if previous else []
    if not (folder/'result.json').exists():
        if previous:attempts.append({k:v for k,v in previous.items() if k!='attempts'})
        write(folder/'identity.json',{**identity,'status':'running','pid':os.getpid(),'command':command,'attempts':attempts})
        with (folder/'command.log').open('a') as log:
            subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,
                env={**os.environ,'MUJOCO_GL':'egl','OPENBLAS_NUM_THREADS':'1'})
    elif not (folder/'trajectory.png').exists():
        restore_plot(folder,cfg);recovered=True
    row=read(folder/'result.json');world=read(folder/'world.json')
    assert row['seed']==world['seed']==SEED and row['method']=='learned'
    assert row['status'] in ['arrived','stopped','collision']
    assert row['trace'] and row['observations'] and row['looks']<=cfg['max_looks']
    with Image.open(folder/'trajectory.png') as image:
        image.load();assert image.width>=1200 and image.height>=400
    files={name:sha(folder/name) for name in ['world.json','result.json','maps.npz','trajectory.png']}
    if previous and previous['status']=='complete':assert previous['files_sha256']==files
    write(folder/'identity.json',{**identity,'status':'complete','passed':True,'command':command,
        'files_sha256':files,'outcome':row['status'],'plot_recovered_from_saved_arrays':recovered,'attempts':attempts})
    print(f'Arbitrary-seed CLI artifacts passed: {SEED}, {row["status"]}; excluded from scored datasets')


if __name__=='__main__':main()
