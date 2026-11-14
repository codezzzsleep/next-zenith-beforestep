"""Check original joint rows, model/input identities, film decoding and captions."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'real-footage-180';sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
out=WORK/'qc/film';out.mkdir(parents=True,exist_ok=True)
delivery=read(WORK/'delivery.json');video=ROOT/'site'/delivery['path'];assert sha(video)==delivery['sha256']
meta=delivery['metadata'];assert len(meta['streams'])==1;v=meta['streams'][0]
assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',5400);assert float(meta['format']['duration'])==180
capture_checks=[]
for path in sorted((WORK/'captures').glob('*.json')):
 d=read(path);assert d['status']=='complete';p=ROOT/d['source'];assert sha(p)==d['source_sha256'];a=np.load(p);assert a['qpos'].shape[1]==23
 assert d['exact_saved_qpos'] and d['physics_advanced'] is False
 assert d['display_transform_verification']['passed'] and d['display_transform_verification']['maximum_transform_error']==0
 for f in d['frame_map']:assert abs(float(a['t'][f['source_row']])-f['saved_sim_s'])<1e-10
 assert sha(ROOT/'site'/d['path'])==d['sha256']
 for item in d.get('candidate_meshes',[]):assert sha(ROOT/item['path'])==item['sha256']
 for item in d.get('additional_sources',[]):assert sha(ROOT/item['path'])==item['sha256']
 capture_checks.append({'id':d['id'],'source_sha256':d['source_sha256'],'frames':len(d['frame_map']),'full_qpos_dimensions':23,'original_time_range':d['source_time_range_s']})
start_poses=[];clocks=[]
for name,end in [('optimistic',80.866),('conservative',142.2),('imagination',112.84)]:
 d=read(WORK/f'captures/r1-synchronised-{name}.json');a=np.load(ROOT/d['source']);start_poses.append(a['qpos'][0]);clocks.append([f['requested_sim_s'] for f in d['frame_map']]);assert abs(d['source_time_range_s'][-1]-end)<1e-8
 assert d['frame_map'][-1]['source_row']==len(a['t'])-1
assert all(np.allclose(q,start_poses[0],atol=1e-10) for q in start_poses)
assert clocks[0]==clocks[1]==clocks[2]
clock=delivery['shared_r1_clock'];assert clock['final_original_terminal_hold_s']==2 and clock['output_knots_s'][-2:]==[40,42]
eye=read(WORK/'captures/r1-first-person.json');assert eye['original_camera_position_error_m']==0 and eye['original_camera_fovy_deg']==70
tail=read(WORK/'captures/r1-tail.json');assert abs(tail['source_time_range_s'][-1]-112.84)<1e-8 and tail['source_time_range_s'][0]==98
failure=read(WORK/'captures/f3-004-contact.json');assert abs(failure['source_time_range_s'][-1]-82.14)<1e-8 and 82.14-failure['source_time_range_s'][0]>=5
screen=read(WORK/'screen.json')
for pair in screen['pairs']:
 assert sha(ROOT/pair['input_source'])==pair['input_sha256'];assert sha(ROOT/pair['glb_source'])==pair['glb_sha256'];assert sha(ROOT/'site'/pair['glb'])==pair['glb_sha256'];assert pair['original_download_glb_member_verified']
manifest=read(ROOT/'site/data/real-footage-180.json');assert len(manifest['chapters'])==8 and sum(c['duration_s'] for c in manifest['chapters'])==180
for c in manifest['chapters']:
 assert sha(ROOT/'site'/c['clean_video'])==c['clean_sha256'];assert sha(ROOT/'site'/c['poster'])==c['poster_sha256']
 for s in c['sources']:assert sha(ROOT/'site'/s['record'])==s['record_sha256']
decoded=subprocess.run(['ffmpeg','-hide_banner','-nostats','-v','info','-threads','1','-i',str(video),'-vf','blackdetect=d=0.1:pix_th=0.05:pic_th=0.999','-an','-f','null','-'],capture_output=True,text=True);(out/'full-decode.log').write_text(decoded.stderr);assert decoded.returncode==0
assert 'frame= 5400' in decoded.stderr or 'frame=5400' in decoded.stderr
assert not any(x in decoded.stderr.lower() for x in ['black_start:','error while decoding','corrupt decoded frame'])
times=[1,9,18,26,34,38,43,49,57,68,83,95,102,110,125,137,146,149,154,161,169,177,179]
font=ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',23)
for n in range(0,len(times),6):
 sheet=Image.new('RGB',(1440,1284),(8,12,18));draw=ImageDraw.Draw(sheet)
 for j,t in enumerate(times[n:n+6]):
  p=out/f'{t:03d}.jpg';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(p)],check=True);im=Image.open(p);im.thumbnail((720,405));xy=((j%2)*720,(j//2)*428);sheet.paste(im,xy);draw.text((xy[0]+8,xy[1]+405),f'{t} 秒',font=font,fill=(180,200,215))
 sheet.save(out/f'contact-{n//6+1}.jpg',quality=94)
result={'passed':True,'film_sha256':delivery['sha256'],'duration_s':180,'decoded_frames':5400,'black_intervals':[],'captures':capture_checks,'original_r1_common_start_and_clock':True,'original_first_eye_camera_matched':True,'continuous_r1_tail_includes_arrival':True,'f3_original_contact_and_termination_retained':True,'raw_GLBS_and_actual_inputs_verified':True,'caption_samples':times,'visual_review':'pending','new_physics_runs':0,'new_generation_tasks':0}
(WORK/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('180 SECOND SOURCE AND COMPLETE DECODE AUDIT PASSED',flush=True)
