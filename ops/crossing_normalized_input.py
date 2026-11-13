"""Rotate real input pixels only; reuse identical observed state and baseline trials."""
import copy,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from beforestep.observation import images as INPUTS
from experimental.crossing.input_images import rectangular_variants
from experimental.crossing.runtime import OUT,write,sha
from experimental.crossing.scene import DEVELOPMENT_SEEDS

REVISION='scene-dev-v8'
FILES=['rgb.png','rgb_gen.png','depth.npy','mask.png','dark.png','visible_points.npy','visible_points_world.npy',
       'state.json','camera_world.json','observation.json','physical-state.npz','blindness.json','identity.json']


def prepare(seed):
    original=OUT/'development/scene-dev-v6'/f'seed-{seed}';folder=OUT/'development'/REVISION/f'seed-{seed}'
    if (folder/'observation/derivation.json').exists():return json.loads((folder/'observation/blindness.json').read_text())
    scene=copy.deepcopy(json.loads((original/'scene.json').read_text()));folder.mkdir(parents=True,exist_ok=True)
    for name in ['threshold','gate-1','gate-2']:shutil.copytree(original/name,folder/name,dirs_exist_ok=True)
    scene['revision']=REVISION;scene['truth_mesh']=str(folder/'threshold/truth.obj')
    scene['spec'].update(name=f'crossing-{REVISION}-{seed}',objects=[{'posed_dir':str(folder/name)} for name in ['threshold','gate-1','gate-2']])
    scene['input_revision']={'source_scene':str(original/'scene.json'),'physical_state_and_geometry_unchanged':True,
                              'input_only':'real 2-D pixel rotation and rectangular crop; shadow RGB retained'}
    write(folder/'scene.json',scene);out=folder/'observation';out.mkdir(parents=True,exist_ok=True)
    for name in FILES:shutil.copyfile(original/'observation'/name,out/name)
    image=Image.open(out/'rgb_gen.png').convert('RGB');low=Image.open(out/'mask.png').convert('L')
    mask_image=low.resize(image.size,Image.Resampling.NEAREST);mask=np.asarray(mask_image)>127
    ys,xs=np.nonzero(mask);points=np.column_stack([xs,ys]).astype(float)
    _,vectors=np.linalg.eigh(np.cov(points.T));axis=vectors[:,-1]
    if axis[0]<0:axis=-axis
    angle=float(np.degrees(np.arctan2(axis[1],axis[0])))
    rotated=image.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True,fillcolor=(232,232,232))
    rotated_mask=mask_image.rotate(angle,resample=Image.Resampling.NEAREST,expand=True,fillcolor=0)
    valid=Image.new('L',image.size,255).rotate(angle,resample=Image.Resampling.NEAREST,expand=True,fillcolor=0)
    rm=np.asarray(rotated_mask)>127;box=INPUTS._pixel_box(rm);height=box[3]-box[1]+1
    variants=rectangular_variants(np.asarray(rotated),rm,box,out/'gen',height,json.loads((ROOT/'config/protocol.json').read_text()))
    validity=np.asarray(valid)>127
    for sample in variants['variants'].values():
        x0,y0,x1,y1=sample['crop_box']
        assert validity[y0:y1,x0:x1].all(),'Synthetic rotation corners must not enter an upload'
    state=json.loads((out/'state.json').read_text())
    state.update(crops=variants['variants'],crossing_input_quality=variants['crossing_quality'],
                 input_controls={'rotation_deg':angle,'rotation_basis':'PCA of observed 2-D target pixels only',
                                 'rotation_resampling':'bicubic RGB / nearest mask','no_rotation_padding_in_uploads':True,
                                 'image_mask':'2-D observed envelope; original shadows kept','depth_and_self_check_mask_changed':False})
    write(out/'state.json',state)
    report=json.loads((out/'blindness.json').read_text());report.update(revision=REVISION,
                   crossing_input_quality=variants['crossing_quality'],upload_ok=variants['upload_ok'])
    write(out/'blindness.json',report)
    inheritance=[]
    for old in (original/'validity').glob('*/result.json'):
        result=json.loads(old.read_text());result['inherited_without_rerun_from']=str(old.relative_to(ROOT))
        destination=folder/'validity'/old.parent.name/'result.json';write(destination,result);inheritance.append(str(old.relative_to(ROOT)))
    for source,target in [(original/'truth-v72-v1/result.json',folder/'truth-v72-v1/result.json'),
                          (original/'method-B-v1/result.json',folder/'method-B-v1/result.json')]:
        if source.exists():
            result=json.loads(source.read_text());result['inherited_without_rerun_from']=str(source.relative_to(ROOT));write(target,result)
    write(out/'derivation.json',{'source_observation':str(original/'observation'),'rotation_deg':angle,
          'raw_rgb_identical':sha(out/'rgb.png')==sha(original/'observation/rgb.png'),
          'depth_identical':sha(out/'depth.npy')==sha(original/'observation/depth.npy'),
          'self_check_mask_identical':sha(out/'mask.png')==sha(original/'observation/mask.png'),
          'physical_state_identical':sha(out/'physical-state.npz')==sha(original/'observation/physical-state.npz'),
          'geometry_sha_identical':all(sha(folder/n/'truth.obj')==sha(original/n/'truth.obj') for n in ['threshold','gate-1','gate-2']),
          'inherited_validity_trials':inheritance,'new_physics_runs':0,'new_lux_tasks':0,'no_padding_in_uploads':True})
    return report


if __name__=='__main__':
    rows=[]
    for seed in [11002]+[s for s in DEVELOPMENT_SEEDS if s!=11002]:
        row=prepare(seed);rows.append(row);print(json.dumps({'seed':seed,'quality':row['crossing_input_quality']}),flush=True)
    write(ROOT/'evidence/crossing/development-blindness-scene-dev-v8.json',{'scenes':rows,'new_lux_tasks':0})
