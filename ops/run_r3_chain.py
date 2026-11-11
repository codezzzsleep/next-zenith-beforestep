"""R3 full chain, first-view reuse and hard-budget cloud recovery."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from beforestep.generation import client as C
from run_suite_imagination import offline_result, sources
from suite_lux_budget import generate_request, PendingTask, BudgetExhausted
from r3_lux_budget import R3Budget

ROOT = C.ROOT


def first_view_source(original, destination):
    original, destination = Path(original), Path(destination)
    if destination.exists():
        return
    looks = destination / 'looks'
    looks.mkdir(parents=True)
    shutil.copytree(original / 'looks/look1', looks / 'look1')
    for path in (original / 'looks').glob('look1_*'):
        if path.is_file():
            shutil.copy2(path, looks / path.name)


def first_view_verification(original, run):
    original, run = Path(original), Path(run)
    comparison = {}
    for name in ('rgb.png', 'depth.npy', 'dark.npy', 'state.npy', 'zmax.npy'):
        filename = 'look1_' + name
        before, after = original / 'looks' / filename, run / 'looks' / filename
        comparison[filename] = before.is_file() and after.is_file() and C.sha(before) == C.sha(after)
    return {'passed': all(comparison.values()), 'files_equal': comparison,
            'source': str(original.relative_to(ROOT))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', required=True)
    ap.add_argument('--policy', default='imagination_strict', choices=['imagination_strict', 'imagination'])
    ap.add_argument('--mode', required=True, choices=['standin', 'real', 'reuse'])
    ap.add_argument('--out', required=True)
    ap.add_argument('--regression', required=True)
    ap.add_argument('--standins', default='evidence/reviews/beforestep_r3/standins/summary.json')
    ap.add_argument('--budget', default='outputs/generation/r3-budget.json')
    ap.add_argument('--first-reuse')
    a = ap.parse_args()
    regression = json.loads((ROOT / a.regression).read_text())
    source = sources()
    assert regression.get('passed') and regression['source_sha256'] == source
    out = (ROOT / a.out).resolve()
    assert out.is_relative_to(ROOT / 'outputs'), 'R3 experiments must use new outputs'
    out.mkdir(parents=True, exist_ok=True)
    ledger = out / 'chain.json'
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r3-chain/v1', 'post_result_revision': True,
        'scene': a.scene, 'policy': a.policy, 'mode': a.mode,
        'source_sha256': source, 'attempts': []}
    assert report['source_sha256'] == source and report['policy'] == a.policy and report['mode'] == a.mode
    live = report.get('live_process', {}).get('pid')
    if live:
        try:
            os.kill(live, 0)
        except ProcessLookupError:
            report.pop('live_process', None)
        else:
            raise RuntimeError(f'Existing chain process {live} still exists; inspect before resuming')
    if a.mode == 'real':
        standins = json.loads((ROOT / a.standins).read_text())
        assert standins['all_passed'] and standins['source_sha256'] == source
        remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
        freeze_commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', 'config/suite/frozen.json'], cwd=ROOT, text=True).strip()
        subprocess.run(['git', 'merge-base', '--is-ancestor', freeze_commit, remote], cwd=ROOT, check=True)
        os.environ.pop('AHOLO_API_KEY', None)
        C.load_credentials(ROOT.parent / '.env')
        budget = R3Budget(ROOT / a.budget)
    run = out / a.policy
    command = [sys.executable, '-m', 'beforestep', 'run', '--scene', a.scene,
               '--controller-model', 'rules', '--policy', a.policy, '--imagine', 'lux', '--out', str(out)]
    if a.first_reuse:
        reuse = out / 'first-view-reuse'
        first_view_source((ROOT / a.first_reuse).resolve(), reuse)
        command.extend(['--reuse-lux', str(reuse)])
    if a.mode == 'standin':
        run.mkdir(exist_ok=True)
        C.atomic_json(run / 'standin_provenance.json', {
            'not_real_lux': True, 'provider': 'offline_standin', 'scene': a.scene, 'paid_tasks': 0,
            'scope': 'Exact scans supplied only as offline candidate assets; production registration/admission/rehearsal/execution'})
    for _ in range(80):
        if (run / 'summary.json').is_file():
            identity = json.loads((run / 'run_identity.json').read_text())
            assert identity['source_sha256'] == source
            summary = json.loads((run / 'summary.json').read_text())
            report.update(completed=True, summary=summary, run_id=identity['run_id'],
                          no_collision=summary['collision'] is None and summary['result'] != 'collision')
            if a.first_reuse:
                report['first_view_verification'] = first_view_verification((ROOT / a.first_reuse).resolve(), run)
                assert report['first_view_verification']['passed'], 'First-view byte reuse mismatch; no new first-view tasks'
            C.atomic_json(ledger, report)
            print(json.dumps({'scene': a.scene, 'summary': summary, 'run_id': identity['run_id']}, ensure_ascii=False), flush=True)
            return
        number = len(report['attempts']) + 1
        log_path = out / f'attempt{number:03d}.log'
        with log_path.open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            report['live_process'] = {'pid': process.pid, 'command': command}
            C.atomic_json(ledger, report)
            code = process.wait()
        report.pop('live_process', None)
        report['attempts'].append({'command': command, 'exit_code': code, 'log': str(log_path.relative_to(ROOT))})
        C.atomic_json(ledger, report)
        if code == 0:
            continue
        if code != 10:
            raise RuntimeError(f'Full chain exited {code}; preserve the log and repair before continuing')
        pending = json.loads((run / 'NEED_LUX3D.json').read_text())
        report['pending'] = pending
        C.atomic_json(ledger, report)
        if a.mode == 'reuse':
            raise RuntimeError('Reuse needs unavailable tasks; preserve run, never create in reuse mode')
        if a.first_reuse and pending['look'] == 1:
            raise RuntimeError('Reused first view cannot create new requests; investigate missing immutable evidence')
        for request in pending['requests']:
            if a.mode == 'standin':
                offline_result(ROOT / request, a.scene)
                continue
            while True:
                try:
                    generate_request(ROOT / request, budget, a.scene)
                    break
                except PendingTask:
                    time.sleep(10)
                except BudgetExhausted:
                    report.update(completed=False, budget_exhausted=True)
                    C.atomic_json(ledger, report)
                    raise SystemExit(2)
        report.pop('pending', None)
        C.atomic_json(ledger, report)
    raise RuntimeError('Five-view chain unexpectedly exceeded 80 resumptions')


if __name__ == '__main__':
    main()
