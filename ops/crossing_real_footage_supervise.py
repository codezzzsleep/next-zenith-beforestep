"""Wait for the first recording slot, then record the original world and accident."""
import json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'real-footage-180';ledger=WORK/'supervisor.json'
def save(status):ledger.write_text(json.dumps({'status':status,'pid':os.getpid(),'new_physics_runs':0,'new_generation_tasks':0}))
save('waiting_for_r1_recordings')
while True:
 p=WORK/'worker-r1.json'
 if p.exists() and json.loads(p.read_text()).get('status')=='complete':break
 time.sleep(5)
save('recording_original_world_and_contact')
with (WORK/'world-failure.log').open('w') as log:subprocess.run(['python3',str(ROOT/'ops/crossing_real_footage_capture.py'),'--group','world-failure'],cwd=ROOT,stdout=log,stderr=log,check=True)
save('complete')
