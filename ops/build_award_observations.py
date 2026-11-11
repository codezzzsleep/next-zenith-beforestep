"""Publish real saved observations and an auditable two-view comparison."""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    first = ROOT / 'evidence/reviews/beforestep_r1/lux/original_b/looks'
    second = ROOT / 'evidence/reviews/beforestep_r1/section25_final_base/conservative/looks'
    media = ROOT / 'site/media/award'
    media.mkdir(parents=True, exist_ok=True)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(first / 'look1_rgb.png') == sha(second / 'look1_rgb.png')
    assert sha(first / 'look1_state.npy') == sha(second / 'look1_state.npy')
    sources = []
    for source, name in [(first / 'look1_rgb.png', 'first.png'),
                         (second / 'look2_rgb.png', 'second.png')]:
        target = media / name
        shutil.copy2(source, target)
        sources.append({'path': str(source.relative_to(ROOT)), 'sha256': sha(source),
                        'published_path': str(target.relative_to(ROOT)), 'published_sha256': sha(target)})
    dark = np.load(first / 'look1_dark.npy').astype(bool)
    depth = np.load(first / 'look1_depth.npy')
    # Remove the recorded far-plane sky pixels only from the visual annotation.
    # Neither the original mask nor any sensor/planner data is changed.
    display_dark = dark & (depth < np.max(depth))
    rgba = np.zeros((*dark.shape, 4), dtype=np.uint8)
    rgba[display_dark] = [242, 174, 79, 80]
    Image.fromarray(rgba).save(media / 'dark-overlay.png')
    labels = []
    for target, label in [('T1', 'A'), ('T2', 'B')]:
        mask = np.asarray(Image.open(first / 'look1' / target / 'mask.png')) > 0
        if mask.ndim == 3:
            mask = mask.any(axis=2)
        y, x = np.where(mask)
        labels.append({'label': label, 'x_percent': float(x.mean() / mask.shape[1] * 100),
                       'y_percent': float(y.mean() / mask.shape[0] * 100),
                       'source': str((first / 'look1' / target / 'mask.png').relative_to(ROOT))})
    a = np.load(first / 'look1_state.npy')
    b = np.load(second / 'look2_state.npy')
    from beforestep.navigation import map as N
    data = {'schema': 'beforestep-award-observations/v1', 'scene': 'stress_v8',
            'sources': sources, 'labels': labels,
            'dark_mask_source': str((first / 'look1_dark.npy').relative_to(ROOT)),
            'dark_mask_sha256': sha(first / 'look1_dark.npy'),
            'display_mask_rule': 'Original DARK mask minus pixels at the recorded maximum depth (far-plane sky); annotation only.',
            'map': {'shape': list(a.shape), 'origin': [N.X0, N.Y0], 'resolution': N.RES,
                    'first': a.ravel().tolist(), 'second': b.ravel().tolist()},
            'map_sources': [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for p in
                           [first / 'look1_state.npy', second / 'look2_state.npy']],
            'hidden_to_observed_cells': int(np.sum((a == N.HIDDEN) & (b < N.DARK))),
            'scope': 'Two actual recorded viewpoints, not interpolated camera motion. '
                     'The solar panel keeps the first RGB and its recorded DARK mask as a fixed reference. '
                     'The map switches to the actual second-view classification; DARK is not a perfect physical shadow label.'}
    path = ROOT / 'site/data/award-observations.json'
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n')
    evidence = ROOT / 'evidence/award'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / 'observations.json').write_text(json.dumps({k: v for k, v in data.items() if k != 'map'},
                                                        ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'same_first_view': True, 'labels': labels,
                      'hidden_to_observed_cells': data['hidden_to_observed_cells']}))


if __name__ == '__main__':
    main()
