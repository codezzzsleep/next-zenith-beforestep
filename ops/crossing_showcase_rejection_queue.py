"""Add the source-verified rejected-model diagnostic after a capture slot frees."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'showcase-real-footage'
def save(status):(WORK/'rejection-queue.json').write_text(json.dumps({'status':status,'pid':os.getpid(),'new_experiments':0},indent=2))
save('waiting_levels')
while True:
 p=WORK/'worker-levels.json'
 if p.exists() and json.loads(p.read_text()).get('status')=='complete':break
 time.sleep(3)
save('filming_original_counterfactual')
with (WORK/'rejected.log').open('w') as log:subprocess.run([sys.executable,'ops/crossing_showcase_capture.py','--group','rejected'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
save('complete')
