"""Retain both strict-check revisions, with one bounded manifest per scene."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
from contextlib import nullcontext

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def main():
    reviews = json.loads((ROOT / 'outputs/qa/r3/standin-postreviews/processes.json').read_text())
    assert reviews['completed'] and len(reviews['runs']) == 8
    archive_root = ROOT.parent / 'artifacts/beforestep-r3'
    archive_root.mkdir(parents=True, exist_ok=True)
    for scene in ('stress_v8', 'suite_r2_v4_F1_020'):
        folders, runs = [], []
        for revision, stage in (('v1', 'S2'), ('v2', 'S2-v2')):
            parent = ROOT / 'outputs/qa/r3' / stage / 'standins'
            for mode in ('truth', 'registered'):
                folder = parent / (scene + '-' + mode)
                actual = folder / 'imagination_strict'
                summary = json.loads((actual / 'summary.json').read_text())
                identity = json.loads((actual / 'run_identity.json').read_text())
                assert summary['collision'] is None
                folders.extend([folder, ROOT / reviews['runs'][identity['run_id']]['sidecar']])
                runs.append({'revision': revision, 'mode': mode, 'run': str(actual.relative_to(ROOT)),
                             'run_id': identity['run_id'], 'summary': summary, 'not_real_lux': True})
        paths = sorted({p for folder in folders for p in folder.rglob('*')
                        if p.is_file() and '__pycache__' not in p.parts})
        public = ROOT / 'evidence/reviews/beforestep_r3/checks' / scene
        public.mkdir(parents=True, exist_ok=True)
        archive = archive_root / (scene + '-checks-v1-v2-complete.tar.gz')
        saved = public / 'manifest.json'
        if saved.exists():
            manifest = json.loads(saved.read_text())
            assert archive.exists() and sha(archive) == manifest['complete_archive']['sha256']
            print(json.dumps({'scene': scene, 'already_preserved': True}), flush=True)
            continue
        write_archive = not archive.exists()
        if not write_archive:
            # Recover a completed archive if the subsequent manifest write failed.
            with tarfile.open(archive, 'r:gz') as previous:
                members = {m.name: m.size for m in previous.getmembers() if m.isfile()}
            assert members == {'repo/' + str(p.relative_to(ROOT)): p.stat().st_size for p in paths}
        files, public_objects = [], {}
        temporary = archive.with_suffix('.gz.partial')
        context = tarfile.open(temporary, 'w:gz', compresslevel=6, dereference=True) if write_archive else nullcontext(None)
        with context as output:
            for path in paths:
                relative, digest, size = str(path.relative_to(ROOT)), sha(path), path.stat().st_size
                if output is not None:
                    output.add(path, arcname='repo/' + relative, recursive=False)
                row = {'path': relative, 'sha256': digest, 'bytes': size}
                # Apply the same size/type rule to every run; never select on outcome.
                selected = path.suffix in ('.json', '.jsonl', '.npz', '.npy', '.obj', '.glb', '.png', '.log') and size <= 3_000_000
                if selected:
                    destination = public / 'objects' / (digest + '.gz')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if not destination.exists():
                        with path.open('rb') as source, destination.open('wb') as target:
                            with gzip.GzipFile(filename='', mode='wb', fileobj=target, mtime=0) as encoded:
                                while block := source.read(1 << 20):
                                    encoded.write(block)
                    row['public_object'] = str(destination.relative_to(ROOT))
                    public_objects[str(destination)] = destination.stat().st_size
                files.append(row)
        if write_archive:
            temporary.replace(archive)
        public_bytes = sum(public_objects.values())
        assert public_bytes < 150_000_000, 'Scene publication exceeds the frozen data-size limit'
        manifest = {'schema': 'beforestep-r3-standin-check-manifest/v1', 'scene': scene,
                    'not_real_lux': True, 'paid_tasks': 0, 'runs': runs,
                    'scope': 'Both check revisions and post-run truth diagnostics; original R1/R2 files unchanged',
                    'complete_archive': {'path': str(archive), 'sha256': sha(archive), 'bytes': archive.stat().st_size},
                    'public_storage_bytes': public_bytes, 'public_storage_limit_bytes': 150_000_000,
                    'retrieval': 'Public objects gzip-decompress to their listed original path, bytes and SHA. The complete archive also retains larger raw RGB-D/native inputs.',
                    'files': files}
        (public / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'scene': scene, 'files': len(files), 'public_storage_bytes': public_bytes,
                          'complete_archive': manifest['complete_archive']}), flush=True)


if __name__ == '__main__':
    main()
