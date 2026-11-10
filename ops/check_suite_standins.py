"""Verify a completed exact-shape full chain for every frozen family before Lux."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', default='config/suite/frozen.json')
    parser.add_argument('--selection', required=True, help='JSON family -> completed stand-in run directory')
    parser.add_argument('--out', default='evidence/suite/standins/summary.json')
    args = parser.parse_args()
    freeze = json.loads((ROOT / args.freeze).read_text())
    selected = json.loads((ROOT / args.selection).read_text())
    source = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((ROOT / 'src').rglob('*.py'))}
    families = {}
    for family, relative in selected.items():
        run = (ROOT / relative).resolve()
        summary = json.loads((run / 'summary.json').read_text())
        identity = json.loads((run / 'run_identity.json').read_text())
        provenance = json.loads((run / 'standin_provenance.json').read_text())
        entry = next(s for s in freeze['scenes'] if s['scene'] == summary['scene_id'])
        assert entry['family'] == family and entry['classification'] == 'decisive'
        assert identity['source_sha256'] == source
        assert provenance['not_real_lux'] and provenance['paid_tasks'] == 0
        assert identity['arguments']['controller_model'] == 'rules' and identity['arguments']['pose_model'] is None
        events = [json.loads(line) for line in (run / 'events.jsonl').read_text().splitlines()]
        panes = [p for e in events if e['kind'] == 'rehearsal' for p in e['panes']]
        passed = (summary['result'] == 'arrived' and summary['collision'] is None and summary['looks'] <= 2
                  and bool(panes) and all(p['completed'] and not p['collided'] for p in panes))
        families[family] = {'scene': summary['scene_id'], 'run': relative, 'run_id': identity['run_id'],
                            'passed': passed, 'summary': summary, 'rehearsals': len(panes),
                            'not_real_lux': True, 'paid_tasks': 0}
    result = {'schema': 'beforestep-suite-full-standin-gate/v1', 'source_sha256': source,
              'frozen_families': freeze['families'], 'families': families,
              'all_passed': set(families) == set(freeze['families']) and all(r['passed'] for r in families.values())}
    output = ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'families': {k: v['passed'] for k, v in families.items()}, 'all_passed': result['all_passed']}))
    raise SystemExit(0 if result['all_passed'] else 1)


if __name__ == '__main__':
    main()
