"""Recheck every executed rejection's saved observation/action prefix."""
import argparse
import json
from pathlib import Path

from run_suite_counterfactuals import prefix_check, rejected_candidates

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='outputs/qa/r2/final-counterfactual-prefixes.json')
    args = parser.parse_args()
    frozen = json.loads((ROOT / 'config/suite/frozen.json').read_text())
    checked = []
    for scene in frozen['scenes']:
        if scene.get('anchor'):
            continue  # The original R1 replay has its own full-array audit.
        name = scene['scene']
        original = ROOT / 'outputs/suite/real' / name / 'imagination'
        cf = json.loads((ROOT / 'outputs/suite/counterfactuals' / name / 'counterfactuals.json').read_text())
        assert cf['completed'] and cf['all_executed_prefixes_verified']
        expected = {f"look{c['look']}_{c['target']}_{c['candidate']}": c for c in rejected_candidates(original)}
        assert set(expected) == set(cf['runs'])
        for key, run in cf['runs'].items():
            if not run['executed']:
                continue
            actual = ROOT / run['run']
            events = [json.loads(line) for line in (actual / 'events.jsonl').read_text().splitlines()]
            result = prefix_check(original, actual, events, expected[key]['look'])
            assert result['passed'] and result == run['prefix_verification'], (name, key)
            assert set(result['arrays_equal']) == {'t', 'qpos', 'phase', 'control_actions', 'control_sources'}
            checked.append({'scene': name, 'candidate': key, **result})
    report = {'schema': 'beforestep-suite-prefix-recheck/v1', 'passed': True,
              'scene_count': len(frozen['scenes']) - 1, 'executed_counterfactuals': len(checked),
              'checks': checked}
    output = ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
