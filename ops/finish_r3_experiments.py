"""Resume prescribed E2, new-rejection checks and preservation after E1.

Only the existing chain runners can create tasks. Their source, offline gates,
first-view identity, deadline and hard-budget checks remain authoritative.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from beforestep.generation import client as C
from run_suite_imagination import sources

ROOT = C.ROOT
BASE = ROOT / 'outputs/r3/v3'
QA = ROOT / 'outputs/qa/r3/final'
REGRESSION = 'outputs/qa/r3/S2-v3/R1-regression/regression.json'
STANDINS = 'evidence/reviews/beforestep_r3/standins/v3/summary.json'


def main():
    QA.mkdir(parents=True, exist_ok=True)
    ledger = BASE / 'completion.json'
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r3-experiment-completion/v1',
        'source_sha256': sources(), 'steps': {}, 'status': 'waiting_e1'}
    assert report['source_sha256'] == sources()
    if report.get('live_process'):
        try:
            os.kill(report['live_process']['pid'], 0)
        except ProcessLookupError:
            report.pop('live_process')
        else:
            raise RuntimeError('Recorded subprocess is alive; inspect instead of duplicating it')

    def save():
        C.atomic_json(ledger, report)

    def step(name, arguments):
        if report['steps'].get(name, {}).get('exit_code') == 0:
            return
        command = [sys.executable, *arguments]
        report['status'] = name
        with (QA / (name + '.log')).open('a') as log:
            process = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                       stdout=log, stderr=subprocess.STDOUT)
            report['live_process'] = {'pid': process.pid, 'command': command}
            save()
            code = process.wait()
        report.pop('live_process')
        report['steps'][name] = {'command': command, 'exit_code': code,
                                'log': str((QA / (name + '.log')).relative_to(ROOT))}
        save()
        if code:
            raise RuntimeError(f'{name} failed ({code}); inspect retained evidence before resuming')

    save()
    while True:
        frozen = json.loads((BASE / 'frozen/processes.json').read_text())
        assert frozen['source_sha256'] == sources()
        if frozen['status'] == 'complete':
            assert frozen['completed']
            break
        if frozen['status'] == 'needs_inspection':
            raise RuntimeError('E1 did not finish; no E2 creation before inspection')
        time.sleep(5)
    step('heldouts', ['ops/run_r3_holdouts.py', '--regression', REGRESSION, '--standins', STANDINS,
                     '--frozen', 'outputs/r3/v3/frozen/processes.json', '--out', 'outputs/r3/v3/holdouts'])
    held = json.loads((BASE / 'holdouts/processes.json').read_text())
    runs = {}
    for scene, job in frozen['jobs'].items():
        if job.get('summary'):
            runs.setdefault(scene, {})['imagination_strict'] = str(
                ((ROOT / job['chain']).parent / 'imagination_strict').relative_to(ROOT))
    for scene, job in held['jobs'].items():
        for policy, row in job.get('runs', {}).items():
            if row.get('summary'):
                runs.setdefault(scene, {})[policy] = row['run']
    for scene, variants in runs.items():
        for policy, run in list(variants.items()):
            if policy not in ('imagination', 'imagination_strict'):
                continue
            step('cf-' + scene + '-' + policy,
                 ['ops/run_r3_counterfactuals.py', '--real-run', run,
                  '--out', f'outputs/r3/v3/counterfactuals/{scene}/{policy}', '--workers', '3'])
    # Every retained run gets an independent post-run XY review. The six-policy
    # comparisons also get physical clearances; CF collision labels come from
    # the original simulator contact events and are never inferred from XY.
    for scene, variants in runs.items():
        for policy, run in list(variants.items()):
            directory = ROOT / run
            identity = json.loads((directory / 'run_identity.json').read_text())
            step('review-' + scene + '-' + policy,
                 ['ops/r3_video_review.py', '--run', run, '--need-xy', '--need-physical'])
            variants[policy + '_postmortem'] = 'outputs/video/r3/reviews/' + identity['run_id']
        cf_scene = BASE / 'counterfactuals' / scene
        for path in sorted(cf_scene.rglob('counterfactuals.json')):
            for key, row in json.loads(path.read_text())['runs'].items():
                if not row.get('summary'):
                    continue
                step('cf-review-' + scene + '-' + path.parent.name + '-' + key,
                     ['ops/r3_video_review.py', '--run', row['run'], '--need-xy'])
                identity = json.loads((ROOT / row['run'] / 'run_identity.json').read_text())
                variants['cf_' + path.parent.name + '_' + key] = row['run']
                variants['cf_' + path.parent.name + '_' + key + '_review'] = 'outputs/video/r3/reviews/' + identity['run_id']
        mapping = QA / (scene + '-runs.json')
        extras = QA / (scene + '-extras.json')
        C.atomic_json(mapping, variants)
        trees = [str(p.relative_to(ROOT)) for p in (BASE / 'frozen' / scene,
                 BASE / 'holdouts' / scene, cf_scene, ROOT / 'outputs/r3/frozen' / scene) if p.exists()]
        C.atomic_json(extras, trees)
        step('preserve-' + scene, ['ops/preserve_suite_scene.py', '--scene', scene,
             '--runs', str(mapping.relative_to(ROOT)), '--extras', str(extras.relative_to(ROOT)),
             '--archive-dir', '/root/3d/artifacts/beforestep-r3/v3',
             '--out', 'evidence/reviews/beforestep_r3/scenes', '--reuse-public-objects'])
    video = [{'scene': scene, 'run': variants['imagination_strict']}
             for scene, variants in runs.items()
             if scene in ('stress_v8', 'suite_r2_v4_F1_020', 'suite_r2_v4_F3_004')]
    assert len(video) == 3
    C.atomic_json(ROOT / 'outputs/reviews/r3/strict-video-runs.json', video)
    step('video-index', ['ops/build_video_index.py'])
    step('video-index-check', ['ops/check_video_index.py'])
    step('summary', ['ops/build_r3_summary.py'])
    report['status'] = 'complete'
    save()


if __name__ == '__main__':
    main()
