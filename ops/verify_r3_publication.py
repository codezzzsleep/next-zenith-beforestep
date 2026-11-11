"""Fetch published R3 LFS objects into separate storage and verify their bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--storage', required=True)
    parser.add_argument('--include', action='append', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    storage = Path(args.storage).resolve()
    assert not storage.is_relative_to(ROOT), 'Use separate verification storage'
    storage.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(['git', 'rev-parse', args.ref], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=ROOT, text=True).split()[0]
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, remote], cwd=ROOT, check=True)
    fetch = ['git', '-c', 'lfs.storage=' + str(storage), 'lfs', 'fetch',
             '--include=' + ','.join(args.include), '--exclude=', 'origin', commit]
    output = ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix('.fetch.log').open('w') as log:
        subprocess.run(fetch, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    listing = subprocess.check_output(['git', 'lfs', 'ls-files', '--long', commit], cwd=ROOT, text=True)
    # Scope by the same directory prefixes used in the explicit fetch globs.
    prefixes = [pattern.removesuffix('**').removesuffix('*') for pattern in args.include]
    checked = {}
    files = 0
    for line in listing.splitlines():
        oid, _, relative = line.split(' ', 2)
        if not any(relative.startswith(prefix) for prefix in prefixes):
            continue
        pointer = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=ROOT).decode()
        expected_oid = re.search(r'^oid sha256:([0-9a-f]{64})$', pointer, re.M).group(1)
        expected_size = int(re.search(r'^size (\d+)$', pointer, re.M).group(1))
        assert oid == expected_oid
        if oid not in checked:
            blob = storage / 'objects' / oid[:2] / oid[2:4] / oid
            digest = hashlib.sha256()
            size = 0
            with blob.open('rb') as stream:
                while block := stream.read(1 << 20):
                    digest.update(block)
                    size += len(block)
            assert digest.hexdigest() == oid and size == expected_size, relative
            checked[oid] = size
        assert checked[oid] == expected_size
        files += 1
    assert files and checked
    report = {'schema': 'beforestep-r3-publication-check/v1', 'passed': True,
              'published_commit': commit, 'remote_main_at_check': remote,
              'include': args.include, 'lfs_pointer_files': files,
              'unique_downloaded_objects': len(checked),
              'downloaded_bytes': sum(checked.values()),
              'method': 'Download from origin into separate LFS storage; verify each committed pointer SHA-256 and size. Local working-tree objects are not used.'}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
