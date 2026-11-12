"""Bounded development smoke and one-time paired LLM runs with durable attempts."""
import argparse
import os
import json
import numpy as np
from pathlib import Path
from .common import ROOT, OUT, read, write, sha
from .registration import require_registration
from .world import World
from .llm import Advisor
from .evaluate import run, summarize


def evaluate(stage, out, env_file='/root/3d/.env'):
    require_registration()
    cfg = read(ROOT / 'experimental/arena/parameters.json')
    split = 'development' if stage == 'smoke' else stage
    count = 3 if stage == 'smoke' else 150
    limits = {'smoke': 50, 'validation': 1450, 'sealed': 1500}
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    advisor = Advisor(env_file, OUT / 'llm/calls', stage=stage, stage_limit=limits[stage])
    identity = {'stage': stage, 'seed_start': cfg[split]['seed_start'], 'worlds': count,
                'parameters_sha256': sha(ROOT / 'experimental/arena/parameters.json'),
                'protocol_sha256': sha(ROOT / 'docs/arena-protocol.md'), 'model': advisor.model,
                'stage_request_limit': limits[stage], 'total_request_limit': 3000}
    if (out / 'identity.json').exists():
        previous = read(out / 'identity.json')
        for key, value in identity.items():
            assert previous[key] == value, f'Changed LLM resume identity: {key}'
        if previous['status'] == 'complete': return
    write(out / 'identity.json', {**identity, 'status': 'running', 'pid': os.getpid()})
    rows = []
    for seed in range(identity['seed_start'], identity['seed_start'] + count):
        folder = out / str(seed)
        result = folder / 'strict_llm.json'
        archive = folder / 'strict_llm-maps.npz'
        if result.exists():
            rows.append(read(result)); continue
        if archive.exists():
            with np.load(archive) as saved: row=json.loads(str(saved['result']))
            write(result,row);rows.append(row);continue
        w = World(seed, split)
        try:
            manifest = w.manifest()
            paired = OUT / split / str(seed) / 'world.json'
            if paired.exists(): assert read(paired) == manifest, 'LLM must use the same paired world'
            write(folder / 'world.json', manifest)
            # Recovered calls use their prior response or fall back if submission was uncertain.
            # They are never sent again to the service.
            row, data = run(w, 'strict_llm', advisor=advisor)
            temporary=archive.with_suffix('.npz.tmp')
            with temporary.open('wb') as f:
                np.savez_compressed(f,result=json.dumps(row),state=data['state'],state_history=data['state_history'],risk=np.asarray(data['risk']),truth=data['truth'])
            temporary.replace(archive)
            write(result, row); rows.append(row)
            write(out / 'progress.json', {'completed_worlds': len(rows)})
            print(stage, seed, row['status'], row['llm_decisions'], row['llm_fallbacks'], flush=True)
        finally: w.close()
    write(out / 'results.json', rows)
    write(out / 'summary.json', {'results': summarize(rows),
          'actual_decisions': sum(r['llm_decisions'] for r in rows),
          'fallbacks': sum(r['llm_fallbacks'] for r in rows),
          'wait_seconds': sum(r['llm_wait_seconds'] for r in rows),
          'mean_wait_seconds_per_observation': sum(r['llm_wait_seconds'] for r in rows) / sum(r['looks'] for r in rows)})
    write(out / 'identity.json', {**identity, 'status': 'complete', 'pid': os.getpid()})


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['smoke', 'validation', 'sealed'], required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(); evaluate(args.stage, args.out)
