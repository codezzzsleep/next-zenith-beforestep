"""Verify each R3 scene manifest, public bytes and optional complete archive."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evidence/reviews/beforestep_r3/scenes'


def digest(stream):
    result = hashlib.sha256()
    size = 0
    while block := stream.read(1 << 20):
        result.update(block)
        size += len(block)
    return result.hexdigest(), size


def verify(scenes=None, archives=False):
    paths = [BASE / scene / 'manifest.json' for scene in scenes] if scenes else sorted(BASE.glob('*/manifest.json'))
    objects = {}
    checked = []
    for path in paths:
        data = json.loads(path.read_text())
        assert data['scene'] == path.parent.name
        public_size = sum(p.stat().st_size for p in path.parent.rglob('*') if p.is_file())
        assert public_size == data['public_bytes'] < 150_000_000, path
        entries = {row['path']: row for row in data['files']}
        assert len(entries) == len(data['files'])
        public_count = 0
        for row in entries.values():
            if not row.get('public_object'):
                continue
            public = (ROOT / row['public_object']).resolve()
            assert public.is_relative_to(ROOT) and public.is_file(), public
            if public not in objects:
                with gzip.open(public, 'rb') as stream:
                    objects[public] = digest(stream)
            assert objects[public] == (row['sha256'], row['bytes']), row['path']
            public_count += 1
        for variant, record in data['runs'].items():
            directory = path.parent / 'runs' / variant
            summary = json.loads((directory / 'summary.json').read_text())
            identity = json.loads((directory / 'run_identity.json').read_text())
            assert summary == record['summary'] and identity['run_id'] == record['run_id']
        archive = data['complete_archive']
        if archives:
            archive_path = Path(archive['path'])
            with archive_path.open('rb') as stream:
                assert digest(stream) == (archive['sha256'], archive['bytes']), archive_path
            members = set()
            content = {}
            with tarfile.open(archive_path, 'r:gz') as tar:
                for member in tar:
                    assert member.name.startswith('repo/')
                    relative = member.name.removeprefix('repo/')
                    assert relative in entries and member.name not in members, member.name
                    row = entries[relative]
                    if member.islnk():
                        assert member.linkname in content, member.linkname
                        actual = content[member.linkname]
                    else:
                        assert member.isfile(), member.name
                        with tar.extractfile(member) as stream:
                            actual = digest(stream)
                    assert actual == (row['sha256'], row['bytes']), member.name
                    members.add(member.name)
                    content[member.name] = actual
            assert members == {'repo/' + relative for relative in entries}, path
        checked.append({'scene': data['scene'], 'manifest': str(path.relative_to(ROOT)),
                        'manifest_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'files': len(entries), 'public_files': public_count,
                        'public_bytes': public_size, 'complete_archive_sha256': archive['sha256'],
                        'archive_bytes_verified': archives})
    return {'schema': 'beforestep-r3-custody-check/v1', 'passed': True,
            'archives_verified': archives, 'unique_public_objects_verified': len(objects),
            'scenes': checked}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', action='append')
    parser.add_argument('--archives', action='store_true')
    parser.add_argument('--out')
    args = parser.parse_args()
    result = verify(args.scene, args.archives)
    if args.out:
        output = ROOT / args.out
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'scenes': len(result['scenes']),
                      'unique_public_objects': result['unique_public_objects_verified'],
                      'archives_verified': args.archives}))
