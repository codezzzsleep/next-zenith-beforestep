"""Build presentation assets from the owner's V5 Beta cover and retained visuals."""
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf
from PIL import Image, ImageDraw, ImageFont, ImageOps

PDF_SHA='fe2ff9b9356202760254cc29deadfa1e963986d69c7c0f1ee39b9ab0764d1cb7'
CROP=(620,225,2156,1089)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--pdf',type=Path,required=True);p.add_argument('--fonts',type=Path,required=True);args=p.parse_args()
    assert sha(args.pdf)==PDF_SHA
    repo=args.repo;out=repo/'docs/readme/m20-bright-20261119';site=repo/'site/media/v5beta-bright-20261119';out.mkdir(parents=True,exist_ok=True);site.mkdir(parents=True,exist_ok=True)
    with pymupdf.open(args.pdf) as document:
        image=max((b for b in document[0].get_text('dict')['blocks'] if b['type']==1),key=lambda b:b['width']*b['height'])
    raw=out/'cover-source.jpeg';raw.write_bytes(image['image']);picture=Image.open(raw).convert('RGB');scene=picture.crop(CROP)
    scene.resize((1600,900),Image.Resampling.LANCZOS).save(out/'m20-exploration.jpg',quality=93,optimize=True)
    (site/'m20-exploration.jpg').write_bytes((out/'m20-exploration.jpg').read_bytes())
    (site/'03-exploration-actions.jpg').write_bytes((out/'m20-exploration.jpg').read_bytes())
    original=Image.open(repo/'docs/readme/m20-showcase/photo-to-model.gif');frames=[]
    font=lambda size:ImageFont.truetype(str(args.fonts/'NotoSansCJKsc-Bold.otf'),size)
    for index in range(original.n_frames):
        original.seek(index);frame=original.convert('RGB').copy()
        if index<12:
            draw=ImageDraw.Draw(frame);draw.rectangle((52,198,537,243),fill='#fffdfa');draw.text((54,207),'山猫 M20 · 月面探索',font=font(24),fill='#1b2433',anchor='lt')
            draw.rounded_rectangle((54,256,530,552),radius=8,fill='#0d1522');fit=ImageOps.contain(scene,(466,286));frame.paste(fit,(59+(466-fit.width)//2,261+(286-fit.height)//2))
        frames.append(frame)
    frames[0].save(out/'photo-to-model.gif',save_all=True,append_images=frames[1:],duration=125,loop=0,optimize=False,disposal=2)
    for name,x,y,w,h,title_y,size in [('model-action-desktop.jpg',830,254,708,398,196,30),('model-action-mobile.jpg',58,771,684,384,713,28)]:
        board=Image.open(repo/'docs/readme/m20-showcase'/name).convert('RGB');draw=ImageDraw.Draw(board)
        draw.rectangle((x,title_y,x+w,title_y+43),fill='#fffdfa');draw.text((x+2,title_y),'山猫 M20 / 月面探索',font=font(size),fill='#1b2433',anchor='lt')
        draw.rectangle((x,y,x+w-1,y+h-1),fill='#0d1522');fit=ImageOps.contain(scene,(w,h));board.paste(fit,(x+(w-fit.width)//2,y+(h-fit.height)//2));board.save(out/name,quality=93,optimize=True)
    # The original twelve-world geometry and results stay intact. This LUT only
    # lifts display shadows in a separate presentation image.
    grid=Image.open(repo/'site/media/m20-showcase/02-twelve-world-rehearsals.jpg').convert('RGB');gamma=.68;lut=[round(255*(i/255)**gamma) for i in range(256)];grid.point(lut*3).save(site/'02-twelve-world-rehearsals.jpg',quality=93,optimize=True)
    source_paths=['docs/readme/m20-showcase/photo-to-model.gif','docs/readme/m20-showcase/model-action-desktop.jpg','docs/readme/m20-showcase/model-action-mobile.jpg','site/media/m20-showcase/02-twelve-world-rehearsals.jpg']
    files=[]
    for folder in [out,site]:
        for f in sorted(folder.iterdir()):
            if f.suffix not in ['.jpg','.jpeg','.gif']:continue
            im=Image.open(f);files.append({'path':str(f.relative_to(repo)),'sha256':sha(f),'bytes':f.stat().st_size,'width':im.width,'height':im.height})
    manifest={'schema':'beforestep-v5beta-bright-visuals/v1','owner_pdf':{'path':'reports/先见一步_项目报告书_v5_beta.pdf','sha256':PDF_SHA,'upload_commit':'33d7dfe1ce1a43c5ea6cc3f72f8b2ec5fb509511'},'cover_inline_image':{'sha256':sha(raw),'size':[picture.width,picture.height],'display_crop':list(CROP)},'retained_sources':[{'path':rel,'sha256':sha(repo/rel)} for rel in source_paths],'gif_frames':len(frames),'gif_updated_frames':list(range(12)),'twelve_world_display_gamma':gamma,'scope':'Use the actual brighter cover capture for robot pictures. Only the separate twelve-world presentation image has display shadow adjustment; source images, inputs, GLBs, dynamics and results remain unchanged.','new_generation_tasks':0,'files':files}
    (out/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(site/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'files':len(files),'pdf_sha256':PDF_SHA,'gif_frames':len(frames)}))

if __name__=='__main__':main()
