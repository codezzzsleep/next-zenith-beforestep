"""Attempt every rejected generated candidate at its original observation view."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def rejected_candidates(original):
    rows = []
    for decision in sorted(original.glob('looks/look*/T*/decide/target_decision.json')):
        target = decision.parent.parent
        state = json.loads((target / 'state.json').read_text())
        look = int(state['look'].removeprefix('look'))
        for candidate in json.loads(decision.read_text())['candidates']:
            if not candidate['admitted']:
                rows.append({'look': look, 'target': target.name, 'candidate': candidate['id'],
                             'glb': candidate.get('glb'), 'source_decision': str(decision.relative_to(ROOT)),
                             'original_rejection': candidate})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', required=True)
    parser.add_argument('--real-run', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    original = (ROOT / args.real_run).resolve()
    assert json.loads((original / 'summary.json').read_text())['scene_id'] == args.scene
    output = (ROOT / args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'counterfactuals.json'
    candidates = rejected_candidates(original)
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-suite-all-rejected-counterfactuals/v1', 'scene': args.scene,
        'original_run': args.real_run, 'candidates': candidates, 'runs': {}}
    assert report['candidates'] == candidates

    def save():
        temporary = ledger.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(ledger)

    def run(row):
        key = f"look{row['look']}_{row['target']}_{row['candidate']}"
        container = output / key
        actual = container / 'trusted'
        if container.exists():
            raise ValueError(f'Unrecorded partial counterfactual exists: {container}; preserve and inspect')
        (container / 'imagination').mkdir(parents=True)
        # The immutable original is read through this machine-local link; the
        # pipeline makes its own actual replay copy before running physics.
        (container / 'imagination/looks').symlink_to(original / 'looks', target_is_directory=True)
        command = [sys.executable, '-m', 'beforestep', 'run', '--scene', args.scene,
                   '--controller-model', 'rules', '--policy', 'imagination', '--imagine', 'lux',
                   '--out', str(container), '--tag', 'trusted', '--reuse-lux', str(original),
                   '--trust', row['target'] + '=' + row['candidate'], '--trust-look', str(row['look'])]
        with (container / 'run.log').open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, env={**os.environ, 'MUJOCO_GL': 'egl'},
                                       stdout=log, stderr=subprocess.STDOUT)
            (container / 'process.json').write_text(json.dumps({'pid': process.pid, 'command': command}) + '\n')
            code = process.wait()
        summary = json.loads((actual / 'summary.json').read_text()) if (actual / 'summary.json').exists() else None
        events = [json.loads(line) for line in (actual / 'events.jsonl').read_text().splitlines()] if (actual / 'events.jsonl').exists() else []
        interventions = [e for e in events if e['kind'] == 'counterfactual_intervention']
        intended = any(e['look'] == row['look'] and e['target'] == row['target']
                       and e['candidate'] == row['candidate'] for e in interventions)
        return key, {'command': command, 'exit_code': code, 'summary': summary,
                     'intervention_verified': intended, 'run': str(actual.relative_to(ROOT)),
                     'executed': code == 0 and summary is not None and intended,
                     'collision': bool(summary and (summary['collision'] is not None or summary['result'] == 'collision')) if intended else None}

    save()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        pending = [executor.submit(run, row) for row in candidates
                   if f"look{row['look']}_{row['target']}_{row['candidate']}" not in report['runs']]
        for future in as_completed(pending):
            key, row = future.result()
            report['runs'][key] = row
            save()
            print(json.dumps({'counterfactual': key, 'exit_code': row['exit_code'],
                              'executed': row['executed'], 'collision': row['collision']}), flush=True)
    executed = [r for r in report['runs'].values() if r['executed']]
    report.update(completed=len(report['runs']) == len(candidates), rejected_candidates=len(candidates),
                  attempted=len(report['runs']), executed=len(executed),
                  collisions=sum(r['collision'] for r in executed),
                  noncollisions=sum(not r['collision'] for r in executed),
                  unexecutable=len(report['runs']) - len(executed), paid_tasks=0)
    save()
    print(json.dumps({k: report[k] for k in ('completed', 'rejected_candidates', 'attempted',
                                           'executed', 'collisions', 'unexecutable', 'paid_tasks')}), flush=True)


if __name__ == '__main__':
    main()
