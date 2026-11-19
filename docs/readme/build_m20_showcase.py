"""Compose the M20 showcase from retained input, model frames and M20 recordings."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter

PAPER='#f5f2ea';CARD='#fffdfa';NAVY='#0d1522';INK='#1b2433';MUTED='#627086';GOLD='#b77a27'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ffmpeg(*args):subprocess.run(['ffmpeg','-v','error','-y',*map(str,args)],check=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--mother',type=Path,required=True);parser.add_argument('--comparison',type=Path,required=True);parser.add_argument('--hold',type=Path,required=True);parser.add_argument('--fonts',type=Path,required=True);parser.add_argument('--images-only',action='store_true')
    args=parser.parse_args();src=args.source;out=args.out;out.mkdir(parents=True,exist_ok=True)
    expected={'mother':'59df5e64488cac17bab916c8b928cf2e0b258721bc4586ef5f104e67067e900f','comparison':'d8fa30e985fc0f30bd30b78be76e46efadbf56ae63019fab13be7de2a8f7007b','hold':'4721134d7ede8cf879703a8d9888c019455a8680ace02474574cd6ce5b5c59d6'}
    for key in expected:
        assert digest(getattr(args,key))==expected[key],key
    sans=lambda n:ImageFont.truetype(str(args.fonts/'NotoSansCJKsc-Bold.otf'),n)
    serif=lambda n:ImageFont.truetype(str(args.fonts/'NotoSerifCJKsc-Bold.otf'),n)
    boxes=[]
    def label(draw,xy,value,font,fill=INK,width=None):
        box=draw.textbbox(xy,value,font=font,anchor='lt')
        if width is not None:assert box[2]-box[0]<=width,value
        draw.text(xy,value,font=font,fill=fill,anchor='lt');boxes.append({'text':value,'bounds':box});return box
    def frame(seconds,name):
        path=out/(name+'-raw.png');ffmpeg('-ss',seconds,'-i',args.mother,'-frames:v',1,path)
        # Preserve the robot and surrounding terrain; presentation omits the old dock.
        image=Image.open(path).convert('RGB');return image.crop((350,125,1550,800))
    shots={'m20-observe':frame(11.5,'m20-observe'),'m20-drive':frame(290,'m20-drive'),'m20-legs':frame(216.368,'m20-legs')}
    for name,im in shots.items():
        # Keep the robot and terrain together in a 16:9 scene composition.
        im.resize((1600,900),Image.Resampling.LANCZOS).save(out/(name+'.jpg'),quality=93,optimize=True)
    photo=Image.open(src/'site/media/real-footage/r1-task-5958685-input.jpg').convert('RGB').crop((0,80,1536,1280))
    original=Image.open(src/'docs/readme/photo-to-model.gif');models=[]
    for index in range(26,original.n_frames):
        original.seek(index);model=original.convert('RGB').crop((461,96,850,405))
        # The solid viewer background is presentation framing, not mesh geometry.
        rgba=model.convert('RGBA');background=Image.new('RGB',model.size,model.getpixel((0,0)))
        from PIL import ImageChops
        difference=ImageChops.difference(model,background).convert('L').point(lambda n:255 if n>12 else 0)
        rgba.putalpha(difference);models.append(rgba)
    def gif_board(left,model,first):
        im=Image.new('RGB',(1200,660),PAPER);d=ImageDraw.Draw(im)
        label(d,(32,25),'NEXT ZENITH / BEFORESTEP',sans(16),GOLD)
        label(d,(32,63),'看见一面，先想一步。',serif(43))
        label(d,(32,126),'二维观测 → 局部想象 → 预测 → M20 探索',sans(20),MUTED)
        for x in (32,648):d.rounded_rectangle((x,185,x+520,580),radius=14,fill=CARD,outline='#d9d2c5',width=2)
        label(d,(54,207),'山猫 M20 · 观察现场' if first else '机器人原始照片',sans(24),INK,476)
        label(d,(670,207),'Aholo Viewer · 旋转查看背面',sans(24),INK,476)
        d.rounded_rectangle((54,256,530,552),radius=8,fill=NAVY);d.rounded_rectangle((670,256,1146,552),radius=8,fill=NAVY)
        fitted=ImageOps.contain(left,(466,286));im.paste(fitted,(59+(466-fitted.width)//2,261+(286-fitted.height)//2))
        fitted=ImageOps.contain(model,(466,286));im.paste(fitted,(675+(466-fitted.width)//2,261+(286-fitted.height)//2),fitted)
        d.line((568,398,630,398),fill=GOLD,width=4);d.polygon([(630,398),(620,392),(620,404)],fill=GOLD)
        label(d,(38,609),'真实任务 5958685',sans(20),MUTED)
        label(d,(670,609),'Aholo Lux3D · 从一面照片想象完整形状',sans(20),MUTED,490)
        return im
    frames=[]
    for n in range(12):frames.append(gif_board(shots['m20-observe'],models[n%len(models)],True))
    for model in models:frames.append(gif_board(photo,model,False))
    frames[0].save(out/'photo-to-model.gif',save_all=True,append_images=frames[1:],duration=125,loop=0,optimize=False,disposal=2)
    viewer=Image.open(src/'docs/readme/viewer.jpg').convert('RGB')
    versions=Image.open(src/'docs/readme/asset-iterations.png').convert('RGB')
    version_names=['V6 / 观测约束融合','V7 / 双视角核对','V8 / 窄道候选','v0.1 / 模块化预演','v0.2 / 完整通行','v0.3 / 训练控制器']
    def board(width,height,title,subtitle):
        im=Image.new('RGB',(width,height),PAPER);d=ImageDraw.Draw(im);pad=44 if width==1600 else 40
        a=label(d,(pad,30),title,serif(50 if width==1600 else 42),width=width-pad*2)
        b=label(d,(pad,108),subtitle,sans(24 if width==1600 else 26),MUTED,width-pad*2);assert b[1]-a[3]>=16
        d.line((pad,153,width-pad,153),fill='#d9d2c5',width=2);return im,d,pad
    for width,columns,name in [(1600,2,'model-action-desktop.jpg'),(800,1,'model-action-mobile.jpg')]:
        pad=44 if width==1600 else 40;gap=24;cw=(width-2*pad-(columns-1)*gap)//columns;ph=int((cw-36)*9/16);ch=84+ph+25;rows=2//columns
        im,d,pad=board(width,176+rows*ch+(rows-1)*gap+32,'看模型，也看机器人怎样走','局部空间想象，连接山猫 M20 的下一步行动')
        for i,(title,picture) in enumerate([('Aholo Lux3D / 真实模型',viewer),('山猫 M20 / 轮腿行动',shots['m20-legs'])]):
            x=pad+i%columns*(cw+gap);y=176+i//columns*(ch+gap);d.rounded_rectangle((x,y,x+cw,y+ch),radius=14,fill=CARD,outline='#d9d2c5',width=2)
            label(d,(x+20,y+20),title,sans(28 if width==800 else 30),width=cw-40)
            d.rectangle((x+18,y+78,x+cw-18,y+78+ph),fill=NAVY);f=ImageOps.contain(picture,(cw-36,ph));im.paste(f,(x+18+(cw-36-f.width)//2,y+78+(ph-f.height)//2))
        im.save(out/name,quality=93,optimize=True)
    for width,columns,name in [(1600,3,'versions-desktop.png'),(800,2,'versions-mobile.png')]:
        pad=44 if width==1600 else 40;gap=24;cw=(width-2*pad-(columns-1)*gap)//columns;ph=int((cw-36)*326/410);ch=82+ph+22;rows=6//columns
        im,d,pad=board(width,176+rows*ch+(rows-1)*gap+32,'六个版本，从观测到行动','每格上方为模型，下方为对应输入')
        for i,title in enumerate(version_names):
            x=pad+i%columns*(cw+gap);y=176+i//columns*(ch+gap);d.rounded_rectangle((x,y,x+cw,y+ch),radius=14,fill=CARD,outline='#d9d2c5',width=2)
            label(d,(x+20,y+19),title,sans(25 if width==800 else 30),width=cw-40)
            left=47+i%3*468;top=181+i//3*437;pic=versions.crop((left,top,left+410,top+326));pic=ImageOps.contain(pic,(cw-36,ph));im.paste(pic,(x+18,y+78))
        im.save(out/name,optimize=True)
    im,d,pad=board(1600,900,'从空间想象，回到 M20 的行动','观察、预测与轮腿接力，连接同一次月面探索')
    cards=[('观察与判断',shots['m20-observe'],['看清眼前的一面','留下你的第一判断']),('沿路线探索',shots['m20-drive'],['把预测变成行动','驶向青色目标信标']),('轮腿接力',shots['m20-legs'],['高石交给空间想象','矮坎用四腿依次跨越'])]
    for i,(title,picture,copy) in enumerate(cards):
        x=44+i*512;d.rounded_rectangle((x,178,x+488,834),radius=14,fill=CARD,outline='#d9d2c5',width=2)
        label(d,(x+22,207),f'0{i+1} / {title}',sans(30),width=444)
        im.paste(picture.resize((448,252),Image.Resampling.LANCZOS),(x+20,275))
        for j,line in enumerate(copy):label(d,(x+22,575+j*48),line,sans(25),MUTED,width=444)
    im.save(out/'exploration-actions.jpg',quality=93,optimize=True)
    segments=[(args.mother,0,26,1),(args.comparison,16.8,48.1,1),(args.mother,65,87,1),(args.mother,87,141.357,1),(args.mother,181.227,296.25,2.4),(args.mother,296.25,299.666667,1)]
    if not args.images_only:
        parts=[]
        for i,(movie,start,end,speed) in enumerate(segments):
            path=out/f'part-{i}.mp4';ffmpeg('-ss',start,'-to',end,'-i',movie,'-an','-vf',f'setpts=PTS/{speed},scale=1280:720,fps=24','-c:v','libx264','-preset','fast','-crf','21','-threads','2',path);parts.append(path)
        concat=out/'parts.txt';concat.write_text(''.join("file '"+str(p)+"'\n" for p in parts));ffmpeg('-f','concat','-safe','0','-i',concat,'-t','185','-c','copy','-movflags','+faststart',out/'m20-demo.mp4')
        for name,movie,start,end in [('m20-observe.mp4',args.mother,7.5,26.15),('m20-imagine.mp4',args.comparison,16.8,48.1),('m20-predict.mp4',args.mother,65,87),('m20-explore.mp4',args.mother,87,144),('m20-legs.mp4',args.mother,181.227,296.25),('m20-stop.mp4',args.hold,40.403,61.3)]:
            ffmpeg('-ss',start,'-to',end,'-i',movie,'-an','-vf','scale=1280:720,fps=24','-c:v','libx264','-preset','fast','-crf','22','-threads','2','-movflags','+faststart',out/name)
    manifest={'schema':'beforestep-m20-showcase/v1','recordings':expected,'source_photo_sha256':digest(src/'site/media/real-footage/r1-task-5958685-input.jpg'),'model_gif_sha256':digest(src/'docs/readme/photo-to-model.gif'),'input_display_crop':[0,80,1536,1280],'M20_photo_times':{'observe':11.5,'drive':290,'legs':216.368},'model_task':5958685,'video_segments':[{'source':str(v.name),'in':a,'out':b,'speed':s} for v,a,b,s in segments],'new_generation_tasks':0,'text_bounds':boxes,'files':[{'name':p.name,'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.suffix in ['.jpg','.gif','.png','.mp4'] and '-raw' not in p.name and not p.name.startswith('part-')]}
    manifest['scene_display_crop']=[350,125,1550,800]
    (out/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'complete','files':len(manifest['files'])}),flush=True)

if __name__=='__main__':main()
