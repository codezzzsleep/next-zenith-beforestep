"""Resume the complete frozen chain with offline shapes or bounded real Lux.

Offline shapes are explicitly marked and never enter the paid client ledger.
Real mode requires the pushed suite freeze, current regression and all-family
stand-in acceptance. Reuse mode never creates additional tasks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import trimesh

from beforestep import scene as S
from beforestep.generation import client as C
from beforestep.navigation import map as N
from beforestep.evaluation import truth_footprints
from suite_lux_budget import Budget, generate_request, PendingTask

ROOT = S.ROOT


def sources():
    return {str(p.relative_to(ROOT)): C.sha(p) for p in sorted((ROOT / 'src').rglob('*.py'))}


def offline_result(request_path, scene_id):
    request_path = Path(request_path)
    if (request_path.parent / 'lux_result.json').exists():
        raise ValueError('Do not overwrite any existing result')
    request = json.loads(request_path.read_text())
    target = request_path.parent.parent if request_path.parent.name == 'retry' else request_path.parent
    definition = S.configure(scene_id)
    state = json.loads((target / 'state.json').read_text())
    cells = np.load(target / 'cells.npy')
    truth = truth_footprints(target)
    overlapping = [key for key, mask in truth.items() if (mask & cells).sum() > 0]
    if not overlapping:
        raise ValueError('Observed target has no matching offline scan; record the failure')
    meshes = []
    origins = []
    for key in overlapping:
        value = definition['rocks'][key]
        path, _ = S.rock_asset_uniform(value['rock'], value['height'])
        mesh = trimesh.load(path, force='mesh', process=False)
        origins.append({'rock': key, 'scan': value['rock'], 'scaled_scan_sha256': C.sha(path)})
        # Exact-shape diagnostics use the same current-view axis convention for
        # every scene and target. Registration still estimates the full pose and
        # scale through its unchanged production search; no matrix is supplied.
        transform = trimesh.transformations.rotation_matrix(np.radians(value['yaw']), [0, 0, 1])
        transform[:2, 3] = [value['x'], value['y']]
        mesh.apply_transform(transform)
        meshes.append(mesh)
    shape = trimesh.util.concatenate(meshes)
    shape.apply_transform(trimesh.transformations.rotation_matrix(
        -state['local_frame']['yaw0'], [0, 0, 1]))
    center = (shape.bounds[0] + shape.bounds[1]) / 2
    center[2] = shape.bounds[0, 2]
    shape.apply_translation(-center)
    glb = request_path.parent / 'offline_true_shape.glb'
    shape.export(glb)
    items = request['items']
    tasks = []
    for index, item in enumerate(items):
        row = {'id': item['id'], 'task_id': f'OFFLINE:{scene_id}:{target.parent.name}:{target.name}:{item["id"]}',
               'status': 'ok' if index == 0 else 'failed',
               'inputs': item.get('paths') or [item['path']], 'input_sha256': item['sha256'],
               'api_field': request['mode'], 'n_images': 2 if request['mode'] == 'imgs' else 1,
               'not_real_lux': True, 'provider': 'offline_standin'}
        if index == 0:
            row.update(glb=str(glb.relative_to(ROOT)), glb_sha256=C.sha(glb))
        else:
            row['offline_reason'] = 'Explicit unused stand-in slot, not a provider failure or paid task'
        tasks.append(row)
    C.atomic_json(request_path.parent / 'lux_result.json', {
        'schema': 'beforestep-lux-result/v1', 'not_real_lux': True,
        'provider': 'offline_standin', 'scope': 'One exact scan candidate; remaining slots are offline placeholders',
        'source_shapes': origins, 'asset_axes': 'current-view horizontal axes; bottom centered; exact scan shape',
        'registration_pose_supplied': False, 'tasks': tasks})


def require_real_gates(scene, freeze_path, regression_path, standins_path, manual=False):
    freeze_path, regression_path, standins_path = map(Path, (freeze_path, regression_path, standins_path))
    freeze = json.loads(freeze_path.read_text())
    if not manual:
        entry = next(row for row in freeze['scenes'] if row['scene'] == scene)
        assert C.sha(ROOT / entry['config']) == entry['config_sha256'], 'Frozen scene bytes changed'
    regression = json.loads(regression_path.read_text())
    standins = json.loads(standins_path.read_text())
    assert regression['passed'] and regression['source_sha256'] == sources()
    assert standins['all_passed'] and standins['source_sha256'] == sources()
    commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', str(freeze_path.relative_to(ROOT))], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, remote], cwd=ROOT, check=True)
    return {'freeze_commit': commit, 'remote_main': remote, 'freeze_sha256': C.sha(freeze_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', required=True)
    parser.add_argument('--mode', choices=['standin', 'real'], required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--freeze', default='config/suite/frozen.json')
    parser.add_argument('--regression', required=True)
    parser.add_argument('--standins', default='evidence/suite/standins/summary.json')
    parser.add_argument('--budget', default='outputs/generation/r2-budget.json')
    parser.add_argument('--reuse-lux')
    parser.add_argument('--manual', action='store_true')
    args = parser.parse_args()
    regression = json.loads((ROOT / args.regression).read_text())
    assert regression['passed'] and regression['source_sha256'] == sources(), 'Current full regression required'
    output = (ROOT / args.out).resolve()
    if not output.is_relative_to(ROOT):
        parser.error('--out must remain in the repository outputs area')
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'chain.json'
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-suite-chain/v1', 'scene': args.scene, 'mode': args.mode,
        'source_sha256': sources(), 'attempts': []}
    assert report['source_sha256'] == sources() and report['mode'] == args.mode
    if args.mode == 'real':
        import os
        os.environ.pop('AHOLO_API_KEY', None)
        C.load_credentials(ROOT.parent / '.env')
        report['gates'] = require_real_gates(args.scene, ROOT / args.freeze, ROOT / args.regression,
                                            ROOT / args.standins, args.manual)
    run = output / 'imagination'
    run.mkdir(exist_ok=True)
    if args.mode == 'standin':
        C.atomic_json(run / 'standin_provenance.json', {
            'not_real_lux': True, 'provider': 'offline_standin',
            'scope': 'Full production registration/admission/rehearsal/execution; exact scans supplied only as offline candidate assets',
            'scene': args.scene, 'paid_tasks': 0})
    command = [sys.executable, '-m', 'beforestep', 'run', '--scene', args.scene,
               '--controller-model', 'rules', '--policy', 'imagination', '--imagine', 'lux',
               '--out', str(output)]
    if args.reuse_lux:
        command.extend(['--reuse-lux', str((ROOT / args.reuse_lux).resolve())])
    for _ in range(20):
        if (run / 'summary.json').exists():
            identity = json.loads((run / 'run_identity.json').read_text())
            assert identity['source_sha256'] == sources()
            summary = json.loads((run / 'summary.json').read_text())
            report.update(completed=True, summary=summary, run_id=identity['run_id'],
                          passed=summary['result'] == 'arrived' and summary['collision'] is None)
            C.atomic_json(ledger, report)
            print(json.dumps(report, ensure_ascii=False), flush=True)
            return
        number = len(report['attempts']) + 1
        with (output / f'attempt{number:03d}.log').open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            report['live_process'] = {'pid': process.pid, 'command': command}
            C.atomic_json(ledger, report)
            code = process.wait()
        report.pop('live_process', None)
        report['attempts'].append({'command': command, 'exit_code': code, 'log': f'attempt{number:03d}.log'})
        C.atomic_json(ledger, report)
        if code == 0:
            continue
        if code != 10:
            raise RuntimeError(f'Full chain exited {code}; preserve its log and fix before paid continuation')
        if args.reuse_lux:
            raise RuntimeError('Reuse requires a new request: no additional paid creation is permitted')
        pending = json.loads((run / 'NEED_LUX3D.json').read_text())
        report['pending'] = pending
        C.atomic_json(ledger, report)
        for request in pending['requests']:
            request_path = ROOT / request
            if args.mode == 'standin':
                offline_result(request_path, args.scene)
            else:
                while True:
                    try:
                        generate_request(request_path, Budget(ROOT / args.budget), args.scene)
                        break
                    except PendingTask:
                        # Existing IDs only: retain the pending result and query on
                        # the next loop. An uncertain identity is never resubmitted.
                        import time
                        time.sleep(10)
        report.pop('pending', None)
        C.atomic_json(ledger, report)
    raise RuntimeError('Unexpected chain state: bounded two views should need fewer than twenty resumptions')


if __name__ == '__main__':
    main()
