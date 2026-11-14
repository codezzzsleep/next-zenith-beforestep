"""Add a credited music bed and gentle transition sounds below retained speech."""
from pathlib import Path
import json
import math
import os
import subprocess
import wave
import numpy as np
from common import OUT,BASE,save,sha,now

SR=48000
tl=json.loads((OUT/'timeline.json').read_text())
N=round(tl['duration_s']*SR)
job={'status':'running','pid':os.getpid(),'started_utc':now(),'new_TTS_requests':0}
save(OUT/'audio-job.json',job)

def command(args,name):
    with (OUT/'logs'/name).open('w') as f:subprocess.run(args,stdout=f,stderr=f,check=True)

def read(path):
    with wave.open(str(path),'rb') as f:
        assert f.getsampwidth()==2 and f.getframerate()==SR
        channels=f.getnchannels();a=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').reshape(-1,channels).astype(np.float32)/32768
    return a

def write(path,data):
    data=np.clip(data,-1,.999969)
    with wave.open(str(path),'wb') as f:
        f.setnchannels(data.shape[1]);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes(np.rint(data*32767).astype('<i2').tobytes())

command(['ffmpeg','-v','info','-y','-ss','10','-i',str(OUT/'music/Fluidscape-source-excerpt.mp3'),'-t',str(tl['duration_s']),
         '-af','highpass=f=85,loudnorm=I=-20:TP=-4:LRA=7:print_format=json','-ar',str(SR),'-ac','2',
         '-c:a','pcm_s16le',str(OUT/'music/music-normalized.wav')],'music-normalize.log')
voice=read(OUT/'sources/narration-refined.wav');assert len(voice)==N
if voice.shape[1]==1:voice=np.repeat(voice,2,axis=1)
music=read(OUT/'music/music-normalized.wav')[:N];assert len(music)==N
gain=np.ones(N,np.float32)
for s in tl['captions']:
    start=round(s['start_s']*SR);end=round(s['end_s']*SR)
    a=max(0,start-round(.16*SR));b=min(N,end+round(.75*SR))
    values=np.full(b-a,.32,np.float32)
    if start>a:values[:start-a]=np.linspace(1,.32,start-a)
    if b>end:values[end-a:]=np.linspace(.32,1,b-end)
    gain[a:b]=np.minimum(gain[a:b],values)
fadein=round(1.6*SR);fadeout=round(3*SR)
gain[:fadein]*=np.linspace(0,1,fadein);gain[-fadeout:]*=np.linspace(1,0,fadeout)
bed=music*gain[:,None]
write(OUT/'music/music-bed-ducked.wav',bed)
mixed=voice+bed
rng=np.random.default_rng(5958685)
sound_times=[4.3667,20.0333,60.0333,72.0333,78.0333,129.5333]
for when in sound_times:
    count=round(.3*SR);t=np.arange(count)/SR
    # A soft editing sweep, not a simulated robot or collision sound.
    noise=rng.standard_normal(count).astype(np.float32)
    kernel=np.ones(25,np.float32)/25
    noise=np.convolve(noise,kernel,mode='same');noise-=np.convolve(noise,np.ones(150,np.float32)/150,mode='same')
    noise/=max(.0001,float(np.max(np.abs(noise))))
    sweep=noise*np.sin(np.pi*np.arange(count)/count)**2*.022
    index=round(when*SR);mixed[index:index+count]+=sweep[:,None]
write(OUT/'audio-unlimited.wav',mixed)
command(['ffmpeg','-v','info','-y','-i',str(OUT/'audio-unlimited.wav'),'-af','alimiter=limit=0.8913:level=false:latency=true',
         '-ar',str(SR),'-ac','2','-c:a','pcm_s16le',str(OUT/'soundtrack.wav')],'mix-limit.log')
result={'status':'complete','source_narration_sha256':sha(OUT/'sources/narration-refined.wav'),'other_21_sentences_preserved':True,
        'duration_s':N/SR,'sample_rate':SR,'channels':2,'music_title':'Fluidscape','music_author':'Kevin MacLeod',
        'license':'CC BY 4.0','music_inpoint_s':10,'music_target_LUFS':-20,'music_speech_gain':.32,
        'music_duck_db':20*math.log10(.32),'duck_attack_s':.16,'duck_release_s':.75,
        'music_fadein_s':1.6,'music_fadeout_s':3,'editing_sweep_times_s':sound_times,
        'original_sentence_starts_preserved':True,'new_TTS_requests':2,'soundtrack_sha256':sha(OUT/'soundtrack.wav'),
        'music_bed_sha256':sha(OUT/'music/music-bed-ducked.wav')}
save(OUT/'mixing.json',result);job.update(status='complete',completed_utc=now());save(OUT/'audio-job.json',job)
print('MUSIC AND NARRATION MIX READY',N/SR,'seconds',flush=True)
