"""Expose all original render data as retrievable repository paths for R3."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from beforestep import scene as S
from beforestep.visualization import textures as T
from beforestep.geometry import imagination as IM

ROOT = S.ROOT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    suite = json.loads((ROOT / 'evidence/suite/summary.json').read_text())
    tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
    objects = {}
    for manifest in (ROOT / 'evidence/suite/scenes').glob('*/manifest.json'):
        for item in json.loads(manifest.read_text())['files']:
            if item.get('public_object'):
                objects.setdefault(item['sha256'], item['public_object'])
    preserved = {}

    def expose(path, asset=False, preferred=None):
        # Machine-local vendor aliases may point at historical evidence. The
        # new public object retains bytes and a portable repository path.
        path = path.absolute()
        assert path.is_relative_to(ROOT) and path.is_file(), str(path)
        relative = str(path.relative_to(ROOT)); digest = sha(path)
        if relative in tracked and (not asset or relative.startswith('assets/')):
            public, encoding = relative, 'identity'
        elif preferred and preferred in tracked and sha(ROOT / preferred) == digest:
            public, encoding = preferred, 'identity'
        elif not asset and digest in objects:
            public, encoding = objects[digest], 'gzip'
        else:
            folder = 'assets/video/objects' if asset else 'evidence/video/objects'
            public = folder + '/' + digest + '.gz'; destination = ROOT / public
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                with path.open('rb') as source, destination.open('wb') as output:
                    with gzip.GzipFile(filename='', fileobj=output, mode='wb', mtime=0) as compressed:
                        while chunk := source.read(1 << 20):
                            compressed.write(chunk)
            encoding = 'gzip'
        record = {'original_path': relative, 'path': public, 'encoding': encoding,
                  'sha256': digest, 'bytes': path.stat().st_size}
        preserved[public] = record
        return record

    selected = []
    anchor = suite['scenes'][0]
    for name, run in anchor['runs'].items():
        selected.append(('stress_v8', name, ROOT / run['run']))
    base = ROOT / 'evidence/reviews/beforestep_r1'
    selected.append(('stress_v8', 'replay', base / 'lux/replay'))
    selected.extend(('stress_v8', 'trust_' + name, base / 'counterfactuals' / name)
                    for name in ('A1', 'B1', 'C2'))
    for scene in suite['scenes']:
        if scene['scene'] in ('suite_r2_v4_F1_020', 'suite_r2_v4_F3_004'):
            selected.extend((scene['scene'], name, ROOT / run['run']) for name, run in scene['runs'].items())
    # Later R3 runs use their own new namespace; originals are never overwritten.
    strict = ROOT / 'outputs/reviews/r3/strict-video-runs.json'
    if strict.exists():
        selected.extend((row['scene'], 'imagination_strict', ROOT / row['run'])
                        for row in json.loads(strict.read_text()))
    records = []
    world_cache = {}
    for scene, name, public_run in selected:
        preservation = public_run / 'preservation.json'
        source = public_run
        if preservation.exists():
            source = ROOT / json.loads(preservation.read_text())['original_output']
        assert source.is_dir(), str(source)
        summary = json.loads((source / 'summary.json').read_text())
        identity = json.loads((source / 'run_identity.json').read_text())
        files = []
        for path in sorted(source.rglob('*')):
            if not path.is_file() or 'lux_cache' in path.parts or '__pycache__' in path.parts:
                continue
            preferred = str((public_run / path.relative_to(source)).relative_to(ROOT))
            files.append({'run_relative_path': str(path.relative_to(source)),
                          **expose(path, preferred=preferred)})
        names = {row['run_relative_path'] for row in files}
        assert {'scene.json', 'summary.json', 'events.jsonl', 'traj.npz'} <= names
        for filename in ('eval.json', 'physical_clearance.json'):
            if filename in names:
                continue
            existing = public_run / filename
            sidecar = ROOT / 'outputs/video/r3/reviews' / identity['run_id'] / filename
            review = existing if existing.exists() else sidecar
            if review.exists():
                files.append({'run_relative_path': filename, 'post_run_sidecar': review == sidecar,
                              **expose(review)})
            else:
                raise ValueError(f'Missing requested video diagnostic: {scene}/{name}/{filename}')
        candidates = []
        for decision in sorted(source.glob('looks/look*/T*/decide/target_decision.json')):
            value = json.loads(decision.read_text())
            for candidate in value['candidates']:
                world = decision.parent / ('world_' + candidate['id'] + '.obj')
                if not world.exists() and candidate.get('glb'):
                    state = json.loads((decision.parent.parent / 'state.json').read_text())
                    key = hashlib.sha256(json.dumps({'glb': candidate['glb'], 'M': candidate['M'],
                        'frame': state['local_frame']}, sort_keys=True).encode()).hexdigest()
                    world = ROOT / 'outputs/video/r3/candidates' / key / 'world.obj'
                    if not world.exists():
                        world.parent.mkdir(parents=True, exist_ok=True)
                        IM.candidate_world_mesh(candidate['glb'], candidate['M'], state['local_frame'], world)
                    world_cache[key] = world
                candidates.append({'look': decision.parents[2].name, 'target': decision.parents[1].name,
                    'id': candidate['id'], 'admitted': candidate['admitted'],
                    'metrics': candidate, 'world': expose(world) if world.exists() else None})
                if candidate.get('glb'):
                    expose(ROOT / candidate['glb'], asset=True)
        S.configure(scene)
        work = ROOT / 'outputs/video/r3' / scene
        spec, _, meta = S.scene_spec(work)
        render_assets = [expose(Path(spec['terrain']['custom_height_file']), asset=True)]
        render_assets.extend(expose(Path(obj['mesh_file']), asset=True) for obj in spec['objects'])
        for rock in S.ROCKS.values():
            _, texture = S.rock_asset_uniform(rock['rock'], rock['height'])
            if texture:
                render_assets.append(expose(Path(texture), asset=True))
        if S.TERRAIN['right_wall']:
            for rock_id in S.WALL_ROCKS:
                _, texture = S.rock_asset_uniform(rock_id, 1.0)
                if texture:
                    render_assets.append(expose(Path(texture), asset=True))
        render_assets.extend(expose(path, asset=True) for path in
                             (T.regolith_texture(), T.sky_texture(), T.earth_texture()))
        robot = ROOT / 'vendor/unitree_mujoco/unitree_robots/go2w'
        render_assets.extend(expose(path, asset=True) for path in robot.rglob('*')
                             if path.is_file() and (path.name == 'go2w.xml' or 'assets' in path.parts))
        records.append({'scene': scene, 'strategy': name, 'run_id': identity['run_id'],
                        'source_run': str(source.relative_to(ROOT)), 'summary': summary,
                        'files': files, 'candidates': candidates,
                        'render_assets': {row['original_path']: row for row in render_assets},
                        'scene_spec': spec, 'scene_metadata': meta})
        print(json.dumps({'scene': scene, 'strategy': name, 'files': len(files)}, ensure_ascii=False), flush=True)
    index = {'schema': 'beforestep-video-data-index/v1',
        'scope': 'Recorded original physics data and assets for owner video rendering; no video rendered by agent',
        'retrieval': 'Clone the repository and git lfs pull. Identity paths are original bytes; gzip paths decompress to the recorded original_path and SHA. No external archive is required.',
        'runs': records, 'objects': preserved}
    out = ROOT / 'evidence/video'; out.mkdir(parents=True, exist_ok=True)
    (out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'runs': len(records), 'unique_public_objects': len(preserved)}), flush=True)


if __name__ == '__main__':
    main()
