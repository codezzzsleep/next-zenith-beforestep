"""Measure the four preregistration-free narrowed fixtures before paid requests."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import write
from ops.crossing_observe import observe

if __name__=='__main__':
    rows=[]
    for seed in [22001,22002,22003,22004]:
        row=observe(seed,'scene-dev-v9',rectangular=True);rows.append(row)
        print(json.dumps({'seed':seed,'quality':row['crossing_input_quality'],'visible_points':row['visible_points']}),flush=True)
    write(ROOT/'evidence/crossing/development-blindness-scene-dev-v9.json',{'scenes':rows,'new_lux_tasks':0})
