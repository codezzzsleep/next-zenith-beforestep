"""Restore the bundled, checksummed runtime models without old-repository paths."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

from .paths import ROOT


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def restore(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    archive = ROOT / manifest['archive']
    if digest(archive) != manifest['archive_sha256']:
        raise ValueError(f'Runtime archive checksum mismatch: {archive.name}')
    destination = ROOT / manifest['destination']
    destination.mkdir(parents=True, exist_ok=True)
    # Existing valid resources need no extraction. Refuse to replace modified files.
    missing = []
    for entry in manifest['files']:
        path = destination / entry['path']
        if path.exists():
            if digest(path) != entry['sha256']:
                raise ValueError(f'Modified runtime asset: {entry["path"]}')
        else:
            missing.append(entry['path'])
    if missing:
        with tarfile.open(archive) as bundle:
            bundle.extractall(destination, members=[bundle.getmember(p) for p in missing], filter='data')
    for entry in manifest['files']:
        if digest(destination / entry['path']) != entry['sha256']:
            raise ValueError(f'Extracted asset checksum mismatch: {entry["path"]}')
    return {'archive': manifest['archive'], 'files': len(manifest['files']), 'ok': True}


def main(argv=None):
    parser = argparse.ArgumentParser(prog='beforestep resources')
    parser.parse_args(argv)
    for name in ('runtime-assets.json', 'robot-assets.json'):
        print(json.dumps(restore(ROOT / 'config' / name)))
