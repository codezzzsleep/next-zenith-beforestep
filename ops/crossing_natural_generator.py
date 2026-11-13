"""Zero-paid fixture range calibration with smaller overlap beyond the real gate."""
import copy,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from experimental.crossing import scene as SCENE
from experimental.crossing.runtime import OUT,write,sha

REVISION='scene-dev-v9'
SEEDS=[22001,22002,22003,22004]
PARAMETERS={**copy.deepcopy(SCENE.GENERATOR),'revision':REVISION,'height_m':[.14,.15],
            'width_m':[1.10,1.20],'gap_m':[.90,1.00],'shallow_depth_m':[.10,.15],
            'deep_depth_m':[.22,.30],'observation_yaw_deg':-25.,'camera_to_target_xy_m':.85}


if __name__=='__main__':
    SCENE.GENERATOR=PARAMETERS
    SCENE.SOURCE_ROCKS=['moon_rock_03','rock_07']
    rows=[]
    for seed in SEEDS:
        folder=OUT/'development'/REVISION/f'seed-{seed}'
        if (folder/'generator-source/registration.json').exists():scene=json.loads((folder/'scene.json').read_text())
        else:
            scene=SCENE.generate(seed,REVISION);theta=np.deg2rad(25.)
            camera=np.array([3.-.85*np.cos(theta),.85*np.sin(theta)])
            scene['observation_stop']=(camera-.42*np.array([np.cos(theta),-np.sin(theta)])).tolist()
            scene['camera_nominal_distance_m']=float(.85*np.cos(theta));scene['camera_to_target_center_xy_m']=.85
            scene['spec']['start']=scene['observation_stop'];scene['observation_yaw_deg']=-25.
            scene['generator_calibration']={'source_version':'v9-narrower-overlap','raw_source_models':SCENE.SOURCE_ROCKS,
                                           'reason':'Previous width exceeded the nominal gate by 0.3-0.6m; reduce stretch while still covering both gate edges.',
                                           'not_preregistered':True,'new_lux_tasks':0}
            write(folder/'scene.json',scene)
            source=folder/'generator-source';source.mkdir(exist_ok=True)
            shutil.copyfile(Path(__file__),source/Path(__file__).name)
            write(source/'registration.json',{'source_sha256':sha(Path(__file__)),'parameters':PARAMETERS,'seeds':SEEDS,
                                              'source_models':SCENE.SOURCE_ROCKS,'new_lux_tasks':0})
        rows.append({'seed':seed,'dimensions_m':scene['dimensions_m'],'gap_m':scene['gap_m'],
                     'overlap_m':scene['dimensions_m']['width']-scene['gap_m'],
                     'ridge_min_high_m':scene['ridge_min_high_m'],'truth_geometry':scene['truth_geometry']})
        print(json.dumps(rows[-1]),flush=True)
    write(ROOT/'evidence/crossing/diagnosis-generator-v9.json',{'parameters':PARAMETERS,'candidates':rows,'new_lux_tasks':0})
