"""Restore and verify archived input bytes without running physics or APIs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from common import ROOT, OUT

parser=argparse.ArgumentParser()
parser.add_argument('--archive',action='append',help='One named archive; default restores both data snapshots.')
parser.add_argument('--verify-only',action='store_true')
parser.add_argument('--destination',type=Path,help='Alternate empty repository root for restoration checks.')
args=parser.parse_args()
root=(args.destination or ROOT).resolve()
out=root/'evidence/production-v6' if args.destination else OUT
archives=args.archive or ['F3_002-terminal.zip','render-inputs.zip']
checked=restored=0
for name in archives:
    if Path(name).name!=name:raise ValueError('Use an archive filename, not a path.')
    archive=OUT/'data'/name
    with zipfile.ZipFile(archive) as z:
        manifest=json.loads(z.read('MANIFEST.json'))
        for row in manifest['members']:
            path=Path(row['path'])
            if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe archive path')
            if path.parts[0]=='repo':dest=root/Path(*path.parts[1:])
            elif path.parts[0]=='production':dest=out/Path(*path.parts[1:])
            else:raise ValueError('Unknown archive root')
            data=z.read(row['path'])
            if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Archived SHA mismatch: '+row['path'])
            checked+=1
            if args.verify_only:continue
            if dest.exists():
                existing=dest.read_bytes()
                if hashlib.sha256(existing).hexdigest()==row['sha256']:continue
                pointer=existing.startswith(b'version https://git-lfs.github.com/spec/v1\n') and ('oid sha256:'+row['sha256']).encode() in existing
                if not pointer:raise FileExistsError('Different existing data retained; use --destination with an empty root: '+str(dest))
            dest.parent.mkdir(parents=True,exist_ok=True)
            temp=dest.with_name(dest.name+'.restoring')
            temp.write_bytes(data);temp.replace(dest);restored+=1
print(json.dumps({'archived_members_verified':checked,'restored_files':restored,'physics_runs':0,'API_calls':0}))
