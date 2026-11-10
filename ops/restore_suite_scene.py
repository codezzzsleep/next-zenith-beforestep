"""Restore exact public review objects, optionally a complete external archive."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--archive', help='Optional downloaded complete scene tar.gz')
    args = parser.parse_args()
    manifest = json.loads((ROOT / args.manifest).read_text())
    contents = {}
    if args.archive:
        archive = Path(args.archive)
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest['complete_archive']['sha256']
        with tarfile.open(archive, 'r:gz') as source:
            for entry in manifest['files']:
                member = source.extractfile('repo/' + entry['path'])
                if member is not None:
                    contents[entry['path']] = member.read()
    else:
        for entry in manifest['files']:
            if entry.get('public_object'):
                contents[entry['path']] = gzip.decompress((ROOT / entry['public_object']).read_bytes())
    restored = 0
    for entry in manifest['files']:
        if entry['path'] not in contents:
            continue
        path = (ROOT / entry['path']).resolve()
        assert path.is_relative_to(ROOT), 'Archive path outside repository'
        value = contents[entry['path']]
        assert hashlib.sha256(value).hexdigest() == entry['sha256'] and len(value) == entry['bytes']
        if path.exists():
            assert path.read_bytes() == value, 'Existing artifact differs; preserve it separately before restoring'
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
            restored += 1
    print(json.dumps({'verified': len(contents), 'restored': restored,
                      'missing_complete_only_files': len(manifest['files'])-len(contents)}))


if __name__ == '__main__':
    main()
