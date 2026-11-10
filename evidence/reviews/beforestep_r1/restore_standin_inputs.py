"""Restore preserved offline test files to their recorded, ignored output paths."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def copy_verified(source, destination, expected):
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Preserved bytes changed: ' + str(source))
    if not destination.resolve().is_relative_to(ROOT / 'outputs/reviews/r1'):
        raise ValueError('Restoration must remain inside the ignored R1 output directory')
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != expected:
            raise ValueError('Existing output differs; refusing to overwrite: ' + str(destination))
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main():
    count = 0
    for path in (BASE / 'standins').glob('*/preservation.json'):
        record = json.loads(path.read_text())
        for relative, expected in record['files_sha256'].items():
            copy_verified(path.parent / relative, ROOT / record['original_output'] / relative, expected)
            count += 1
    for item in json.loads((BASE / 'standins/shared_geometry/manifest.json').read_text())['files']:
        copy_verified(BASE / item['archive'], ROOT / item['original'], item['sha256'])
        count += 1
    print('Verified/restored offline files:', count, '; no provider calls or paid identities.')


if __name__ == '__main__':
    main()
