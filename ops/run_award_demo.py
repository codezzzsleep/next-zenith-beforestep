"""Run the predeclared demonstration with a separate quota and full custody."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from beforestep.generation import client as C
from run_suite_imagination import sources

ROOT = C.ROOT


def main():
    plan_path = ROOT / 'evidence/award/demo/plan.json'
    plan = json.loads(plan_path.read_text())
    gate = json.loads((ROOT / 'evidence/award/P1-P2-complete.json').read_text())
    assert gate['passed'] and datetime.fromisoformat(gate['completed_at']) < datetime(2026, 11, 15, 4, tzinfo=timezone.utc)
    assert json.loads((ROOT / 'outputs/r3/v3/completion.json').read_text())['status'] == 'complete'
    assert sources() == plan['source_sha256']
    commit = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--', str(plan_path.relative_to(ROOT))], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, remote], cwd=ROOT, check=True)
    assert subprocess.check_output(['git', 'show', commit + ':' + str(plan_path.relative_to(ROOT))], cwd=ROOT) == plan_path.read_bytes()
    scene = plan['scene']
    base = ROOT / 'outputs/award/demo' / scene
    base.mkdir(parents=True, exist_ok=True)
    path = ROOT / 'outputs/award/demo/processes.json'
    report = json.loads(path.read_text()) if path.exists() else {
        'schema': 'beforestep-award-demo-processes/v1', 'source_sha256': sources(),
        'scene': scene, 'runs': {}, 'steps': {}, 'label': plan['label'], 'status': 'running',
        'plan_commit': commit, 'supervisor_pid': os.getpid()}
    if report.get('live_process'):
        try:
            os.kill(report['live_process']['pid'], 0)
        except ProcessLookupError:
            report.pop('live_process')
        else:
            raise RuntimeError('A previous demonstration subprocess is alive; do not duplicate it')

    def save():
        C.atomic_json(path, report)

    def step(name, arguments, accepted=(0,)):
        if report['steps'].get(name, {}).get('exit_code') in accepted:
            return
        report['status'] = name
        log_path = base / (name + '.log')
        with log_path.open('a') as log:
            process = subprocess.Popen([sys.executable, *arguments], cwd=ROOT,
                env={**os.environ, 'MUJOCO_GL': 'egl'}, stdout=log, stderr=subprocess.STDOUT)
            report['live_process'] = {'pid': process.pid, 'command': [sys.executable, *arguments]}
            save()
            code = process.wait()
        report.pop('live_process')
        report['steps'][name] = {'exit_code': code, 'log': str(log_path.relative_to(ROOT))}
        save()
        if code not in accepted:
            raise RuntimeError(f'{name} exited {code}; recover retained bytes and known IDs')

    save()
    baselines = {'conservative': ['--policy', 'conservative'],
                 'see_dark': ['--policy', 'conservative', '--see-dark'],
                 'optimistic': ['--policy', 'optimistic'],
                 'truth': ['--policy', 'imagination', '--imagine', 'truth']}
    for policy, extra in baselines.items():
        folder = base / 'baselines' / policy
        step('baseline-' + policy, ['-m', 'beforestep', 'run', '--scene', scene,
            '--controller-model', 'rules', '--out', str(folder.parent), '--tag', policy, *extra])
        summary = json.loads((folder / 'summary.json').read_text())
        identity = json.loads((folder / 'run_identity.json').read_text())
        assert identity['source_sha256'] == sources()
        report['runs'][policy] = {'run': str(folder.relative_to(ROOT)), 'summary': summary, 'run_id': identity['run_id']}
        save()
    for policy in ['imagination', 'imagination_strict']:
        args = ['ops/run_award_chain.py', '--scene', scene, '--policy', policy, '--mode', 'real',
                '--out', str((base / policy).relative_to(ROOT)), '--budget', 'outputs/generation/award-budget.json',
                '--regression', 'outputs/qa/r3/S2-v3/R1-regression/regression.json',
                '--standins', 'evidence/reviews/beforestep_r3/standins/v3/summary.json']
        if policy == 'imagination_strict':
            original = base / 'imagination/imagination'
            if not (original / 'looks/look1_state.npy').exists():
                report['strict_not_started_reason'] = 'Original first view did not settle before quota; no substitute first-view creation.'
                save()
                continue
            args.extend(['--first-reuse', str(original.relative_to(ROOT))])
        step('real-' + policy, args, (0, 2))
        chain = json.loads((base / policy / 'chain.json').read_text())
        folder = base / policy / policy
        report['runs'][policy] = {k: chain[k] for k in ('completed', 'summary', 'run_id', 'first_view_verification', 'budget_exhausted') if k in chain}
        report['runs'][policy]['run'] = str(folder.relative_to(ROOT))
        save()
    variants = {p: r['run'] for p, r in report['runs'].items() if r.get('summary')}
    for policy in ['imagination', 'imagination_strict']:
        if policy not in variants:
            continue
        out = f'outputs/award/demo/counterfactuals/{scene}/{policy}'
        step('cf-' + policy, ['ops/run_r3_counterfactuals.py', '--real-run', variants[policy],
             '--out', out, '--budget', 'outputs/generation/award-budget.json', '--workers', '1'])
    for policy, run in list(variants.items()):
        step('review-' + policy, ['ops/r3_video_review.py', '--run', run, '--need-xy', '--need-physical'])
        identity = json.loads((ROOT / run / 'run_identity.json').read_text())
        variants[policy + '_postmortem'] = 'outputs/video/r3/reviews/' + identity['run_id']
    cf_tree = ROOT / 'outputs/award/demo/counterfactuals' / scene
    for cf_path in sorted(cf_tree.glob('*/counterfactuals.json')):
        for key, row in json.loads(cf_path.read_text())['runs'].items():
            if not row.get('summary'):
                continue
            step('cf-review-' + cf_path.parent.name + '-' + key,
                 ['ops/r3_video_review.py', '--run', row['run'], '--need-xy'])
            identity = json.loads((ROOT / row['run'] / 'run_identity.json').read_text())
            variants['cf_' + cf_path.parent.name + '_' + key] = row['run']
            variants['cf_' + cf_path.parent.name + '_' + key + '_review'] = 'outputs/video/r3/reviews/' + identity['run_id']
    mapping, extras = base / 'custody-runs.json', base / 'custody-extras.json'
    C.atomic_json(mapping, variants)
    paid = json.loads((ROOT / 'outputs/generation/award-budget.json').read_text())
    from award_lux_budget import AwardBudget
    extra_trees = [str(base.relative_to(ROOT))]
    if cf_tree.exists():
        extra_trees.append(str(cf_tree.relative_to(ROOT)))
    for task in paid['tasks'].values():
        folder = ROOT / 'assets/candidates' / str(task.get('task_id'))
        if folder.is_dir():
            extra_trees.append(str(folder.relative_to(ROOT)))
    C.atomic_json(extras, sorted(set(extra_trees)))
    C.atomic_json(ROOT / 'evidence/award/demo/generation.json', {
        'schema': 'beforestep-award-generation-provenance/v1', 'new_tasks': AwardBudget.usage(paid),
        'limit': paid['limit'], 'cumulative_limit': paid['cumulative_limit'],
        'prior_r2_tasks': paid['prior_r2_tasks'], 'prior_r3_tasks': paid['prior_r3_tasks'],
        'label': plan['label'], 'tasks': [{key: value for key, value in row.items() if key != 'new_r3_task'}
                                        for row in paid['tasks'].values()]})
    step('preserve', ['ops/preserve_suite_scene.py', '--scene', scene, '--runs', str(mapping.relative_to(ROOT)),
                     '--extras', str(extras.relative_to(ROOT)), '--archive-dir', '/root/3d/artifacts/award-demo',
                     '--out', 'evidence/award/demo/scenes', '--reuse-public-objects'])
    report['status'] = 'complete' if all(report['runs'].get(p, {}).get('summary') for p in plan['policies']) else 'incomplete_quota'
    report['completed_at'] = datetime.now(timezone.utc).isoformat()
    report['paid_ledger'] = 'outputs/generation/award-budget.json'
    save()
    C.atomic_json(ROOT / 'evidence/award/demo/result.json', report)
    print(json.dumps({'status': report['status'], 'scene': scene, 'label': plan['label']}))


if __name__ == '__main__':
    main()
