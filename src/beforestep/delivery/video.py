"""Render actual MuJoCo trajectories; no invented motion or success states."""
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from beforestep import scene
from beforestep.visualization import camera
from .artifacts import MEDIA, font


def render(paths, fps=12, speed=6):
    import mujoco
    traces={p:dict(np.load(Path(d)/'traj.npz')) for p,d in paths.items()}
    summaries={p:json.loads((Path(d)/'summary.json').read_text()) for p,d in paths.items()}
    spec,rocks,_=scene.scene_spec(MEDIA/'video-scene')
    env=scene.make_env(spec)
    vm=camera.video_model(env,rocks,width=640,height=360,off=(640,360))
    # This profile only renders saved trajectories; the RGB-D sensor stays frozen.
    vm.m.vis.quality.shadowsize=1024
    vm.m.vis.quality.offsamples=1
    cam=mujoco.MjvCamera();cam.lookat[:]=[5.0,0.0,.0];cam.distance=13;cam.azimuth=105;cam.elevation=-57
    for group in range(6):vm.opt.geomgroup[group]=1 if group in (0,1,2) else 0
    output=MEDIA/'demo.mp4'
    command=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(fps),'-i','-',
             '-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    max_time=max(float(t['t'][-1]) for t in traces.values())
    frames=int((max_time/speed+8)*fps)
    last_render={}
    labels={'conservative':'看清再走','optimistic':'直接走','imagination':'想一想再走 · Lux3D'}
    outcomes={'stuck':'证据不足，停下','collision':'接触真实岩石','arrived':'到达','stopped_short':'未完成'}
    for i in range(frames):
        image=Image.new('RGB',(1920,1080),'#0b0e13');draw=ImageDraw.Draw(image)
        draw.text((65,38),'先见一步 / NEXT ZENITH',font=font(40),fill='#e9edf1')
        draw.text((65,100),'真实 MuJoCo 运行轨迹回放 · 6×播放 · 同一窄道 · 同一机器人',font=font(25),fill='#70dbb2')
        time_sim=max(0,min(max_time,(i/fps-4)*speed))
        for col,policy in enumerate(('optimistic','conservative','imagination')):
            trace=traces[policy];idx=min(int(np.searchsorted(trace['t'],time_sim)),len(trace['t'])-1)
            if policy not in last_render or last_render[policy][0]!=idx:
                vm.sync(trace['qpos'][idx]);vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt)
                last_render[policy]=(idx,Image.fromarray(vm.r.render().copy()))
            image.paste(last_render[policy][1],(col*640,235))
            draw.text((col*640+35,175),labels[policy],font=font(30),fill='#e9edf1')
            summary=summaries[policy];ended=time_sim>=float(trace['t'][-1])
            phase=str(trace['phase'][idx])
            action={'start':'出发','approach':'驶向观察点','execute':'执行路线','crash':'碰撞停止','stuck':'停下'}.get(phase,'观察环境' if phase.startswith('look') else '前往新的观察点')
            line=outcomes[summary['result']] if ended else f'{float(trace["t"][idx]):.1f}s / {action}'
            draw.text((col*640+35,620),line,font=font(23),fill='#70dbb2' if summary['result']!='collision' else '#ff997c')
            draw.text((col*640+35,665),f'观察 {summary["looks"]} 次 · 总时长 {summary["sim_time_s"]}s',font=font(20),fill='#93a2b1')
        draw.line((65,750,1855,750),fill='#303d48',width=2)
        draw.text((65,790),'Lux3D 的真实资产 → 观测配准 → 冻结自检 → 候选物理预演 → 独立真值执行',font=font(28),fill='#e9edf1')
        draw.text((65,850),'生成不等于可信：保留被拒资产；最多两眼；没有证据就停下。',font=font(26),fill='#a2adbb')
        draw.text((65,910),'Lux3D 分支明确采用记录 RGB-D 与真实生成输入。真值替身不作为作品收益证据。',font=font(22),fill='#83919f')
        if i==int(12*fps):image.save(MEDIA/'demo-poster.jpg',quality=92)
        process.stdin.write(image.tobytes())
    process.stdin.close()
    if process.wait()!=0:raise RuntimeError('Video encoding failed')
    camera.release(vm)
    print('Real trajectory video:',output,flush=True)


def outcome_cards(paths):
    """Append closer real terminal views so the robot is visible to a judge."""
    import mujoco
    spec,rocks,_=scene.scene_spec(MEDIA/'video-scene')
    env=scene.make_env(spec);vm=camera.video_model(env,rocks,width=960,height=540,off=(960,540))
    vm.m.vis.quality.shadowsize=512;vm.m.vis.quality.offsamples=1
    for group in range(6):vm.opt.geomgroup[group]=1 if group in (0,1,2) else 0
    clips=[]
    labels={'optimistic':'直接走 / 碰撞立即停止','conservative':'看清再走 / 无路可走','imagination':'Lux3D / 两眼后证据不足，停下'}
    for policy,path in paths.items():
        trace=np.load(Path(path)/'traj.npz');q=trace['qpos'][-1];summary=json.loads((Path(path)/'summary.json').read_text())
        cam=mujoco.MjvCamera();cam.lookat[:]=[q[0],q[1],.2];cam.distance=3.6;cam.azimuth=90;cam.elevation=-72
        vm.sync(q);vm.r.update_scene(vm.d,camera=cam,scene_option=vm.opt)
        image=Image.new('RGB',(1920,1080),'#0b0e13');draw=ImageDraw.Draw(image)
        picture=Image.fromarray(vm.r.render().copy()).resize((1440,810))
        image.paste(picture,(240,150));draw.text((70,35),labels[policy],font=font(40),fill='#70dbb2')
        draw.text((70,980),f'真实终态 / {summary["sim_time_s"]}s / 观察{summary["looks"]}次 / 不使用真值替身作为Lux3D收益',font=font(26),fill='#ccd5de')
        shot=MEDIA/f'outcome-{policy}.jpg';image.save(shot,quality=92)
        clip=MEDIA/'video-scene'/f'{policy}.mp4'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(shot),'-t','4','-r','12','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p',str(clip)],check=True)
        clips.append(clip)
    original=MEDIA/'video-scene/overview.mp4'
    (MEDIA/'demo.mp4').replace(original)
    listing=MEDIA/'video-scene/concat.txt';listing.write_text('\n'.join("file '"+str(p)+"'" for p in [original,*clips])+'\n')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(MEDIA/'demo.mp4')],check=True)
    camera.release(vm)
