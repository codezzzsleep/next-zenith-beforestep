"""Copy the project lead's homepage, changing asset paths only.

Use --out for a separate preview before changing the delivered site's homepage.
The author owns text/design; this tool does not fix acceptance discrepancies.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
MODEL_TASKS = {'A-A1':5958685, 'A-A2':5958690, 'A-B1':5958877,
               'A-B2':5958911, 'A-C1':5958948, 'A-C2':5959025,
               'B-A1':5958642, 'B-A2':5958654, 'B-B1':5958703,
               'B-C1':5958934, 'B-C2':5958937}


def bind(text, bindings):
    pattern = '|'.join(re.escape(key) for key in sorted(bindings, key=len, reverse=True))
    return re.sub(pattern, lambda match: bindings[match.group()], text)


def rebuild_data(out):
    """Regenerate canonical numbers, then apply the recorded URL bindings."""
    subprocess.run([sys.executable, str(ROOT / 'ops/build_home_data.py')], check=True)
    manifest = json.loads((out / 'homepage-integration.json').read_text())
    canonical = ROOT / 'evidence/award/home-contract/assets/data/site.json'
    (out / 'home-assets/data/site.json').write_text(bind(canonical.read_text(), manifest['path_bindings']))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='/root/3d/homepage')
    parser.add_argument('--out', required=True, help='Destination site directory or separate preview export')
    args = parser.parse_args()
    source, out = Path(args.source).resolve(), Path(args.out).resolve()
    assert source != out
    required = ['index.html', 'home.css', 'home.js', 'assets/data/site.json', 'vendor/model-viewer.min.js']
    assert all((source / p).is_file() for p in required), 'Homepage delivery is incomplete'
    assert sha(source / 'vendor/model-viewer.min.js') == sha(ROOT / 'site/vendor/model-viewer.min.js'), 'Use the existing vendored model viewer'
    subprocess.run([sys.executable, str(ROOT / 'ops/build_home_data.py')], check=True)
    canonical = ROOT / 'evidence/award/home-contract/assets/data/site.json'
    assert json.loads(canonical.read_text()) == json.loads((source / 'assets/data/site.json').read_text()), 'Delivered data contract changed'
    bindings = {'assets/': 'home-assets/'}
    for name, task in MODEL_TASKS.items():
        existing = ROOT / f'evidence/web-assets/models/{task}.glb'
        assert sha(existing) == sha(source / f'assets/glb/{name}.glb')
        bindings[f'assets/glb/{name}.glb'] = f'evidence/web-assets/models/{task}.glb'
    originals = {str(p.relative_to(source)): sha(p) for p in source.rglob('*')
                 if p.is_file() and ('dev' not in p.relative_to(source).parts) and p.name != 'INTEGRATION_EVIDENCE.md'}
    out.mkdir(parents=True, exist_ok=True)
    items = []
    for relative, digest in originals.items():
        path = source / relative
        if relative.startswith(('assets/glb/', 'vendor/')):
            continue
        target_relative = 'home-assets/' + relative.removeprefix('assets/') if relative.startswith('assets/') else relative
        target = out / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative in ('index.html', 'home.js', 'home.css'):
            text = path.read_text()
            target.write_text(bind(text, bindings))
            assert bind(target.read_text(), {v:k for k,v in bindings.items()}) == text
        elif relative.endswith('.json'):
            text = path.read_text()
            bound = bind(text, bindings)
            target.write_text(bound)
            restored = bind(bound, {v:k for k,v in bindings.items()})
            assert restored == text
        else:
            shutil.copy2(path, target)
            assert sha(target) == digest
        items.append({'source_path': relative, 'source_sha256': digest, 'path': target_relative,
                      'sha256': sha(target), 'bytes': target.stat().st_size})
    assert all(sha(source / p) == digest for p, digest in originals.items()), 'Source changed during integration; retry from a stable delivery'
    result = {'schema': 'beforestep-owner-homepage-integration/v1',
              'integrated_at': datetime.now(timezone.utc).isoformat(),
              'path_bindings': bindings, 'model_tasks': MODEL_TASKS,
              'canonical_data_sha256': sha(canonical), 'contract_field_equal': True,
              'design_and_copy_unchanged': True,
              'originals_unchanged': True, 'existing_model_viewer_exact': True, 'items': items,
              'acceptance_status': 'pending browser and number audit'}
    (out / 'homepage-integration.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'files': len(items), 'path_bindings': result['path_bindings'], 'design_and_copy_unchanged': True}))


if __name__ == '__main__':
    main()
