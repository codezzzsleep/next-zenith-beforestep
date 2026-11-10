"""One SHA manifest per scene, complete external archive and a bounded review set.

The public set stores exact bytes in content-addressed gzip objects, preserving
duplicate observation/trajectory identities without repeated binary copies.
Raw generated GLBs are retained in the complete archive. Private upload ledgers
and authentication files are never read or included.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 150_000_000
ESSENTIAL = {'traj.npz', 'events.jsonl', 'summary.json', 'run_identity.json', 'scene.json',
             'eval.json', 'physical_clearance.json', 'standin_provenance.json'}
TARGET_FILES = {'state.json', 'observation.json', 'camera_world.json', 'cells.npy',
                'visible_points.npy', 'lux_request.json', 'lux_result.json'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_file(path, relative):
    if relative.name in ESSENTIAL or relative.name in TARGET_FILES:
        return True
    if 'looks' in relative.parts and len(relative.parts) == 2:
        return relative.suffix in ('.png', '.npy')
    if 'gen' in relative.parts:
        return relative.suffix in ('.png', '.jpg', '.json')
    if 'decide' in relative.parts:
        return (relative.name == 'target_decision.json' or relative.name.startswith(('footprint_', 'world_'))
                or relative.name == 'align.json')
    return 'rehearsal' in relative.parts and relative.name in ('traj.npz', 'pane.json')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', required=True)
    parser.add_argument('--runs', required=True, help='JSON mapping variant names to completed run directories')
    parser.add_argument('--extras', help='JSON list of this scene\'s real/review/CF trees, including failed attempts')
    parser.add_argument('--archive-dir', default='/root/3d/artifacts/beforestep-r2')
    parser.add_argument('--out', default='evidence/suite/scenes')
    args = parser.parse_args()
    mapping = json.loads((ROOT / args.runs).read_text())
    files = {}
    selected = set()
    runs = {}
    for name, relative_root in mapping.items():
        directory = (ROOT / relative_root).resolve()
        assert directory.is_relative_to(ROOT)
        summary = json.loads((directory / 'summary.json').read_text())
        assert summary['scene_id'] == args.scene
        runs[name] = {'source': str(directory.relative_to(ROOT)), 'summary': summary,
                      'run_id': json.loads((directory / 'run_identity.json').read_text())['run_id']}
        for path in directory.rglob('*'):
            if not path.is_file() or 'lux_cache' in path.parts:
                continue
            # The complete archive contains raw run artifacts, not transport caches.
            repo_path = str(path.relative_to(ROOT))
            files[repo_path] = path
            if public_file(path, path.relative_to(directory)):
                selected.add(repo_path)
        for result in directory.glob('looks/look*/T*/**/lux_result.json'):
            for task in json.loads(result.read_text()).get('tasks', []):
                if task.get('glb'):
                    path = ROOT / task['glb']
                    assert path.is_file() and sha(path) == task['glb_sha256']
                    files[str(path.relative_to(ROOT))] = path
    extras = json.loads((ROOT / args.extras).read_text()) if args.extras else []
    for relative_root in extras:
        directory = (ROOT / relative_root).resolve()
        assert directory.is_relative_to(ROOT / 'outputs/suite') and directory.name == args.scene
        for path in directory.rglob('*'):
            if not path.is_file() or 'lux_cache' in path.parts:
                continue
            relative = str(path.relative_to(ROOT))
            files[relative] = path
            if path.name in ('chain.json', 'counterfactuals.json'):
                selected.add(relative)
    output = ROOT / args.out / args.scene
    output.mkdir(parents=True, exist_ok=True)
    archive_dir = Path(args.archive_dir).resolve()
    assert not archive_dir.is_relative_to(ROOT)
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / (args.scene + '-complete.tar.gz')
    temporary = archive.with_suffix('.tmp')
    entries = []
    seen = {}
    with tarfile.open(temporary, 'w:gz', compresslevel=6) as tar:
        for relative, path in sorted(files.items()):
            digest = sha(path)
            entry = {'path': relative, 'sha256': digest, 'bytes': path.stat().st_size}
            entries.append(entry)
            info = tar.gettarinfo(str(path), arcname='repo/' + relative)
            info.mtime = 0; info.uid = info.gid = 0; info.uname = info.gname = ''
            # Store file bytes even when a runtime asset is a machine-local
            # symlink. The portable archive must not depend on its old target.
            info.type = tarfile.REGTYPE; info.linkname = ''; info.size = path.stat().st_size
            if digest in seen:
                info.type = tarfile.LNKTYPE; info.linkname = seen[digest]; info.size = 0
                tar.addfile(info)
            else:
                with path.open('rb') as stream:
                    tar.addfile(info, stream)
                seen[digest] = info.name
    temporary.replace(archive)
    # Every retained public byte has the same SHA as the original artifact.
    objects = output / 'objects'
    objects.mkdir(exist_ok=True)
    # Small direct files make identities and results readable on GitHub without
    # requiring a local restore of the content-addressed review data.
    for name, record in runs.items():
        public_run = output / 'runs' / name
        public_run.mkdir(parents=True, exist_ok=True)
        for filename in ('summary.json', 'run_identity.json', 'eval.json', 'physical_clearance.json'):
            source = ROOT / record['source'] / filename
            if source.exists():
                shutil.copyfile(source, public_run / filename)
    for entry in entries:
        if entry['path'] not in selected:
            continue
        blob = objects / (entry['sha256'] + '.gz')
        if not blob.exists():
            with files[entry['path']].open('rb') as source, blob.open('wb') as destination:
                with gzip.GzipFile(filename='', mode='wb', fileobj=destination, mtime=0) as compressed:
                    shutil.copyfileobj(source, compressed)
        assert hashlib.sha256(gzip.decompress(blob.read_bytes())).hexdigest() == entry['sha256']
        entry['public_object'] = str(blob.relative_to(ROOT))
    size = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    if size >= LIMIT:
        raise ValueError(f'Public scene review set exceeds 150 MB ({size}); keep the full archive and narrow derived caches')
    manifest = {'schema': 'beforestep-suite-scene-preservation/v1', 'scene': args.scene,
                'runs': runs, 'files': entries, 'public_bytes': size,
                'supplementary_run_trees': extras,
                'complete_archive': {'path': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha(archive)},
                'scope': 'Exact raw run artifacts and original generated GLBs in the external archive; bounded public evidence objects retain exact original byte identities. No credentials or upload ledgers.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'scene': args.scene, 'files': len(entries), 'public_bytes': size,
                      'archive_bytes': archive.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    main()
