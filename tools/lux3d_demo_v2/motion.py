"""Presentation animation using only retained photographs and recorded video pixels."""
from pathlib import Path
import json
import math
import subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from common import OUT,BASE,save,sha

W,H,FPS=1920,1080,30
TOP,BOTTOM=140,932
HEIGHT=BOTTOM-TOP
BG=(11,20,25)
FONT='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
tl=json.loads((OUT/'timeline.json').read_text())
source=BASE/'BeforeStep-Lux3D-Demo.mp4'
styles={
 'core-pair':('photo_reveal',0,.8),
 'question-rgb':('soft_push',.23,.3),
 'proof-pair':('photo_reveal',0,.8),
 'viewer-ui':('viewer_match',.2,.27),
 'viewer-close':('viewer_match',.23,.33),
 'check-model':('dissolve',.2,.23),
 'check-plot':('soft_push',.2,.27),
 'world-main':('model_world',0,.75),
 'world-grid':('world_grid',0,.7),
 'action-route':('soft_push',.23,.3),
 'compare':('soft_push',.23,.3),
 'back-error':('dissolve',.2,.23),
 'safe-stop':('scene_fade',0,.27),
 'versions-early':('soft_push',.2,.27),
 'versions-later':('carousel',.23,.3),
 'records-pair':('dissolve',.2,.27),
 'ending-card':('dissolve',.23,.3),
}
plan=[]
for previous,part in zip(tl['parts'],tl['parts'][1:]):
    style,before,after=styles[part['id']]
    cut=round(part['start_s']*FPS)
    a=cut-round(before*FPS);b=cut+round(after*FPS)
    plan.append({'incoming':part['id'],'style':style,'cut_frame':cut,'start_frame':a,'end_frame':b,
        'duration_s':(b-a)/FPS,'source_a_frame':a-1,'source_b_frame':b,'content_only':True,
        'captions_kept_from_current_frame':True,'scene_identity_label_kept':style=='scene_fade',
        'chapter_changes':previous['chapter']!=part['chapter']})

def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def get_frame(index):
    path=OUT/'qc'/f'endpoint-{index:04d}.png'
    if not path.exists():
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(index/FPS),'-i',str(source),'-frames:v','1',str(path)],check=True)
    return Image.open(path).convert('RGB')

def layer(canvas,image,x,y,alpha=1):
    if alpha<=0:return
    image=image.convert('RGBA');image.putalpha(round(255*min(1,alpha)))
    canvas.paste(image,(round(x),round(y)),image)

class Animator:
    def __init__(self):
        assert sha(source)=='73258f05fd1ef30ebc30686fd7b35676ea5235547f7650268365c2f9fe383006'
        self.parts=tl['parts'];self.transitions=[]
        for spec in plan:
            a=get_frame(spec['source_a_frame']);b=get_frame(spec['source_b_frame'])
            if spec['source_a_frame']/FPS>=148.033:self.clean_ending(a)
            if spec['source_b_frame']/FPS>=148.033:self.clean_ending(b)
            self.transitions.append((spec,a,b,a.crop((0,TOP,W,BOTTOM)),b.crop((0,TOP,W,BOTTOM))))
        self.photo=Image.open(BASE/'sources/r1-task-5958685-input.jpg').convert('RGB')
        self.model=get_frame(round(41.03*FPS)).crop((530,176,1390,922))
        self.flowfont=ImageFont.truetype(FONT,23)
        self.creditfont=ImageFont.truetype(FONT,20)
        self.captionfont=ImageFont.truetype(FONT,46)
        self.line_ranges=[];x=50
        for label in ['照片','Lux3D 模型','核对','路线预演','行动']:
            width=self.flowfont.getlength(label);self.line_ranges.append((x,x+width));x+=width+self.flowfont.getlength('  →  ')
        save(OUT/'motion-plan.json',{'source_video_sha256':sha(source),'transitions':plan,'total_duration_s':tl['duration_s'],
             'frames':tl['frames'],'new_generated_images':False,'new_physics_runs':0,'new_Lux3D_tasks':0,
             'source_endpoints':'Actual retained video frames; images moved only for editing transitions',
             'original_sentence_starts_and_other_21_timings_preserved':True,'closing_two_sentences_refined':True})

    @staticmethod
    def clean_ending(image):
        draw=ImageDraw.Draw(image);draw.rectangle((60,450,915,585),fill=BG)
        draw.text((77,465),'400+ 次实际使用 Lux3D',font=ImageFont.truetype(FONT,37),fill='#eef3f1')
        draw.text((77,526),'模型用于核对、预演与行动',font=ImageFont.truetype(FONT,30),fill='#a9bbb7')

    def region(self,spec,A,B,current,p):
        e=ease(p);style=spec['style']
        if style=='dissolve':return Image.blend(A,B,e)
        if style=='scene_fade':
            result=Image.blend(Image.new('RGB',(W,HEIGHT),BG),current,e)
            result.paste(current.crop((0,0,W,58)),(0,0))
            return result
        if style=='soft_push':
            first=Image.new('RGB',(W,HEIGHT),BG);second=first.copy()
            size=1-.025*e;img=A.resize((round(W*size),round(HEIGHT*size)),Image.Resampling.BICUBIC)
            first.paste(img,((W-img.width)//2,(HEIGHT-img.height)//2-round(14*e)))
            size=.975+.025*e;img=B.resize((round(W*size),round(HEIGHT*size)),Image.Resampling.BICUBIC)
            second.paste(img,((W-img.width)//2,(HEIGHT-img.height)//2+round(18*(1-e))))
            return Image.blend(first,second,e)
        if style=='carousel':
            result=Image.new('RGB',(W,HEIGHT),BG)
            offset=round(W*e);result.paste(A,(-offset,0));result.paste(B,(W-offset,0))
            ImageDraw.Draw(result).line((W-offset,35,W-offset,HEIGHT-20),fill=(115,202,174),width=2)
            return result
        if style=='photo_reveal':
            context=B.copy();draw=ImageDraw.Draw(context)
            draw.rectangle((137,70,747,680),fill=(20,31,36))
            draw.rectangle((983,63,1813,781),fill=tuple(B.getpixel((986,65))))
            result=Image.blend(A,context,ease(p/.22))
            size=round(910+(610-910)*e)
            x=round(500+(137-500)*e);y=round(-55+(70+55)*e)
            photo=self.photo.resize((size,size),Image.Resampling.LANCZOS)
            opacity=ease(p/.18)
            layer(result,photo,x,y,opacity)
            # Reveal one recorded model viewport; there is no simulated API loading progress.
            right=B.crop((983,63,1813,781));scale=.88+.12*ease((p-.2)/.8)
            image=right.resize((round(right.width*scale),round(right.height*scale)),Image.Resampling.BICUBIC)
            layer(result,image,983+(right.width-image.width)//2,63+(right.height-image.height)//2,ease((p-.2)/.8))
            if p>.5 and p<.98:
                draw=ImageDraw.Draw(result);end=983;start=min(930,x+size+12)
                if start<end:
                    yline=HEIGHT//2;draw.line((start,yline,end,yline),fill='#a4e5ce',width=4)
                    draw.polygon([(end,yline),(end-14,yline-8),(end-14,yline+8)],fill='#a4e5ce')
            return result
        if style=='viewer_match':
            if spec['incoming']=='viewer-ui':
                box_a=(983,63,1813,781);box_b=(290,139,973,729)
            else:
                box_a=(290,139,973,729);box_b=(530,34,1392,779)
            sa=A.crop(box_a);sb=B.crop(box_b)
            first=A.copy();last=B.copy()
            ImageDraw.Draw(first).rectangle(box_a,fill=tuple(sa.getpixel((3,3))))
            ImageDraw.Draw(last).rectangle(box_b,fill=tuple(sb.getpixel((3,3))))
            if spec['incoming']=='viewer-ui':
                ImageDraw.Draw(sa).rectangle((0,sa.height-50,sa.width,sa.height),fill=tuple(sa.getpixel((3,3))))
            result=Image.blend(first,last,e)
            x=round(box_a[0]+(box_b[0]-box_a[0])*e);y=round(box_a[1]+(box_b[1]-box_a[1])*e)
            width=round(sa.width+(sb.width-sa.width)*e);height=round(sa.height+(sb.height-sa.height)*e)
            sprite=Image.blend(sa.resize((width,height),Image.Resampling.BICUBIC),sb.resize((width,height),Image.Resampling.BICUBIC),e)
            result.paste(sprite,(x,y))
            return result
        if style=='model_world':
            result=Image.blend(A,B,ease(min(1,p*1.6)))
            width=round(720+(190-720)*e);height=round(width*self.model.height/self.model.width)
            image=self.model.resize((width,height),Image.Resampling.BICUBIC)
            x=round(985+(1500-985)*e);y=round(25+(410-25)*e)
            opacity=math.sin(math.pi*p)**.7
            ImageDraw.Draw(image).rectangle((0,0,width-1,height-1),outline='#9ddfc5',width=2)
            layer(result,image,x,y,opacity)
            return result
        if style=='world_grid':
            result=B.copy()
            width=round(W+(640-W)*e);height=round(HEIGHT+(264-HEIGHT)*e)
            img=A.resize((width,height),Image.Resampling.BICUBIC)
            layer(result,img,0,round(130*e),1-ease((p-.7)/.3))
            return result
        raise ValueError(style)

    def step(self,index,raw):
        # Only the editing canvas changes. The final caption band always uses the current original frame.
        im=Image.frombytes('RGB',(W,H),raw)
        for spec,first,last,A,B in self.transitions:
            if spec['start_frame']<=index<spec['end_frame']:
                p=(index-spec['start_frame'])/(spec['end_frame']-spec['start_frame']-1)
                region=self.region(spec,A,B,im.crop((0,TOP,W,BOTTOM)),p)
                im.paste(region,(0,TOP))
                if spec['chapter_changes']:
                    current_title=im.crop((0,50,W,104))
                    amount=ease((spec['cut_frame']-index)/max(1,spec['cut_frame']-spec['start_frame'])) if index<spec['cut_frame'] else ease((index-spec['cut_frame'])/max(1,spec['end_frame']-spec['cut_frame']))
                    title=Image.blend(Image.new('RGB',current_title.size,(8,16,20)),current_title,amount)
                    im.paste(title,(0,50))
                break
        current=next((p for p in self.parts if round(p['start_s']*FPS)<=index<round(p['end_s']*FPS)),self.parts[-1])
        phase={'core-robot':0,'core-pair':1,'question-rgb':0,'proof-pair':1,'viewer-ui':1,'viewer-close':1,
               'check-model':2,'check-plot':2,'world-main':3,'world-grid':3,'action-route':4,'compare':4,
               'back-error':2,'safe-stop':2,'versions-early':1,'versions-later':1,'records-pair':1,'ending-card':4}[current['id']]
        x1,x2=self.line_ranges[phase]
        progress=ease((index/FPS-current['start_s'])/.65)
        draw=ImageDraw.Draw(im);draw.line((x1,135,x1+(x2-x1)*progress,135),fill='#9ad9c1',width=3)
        if current['group']=='records':
            draw.rectangle((0,50,W,104),fill=(8,16,20))
            alpha=ease((index/FPS-current['start_s'])/.27)
            color=tuple(round(c*alpha+(1-alpha)*b) for c,b in zip((210,238,229),(8,16,20)))
            draw.text((48,57),'400+ 次实际使用 Lux3D',font=ImageFont.truetype(FONT,38),fill=color)
            draw.rectangle((0,932,W,H),fill=(8,16,20))
            for sentence in tl['captions']:
                t=index/FPS
                if sentence['group']=='records' and sentence['start_s']<=t<sentence['end_s']:
                    text=sentence['text'];assert self.captionfont.getlength(text)<=1650
                    opacity=min(1,(t-sentence['start_s'])/.08,(sentence['end_s']-t)/.08)
                    overlay=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(overlay)
                    box=d.textbbox((0,0),text,font=self.captionfont,stroke_width=2)
                    x=(W-(box[2]-box[0]))/2-box[0];y=H-36-(box[3]-box[1])-box[1]
                    d.text((x,y),text,font=self.captionfont,fill=(255,255,255,round(255*opacity)),stroke_width=2,stroke_fill=(0,0,0,round(255*opacity)))
                    im.paste(overlay,(0,0),overlay)
        if index/FPS>=148.033:self.clean_ending(im)
        if index/FPS>=149:
            draw.rectangle((65,845,910,929),fill=(10,20,24))
            draw.text((77,856),'Music: Fluidscape — Kevin MacLeod (incompetech.com)',font=self.creditfont,fill='#bacfc7')
            draw.text((77,887),'CC BY 4.0 · creativecommons.org/licenses/by/4.0/',font=self.creditfont,fill='#93aaa1')
        return im.tobytes()
