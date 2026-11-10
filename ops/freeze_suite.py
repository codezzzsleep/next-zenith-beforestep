"""R2 B3: freeze the earliest qualifying seeds before seeing any new Lux result."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def select(rows, families):
    selected = []
    for family in families:
        candidates = sorted((row for row in rows if row['family'] == family), key=lambda row: row['seed'])
        decisive = [row for row in candidates if row['classification'] == 'decisive']
        ordinary = [row for row in candidates if row['classification'] == 'ordinary']
        required = 1 if family == 'F0' else 2
        if len(decisive) < required:
            raise ValueError(f'{family}: insufficient decisive candidates ({len(decisive)}/{required})')
        selected.extend(decisive[:required])
        selected.extend(ordinary[:1])
    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pool', nargs='+', required=True)
    parser.add_argument('--regression', required=True)
    parser.add_argument('--out', default='config/suite/frozen.json')
    parser.add_argument('--families', nargs='+', default=['F0', 'F1', 'F2', 'F3'])
    parser.add_argument('--gate-reduction', action='store_true')
    args = parser.parse_args()
    regression = json.loads((ROOT / args.regression).read_text())
    source = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((ROOT / 'src').rglob('*.py'))}
    assert regression['passed'] and regression['source_sha256'] == source
    if args.gate_reduction:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        assert datetime.now(ZoneInfo('Asia/Shanghai')) >= datetime(2026, 11, 12, 20, tzinfo=ZoneInfo('Asia/Shanghai'))
    else:
        assert args.families == ['F0', 'F1', 'F2', 'F3']
    rows, manifests = {}, []
    for relative in args.pool:
        path = ROOT / relative
        data = json.loads(path.read_text())
        assert data['completed'] and data['source_sha256'] == source
        assert all(row['classification'] != 'incomplete' for row in data['scenes'].values())
        manifests.append({'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        for scene, row in data['scenes'].items():
            if scene in rows:
                assert rows[scene] == row
            rows[scene] = row
    chosen = select(list(rows.values()), args.families)
    r1 = ROOT / 'evidence/reviews/beforestep_r1'
    scenes = []
    if 'F0' in args.families:
        runs = {key: {'run': str((r1 / 'section25_final_base' / key).relative_to(ROOT)),
                     'summary': json.loads((r1 / 'section25_final_base' / key / 'summary.json').read_text())}
                for key in ('conservative', 'see_dark', 'optimistic', 'truth')}
        config = 'config/scenes/stress_v8.json'
        scenes.append({'scene': 'stress_v8', 'family': 'F0', 'seed': None, 'classification': 'decisive',
                       'anchor': True, 'config': config, 'config_sha256': hashlib.sha256((ROOT / config).read_bytes()).hexdigest(),
                       'runs': runs, 'real_run': 'evidence/reviews/beforestep_r1/lux/original_b',
                       'expectation': 'Existing R1 real run: arrived in one view; not rerun or regenerated in R2.'})
    for row in chosen:
        scenes.append({'scene': row['scene'], 'family': row['family'], 'seed': row['seed'],
                       'classification': row['classification'], 'config': row['path'],
                       'config_sha256': row['sha256'], 'runs': row['runs'],
                       'expectation': 'Expect arrival within two views, all selected-route rehearsals complete without collision and independent execution without collision. Preserve actual failure or safe stop; do not change thresholds or replace this scene.'})
    if not args.gate_reduction:
        assert 8 <= len(scenes) <= 12, f'Need 8–12 frozen scenes; found {len(scenes)}'
    output = ROOT / args.out
    data = {'schema': 'beforestep-preregistered-suite/v1', 'families': args.families,
            'scene_count': len(scenes), 'pool_sources': manifests,
            'regression_at_freeze': args.regression, 'source_sha256_at_freeze': source,
            'selection_rule': 'By ascending seed: two decisive and up to one ordinary per family; R1 anchor counts as the first F0 decisive.',
            'gate_reduction': args.gate_reduction, 'scenes': scenes}
    content = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if output.exists() and output.read_text() != content:
        raise ValueError('Frozen list differs; do not edit it after freezing')
    budget = ROOT / 'outputs/generation/r2-budget.json'
    if not output.exists() and budget.exists() and json.loads(budget.read_text())['tasks']:
        raise ValueError('Cannot create another preregistration after paid tasks have been reserved')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)
    print(json.dumps({'frozen': args.out, 'scenes': len(scenes), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
