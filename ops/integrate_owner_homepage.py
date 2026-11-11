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

ROOT = Path(__file__).resolve().parents[1]


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
    originals = {str(p.relative_to(source)): sha(p) for p in source.rglob('*')
                 if p.is_file() and ('dev' not in p.relative_to(source).parts) and p.name != 'INTEGRATION_EVIDENCE.md'}
    out.mkdir(parents=True, exist_ok=True)
    items = []
    for relative, digest in originals.items():
        path = source / relative
        target_relative = 'home-assets/' + relative.removeprefix('assets/') if relative.startswith('assets/') else relative
        target = out / target_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative in ('index.html', 'home.js', 'home.css'):
            text = path.read_text()
            target.write_text(text.replace('assets/', 'home-assets/'))
            assert target.read_text().replace('home-assets/', 'assets/') == text
        elif relative.endswith('.json'):
            text = path.read_text()
            bound = text
            for asset in originals:
                if asset.startswith('assets/'):
                    bound = bound.replace(json.dumps(asset), json.dumps('home-assets/' + asset.removeprefix('assets/')))
            target.write_text(bound)
            restored = bound
            for asset in originals:
                if asset.startswith('assets/'):
                    restored = restored.replace(json.dumps('home-assets/' + asset.removeprefix('assets/')), json.dumps(asset))
            assert restored == text
        else:
            shutil.copy2(path, target)
            assert sha(target) == digest
        items.append({'source_path': relative, 'source_sha256': digest, 'path': target_relative,
                      'sha256': sha(target), 'bytes': target.stat().st_size})
    assert all(sha(source / p) == digest for p, digest in originals.items()), 'Source changed during integration; retry from a stable delivery'
    result = {'schema': 'beforestep-owner-homepage-integration/v1',
              'integrated_at': datetime.now(timezone.utc).isoformat(),
              'path_bindings': {'assets/': 'home-assets/'}, 'design_and_copy_unchanged': True,
              'originals_unchanged': True, 'existing_model_viewer_exact': True, 'items': items,
              'acceptance_status': 'pending browser, number audit and real first-screen feedback'}
    (out / 'homepage-integration.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'files': len(items), 'path_bindings': result['path_bindings'], 'design_and_copy_unchanged': True}))


if __name__ == '__main__':
    main()
