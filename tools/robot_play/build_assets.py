"""Package original Go2W meshes and retained Lux3D hypotheses for browser physics."""
from pathlib import Path
import argparse
import gzip
import hashlib
import io
import json
import tarfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh


def build(repo, output):
    robot = repo / 'vendor/unitree_mujoco/unitree_robots/go2w'
    tree = ET.fromstring((robot / 'go2w.xml').read_bytes())
    tree.set('model', 'BeforeStep interactive driving')
    tree.find('compiler').set('meshdir', '/play/assets')
    option = tree.find('option')
    option.set('gravity', '0 0 -1.62')
    option.set('timestep', '0.002')
    option.set('iterations', '30')
    assets = tree.find('asset')
    world = tree.find('worldbody')
    buffers = {}
    sources = []
    display = {}

    def display_mesh(name, content, pitch=.006):
        suffix = name.rsplit('.', 1)[-1]
        mesh = trimesh.load(io.BytesIO(content), file_type=suffix, force='mesh', process=False)
        vertices = np.asarray(mesh.vertices)
        cells = np.floor(vertices / pitch).astype(np.int64)
        _, inverse = np.unique(cells, axis=0, return_inverse=True)
        count = np.bincount(inverse)
        reduced = np.column_stack([np.bincount(inverse, weights=vertices[:, j]) / count for j in range(3)])
        faces = inverse[np.asarray(mesh.faces)]
        faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 2] != faces[:, 0])]
        _, indices = np.unique(np.sort(faces, axis=1), axis=0, return_index=True)
        faces = faces[np.sort(indices)]
        display[name.rsplit('.', 1)[0]] = {'positions': reduced.ravel().tolist(), 'indices': faces.ravel().tolist(),
            'original_faces': len(mesh.faces), 'display_faces': len(faces), 'display_grid_m': pitch}

    def add(name, content, source=None):
        buffers[name] = content
        entry = {'file': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
        if source:
            entry['source'] = str(source.relative_to(repo))
            entry['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        sources.append(entry)

    for mesh in assets.findall('mesh'):
        p = robot / 'assets' / mesh.get('file')
        add('assets/' + p.name, p.read_bytes(), p)
        display_mesh(p.name, p.read_bytes())
    ET.SubElement(world, 'geom', name='ground', type='plane', size='15 10 .1',
                  friction='.9 .02 .001', rgba='.36 .33 .28 1')
    for name, pos, size in [('edge_left', '5 3 .15', '7 .06 .15'),
                            ('edge_right', '5 -3 .15', '7 .06 .15'),
                            ('edge_back', '-1.5 0 .15', '.06 3 .15'),
                            ('edge_end', '11.7 0 .15', '.06 3 .15')]:
        ET.SubElement(world, 'geom', name=name, type='box', pos=pos, size=size,
                      friction='.9 .02 .001', rgba='.23 .24 .25 1')
    for label, name, height in [('A', 'rock_07', .55), ('B', 'moon_rock_04', .42)]:
        src = repo / 'assets/rocks' / name / 'h0/body.stl'
        mesh = trimesh.load(src, force='mesh', process=False)
        mesh.vertices -= np.array([0., 0., mesh.bounds[0, 2]])
        mesh.vertices *= height / mesh.extents[2]
        filename = 'rock_' + label + '.stl'
        add('assets/' + filename, mesh.export(file_type='stl'), src)
        display_mesh(filename, buffers['assets/' + filename], .018)
        ET.SubElement(assets, 'mesh', name='rock_' + label, file=filename)
        body = ET.SubElement(world, 'body', name='rock_body_' + label, pos='100 0 0')
        ET.SubElement(body, 'geom', name='rock_' + label, type='mesh', mesh='rock_' + label,
                      rgba='.57 .51 .43 1', friction='.9 .02 .001')
    ET.SubElement(world, 'geom', name='threshold', type='box', pos='1.82 0 .06',
                  size='.02 3 .06', rgba='.66 .58 .43 1', friction='.9 .02 .001')
    gallery = json.loads((repo / 'site/data/gallery.json').read_text())
    models = []
    for target, task in [('T1', 5958685), ('T2', 5958654)]:
        item = next(r for r in gallery['models'] if r['task_id'] == task)
        context = next(c for c in item['contexts'] if c['run'] == 'evidence/reviews/beforestep_r1/lux/original_b')
        assert context['admitted'] and context['target'] == target
        src = repo / 'assets/candidates' / str(task) / 'tex_mesh.glb'
        mesh = trimesh.load(src, force='mesh')
        mesh.apply_transform(np.array(context['world_from_generated']))
        label = 'A' if target == 'T1' else 'B'
        name = 'hypothesis_' + label
        add('assets/' + name + '.stl', mesh.export(file_type='stl'), src)
        display_mesh(name + '.stl', buffers['assets/' + name + '.stl'], .018)
        ET.SubElement(assets, 'mesh', name=name, file=name + '.stl')
        ET.SubElement(world, 'geom', name=name, type='mesh', mesh=name, contype='0',
                      conaffinity='0', group='4', rgba='.25 .92 .71 .4')
        from scipy.spatial import ConvexHull
        vertices = mesh.vertices[:, :2]
        polygon = vertices[ConvexHull(vertices).vertices].tolist()
        models.append({'label': label, 'task_id': task, 'admitted': True, 'polygon': polygon,
                       'source_sha256': item['source_sha256'],
                       'registration': context['world_from_generated'],
                       'input': item['input'], 'original_model': 'assets/candidates/' + str(task) + '/tex_mesh.glb',
                       'note': 'Retained R1 generated hypothesis, reused for this independent driving playground.'})
    xml = ET.tostring(tree, encoding='utf-8')
    add('scene.xml', xml)
    output.mkdir(parents=True, exist_ok=True)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, content in buffers.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(content))
    packed = gzip.compress(raw.getvalue(), compresslevel=9, mtime=0)
    (output / 'world.tar.gz').write_bytes(packed)
    (output / 'display.json.gz').write_bytes(gzip.compress(json.dumps(display, separators=(',', ':')).encode(), compresslevel=9, mtime=0))
    manifest = {'schema': 'beforestep-robot-play/v1', 'engine': 'MuJoCo 3.17.0',
                'robot': 'Original Unitree Go2W mesh, inertial, joints and actuator model',
                'scope': 'New browser driving playground. Not an R1/R2/R3 research result or a new Lux3D request.',
                'changes': ['Lunar gravity 1.62', '2ms timestep', '30 solver iterations',
                            'Independent training/playground scenery', 'Retained model hypotheses are non-colliding overlays',
                            '12cm threshold at fixed compiled position; collision masks disabled outside threshold course'],
                'files': sources, 'models': models, 'bundle_sha256': hashlib.sha256(packed).hexdigest(),
                'bundle_bytes': len(packed)}
    manifest['display_meshes'] = {name: {k: value for k, value in row.items() if k not in ['positions', 'indices']} for name, row in display.items()}
    manifest['display_only'] = 'Grid-clustered display meshes. Original collision meshes, joint and inertial model remain unchanged.'
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (output / 'UNITREE_LICENSE').write_bytes((repo / 'vendor/unitree_mujoco/LICENSE').read_bytes())
    print(json.dumps({'bundle_bytes': len(packed), 'files': len(buffers), 'models': [m['task_id'] for m in models]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)
