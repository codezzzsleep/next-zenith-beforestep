"""Build preserved pose-control evidence from the documented physical runs."""
import argparse
import ast
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

import numpy as np

from beforestep.paths import ROOT
from beforestep.delivery.learning import run_data, evaluation_data

OUT = ROOT/'evidence/learning/observation_pose_v2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def capture_audit(source):
    events = [json.loads(line) for line in (source/'events.jsonl').read_text().splitlines()]
    target = None
    rows = []
    for event in events:
        if event['kind'] == 'second_look_plan':
            target = event['requested_viewpoint']
        if event['kind'] == 'look' and event['k'] > 1:
            pose, velocity = event['measured_pose'], event['measured_velocity']
            row = {'look': event['k'], 'requested_pose': target, 'measured_pose': pose,
                   'position_error_m': float(np.linalg.norm(np.asarray(pose[:2])-target[:2])),
                   'yaw_error_degrees': float(np.degrees(abs((pose[2]-target[2]+np.pi)%(2*np.pi)-np.pi))),
                   'linear_speed_mps': float(np.linalg.norm(velocity[:2])),
                   'yaw_rate_rps': abs(velocity[5]), 'sensor_source': event['sensor_source']}
            assert row['position_error_m'] < .075 and row['yaw_error_degrees'] < 4.
            assert row['linear_speed_mps'] < .035 and row['yaw_rate_rps'] < .08
            rows.append(row)
    return rows


def archive_inputs(label, source):
    directory = ROOT/'assets/observations'/label
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory/'sensors.tar.gz'
    inputs = sorted(p for p in (source/'looks').iterdir() if p.is_file())
    entries = []
    with archive.open('wb') as stream, gzip.GzipFile(fileobj=stream, mode='wb', filename='', mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as tar:
            for path in inputs:
                info = tar.gettarinfo(str(path), arcname=path.name)
                info.mtime = info.uid = info.gid = 0
                info.uname = info.gname = ''
                with path.open('rb') as f:
                    tar.addfile(info, f)
                entries.append({'path': path.name, 'sha256': sha(path), 'bytes': path.stat().st_size})
                if path.suffix == '.png':
                    shutil.copy2(path, directory/path.name)
    with tarfile.open(archive, 'r:gz') as tar:
        assert len(tar.getmembers()) == len(entries)
        for entry in entries:
            assert hashlib.sha256(tar.extractfile(entry['path']).read()).hexdigest() == entry['sha256']
    write(directory/'manifest.json', {'archive': str(archive.relative_to(ROOT)), 'sha256': sha(archive),
          'files': entries, 'note': 'Original captured RGB-D, dark masks and maps, preserved byte for byte; PNG files also provided as previews.'})
    return {'path': str(archive.relative_to(ROOT)), 'sha256': sha(archive), 'files': len(entries)}


def figures(proof, replays):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    ax = axes[0]
    for rock in replays[0]['rocks']:
        ax.add_patch(Polygon(rock['polygon'], facecolor='#cbd5df', edgecolor='#8999a9'))
    for label, color in [('pose_v2_joint', '#cf6a54'), ('pose_v2_recorded', '#227bba')]:
        with np.load(ROOT/f'evidence/learning/{label}/traj.npz') as trace:
            ax.plot(trace['qpos'][:, 0], trace['qpos'][:, 1], color=color, label=label)
    ax.scatter([5.7], [-.5], c='#168b50', marker='*', s=110, label='task goal')
    ax.set(xlim=(2.1, 6.1), ylim=(-1., 1.1), xlabel='world x (m)', ylabel='world y (m)',
           title='Same first RGB-D and initial robot state')
    ax.set_aspect('equal'); ax.legend(fontsize=7)
    for label, color in [('pose_v2_live', '#227bba'), ('pose_v2_recorded', '#168b50')]:
        rows = proof['trials'][label]['capture_poses']
        axes[1].plot([r['look'] for r in rows], [r['position_error_m']*1000 for r in rows], 'o-', color=color, label=label)
        axes[2].plot([r['look'] for r in rows], [r['yaw_error_degrees'] for r in rows], 'o-', color=color, label=label)
    axes[1].axhline(75, color='#cf6a54', linestyle='--'); axes[2].axhline(4, color='#cf6a54', linestyle='--')
    axes[1].set(title='Actual pose when image was captured', xlabel='look number', ylabel='position error (mm)', ylim=(0, 85))
    axes[2].set(title='Original 4-degree gate retained', xlabel='look number', ylabel='yaw error (degrees)', ylim=(0, 4.5))
    for ax in axes[1:]: ax.set_xticks([2, 3, 4]); ax.legend(fontsize=7); ax.grid(alpha=.15)
    fig.tight_layout(); fig.savefig(OUT/'comparison.png', dpi=180); plt.close(fig)
    from beforestep.learning.pose import PosePolicy
    from beforestep.learning import ppo
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for version in ('v1', 'v2'):
        history = read(ROOT/f'evidence/training/observation_pose_{version}/behavior_cloning.json')
        axes[0].semilogy([r['epoch'] for r in history], [r['loss'] for r in history], label=version)
        policy = PosePolicy(ROOT/f'assets/models/observation_pose_{version}/pose.npz')
        degrees = np.linspace(-12., 12., 241)
        turns = [ppo.deterministic_action(policy.params, np.array([np.radians(deg)/.1, 0.]))[3]*4 for deg in degrees]
        axes[1].plot(degrees, turns, label=version)
    axes[0].set(title='BC objectives differ; losses are not task scores', xlabel='epoch', ylabel='weighted action MSE')
    axes[1].set(title='Learned small-angle turn at zero yaw rate', xlabel='yaw error (degrees)', ylabel='wheel differential (rad/s)')
    for ax in axes: ax.legend(); ax.grid(alpha=.15)
    fig.tight_layout(); fig.savefig(OUT/'training.png', dpi=180); plt.close(fig)


def video():
    import mujoco
    from PIL import Image, ImageDraw
    from beforestep import scene
    from beforestep.visualization import camera
    from beforestep.delivery.artifacts import font
    labels = ['pose_v2_joint', 'pose_v2_recorded']
    traces = {label: dict(np.load(ROOT/f'evidence/learning/{label}/traj.npz')) for label in labels}
    summaries = {label: read(ROOT/f'evidence/learning/{label}/summary.json') for label in labels}
    scene.configure('gate_passage_001'); scene.GOAL = (5.7, -.5)
    spec, rocks, _ = scene.scene_spec(ROOT/'outputs/qa/pose-video-scene')
    env = scene.make_env(spec)
    vm = camera.video_model(env, rocks, width=640, height=360, off=(640, 360))
    vm.m.vis.quality.shadowsize = 512; vm.m.vis.quality.offsamples = 1
    for group in range(6): vm.opt.geomgroup[group] = int(group in (0, 1, 2))
    cam = mujoco.MjvCamera(); cam.distance = 3.8; cam.azimuth = 90; cam.elevation = -65
    fps, speed = 10, 8
    duration = max(float(t['t'][-1]-t['t'][0]) for t in traces.values())
    temporary = OUT/'demo.tmp.mp4'
    process = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', '1280x720', '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264', '-threads', '2',
        '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(temporary)], stdin=subprocess.PIPE)
    for i in range(int((duration/speed+4)*fps)):
        picture = Image.new('RGB', (1280, 720), '#0b0e13'); draw = ImageDraw.Draw(picture)
        draw.text((30, 20), '主动观察 / 同观测、同物理环境的真实任务对照', font=font(30), fill='#edf3f9')
        draw.text((30, 68), '首次记录 RGB-D，后续实时仿真采集 · 8×实际轨迹回放', font=font(22), fill='#79d6b4')
        elapsed = max(0., min(duration, (i/fps-2)*speed))
        for column, label in enumerate(labels):
            trace = traces[label]
            index = min(int(np.searchsorted(trace['t']-trace['t'][0], elapsed)), len(trace['t'])-1)
            q = trace['qpos'][index]
            cam.lookat[:] = [q[0]+.3, q[1], .15]
            vm.sync(q); vm.r.update_scene(vm.d, camera=cam, scene_option=vm.opt)
            picture.paste(Image.fromarray(vm.r.render().copy()), (column*640, 162))
            draw.text((column*640+25, 118), '原 v4 联合目标控制' if column == 0 else 'v4 + 已训练朝向网络 v2', font=font(26), fill='#edf3f9')
            finished = elapsed >= float(trace['t'][-1]-trace['t'][0])
            outcome = '观察姿态未完成' if column == 0 else '4 眼到达 / 无碰撞'
            draw.text((column*640+25, 546), outcome if finished else f'实际执行 {trace["t"][index]-trace["t"][0]:.1f}s', font=font(24), fill='#ffac8c' if column == 0 else '#79d6b4')
            draw.text((column*640+25, 590), f'终态：{summaries[label]["execution_elapsed_s"]}s / 观察 {summaries[label]["looks"]} 次', font=font(21), fill='#a8b5c1')
        draw.text((30, 652), '保留观察点超时重试；原 75mm / 4° / 连续 5 帧停稳门槛。', font=font(22), fill='#a8b5c1')
        if i == 12*fps: picture.save(OUT/'demo-poster.jpg', quality=92)
        process.stdin.write(picture.tobytes())
    process.stdin.close()
    if process.wait() != 0: raise RuntimeError('Video encoding failed')
    camera.release(vm)
    temporary.replace(OUT/'demo.mp4')


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--video', action='store_true')
    args = parser.parse_args()
    sources = {label: ROOT/f'outputs/learning/{name}/{policy}' for label, name, policy in [
        ('pose_v2_live', 'observation_pose_v2_final_live', 'conservative'),
        ('pose_v2_recorded', 'observation_pose_v2_final_recorded', 'conservative'),
        ('pose_v2_joint', 'observation_pose_v2_final_joint', 'conservative'),
        ('pose_v2_lux_regression', 'observation_pose_v2_lux_regression', 'imagination'),
        ('pose_v1_initial_live', 'observation_pose_v1_live', 'conservative'),
        ('pose_v1_capture_failed', 'observation_pose_v1_live_capture_margin', 'conservative'),
        ('pose_v1_calibrated_failed', 'observation_pose_v1_calibrated_live', 'conservative'),
        ('pose_v2_unsettled_failed', 'observation_pose_v2_live', 'conservative')]}
    assert all((source/'summary.json').is_file() for source in sources.values())
    replays = [run_data(label, source) for label, source in sources.items()]
    for replay in replays:
        replay['pose_controller_sha256'] = read(sources[replay['id']]/'run_identity.json')['controller']['pose_checkpoint_sha256']
        if replay['id'] in ('pose_v2_recorded', 'pose_v2_joint'):
            replay['note'] = '从同一首次记录观测状态开始；后续由真实动力学推进并实时采集，无生成几何；接近第一观察点不计入本次执行。'
        if replay['id'] == 'pose_v1_initial_live':
            replay['note'] = '历史初版曾到达，但停车后采集朝向处于4°边缘；不计入最终严格采集姿态验收。'
    # Full physical frames remain in each checksummed traj.npz. The version
    # index links those records instead of duplicating dense frames as JSON.
    index = [{**{k: v for k, v in replay.items() if k not in ('frames', 'rocks')},
              'trajectory': f'evidence/learning/{replay["id"]}/traj.npz',
              'execution_source': f'evidence/learning/{replay["id"]}/source_manifest.json'} for replay in replays]
    write(OUT/'replays.json', index)
    identities = {label: read(source/'run_identity.json') for label, source in sources.items()}
    a, b = identities['pose_v2_recorded'], identities['pose_v2_joint']
    assert a['source_sha256'] == b['source_sha256'] and a['scene'] == b['scene']
    assert a['controller']['checkpoint_sha256'] == b['controller']['checkpoint_sha256']
    assert a['recorded_initial_state'] == b['recorded_initial_state']
    observations = {}
    for name in ('look1_rgb.png', 'look1_depth.npy', 'look1_state.npy', 'look1_dark.npy'):
        assert sha(sources['pose_v2_recorded']/'looks'/name) == sha(sources['pose_v2_joint']/'looks'/name)
        observations[name] = sha(sources['pose_v2_recorded']/'looks'/name)
    current = (ROOT/'src/beforestep/learning/policy.py').read_text()
    baseline = OUT/'frozen_baseline'
    baseline.mkdir(exist_ok=True)
    if not (baseline/'policy.py').exists():
        (baseline/'policy.py').write_bytes(subprocess.check_output(['git', 'show', '39fd2b5:src/beforestep/learning/policy.py'], cwd=ROOT))
        (baseline/'protocol.json').write_bytes(subprocess.check_output(['git', 'show', '39fd2b5:config/protocol.json'], cwd=ROOT))
    frozen = (baseline/'policy.py').read_text()
    def acceptance(text):
        return ast.dump(next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == 'completed'))
    assert acceptance(current) == acceptance(frozen)
    original_protocol = (baseline/'protocol.json').read_bytes()
    assert original_protocol == (ROOT/'config/protocol.json').read_bytes()
    write(baseline/'manifest.json', {'source_commit': '39fd2b5',
          'policy_sha256': sha(baseline/'policy.py'), 'protocol_sha256': sha(baseline/'protocol.json')})
    proof = {'schema': 'beforestep-pose-validation/v1', 'base_model_sha256': a['controller']['checkpoint_sha256'],
             'pose_model_sha256': a['controller']['pose_checkpoint_sha256'],
             'fair_comparison': {'same_source': True, 'same_scene': True, 'same_initial_state': True,
                                 'same_first_rgb_depth_map': observations, 'original_acceptance_function_retained': True}, 'trials': {}}
    for label in ('pose_v2_live', 'pose_v2_recorded', 'pose_v2_joint', 'pose_v2_lux_regression'):
        source = sources[label]
        with np.load(source/'traj.npz') as trace:
            assert 'rules' not in trace['control_sources']
            assert np.isfinite(trace['qpos']).all() and np.isfinite(trace['control_actions']).all()
            error = float(np.linalg.norm(trace['qpos'][-1, :2]-[5.7, -.5]))
        summary = read(source/'summary.json')
        assert summary['result'] == ('stopped_short' if label == 'pose_v2_joint' else 'arrived')
        if label != 'pose_v2_joint': assert error < .075
        proof['trials'][label] = {'run_id': identities[label]['run_id'], 'summary': summary,
            'final_position_error_m': error, 'trajectory_sha256': sha(source/'traj.npz'),
            'capture_poses': capture_audit(source) if label in ('pose_v2_live', 'pose_v2_recorded') else []}
        if label in ('pose_v2_live', 'pose_v2_recorded'):
            proof['trials'][label]['sensor_archive'] = archive_inputs(label, source)
    for version in ('v1', 'v2'):
        folder = ROOT/f'evidence/training/observation_pose_{version}'
        identity = read(folder/'run_identity.json')
        for relative, expected in identity['source_sha256'].items(): assert sha(folder/'source_snapshot'/relative) == expected
        write(folder/'manifest.json', {'checkpoint': f'assets/models/observation_pose_{version}/pose.npz',
            'sha256': sha(ROOT/f'assets/models/observation_pose_{version}/pose.npz'),
            'physical_demonstrations': 'assets/training/observation_pose_v1/demonstrations.npz',
            'physical_demonstrations_sha256': identity['demonstrations_sha256'],
            'summary': f'evidence/training/observation_pose_{version}/summary.json',
            'startup_source_manifest': f'evidence/training/observation_pose_{version}/source_snapshot/manifest.json'})
    evaluations = [evaluation_data(label, ROOT/f'outputs/learning/{source}') for label, source in [
        ('pose_v1_held_out', 'observation_pose_v1_held_out'), ('pose_v2_held_out', 'observation_pose_v2_held_out'),
        ('pose_v2_final_held_out', 'observation_pose_v2_final_held_out')]]
    proof['held_out_final'] = read(ROOT/'evidence/learning/pose_v2_final_held_out/summary.json')
    write(OUT/'evaluations.json', evaluations); write(OUT/'validation.json', proof)
    figures(proof, replays)
    if args.video: video()
    print(json.dumps({'ok': True, 'trials': len(sources), 'capture_poses_verified': 6, 'video': args.video}), flush=True)


if __name__ == '__main__': main()
