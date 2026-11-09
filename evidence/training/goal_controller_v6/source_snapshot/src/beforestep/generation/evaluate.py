"""Evaluate an independent Lux3D batch with resumable per-candidate evidence."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil

import numpy as np

from beforestep.geometry import imagination
from beforestep.paths import ROOT
from .client import atomic_json, sha


def evaluate_one(job):
    observation,out,candidate=job
    directory=out/'samples'/candidate['id'];saved=directory/'target_decision.json'
    identity=imagination.decision_identity(observation,[candidate])
    record=json.loads(saved.read_text()) if saved.exists() else {}
    if record.get('cache_identity')!=identity:
        record=imagination.decide_target(observation,[candidate],directory)
    print(json.dumps({'candidate':candidate['id'],'admitted':record['admitted_ids']}),flush=True)
    return record['candidates'][0],directory


def main(argv=None):
    parser=argparse.ArgumentParser(prog='beforestep admit')
    parser.add_argument('--observation',required=True);parser.add_argument('--result',required=True)
    parser.add_argument('--out',required=True);parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args(argv)
    if not 1<=args.workers<=4:parser.error('Use 1–4 workers to keep volume memory bounded')
    observation=ROOT/args.observation;out=ROOT/args.out
    result=json.loads((ROOT/args.result).read_text())
    candidates=[]
    for task in result['tasks']:
        if task['status']!='ok':continue
        path=ROOT/task['glb']
        if sha(path)!=task['glb_sha256']:raise ValueError('Generated asset checksum mismatch')
        candidates.append({'id':task['id'],'glb':str(path)})
    if not candidates:raise ValueError('No completed real candidates')
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows=list(pool.map(evaluate_one,[(observation,out,c) for c in candidates]))
    union=None
    for row,directory in rows:
        footprint=np.load(directory/f'footprint_{row["id"]}.npy')
        if union is None:union=np.zeros_like(footprint)
        if row['admitted']:union|=footprint
        shutil.copy2(directory/f'footprint_{row["id"]}.npy',out/f'footprint_{row["id"]}.npy')
    np.save(out/'footprint_union.npy',union)
    atomic_json(out/'target_decision.json',{'schema':'beforestep-batch-admission/v1',
        'cache_identity':imagination.decision_identity(observation,candidates),
        'source_result':args.result,'observation':args.observation,
        'candidates':[r for r,d in rows],'admitted_ids':[r['id'] for r,d in rows if r['admitted']]})
    print(json.dumps({'evaluated':len(rows),'admitted':sum(r['admitted'] for r,d in rows)}),flush=True)
