"""Confirm the final cut against terminal evidence without encoding twice."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from experimental.crossing.runtime import sha, write
from ops.crossing_route_video import narrations, OUT


if __name__ == '__main__':
    plan = json.loads((ROOT / 'evidence/crossing/route/additional-scenes.json').read_text())
    assert plan.get('selection_complete') and all(row['status'] == '终态' for row in plan['scenes'])
    summary = json.loads((ROOT / 'evidence/crossing/route/summary.json').read_text())
    assert summary['all_terminal']
    video_path = ROOT / 'evidence/crossing/route/video-v2.json'
    video = json.loads(video_path.read_text())
    assert sha(ROOT / video['path']) == video['sha256']
    captions, branch, errors = narrations()
    assert not errors, errors
    changed = []
    for shot in range(1, 10):
        metadata = json.loads((OUT / 'shots' / f'{shot}.json').read_text())
        if metadata['inputs']['text'] != captions[shot]:
            changed.append(shot)
    assert not changed, f'Terminal evidence changes captions in shots {changed}; update those shots before finalizing'
    assert video['branch'] == branch
    write(ROOT / 'evidence/crossing/route/video-v2-final.json', {
        'schema': 'beforestep-demo-video-final/v1', 'status': 'complete', 'path': video['path'],
        'sha256': video['sha256'], 'branch': branch, 'all_nine_captions_match_terminal_evidence': True,
        'first_scene_D_result': next(row['total_result'] for row in summary['rows'] if row['vehicle'] == 'D'),
        'current_summary_sha256': sha(ROOT / 'evidence/crossing/route/summary.json'),
        'numeric_audit_sha256': sha(OUT / 'numeric-audit.json'),
        'same_video_bytes_as_first_cut': True, 'additional_scenes_terminal': True,
        'responsible_reviewer_status': '待负责人看片', 'finished_at': datetime.now(timezone.utc).isoformat(),
    })
    checklist = ROOT / 'docs/hackathon-submission.md'
    text = checklist.read_text().replace('初版已合成并核验', '定版已合成并核验')
    checklist.write_text(text)
    print(json.dumps({'branch': branch, 'sha256': video['sha256'], 'terminal_captions_match': True}))
