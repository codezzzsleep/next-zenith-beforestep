"""Separate the frozen camera's 4cm filter from rear-edge geometry blindness."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import trimesh
from experimental.crossing.scene import generate,track_geometry
from experimental.crossing.runtime import write

if __name__=='__main__':
    observed=json.loads((ROOT/'evidence/crossing/development-blindness.json').read_text())
    rows=[]
    for scene in observed['scenes']:
        truth=generate(scene['seed'],scene['revision']);mesh=trimesh.load(truth['truth_mesh'],force='mesh',process=False)
        matched=track_geometry(mesh,minimum_z=.04)
        rows.append({'seed':scene['seed'],'revision':scene['revision'],'tracks':[
            {'track_y_m':track['track_y_m'],'observed_far_m':track['observed']['far'],
             'true_far_at_4mm_m':track['truth']['far'],'true_far_at_4cm_m':matched['far'][i],
             'unseen_far_above_4cm_m':matched['far'][i]-track['observed']['far'],
             'low_skirt_far_difference_m':track['truth']['far']-matched['far'][i]}
            for i,track in enumerate(scene['tracks'])]})
    report={'schema':'beforestep-crossing-blindness-matched-height/v1','minimum_stone_height_m':.04,
            'purpose':'Diagnostic separates missing low skirt from unseen rear surface above the same observation filter','scenes':rows}
    write(ROOT/'evidence/crossing/development-blindness-matched-height.json',report)
    print(json.dumps(rows))
