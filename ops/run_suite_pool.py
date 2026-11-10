"""Run and classify every non-Lux candidate, retaining all four raw runs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {'conservative': ['--policy', 'conservative'],
            'see_dark': ['--policy', 'conservative', '--see-dark'],
            'optimistic': ['--policy', 'optimistic'],
            'truth': ['--policy', 'imagination', '--imagine', 'truth']}


def classify(runs):
    if set(runs) != set(VARIANTS) or any(not r.get('summary') or r['exit_code'] for r in runs.values()):
        return 'incomplete'
    truth, optimistic, conservative = (runs[k]['summary'] for k in ('truth', 'optimistic', 'conservative'))
    if truth['result'] != 'arrived':
        return 'unsolvable'
    if optimistic['result'] == 'arrived':
        return 'ordinary'
    if (optimistic['result'] == 'collision' and conservative['collision'] is None
            and (conservative['result'] == 'stuck' or conservative['looks'] == 5)):
        return 'decisive'
    # Do not silently broaden the preregistered definitions to force selection.
    return 'unclassified'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--regression', required=True)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    regression = json.loads((ROOT / args.regression).read_text())
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted((ROOT / 'src').rglob('*.py'))}
    assert regression['passed'] and sources == regression['source_sha256'], 'Full regression required for this source'
    manifest_path = ROOT / args.manifest
    manifest = json.loads(manifest_path.read_text())
    output = (ROOT / args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    ledger = output / 'pool.json'
    identity = {'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(), 'source_sha256': sources}
    report = json.loads(ledger.read_text()) if ledger.exists() else {
        'schema': 'beforestep-suite-pool-results/v1', **identity, 'scenes': {}}
    assert all(report[k] == v for k, v in identity.items()), 'Changed pool identity: preserve and use a fresh output'
    environment = {**os.environ, 'MUJOCO_GL': 'egl', 'PYTHONDONTWRITEBYTECODE': '1'}

    def save():
        temporary = ledger.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(ledger)

    pending = []
    for entry in manifest['scenes']:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256']
        row = report['scenes'].setdefault(entry['scene'], {**entry, 'runs': {}})
        for key, arguments in VARIANTS.items():
            if key not in row['runs']:
                pending.append((entry['scene'], key, arguments))
    save()

    def run(scene, key, arguments):
        container = output / scene / key
        run_dir = container / 'run'
        if run_dir.exists():
            summary_file = run_dir / 'summary.json'
            if not summary_file.exists():
                raise ValueError(f'Uncertain interrupted run: {run_dir}; inspect it instead of overwriting')
            record = json.loads((run_dir / 'run_identity.json').read_text())
            assert record['source_sha256'] == sources and record['arguments']['scene'] == scene
            return scene, key, {'exit_code': 0, 'recovered_completed_output': True,
                                'summary': json.loads(summary_file.read_text()),
                                'run_id': record['run_id'], 'run': str(run_dir.relative_to(ROOT))}
        container.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, '-m', 'beforestep', 'run', '--scene', scene,
                   '--controller-model', 'rules', '--out', str(container), '--tag', 'run', *arguments]
        (container / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
        with (container / 'run.log').open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
            (container / 'process.json').write_text(json.dumps({'pid': process.pid, 'command': command}) + '\n')
            code = process.wait()
        summary = json.loads((run_dir / 'summary.json').read_text()) if (run_dir / 'summary.json').exists() else None
        record = json.loads((run_dir / 'run_identity.json').read_text()) if (run_dir / 'run_identity.json').exists() else None
        return scene, key, {'command': command, 'exit_code': code, 'summary': summary,
                            'run_id': record['run_id'] if record else None, 'run': str(run_dir.relative_to(ROOT))}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(run, *job) for job in pending]
        for future in as_completed(futures):
            scene, key, row = future.result()
            report['scenes'][scene]['runs'][key] = row
            report['scenes'][scene]['classification'] = classify(report['scenes'][scene]['runs'])
            save()
            print(json.dumps({'scene': scene, 'variant': key, 'exit_code': row['exit_code'],
                              'result': row['summary']['result'] if row['summary'] else None,
                              'classification': report['scenes'][scene]['classification']}), flush=True)
    families = {}
    for row in report['scenes'].values():
        category = row['classification'] = classify(row['runs'])
        counts = families.setdefault(row['family'], {k: 0 for k in
                                     ('decisive', 'ordinary', 'unsolvable', 'unclassified', 'incomplete')})
        counts[category] += 1
    report['counts'] = families
    report['completed'] = all(len(row['runs']) == 4 for row in report['scenes'].values())
    save()
    public = ROOT / 'evidence/suite/pool' / Path(args.manifest).parent.name
    public.mkdir(parents=True, exist_ok=True)
    (public / (manifest_path.stem + '_results.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'completed': report['completed'], 'counts': families}, ensure_ascii=False), flush=True)
    raise SystemExit(0 if report['completed'] and not any(x['incomplete'] for x in families.values()) else 1)


if __name__ == '__main__':
    main()
