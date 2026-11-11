"""Run all fixed first-view reuses without creating any cloud tasks."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

from beforestep.generation import client as C
from run_suite_imagination import sources

ROOT = C.ROOT


def main():
    regression_path = 'outputs/qa/r3/S2-v2/R1-regression/regression.json'
    regression = json.loads((ROOT / regression_path).read_text())
    assert regression['passed'] and regression['source_sha256'] == sources()
    plan = json.loads((ROOT / 'evidence/reviews/beforestep_r3/experiment-plan.json').read_text())
    originals = {r['scene']: r for r in json.loads((ROOT / 'evidence/suite/summary.json').read_text())['scenes']}
    out = ROOT / 'outputs/r3/frozen'
    out.mkdir(parents=True, exist_ok=True)
    ledger = out / 'processes.json'
    scenes = [r['scene'] for r in plan['frozen']]
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r3-frozen-processes/v1', 'source_sha256': sources(), 'scenes': scenes,
        'jobs': {}, 'status': 'reuse_only', 'post_result_revision': True, 'paid_tasks': 0,
        'scope': 'No create, upload or query. Reuse only old real first-view tasks; additional views remain awaiting samples.'}
    assert report['source_sha256'] == sources() and report['scenes'] == scenes
    lock = threading.Lock()
    C.atomic_json(ledger, report)

    def run(scene):
        if scene in report['jobs']:
            return
        original = originals[scene]['runs']['imagination']['run']
        reuse = 'outputs/qa/r3/S2-v2/R1-regression/replay' if scene == 'stress_v8' else original
        folder = out / scene
        command = [sys.executable, 'ops/run_r3_chain.py', '--scene', scene, '--mode', 'reuse',
                   '--out', str(folder.relative_to(ROOT)), '--regression', regression_path, '--first-reuse', reuse]
        with (out / (scene + '-reuse.log')).open('a') as stream:
            child = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                     stdout=stream, stderr=subprocess.STDOUT)
            C.atomic_json(out / (scene + '-reuse-process.json'), {'pid': child.pid, 'command': command})
            code = child.wait()
        chain_path = folder / 'chain.json'
        chain = json.loads(chain_path.read_text()) if chain_path.exists() else {}
        with lock:
            report['jobs'][scene] = {'status': 'complete' if code == 0 and chain.get('completed') else
                                    'awaiting_new_samples' if code == 10 else 'failed',
                                    'exit_code': code, 'summary': chain.get('summary'), 'run_id': chain.get('run_id'),
                                    'chain': str(chain_path.relative_to(ROOT)), 'original_r1_r2_run': original,
                                    'pending': chain.get('pending')}
            C.atomic_json(ledger, report)
        print(json.dumps({'scene': scene, 'exit_code': code, 'summary': chain.get('summary')}, ensure_ascii=False), flush=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(run, scene) for scene in scenes]):
            future.result()
    report['completed'] = len(report['jobs']) == 12 and all(r['status'] == 'complete' for r in report['jobs'].values())
    report['reuse_wave_finished'] = len(report['jobs']) == 12
    report['status'] = 'complete' if report['completed'] else 'reuse_finished_additional_samples_not_created'
    C.atomic_json(ledger, report)


if __name__ == '__main__':
    main()
