"""Unselected first-24 sealed physics and six real heldout scenes, all failures kept."""
import argparse
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import torch
from .common import ROOT, OUT, HELDOUT, read, write, sha
from .registration import require_registration
from .world import World
from .model import load
from .physics import run, real_world


def one(identifier, method, out, model_path, threshold, real=False):
    torch.set_num_threads(1)
    folder = Path(out) / str(identifier) / method
    if (folder / 'result.json').exists(): return read(folder / 'result.json')
    write(folder / 'identity.json', {'status': 'running', 'pid': os.getpid(),
          'identifier': identifier, 'method': method, 'real_heldout': real,
          'model_sha256': sha(model_path) if method == 'learned' else None,
          'threshold': threshold, 'new_lux_tasks': 0})
    w = None
    try:
        if real: w, recorded = real_world(identifier)
        else: w, recorded = World(identifier, 'sealed'), None
        row = run(w, method, load(model_path) if method == 'learned' else None,
                  threshold, folder, recorded)
    except Exception as exc:
        row = {'identifier': identifier, 'method': method, 'status': 'execution_error',
               'error_type': type(exc).__name__, 'error': str(exc),
               'new_lux_tasks': 0, 'note': 'Failure retained; not rerun or counted as safe parking.'}
        write(folder / 'result.json', row)
        print(identifier, method, 'execution_error', type(exc).__name__, flush=True)
    finally:
        if w is not None: w.close()
    identity = read(folder / 'identity.json')
    identity.update(status='complete', outcome=row['status'])
    write(folder / 'identity.json', identity)
    return row


def evaluate(out, model_path, real=False, workers=2):
    require_registration()
    cfg = read(ROOT / 'experimental/arena/parameters.json')
    threshold = read(OUT / 'validation/workpoint.json')['chosen']['learned']
    identifiers = sorted(HELDOUT) if real else list(range(cfg['sealed']['seed_start'], cfg['sealed']['seed_start'] + 24))
    methods = ['learned'] if real else ['optimistic', 'strict', 'learned']
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    identity = {'status': 'running', 'pid': os.getpid(), 'real_heldout': real,
                'identifiers': identifiers, 'methods': methods,
                'model_sha256': sha(model_path), 'threshold': threshold,
                'protocol_sha256': sha(ROOT / 'docs/arena-protocol.md'), 'new_lux_tasks': 0}
    if (out / 'identity.json').exists():
        previous = read(out / 'identity.json')
        for key in ['real_heldout', 'identifiers', 'methods', 'model_sha256', 'threshold', 'protocol_sha256']:
            assert previous[key] == identity[key], f'Changed physical resume identity: {key}'
        if previous['status'] == 'complete': return
    write(out / 'identity.json', identity)
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = [(i, m, pool.submit(one, i, m, out, model_path, threshold, real)) for i in identifiers for m in methods]
        for identifier, method, future in jobs:
            row = future.result(); rows.append(row)
            write(out / 'progress.json', {'complete_episodes': len(rows), 'target': len(jobs)})
            print(identifier, method, row['status'], flush=True)
    write(out / 'results.json', rows)
    identity['status'] = 'complete'; write(out / 'identity.json', identity)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True); ap.add_argument('--model', required=True)
    ap.add_argument('--real', action='store_true'); ap.add_argument('--workers', type=int, default=2)
    args = ap.parse_args(); evaluate(args.out, args.model, args.real, args.workers)
