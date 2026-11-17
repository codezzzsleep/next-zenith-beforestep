"""Build the M20 visual meshes for the existing browser simulation.

The source is DeepRoboticsLab/deep_robotics_model, commit 52352f5. This only
changes displayed geometry; it does not replace the simulated robot.
Usage: python build_m20_skin.py /path/to/deep_robotics_model
"""
import argparse
import gzip
import json
import shutil
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE_COMMIT = '52352f5bbf2a30b5d02ece91900415188e7abc74'
PARTS = ['base_link'] + [f'{leg}_{part}' for leg in ('fl', 'fr', 'hl', 'hr') for part in ('hipx', 'hipy', 'knee', 'wheel')]
DTYPE = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])


def load_stl(path):
    with path.open('rb') as source:
        source.read(80)
        count = struct.unpack('<I', source.read(4))[0]
        triangles = np.fromfile(source, dtype=DTYPE, count=count)
    if len(triangles) != count:
        raise ValueError(f'Truncated binary STL: {path}')
    return triangles['vertices'].reshape(-1, 3).astype(np.float64)


def adapt(part, vertices):
    # Fit the official M20 visual links to the existing Go2W body frames.
    # This transformation affects visual mesh vertices only.
    v = vertices.copy()
    if part == 'base_link':
        v *= [0.1934 / 0.3141, 0.0465 / 0.0685, 0.85]
    elif part.endswith('_hipx'):
        v *= [0.85, 0.80, 0.85]
    elif part.endswith('_hipy'):
        side = 1 if part.startswith(('fl_', 'hl_')) else -1
        v[:, 1] -= side * 0.0955
        v *= [0.85, 1.0, 0.213 / 0.25]
    elif part.endswith('_knee'):
        side = 1 if part.startswith(('fl_', 'hl_')) else -1
        v[:, 1] -= side * 0.059676 * np.clip(-v[:, 2] / 0.25, 0, 1)
        v *= [0.85, 1.0, 0.2264 / 0.25]
    else:
        v *= 0.086 / 0.09
    return v


def compact(vertices):
    # Merge nearby STL vertices to reduce bandwidth while retaining the
    # original triangular surface and silhouette for real-time rendering.
    cells = np.rint(vertices / 0.0025).astype(np.int32)
    _, first, inverse = np.unique(cells, axis=0, return_index=True, return_inverse=True)
    faces = inverse.reshape(-1, 3)
    faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
    return {'positions': np.round(vertices[first], 5).flatten().tolist(), 'indices': faces.flatten().tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model_repo', type=Path)
    args = parser.parse_args()
    mesh_dir = args.model_repo / 'M20/mjcf/meshes'
    parts = {name: compact(adapt(name, load_stl(mesh_dir / f'{name}.STL'))) for name in PARTS}
    skin = {'source': 'DeepRoboticsLab/deep_robotics_model', 'commit': SOURCE_COMMIT, 'parts': parts}
    output = ROOT / 'site/media/mission/m20-skin.json.gz'
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('wb') as stream:
        with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as zipped:
            zipped.write(json.dumps(skin, separators=(',', ':')).encode())
    credit = ROOT / 'site/media/mission/m20'
    credit.mkdir(exist_ok=True)
    shutil.copyfile(args.model_repo / 'LICENSE.txt', credit / 'LICENSE.txt')
    (credit / 'README.txt').write_text(
        'M20 visual geometry adapted from DeepRoboticsLab/deep_robotics_model\n'
        f'https://github.com/DeepRoboticsLab/deep_robotics_model/tree/{SOURCE_COMMIT}/M20\n'
        'The mesh is scaled and fitted to the existing simulated robot.\n'
        'The original simulation, collision geometry and controls are unchanged.\n', encoding='utf-8')
    print(f'{output}: {output.stat().st_size:,} bytes; {len(parts)} parts')


if __name__ == '__main__':
    main()
