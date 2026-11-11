"""Open a real, zero-paid Lux reuse run for the project lead's screen recording.

The optional passive viewer observes the independent physics run. No Demo video
is rendered or encoded. The frozen controller, observations and source stay intact.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true', help='Verify the real reuse command without a desktop viewer')
    parser.add_argument('--port', type=int, default=8082)
    parser.add_argument('--out', help='A new output directory; existing results are never overwritten')
    parser.add_argument('--reuse-lux', default='evidence/reviews/beforestep_r1/lux/original_b',
                        help='The preserved anchor Lux run; this screen-recording entry never creates tasks')
    args = parser.parse_args()
    os.environ.setdefault('MUJOCO_GL', 'egl' if args.headless else 'glfw')
    os.environ.pop('AHOLO_API_KEY', None)
    from beforestep import pipeline
    first = (ROOT / args.reuse_lux).resolve()
    if first != (ROOT / 'evidence/reviews/beforestep_r1/lux/original_b').resolve():
        parser.error('Use the preserved stress_v8 anchor for this screen-recording entry')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = Path(args.out) if args.out else ROOT / 'outputs/award/screen-recording' / stamp
    if (out / 'imagination').exists():
        parser.error('Choose a fresh --out; preserved runs must not be overwritten')
    out.mkdir(parents=True, exist_ok=True)
    server = None
    handle = None
    main_recorder = None
    start_wall = None
    start_sim = None
    original_frame = pipeline.Recorder.frame

    def frame(recorder, env, kind, phase):
        nonlocal handle, main_recorder, start_wall, start_sim
        original_frame(recorder, env, kind, phase)
        if main_recorder is None and phase == 'start':
            import mujoco.viewer
            main_recorder = recorder
            handle = mujoco.viewer.launch_passive(env.model, env.data)
            handle.cam.lookat[:] = [5.5, 0, 0.3]
            handle.cam.distance, handle.cam.azimuth, handle.cam.elevation = 11, 90, -45
            start_wall, start_sim = time.monotonic(), env.t
        if recorder is main_recorder and handle and handle.is_running():
            time.sleep(max(0, env.t - start_sim - (time.monotonic() - start_wall)))
            handle.sync()

    if not args.headless:
        pipeline.Recorder.frame = frame
        server = subprocess.Popen([sys.executable, '-m', 'beforestep', 'serve', '--port', str(args.port)], cwd=ROOT)
        webbrowser.open(f'http://127.0.0.1:{args.port}/')
    (out / 'visual-observer.json').write_text(json.dumps({'scope': 'Actual independent simulation, with optional passive viewer. No video encoder.',
        'reused_run': str(first.relative_to(ROOT)), 'controller': 'rules', 'new_paid_tasks': 0,
        'headless_verification': args.headless, 'browser_url': f'http://127.0.0.1:{args.port}/'}, indent=2) + '\n')
    sys.argv = ['beforestep', '--scene', 'stress_v8', '--controller-model', 'rules',
                '--policy', 'imagination', '--imagine', 'lux', '--reuse-lux', str(first), '--out', str(out)]
    try:
        pipeline.main()
    finally:
        pipeline.Recorder.frame = original_frame
        if handle:
            handle.close()
        if server:
            server.terminate()
            server.wait(timeout=10)
    print('Actual reuse run completed. No paid generation and no encoded Demo video.')


if __name__ == '__main__':
    main()
