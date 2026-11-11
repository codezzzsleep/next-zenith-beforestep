"""Check that every indexed original byte and requested render item is present."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    index = json.loads((ROOT / 'evidence/video/index.json').read_text())
    checked = set()
    for record in index['objects'].values():
        path = ROOT / record['path']
        assert path.is_file(), record['path']
        data = gzip.decompress(path.read_bytes()) if record['encoding'] == 'gzip' else path.read_bytes()
        assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256'], record['path']
        checked.add(record['path'])
    for row in index['runs']:
        names = {item['run_relative_path'] for item in row['files']}
        assert {'scene.json','summary.json','events.jsonl','traj.npz','eval.json','physical_clearance.json'} <= names
        summary = row['summary']
        for look in range(1, summary['looks'] + 1):
            for suffix in ('rgb.png','depth.npy','dark.npy','state.npy','zmax.npy'):
                assert f'looks/look{look}_{suffix}' in names, (row['run_id'], look, suffix)
        for candidate in row['candidates']:
            assert candidate['world'] is not None and candidate['world']['path'] in checked
        assert row['render_assets']
        assert all(value['path'].startswith('assets/') and value['path'] in checked
                   for value in row['render_assets'].values())
    result = {'passed': True, 'runs': len(index['runs']), 'unique_public_byte_objects': len(checked),
              'all_required_arrays_meshes_reviews_assets_present': True,
              'source': 'evidence/video/index.json'}
    out = ROOT / 'evidence/reviews/beforestep_r3/video-index-check.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
