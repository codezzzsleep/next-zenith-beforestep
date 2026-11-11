"""Select the first unused decisive seed before any demonstration result."""
import hashlib
import json
from pathlib import Path

from run_suite_imagination import sources

ROOT = Path(__file__).resolve().parents[1]


def main():
    pool = ROOT / 'evidence/suite/pool/r2_v4/manifest_F0_F1_F2_F3_1_12_results.json'
    data = json.loads(pool.read_text())
    original = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    r3 = json.loads((ROOT / 'evidence/reviews/beforestep_r3/experiment-plan.json').read_text())
    used = {r['scene'] for r in original['scenes']} | {r['scene'] for r in r3['holdouts']}
    # A scene already present in the real paid ledgers is also unavailable.
    for name in ['r3-budget.json', 'suite-budget.json']:
        path = ROOT / 'outputs/generation' / name
        if path.exists():
            used |= {r['scene'] for r in json.loads(path.read_text())['tasks'].values() if r.get('task_id')}
    candidates = [r for r in data['scenes'].values() if r['scene'] not in used]
    selected = sorted((r for r in candidates if r['classification'] == 'decisive'),
                      key=lambda r: (r['seed'], r['family']))
    rule = 'first unused decisive by seed, family only breaks equal-seed ties'
    if not selected:
        selected = sorted((r for r in candidates if r['classification'] == 'ordinary'),
                          key=lambda r: (r['seed'], r['family']))
        rule = 'no unused decisive; first unused ordinary by seed'
    assert selected
    row = selected[0]
    plan = {'schema': 'beforestep-award-demo-plan/v1', 'scene': row['scene'], 'seed': row['seed'],
            'classification': row['classification'], 'selection_rule': rule,
            'eligible_in_order': [r['scene'] for r in selected], 'already_used': sorted(used),
            'pool': str(pool.relative_to(ROOT)), 'pool_sha256': hashlib.sha256(pool.read_bytes()).hexdigest(),
            'scene_config': row['path'], 'scene_config_sha256': hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(),
            'source_sha256': sources(),
            'expectation': 'Complete the six columns; original and strict real imagination should arrive without collision. Preserve stops, collisions and quota-interrupted attempts without changing the selected scene.',
            'policies': ['conservative', 'see_dark', 'optimistic', 'truth', 'imagination', 'imagination_strict'],
            'new_task_limit': 30, 'cumulative_limit': 316,
            'condition': 'P1/P2 completed before 2026-11-15T04:00:00Z',
            'label': '赛后补充演示运行，不参与结论、不作为泛化证据'}
    out = ROOT / 'evidence/award/demo/plan.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        assert json.loads(out.read_text()) == plan, 'Do not reselect a declared demonstration'
    else:
        out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    result = ROOT / 'docs/reviews/RESULT_HACKATHON_AWARD.md'
    if '## P3 运行前声明' not in result.read_text():
        result.write_text(result.read_text() + f"\n## P3 运行前声明\n\n选定 `{row['scene']}`（种子 {row['seed']}，{row['classification']}），按原候选池中未用决定性场景的种子顺序，类别仅用于同种子打破并列。开跑前提交 [固定计划](../../evidence/award/demo/plan.json)。预期两种真实想象完整无碰撞到达；实际失败照实保留，不换场景。四基线与原/修订共六栏，首眼同字节复用；新增≤30、累计≤316/360。P1/P2 按时完成后才执行。**赛后补充演示运行，不参与结论、不作为泛化证据。**\n")
    print(json.dumps({'scene': row['scene'], 'seed': row['seed'], 'selection_rule': rule}))


if __name__ == '__main__':
    main()
