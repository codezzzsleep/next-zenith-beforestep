"""Continue the authorised capture queue without starting any experiment."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'showcase-real-footage'
def save(status,group):
 p=WORK/'supervisor.json';p.write_text(json.dumps({'status':status,'group':group,'pid':os.getpid(),'new_experiments':0},indent=2))
save('waiting_worlds','worlds')
while True:
 p=WORK/'worker-worlds.json'
 if p.exists() and json.loads(p.read_text()).get('status')=='complete':break
 time.sleep(3)
for group in ('holdouts','routes'):
 save('recording',group)
 with (WORK/f'{group}.log').open('w') as stream:
  subprocess.run([sys.executable,'ops/crossing_showcase_capture.py','--group',group],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
save('complete','all')
