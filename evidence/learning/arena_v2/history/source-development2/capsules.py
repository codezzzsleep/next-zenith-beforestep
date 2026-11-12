"""Immutable provenance catalog. Missing registrations remain explicit inventory entries."""
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from beforestep import scene as S
from beforestep.navigation import map as N
from beforestep.geometry.admission import admitted
from .common import ROOT,OUT,HELDOUT,METRICS,read,write,sha,finite,rigid,transform_points


def build(out=OUT/'capsules.json'):
    gallery=read(ROOT/'site/data/gallery.json')['models']
    sources=[]
    for m in gallery:
        contexts=m['contexts']; selected=None
        for c in contexts:
            p=ROOT/c.get('original_source',c['source_decision'])
            ob=p.parent.parent
            if (ob/'state.json').exists():selected=(c,p,ob);break
        if selected:
            c,p,ob=selected
            sources.append({'task_id':m['task_id'],'glb':c['metrics']['glb'],
                            'source':c['source_decision'],'decision':str(p.relative_to(ROOT)),
                            'observation':str(ob.relative_to(ROOT)),'scene':c['scene'],
                            'candidate':c['metrics'],'catalog':'gallery_306'})
        else:
            c=contexts[0]
            sources.append({'task_id':m['task_id'],'glb':c['metrics']['glb'],
                            'source':c['source_decision'],'scene':c['scene'],
                            'candidate':c['metrics'],'catalog':'gallery_306',
                            'unavailable_reason':'Historical result has no preserved v8 camera/target-state registration context'})
    c7=ROOT/'outputs/award/demo/suite_r2_v4_F0_006/imagination/imagination'
    for p in sorted(c7.glob('looks/look*/T*/decide/target_decision.json')):
        for c in read(p)['candidates']:
            sources.append({'task_id':int(Path(c['glb']).parent.name),'glb':c['glb'],
                            'source':str(p.relative_to(ROOT)),'decision':str(p.relative_to(ROOT)),
                            'observation':str(p.parent.parent.relative_to(ROOT)),
                            'scene':'suite_r2_v4_F0_006','candidate':c,'catalog':'C7'})
    assert len({s['task_id'] for s in sources if s['catalog']=='gallery_306'})==306
    grouped=defaultdict(list);inventory=[]
    for s in sources:
        c=s['candidate'];glb=Path(s['glb'])
        if not glb.exists():glb=ROOT/'assets/candidates'/str(s['task_id'])/'tex_mesh.glb'
        assert glb.exists(),s['task_id']
        s['glb']=str(glb.relative_to(ROOT));s['glb_sha256']=sha(glb)
        s['source_sha256']=sha(ROOT/s['source'])
        available=bool(c.get('M') is not None and s.get('observation'))
        inventory.append({k:s[k] for k in ['task_id','glb','glb_sha256','source','source_sha256','scene','catalog']}
                         | {'registration_available':available,'unavailable_reason':s.get('unavailable_reason',None)})
        grouped[s.get('observation','historical/'+s['scene'])].append(s)
    capsules=[]
    for index,(obrel,ss) in enumerate(sorted(grouped.items())):
        row={'id':f'C{index:03d}','scene':ss[0]['scene'],'observation':obrel,
             'split':'heldout' if ss[0]['scene'] in HELDOUT else 'training_side',
             'candidates':[],'eligible':False}
        if not obrel.startswith('historical/'):
            ob=ROOT/obrel;state=read(ob/'state.json');frame=state['local_frame']
            run=ob.parents[1];scene_path=run/'scene.json'
            if not scene_path.exists():
                name='stress_v8' if row['scene']=='stress_v8_history' else row['scene']
                scene_path=ROOT/'config/scenes'/f'{name}.json'
            definition=read(scene_path)
            cam_path=ob/'camera_world.json';camera=read(cam_path) if cam_path.exists() else None
            row.update(source_look=state['look'],local_frame=frame,
                       robot_qpos_world=state['robot_qpos_world'],camera_world=camera,
                       source_scene=definition,source_scene_path=str(scene_path.relative_to(ROOT)),
                       observation_state_sha256=sha(ob/'state.json'))
            cells=np.load(ob/'cells.npy'); points=np.column_stack([N.GX[cells],N.GY[cells]])
            # Target labels come from visible components, never assume T1=A.
            rocks={}
            for key,p in definition['rocks'].items():
                distance=np.linalg.norm(points-[p['x'],p['y']],axis=1).min() if len(points) else np.inf
                if distance<max(1.0,p['height']*2.5): rocks[key]=p
            if not rocks:
                key=min(definition['rocks'],key=lambda k:np.linalg.norm(points.mean(0)-[definition['rocks'][k]['x'],definition['rocks'][k]['y']]))
                rocks={key:definition['rocks'][key]}
            row['truth_rocks']=rocks
            row['background_rocks']={k:p for k,p in definition['rocks'].items() if k not in rocks}
            row['visible_cells_world_xy']=points.tolist()
            row['eligible']=camera is not None
        for s in ss:
            c=s['candidate'];candidate={k:s[k] for k in ['task_id','glb','glb_sha256','source','source_sha256','catalog']}
            candidate.update(sample=c.get('id'),metrics={k:c.get(k) for k in METRICS},
                             original_admitted=c['admitted'],frozen_admitted=admitted(c),
                             local_from_generated=c.get('M'),registration_available=c.get('M') is not None)
            if s.get('observation') and c.get('M') is not None:
                frame=row['local_frame'];T=rigid(np.degrees(frame['yaw0']),[frame['x0'],frame['y0']])
                candidate['world_from_generated']=(T@np.asarray(c['M'])).tolist()
                fp=ROOT/s['observation']/'decide'/f"footprint_{c['id']}.npy"
                if fp.exists():
                    mask=np.load(fp);candidate['footprint_world_xy']=np.column_stack([N.GX[mask],N.GY[mask]]).tolist()
                    candidate['footprint_source']=str(fp.relative_to(ROOT));candidate['footprint_sha256']=sha(fp)
                else:candidate['footprint_world_xy']=[]
            row['candidates'].append(candidate)
        row['eligible'] &= any(c['registration_available'] and c.get('footprint_world_xy') for c in row['candidates'])
        capsules.append(row)
    asset_counts={}
    for side in ['training_side','heldout']:
        asset_counts[side]=dict(Counter(p['rock'] for c in capsules if c['split']==side for p in c.get('truth_rocks',{}).values()))
    result={'schema':'beforestep-arena-capsules/v2','scope':'Existing real Lux outputs transplanted to nearby viewing geometry; no new image generation',
            'inventory':inventory,'capsules':capsules,'heldout_scenes':sorted(HELDOUT),
            'asset_distribution':asset_counts,'asset_holdout':'Layouts, poses and real Lux results are held out; asset kinds overlap. No asset exclusion chosen before prechecks.',
            'stats':{'gallery_results':306,'C7_results':sum(s['catalog']=='C7' for s in sources),
                     'gallery_primary_registered':sum(m['contexts'][0]['metrics'].get('M') is not None for m in gallery),
                     'gallery_registered':sum(i['registration_available'] for i in inventory if i['catalog']=='gallery_306'),
                     'capsules':len(capsules),'eligible':sum(c['eligible'] for c in capsules),
                     'heldout_eligible':sum(c['eligible'] and c['split']=='heldout' for c in capsules)}}
    write(out,finite(result));return result


def transplant(capsule, yaw_deg, translation):
    T=rigid(yaw_deg,translation);row=read_copy(capsule)
    row['transplant_world_from_source']=T.tolist()
    row['camera_world']['world_pos']=transform_points([row['camera_world']['world_pos']],T)[0].tolist()
    row['camera_world']['R_world_from_camera']=(T[:3,:3]@np.asarray(row['camera_world']['R_world_from_camera'])).tolist()
    for c in row['candidates']:
        if c['registration_available']:
            c['world_from_generated']=(T@np.asarray(c['world_from_generated'])).tolist()
            xy=np.asarray(c['footprint_world_xy']).reshape(-1,2)
            c['footprint_world_xy']=transform_points(np.column_stack([xy,np.zeros(len(xy))]),T)[:,:2].tolist()
    for p in [*row['truth_rocks'].values(),*row.get('background_rocks',{}).values()]:
        q=transform_points([[p['x'],p['y'],0]],T)[0];p['x'],p['y']=float(q[0]),float(q[1]);p['yaw']+=yaw_deg
    frame=row['local_frame'];q=transform_points([[frame['x0'],frame['y0'],0]],T)[0]
    row['local_frame']={'x0':float(q[0]),'y0':float(q[1]),'yaw0':frame['yaw0']+np.radians(yaw_deg)}
    row['sun']=dict(row['source_scene'].get('sun',{'elevation_deg':10.,'azimuth_deg':35.}))
    # Scene's azimuth uses negative mathematical yaw.
    row['sun']['azimuth_deg']-=yaw_deg
    row['deviations']={'camera_distance_ratio':1.,'view_azimuth_deviation_deg':0.,'sun_relative_azimuth_deviation_deg':0.}
    return row


def read_copy(value):
    import copy
    return copy.deepcopy(value)

if __name__=='__main__': print(build()['stats'])
