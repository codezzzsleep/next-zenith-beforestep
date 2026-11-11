"""Freeze the completed E1 publication proof before the prescribed E2 runs."""
import hashlib
import json
from pathlib import Path

from beforestep.generation import client as C
from run_r3_chain import first_view_verification
from r3_lux_budget import R3Budget
from run_suite_imagination import sources

ROOT = C.ROOT
BASE = ROOT / 'evidence/reviews/beforestep_r3'


def main():
    destination = BASE / 'frozen-complete.json'
    if destination.exists():
        data = json.loads(destination.read_text())
        assert data['completed'] and data['source_sha256'] == sources()
        print(json.dumps({'already_frozen': True, 'scenes': len(data['runs'])}))
        return
    ledger = json.loads((ROOT / 'outputs/r3/v3/frozen/processes.json').read_text())
    completion = json.loads((ROOT / 'outputs/r3/v3/completion.json').read_text())
    assert ledger['completed'] and ledger['source_sha256'] == sources()
    assert completion['status'] == 'waiting_e1_public_checkpoint'
    assert completion['steps']['summary-e1']['exit_code'] == 0
    custody = json.loads((BASE / 'frozen-custody-audit.json').read_text())
    assert custody['passed'] and custody['archives_verified']
    audited = {row['scene']: row for row in custody['scenes']}
    rows = []
    for scene, job in ledger['jobs'].items():
        assert job['status'] == 'complete' and job['exit_code'] == 0
        chain = json.loads((ROOT / job['chain']).read_text())
        run = (ROOT / job['chain']).parent / 'imagination_strict'
        first = first_view_verification(ROOT / chain['first_view_verification']['source'], run)
        assert first['passed']
        manifest_path = BASE / 'scenes' / scene / 'manifest.json'
        assert audited[scene]['manifest_sha256'] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        manifest = json.loads(manifest_path.read_text())
        assert manifest['runs']['imagination_strict']['summary'] == job['summary']
        sidecar = ROOT / 'outputs/video/r3/reviews' / job['run_id']
        for filename in ('eval.json', 'physical_clearance.json'):
            review = json.loads((sidecar / filename).read_text())
            assert review['run_id'] == job['run_id']
        cf_path = ROOT / 'outputs/r3/v3/counterfactuals' / scene / 'imagination_strict/counterfactuals.json'
        cf = json.loads(cf_path.read_text())
        assert cf['completed'] and cf['all_executed_prefixes_verified']
        entries = {item['path']: item for item in manifest['files']}
        public_cf = entries[str(cf_path.relative_to(ROOT))]
        assert public_cf.get('public_object')
        rows.append({'scene': scene, 'run_id': job['run_id'], 'summary': job['summary'],
                     'first_view_verification': first,
                     'public_summary': str((manifest_path.parent / 'runs/imagination_strict/summary.json').relative_to(ROOT)),
                     'public_manifest': str(manifest_path.relative_to(ROOT)),
                     'public_manifest_sha256': audited[scene]['manifest_sha256'],
                     'counterfactuals': {key: cf[key] for key in (
                         'rejected_candidates', 'executed', 'collisions', 'noncollisions',
                         'unexecutable', 'all_executed_prefixes_verified')},
                     'public_counterfactual_ledger': public_cf['public_object']})
    budget = json.loads((ROOT / 'outputs/generation/r3-budget.json').read_text())
    assert all(row['status'] in ('ok', 'failed', 'not_submitted') for row in budget['tasks'].values())
    proof = {'schema': 'beforestep-r3-frozen-complete/v1', 'completed': True,
             'source_sha256': sources(), 'post_result_revision': True,
             'scope': 'Completed known-scene E1 reruns, counterfactuals, postmortems and custody; this is not held-out evidence.',
             'runs': rows, 'new_r3_tasks_at_e1_completion': R3Budget.usage(budget),
             'custody_audit': str((BASE / 'frozen-custody-audit.json').relative_to(ROOT))}
    C.atomic_json(destination, proof)
    print(json.dumps({'completed': True, 'scenes': len(rows), 'new_r3_tasks': R3Budget.usage(budget)}))


if __name__ == '__main__':
    main()
