"""Independently stream original GLBs from GitHub LFS and verify their bytes.

No local object cache is consulted and no downloaded GLB is stored. Credentials
are captured only inside this process and never included in the output record.
"""
import argparse
import base64
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
REPOSITORY='codezzzsleep/next-zenith-beforestep'


def command(*args):
    return subprocess.check_output(args,cwd=ROOT)


def download(row,action):
    request=urllib.request.Request(action['href'],headers={**action.get('header',{}),'Accept-Encoding':'identity'})
    digest=hashlib.sha256();size=0
    with urllib.request.urlopen(request,timeout=120) as response:
        assert response.status==200, f"Remote LFS status for {row['path']}: {response.status}"
        while block:=response.read(1024*1024):
            digest.update(block);size+=len(block)
    assert digest.hexdigest()==row['sha256'] and size==row['bytes'], f"Remote original bytes differ: {row['path']}"
    return {**row,'remote_bytes_verified':True}


def verify(out,workers=4):
    custody=json.loads((ROOT/'evidence/learning/arena_v2/canonical-glb-custody.json').read_text())
    rows=custody['files'];commit=json.loads((ROOT/'evidence/learning/arena_v2/protocol.json').read_text())['commit']
    remote=command('git','ls-remote','origin','refs/heads/main').decode().split()[0]
    assert command('git','merge-base','--is-ancestor',commit,remote)==b''
    for row in rows:
        pointer=command('git','show',f"{commit}:{row['path']}").decode().splitlines()
        assert 'oid sha256:'+row['sha256'] in pointer and 'size '+str(row['bytes']) in pointer, row['path']
    token=command('gh','auth','token').decode().strip()
    authorization=base64.b64encode(('x-access-token:'+token).encode()).decode()
    records=[]
    for start in range(0,len(rows),50):
        batch=rows[start:start+50]
        payload={'operation':'download','transfers':['basic'],'objects':[{'oid':r['sha256'],'size':r['bytes']} for r in batch]}
        request=urllib.request.Request(f'https://github.com/{REPOSITORY}.git/info/lfs/objects/batch',
            data=json.dumps(payload).encode(),headers={'Authorization':'Basic '+authorization,
            'Content-Type':'application/vnd.git-lfs+json','Accept':'application/vnd.git-lfs+json'})
        with urllib.request.urlopen(request,timeout=120) as response:
            objects={r['oid']:r for r in json.load(response)['objects']}
        for row in batch:
            obj=objects[row['sha256']]
            assert not obj.get('error') and obj.get('size')==row['bytes'] and 'download' in obj.get('actions',{}), f"LFS download unavailable: {row['path']}"
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(download,row,objects[row['sha256']]['actions']['download']) for row in batch]
            records.extend(f.result() for f in futures)
        print(f'Verified original remote GLBs: {len(records)}/{len(rows)}',flush=True)
    result={'passed':True,'repository':REPOSITORY,'protocol_commit':commit,'remote_main':remote,
            'verified_utc':datetime.now(timezone.utc).isoformat(),'original_glbs':len(records),
            'bytes':sum(r['bytes'] for r in records),'files':records,
            'verification':'Independent HTTP stream from origin LFS; SHA256 and size; no local object-cache reuse'}
    destination=Path(out);destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args();verify(args.out,args.workers)
