"""Synchronize private recovery metadata at each returned cloud task ID."""
import json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def checkpoint(stage):
    explicit=os.environ.get('BEFORESTEP_RECOVERY_REPO')
    candidates=[Path(explicit)] if explicit else list((ROOT.parent/'.recovery').glob('*'))+[ROOT.parent/'beforestep-recovery',ROOT.parent/'next-zenith-beforestep-recovery']
    repo=next((p for p in candidates if (p/'checkpoint_now.py').exists() and (p/'LATEST.json').exists()),None)
    if repo is None:raise RuntimeError('Configure BEFORESTEP_RECOVERY_REPO before any further task creation')
    result=subprocess.run(['/usr/bin/python3',str(repo/'checkpoint_now.py'),'--stage',stage],cwd=repo,text=True,capture_output=True)
    if result.returncode:raise RuntimeError('Private recovery sync failed; keep the returned task ID and sync it before continuing: '+result.stderr[-1200:])
    return json.loads(result.stdout.splitlines()[-1])
