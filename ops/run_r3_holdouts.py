"""Run the prescribed held-out scenes, without selecting on new baselines."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys

from beforestep.generation import client as C
from run_suite_imagination import sources
from r3_lux_budget import R3Budget

ROOT = C.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--regression', required=True)
    ap.add_argument('--out', default='outputs/r3/holdouts')
    ap.add_argument('--frozen', default='outputs/r3/frozen/processes.json')
    a = ap.parse_args()
    frozen = json.loads((ROOT / a.frozen).read_text())
    assert frozen['completed'] and frozen['source_sha256'] == sources(), 'Finish E1 before E2'
    plan = json.loads((ROOT / 'evidence/reviews/beforestep_r3/experiment-plan.json').read_text())
    output = ROOT / a.out
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'processes.json'
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-r3-holdout-processes/v1', 'source_sha256': sources(),
        'scenes': [r['scene'] for r in plan['holdouts']], 'jobs': {}, 'post_result_revision': True,
        'out_of_sample_evidence': True, 'f1_unused_decisive_available': False}
    assert report['source_sha256'] == sources()

    def usage():
        return R3Budget.usage(json.loads((ROOT / 'outputs/generation/r3-budget.json').read_text()))

    def save():
        C.atomic_json(ledger, report)

    def baseline(scene, name, arguments):
        folder = output / scene / 'baselines'
        actual = folder / name
        if (actual / 'summary.json').exists():
            summary = json.loads((actual / 'summary.json').read_text())
            identity = json.loads((actual / 'run_identity.json').read_text())
            assert identity['source_sha256'] == sources()
            return name, {'exit_code': 0, 'summary': summary, 'run_id': identity['run_id'],
                          'run': str(actual.relative_to(ROOT))}
        if actual.exists():
            raise RuntimeError(f'Unrecorded partial baseline exists: {actual}; retain and inspect')
        folder.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, '-m', 'beforestep', 'run', '--scene', scene,
                   '--controller-model', 'rules', '--out', str(folder), '--tag', name, *arguments]
        with (folder / (name + '.log')).open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                       stdout=log, stderr=subprocess.STDOUT)
            C.atomic_json(folder / (name + '-process.json'), {'pid': process.pid, 'command': command})
            code = process.wait()
        summary = json.loads((actual / 'summary.json').read_text()) if (actual / 'summary.json').exists() else None
        return name, {'command': command, 'exit_code': code, 'summary': summary,
                      'run': str(actual.relative_to(ROOT)),
                      'run_id': json.loads((actual / 'run_identity.json').read_text())['run_id'] if summary else None}

    save()
    for entry in plan['holdouts']:
        scene = entry['scene']
        assert C.sha(ROOT / entry['config']) == entry['config_sha256']
        if entry['budget_optional'] and usage() >= 170:
            report['jobs'][scene] = {'status': 'not_started_no_remaining_budget', 'budget_optional': True}
            save()
            continue
        row = report['jobs'].setdefault(scene, {'status': 'running', 'runs': {}})
        if row['status'] == 'complete':
            continue
        baselines = [('conservative', ['--policy', 'conservative']),
                     ('see_dark', ['--policy', 'conservative', '--see-dark']),
                     ('optimistic', ['--policy', 'optimistic']),
                     ('truth', ['--policy', 'imagination', '--imagine', 'truth'])]
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(baseline, scene, name, args) for name, args in baselines if name not in row['runs']]
            for future in as_completed(futures):
                name, value = future.result()
                row['runs'][name] = value
                save()
                assert value['exit_code'] == 0 and value['summary'], 'Baseline failed; no selecting a replacement scene'
        for policy in ('imagination', 'imagination_strict'):
            if policy in row['runs'] and row['runs'][policy].get('completed'):
                continue
            container = output / scene / policy
            command = [sys.executable, 'ops/run_r3_chain.py', '--scene', scene, '--policy', policy,
                       '--mode', 'real', '--out', str(container.relative_to(ROOT)), '--regression', a.regression]
            if policy == 'imagination_strict':
                original = output / scene / 'imagination/imagination'
                if not (original / 'summary.json').exists():
                    row['runs'][policy] = {'completed': False, 'reason': 'original-first-view-chain-incomplete'}
                    save()
                    continue
                command.extend(['--first-reuse', str(original.relative_to(ROOT))])
            with (output / scene / (policy + '-driver.log')).open('a') as log:
                process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                row['live_process'] = {'pid': process.pid, 'command': command}
                save()
                code = process.wait()
            row.pop('live_process', None)
            chain_path = container / 'chain.json'
            chain = json.loads(chain_path.read_text()) if chain_path.exists() else {}
            row['runs'][policy] = {**{k: chain[k] for k in ('completed', 'summary', 'run_id') if k in chain},
                                   'exit_code': code, 'run': str((container / policy).relative_to(ROOT)),
                                   'chain': str(chain_path.relative_to(ROOT))}
            save()
            if code not in (0, 2):
                raise RuntimeError('Real held-out chain failed; recover the same known identities, never select another scene')
        row['status'] = 'complete' if all(row['runs'].get(k, {}).get('completed', False) for k in ('imagination', 'imagination_strict')) else 'incomplete'
        save()
        print(json.dumps({'scene': scene, 'status': row['status'], 'paid_tasks': usage()}, ensure_ascii=False), flush=True)
    report.update(status='complete', paid_tasks=usage())
    save()


if __name__ == '__main__':
    main()
