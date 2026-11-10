"""Read-only comparison of suite presentation with immutable raw run evidence."""
import json
import hashlib
from pathlib import Path
import subprocess
import sys

import numpy as np

from beforestep.navigation.controller import yaw_of

ROOT = Path(__file__).resolve().parents[1]


def check():
    summary = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    scratch = ROOT / 'outputs/qa/r2/suite-summary-recomputed.json'
    scratch.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(ROOT / 'ops/build_suite_summary.py'), '--out', str(scratch.relative_to(ROOT))]
    if summary['incomplete_scenes']:
        command.append('--allow-incomplete')
    subprocess.run(command,
                   cwd=ROOT, check=True, stdout=subprocess.PIPE)
    assert summary == json.loads(scratch.read_text()), 'Summary diverges from raw evidence'
    levels = json.loads((ROOT / 'site/data/levels.json').read_text())
    assert not levels['anchor_only_development']
    assert [r['id'] for r in levels['levels']] == [r['scene'] for r in summary['scenes']]
    assets = json.loads((ROOT / 'site/data/levels-assets.json').read_text())
    assert not assets['anchor_only_development']
    asset_names = {a['path'].removeprefix('site/') for a in assets['entries']}
    for asset in assets['entries']:
        path = ROOT / asset['path']
        assert path.stat().st_size == asset['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == asset['sha256']
    candidates, points = 0, 0
    for row, level in zip(summary['scenes'], levels['levels']):
        image = level['observation']
        assert hashlib.sha256((ROOT / 'site' / image['image']).read_bytes()).hexdigest() == image['image_sha256']
        original_image = ROOT / row['runs']['imagination']['run'] / 'looks/look1_rgb.png'
        assert hashlib.sha256(original_image.read_bytes()).hexdigest() == image['source_sha256']
        for key in ('optimistic', 'conservative', 'imagination'):
            run = row['runs'][key]
            shown = level['runs'][key]
            assert all(shown[k] == v for k, v in run['summary'].items())
            assert shown['run_id'] == run['run_id']
            with np.load(ROOT / run['run'] / 'traj.npz') as actual:
                for t, x, y, yaw in shown['trajectory']:
                    index = int(np.argmin(np.abs(actual['t']-t)))
                    assert abs(actual['t'][index]-t) < 1e-9
                    assert x == actual['qpos'][index, 0] and y == actual['qpos'][index, 1]
                    assert abs(yaw-yaw_of(actual['qpos'][index])) < 1e-10
                    points += 1
        for candidate in level['candidates']:
            decision = json.loads((ROOT / candidate['source_decision']).read_text())
            original = next(c for c in decision['candidates'] if c['id'] == candidate['sample'])
            assert original['admitted'] == candidate['admitted']
            for key in ('model', 'truth_model'):
                if candidate[key]:
                    assert candidate[key] in asset_names
            if candidate['model']:
                assert hashlib.sha256((ROOT / 'site' / candidate['model']).read_bytes()).hexdigest() == candidate['model_sha256']
            if original.get('glb'):
                assert hashlib.sha256((ROOT / original['glb']).read_bytes()).hexdigest() == candidate['original_glb_sha256']
            footprint = ROOT / candidate['source_decision']
            occupied = np.load(footprint.parent / ('footprint_'+candidate['sample']+'.npy'))
            from beforestep.navigation import map as N
            i, j = np.nonzero(occupied)
            assert candidate['footprint'] == np.c_[N.XS[i], N.YS[j]].tolist()
            candidates += 1
    suite = (ROOT / 'docs/suite.md').read_text().strip()
    generated_suite = ROOT / 'outputs/qa/r2/suite-document-recomputed.md'
    subprocess.run([sys.executable, str(ROOT / 'ops/write_suite_docs.py'), '--out',
                    str(generated_suite.relative_to(ROOT))], cwd=ROOT, check=True, stdout=subprocess.PIPE)
    assert suite == generated_suite.read_text().strip(), 'Published table differs from the recomputed raw result table'
    from integrate_suite import related_work_block
    related = (ROOT / 'docs/related-work.md').read_text()
    contribution = related.split('<!-- SUITE-CONTRIBUTION-START -->', 1)[1].split('<!-- SUITE-CONTRIBUTION-END -->', 1)[0].strip()
    assert contribution == related_work_block(summary), 'Related-work contribution differs from measured suite outcomes'
    report = (ROOT / 'docs/report.md').read_text()
    assert '<!-- SUITE-START -->' in report and '<!-- SUITE-END -->' in report
    block = report.split('<!-- SUITE-START -->', 1)[1].split('<!-- SUITE-END -->', 1)[0].strip()
    assert block == suite, 'Report suite chapter differs from the generated evidence table'
    homepage = (ROOT / 'site/index.html').read_text()
    for scene in summary['imagination_collision_scenes']:
        assert scene in homepage and '想象策略实际发生碰撞' in homepage
    assert 'levels.html' in homepage and 'id="suite-summary"' in homepage
    return {'schema': 'beforestep-suite-presentation-audit/v1', 'passed': True,
            'scenes': len(summary['scenes']), 'candidate_footprints': candidates,
            'actual_trajectory_points': points, 'raw_summary_recomputed_equal': True,
            'presentation_asset_sha_count': len(assets['entries']),
            'report_suite_chapter_matches': True, 'collision_scenes_prominent': summary['imagination_collision_scenes']}


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
