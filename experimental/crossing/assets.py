"""Prepare crossing fixtures from retained, SHA-bound source rock assets."""
import hashlib
import io
import json
import tarfile
from pathlib import Path
import numpy as np
import trimesh
from .runtime import ROOT, OUT, write, sha

ROCKS = ['rock_07', 'moon_rock_04', 'moon_rock_03']

def rock_fixture(name, height=.12, depth=.15, width=1.2):
    archive = ROOT / 'assets/runtime-rocks.tar.gz'
    folder = OUT / 'runtime/true-rocks' / f'{name}-h{height:.6f}-d{depth:.6f}-w{width:.6f}'
    manifest_path = folder / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        assert sha(folder / 'truth.stl') == manifest['parts_sha256']['truth.stl']
        return {'posed_dir': str(folder)}, manifest
    with tarfile.open(archive, 'r:gz') as source:
        metadata = json.load(source.extractfile(name + '/rock.json'))
        member = name + '/h1/body_vis.obj'
        payload = source.extractfile(member).read()
    original_sha = hashlib.sha256(payload).hexdigest()
    level = next(item for item in metadata['levels'] if item['level'] == 1)
    assert original_sha == level['vis_obj_sha256']
    mesh = trimesh.load(io.BytesIO(payload), file_type='obj', force='mesh', process=False)
    lo, hi = mesh.bounds
    scale = np.array([depth, width, height]) / (hi - lo)
    transform = np.eye(4)
    transform[:3, :3] = np.diag(scale)
    transform[:3, 3] = [-lo[0]*scale[0], -(lo[1]+hi[1])*.5*scale[1], -lo[2]*scale[2]]
    mesh.apply_transform(transform)
    folder.mkdir(parents=True, exist_ok=True)
    mesh.export(folder / 'truth.stl')
    mesh.export(folder / 'truth.glb')
    manifest = {'schema': 'beforestep-crossing-rock-fixture/v1', 'coordinate_frame': 'world',
                'parts': ['truth.stl'], 'parts_sha256': {'truth.stl': sha(folder / 'truth.stl')},
                'visual_glb_sha256': sha(folder / 'truth.glb'),
                'source': {'rock_id': name, 'archive': 'assets/runtime-rocks.tar.gz',
                           'archive_sha256': sha(archive), 'member': member,
                           'member_sha256': original_sha, 'url': metadata['source_url'],
                           'license': metadata['license'], 'authors': metadata['authors']},
                'world_from_source': transform.tolist(), 'bounds_m': mesh.bounds.tolist(),
                'nominal_dimensions_m': {'height': height, 'depth': depth, 'width': width},
                'note': 'Affine scaling gives common trial dimensions and spans the wheel tracks; these are source-shape variants, not newly observed rocks. MuJoCo mesh collision uses its convex hull.'}
    write(manifest_path, manifest)
    return {'posed_dir': str(folder)}, manifest

if __name__ == '__main__':
    for name in ROCKS:
        _, manifest = rock_fixture(name)
        print(json.dumps({'rock': name, 'dimensions': manifest['nominal_dimensions_m'],
                          'source_sha256': manifest['source']['member_sha256']}))
