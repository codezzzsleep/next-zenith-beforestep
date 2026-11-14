"""Decode the delivered film and export caption/scene samples for visual review."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent/'showcase-real-footage'
OUT=WORK/'qc/film';OUT.mkdir(parents=True,exist_ok=True)
VIDEO=ROOT/'site/media/demo-v3.mp4'
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,codec_type,width,height,nb_frames,r_frame_rate','-of','json',str(VIDEO)],text=True))
assert len(meta['streams'])==1
v=meta['streams'][0]
assert (v['codec_name'],v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==('h264',1920,1080,'30/1',4500)
assert float(meta['format']['duration'])==150
decoded=subprocess.run(['ffmpeg','-hide_banner','-nostats','-v','info','-threads','1','-i',str(VIDEO),'-vf','blackdetect=d=0.1:pix_th=0.05:pic_th=0.999','-an','-f','null','-'],capture_output=True,text=True)
(OUT/'full-decode.log').write_text(decoded.stderr)
assert decoded.returncode==0,decoded.stderr[-1000:]
assert 'frame= 4500' in decoded.stderr or 'frame=4500' in decoded.stderr
assert not any(x in decoded.stderr.lower() for x in ['error while decoding','corrupt decoded frame','invalid nal unit'])
black=[x for x in decoded.stderr.splitlines() if 'black_start:' in x]
assert not black,black
times=[4,12,22,35,44,51,61,69,74,84,94,100,105,112,122,131,137,147]
font=ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',23)
for n in range(0,len(times),6):
 sheet=Image.new('RGB',(1440,1284),(8,12,18));d=ImageDraw.Draw(sheet)
 for j,t in enumerate(times[n:n+6]):
  p=OUT/f'{t:03d}.jpg';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(VIDEO),'-frames:v','1','-q:v','2',str(p)],check=True)
  im=Image.open(p);im.thumbnail((720,405));xy=((j%2)*720,(j//2)*428);sheet.paste(im,xy);d.text((xy[0]+8,xy[1]+404),f'{t} 秒',font=font,fill=(170,190,215))
 sheet.save(OUT/f'contact-{n//6+1}.jpg',quality=94)
result={'automated_passed':True,'visual_review':'pending','metadata':meta,'full_decode_frames':4500,'black_intervals':black,'samples_s':times,'audio':False,'sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest()}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('FILM DECODE AND 18 CAPTION SAMPLES PASSED',flush=True)
