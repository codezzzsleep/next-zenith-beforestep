"""Front observations with real shadow pixels preserved in the generation mask."""
import copy,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from beforestep.observation import images as INPUTS
from experimental.crossing.input_images import rectangular_variants
from experimental.crossing.runtime import OUT,write,sha
from experimental.crossing.scene import DEVELOPMENT_SEEDS
from ops.crossing_observe import observe

REVISION='scene-dev-v7'


def prepare(seed):
    original=OUT/'development/scene-dev-v5'/f'seed-{seed}';folder=OUT/'development'/REVISION/f'seed-{seed}'
    if (folder/'scene.json').exists():return folder
    scene=copy.deepcopy(json.loads((original/'scene.json').read_text()));folder.mkdir(parents=True,exist_ok=True)
    for name in ['threshold','gate-1','gate-2']:shutil.copytree(original/name,folder/name,dirs_exist_ok=True)
    scene.update(revision=REVISION,observation_yaw_deg=0,observation_stop=[1.73,0.],camera_nominal_distance_m=.85,
                 truth_mesh=str(folder/'threshold/truth.obj'))
    if seed==11002:scene['sun']={'elevation_deg':10.,'azimuth_deg':0.}
    scene['spec'].update(name=f'crossing-{REVISION}-{seed}',start=scene['observation_stop'],
                         objects=[{'posed_dir':str(folder/name)} for name in ['threshold','gate-1','gate-2']])
    scene['input_revision']={'source_scene':str(original/'scene.json'),'physical_geometry_changed':False,
                              'rectangular_crop':True,'image_mask':'observed 2-D envelope; actual internal shadow RGB retained'}
    write(folder/'scene.json',scene);return folder


def first_existing_frame(folder):
    out=folder/'observation'
    if (out/'blindness.json').exists():return json.loads((out/'blindness.json').read_text())
    original=OUT/'development/input-front-rect-sun0/seed-11002/observation';shutil.copytree(original,out,dirs_exist_ok=True)
    image=np.asarray(Image.open(out/'rgb_gen.png'));low=np.asarray(Image.open(out/'mask.png'))>127
    # Only observed low-resolution pixels form the image envelope. This does
    # not consult dark target labels, a true mesh, or unseen geometry.
    mask=np.asarray(Image.fromarray(low.astype(np.uint8)*255).resize((image.shape[1],image.shape[0]),Image.Resampling.NEAREST))>127
    state=json.loads((out/'state.json').read_text());box=INPUTS._pixel_box(mask)
    proto=json.loads((ROOT/'config/protocol.json').read_text())
    variants=rectangular_variants(image,mask,box,out/'gen',state['crop_native_px'],proto)
    state.update(crops=variants['variants'],crossing_input_quality=variants['crossing_quality'],
                 input_controls={'rectangular_crops':True,'generation_mask_only':'2-D envelope of observed pixels; shadow RGB retained',
                                 'self_check_mask_unchanged':True})
    write(out/'state.json',state)
    report=json.loads((out/'blindness.json').read_text());report.update(revision=REVISION,
                   crossing_input_quality=variants['crossing_quality'],upload_ok=variants['upload_ok'])
    write(out/'blindness.json',report)
    write(out/'derivation.json',{'source_observation':str(original),'rgb_identical':sha(out/'rgb.png')==sha(original/'rgb.png'),
                                 'depth_identical':sha(out/'depth.npy')==sha(original/'depth.npy'),
                                 'self_check_mask_identical':sha(out/'mask.png')==sha(original/'mask.png'),
                                 'physical_state_identical':sha(out/'physical-state.npz')==sha(original/'physical-state.npz'),
                                 'only_generation_crops_and_image_mask_changed':True,'new_lux_tasks':0})
    return report


if __name__=='__main__':
    rows=[]
    for seed in [11002]+[s for s in DEVELOPMENT_SEEDS if s!=11002]:
        folder=prepare(seed);row=first_existing_frame(folder) if seed==11002 else observe(seed,REVISION,rectangular=True)
        rows.append(row);print(json.dumps({'seed':seed,'quality':row['crossing_input_quality'],'old_height_gate':row['native_ok'] and row['upload_ok']}),flush=True)
    write(ROOT/'evidence/crossing/development-blindness-scene-dev-v7.json',{'new_lux_tasks':0,'scenes':rows})
