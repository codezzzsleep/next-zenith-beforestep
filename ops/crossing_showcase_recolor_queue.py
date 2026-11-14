"""Retain the first colour study and film that same saved world in the final palette."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'showcase-real-footage';OUT=ROOT/'site/media/footage'
def save(s):(WORK/'recolor-queue.json').write_text(json.dumps({'status':s,'pid':os.getpid(),'new_experiments':0},indent=2))
save('waiting_rejection_capture')
while True:
 p=WORK/'rejection-queue.json'
 if p.exists() and json.loads(p.read_text()).get('status')=='complete':break
 time.sleep(3)
archive=WORK/'history/world00-first-colour-study'
if not archive.exists():
 archive.mkdir(parents=True)
 for p in [OUT/'world-00.mp4',OUT/'world-00.jpg',WORK/'clips/world-00.json']:shutil.copy2(p,archive/p.name)
 (WORK/'clips/world-00.json').unlink()
save('recording_same_world_final_display_materials')
with (WORK/'recolor.log').open('w') as log:subprocess.run([sys.executable,'ops/crossing_showcase_capture.py','--group','worlds'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
save('complete')
