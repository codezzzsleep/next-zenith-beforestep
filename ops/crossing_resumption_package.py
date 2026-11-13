"""Preserve resumption originals once; reuse the completed zero-paid archive."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops.crossing_development_evidence import bundle


if __name__ == '__main__':
    folder = ROOT / 'outputs/crossing/development/scene-dev-v5/seed-11002'
    files = [p for p in folder.rglob('*') if p.is_file() and
             any(part.startswith('lux') or part == 'decision' or part.startswith('method-D') for part in p.parts)]
    report = json.loads((folder / 'lux-development.json').read_text())
    for task in report['task_ids']:
        files += [p for p in (ROOT / 'assets/candidates' / str(task)).rglob('*') if p.is_file()]
    files += [ROOT / 'evidence/crossing' / name for name in
              ['development-lux-scene-dev-v5-11002.json', 'development-stop-scene-dev-v5.json',
               'development-resumption.json']]
    lux = bundle('resume-20261113-real-lux', sorted(set(files)))
    index = {'schema': 'beforestep-crossing-resumption-artifacts/v1',
             'zero_paid': json.loads((ROOT / 'evidence/crossing/development/resume-20261113-zero-paid-manifest.json').read_text()),
             'lux': lux, 'formal_test_scenes': 0}
    (ROOT / 'evidence/crossing/development/resumption-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'lux_bytes': lux['bytes'], 'member_sha_check': lux['member_sha_check']}))
