"""Expose every retained gait development outcome without changing raw trials."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experimental.crossing.runtime import OUT, sha, write


def derive():
    jobs = json.loads((OUT / 'jobs.json').read_text())['jobs']
    attempts = []
    for folder in sorted((OUT / 'calibration').glob('gait-v*'),
                         key=lambda p: (int(re.match(r'gait-v(\d+)', p.name)[1]), p.name)):
        rows = []
        for result_path in sorted(folder.glob('*/result.json')):
            result = json.loads(result_path.read_text())
            trial = result_path.parent
            trajectory_sha = result.get('trajectory_sha256') or (
                sha(trial / 'trajectory.npz') if (trial / 'trajectory.npz').exists() else None)
            contacts_sha = result.get('contacts_sha256') or (
                sha(trial / 'contacts.npz') if (trial / 'contacts.npz').exists() else None)
            audits = {}
            for name, key in [('support-audit.json', 'steps_missing_stance_support'),
                              ('support-physical-audit.json',
                               'steps_stance_missing_while_commanded_wheel_unloaded')]:
                path = trial / name
                if path.exists():
                    value = json.loads(path.read_text())
                    assert value['trajectory_sha256'] == trajectory_sha
                    assert value['contacts_sha256'] == contacts_sha
                    audits[name] = value[key]
            rows.append({
                'id': trial.name,
                **{key: result.get(key) for key in
                   ['h_m', 'd_m', 'angle_deg', 'status', 'sim_seconds', 'last_phase']},
                'contact': result.get('contact'),
                'last_script_event': result.get('stages', [None])[-1]
                    if result.get('stages') else None,
                'raw_path': str(trial.relative_to(ROOT)),
                'result_sha256': sha(result_path),
                'trajectory_sha256': trajectory_sha,
                'contacts_sha256': contacts_sha,
                'legacy_diagnostic': 'status' not in result,
                'audits': audits,
            })
        attempts.append({
            'attempt': folder.name,
            'job_status': jobs.get(folder.name, {}).get('status', 'unregistered'),
            'source_sha256': jobs.get(folder.name, {}).get('source_sha256', {}),
            'counts': dict(Counter(row['status'] for row in rows)),
            'trials': rows,
        })
    return {
        'schema': 'beforestep-crossing-development/v1',
        'scope': 'Development calibration only; excluded from registered tests and Lux3D outcomes.',
        'task_outcomes_and_support_audits_are_separate': True,
        'attempt_count': len(attempts),
        'trial_count': sum(len(row['trials']) for row in attempts),
        'attempts': attempts,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    data = derive()
    write(ROOT / args.out, data)
    print(json.dumps({key: data[key] for key in ['attempt_count', 'trial_count']}))
