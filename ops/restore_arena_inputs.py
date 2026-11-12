"""Restore preserved first-look inputs for six real-scene policy reproductions."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]


def restore(archive,destination):
    destination=Path(destination).resolve()
    with tarfile.open(archive,'r:gz') as tar:
        manifest=json.load(tar.extractfile('arena-inputs-manifest.json'))
        for row in manifest['files']:
            relative=Path(row['path'])
            assert not relative.is_absolute() and '..' not in relative.parts
            target=destination/relative
            body=tar.extractfile(row['path']).read()
            assert len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
            if target.exists():
                assert target.read_bytes()==body, f'Existing input differs; preserve and inspect: {target}'
            else:
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(body)
    print(f"Verified/restored {len(manifest['files'])} preserved input files")


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive',default=str(ROOT/'assets/runtime-arena-real-inputs.tar.gz'))
    ap.add_argument('--destination',default=str(ROOT))
    args=ap.parse_args();restore(args.archive,args.destination)
