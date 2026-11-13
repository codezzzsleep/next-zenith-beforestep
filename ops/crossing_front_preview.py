"""Actual front-camera rectangular inputs, retaining both tested sunlight cases."""
import copy,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experimental.crossing.runtime import OUT,write
from ops.crossing_observe import observe


if __name__=='__main__':
    original=OUT/'development/scene-dev-v5/seed-11002';base=json.loads((original/'scene.json').read_text());rows=[]
    for azimuth in [0,180]:
        revision=f'input-front-rect-sun{azimuth}';folder=OUT/'development'/revision/'seed-11002'
        if not (folder/'scene.json').exists():
            scene=copy.deepcopy(base);folder.mkdir(parents=True,exist_ok=True)
            for name in ['threshold','gate-1','gate-2']:shutil.copytree(original/name,folder/name,dirs_exist_ok=True)
            scene.update(revision=revision,observation_yaw_deg=0,observation_stop=[1.73,0.],camera_nominal_distance_m=.85,
                         truth_mesh=str(folder/'threshold/truth.obj'),sun={'elevation_deg':10.,'azimuth_deg':float(azimuth)})
            scene['spec'].update(name=f'crossing-{revision}-11002',start=scene['observation_stop'],
                                 objects=[{'posed_dir':str(folder/name)} for name in ['threshold','gate-1','gate-2']])
            scene['input_revision']={'physical_mesh_changed':False,'rectangular_crops':True,'source_scene':str(original/'scene.json')}
            write(folder/'scene.json',scene)
        report=observe(11002,revision,rectangular=True);rows.append(report)
        print(json.dumps({'revision':revision,'visible_points':report['visible_points'],'quality':report['crossing_input_quality']}),flush=True)
    write(ROOT/'evidence/crossing/diagnosis-front-previews-v1.json',{'new_lux_tasks':0,'scenes':rows})
