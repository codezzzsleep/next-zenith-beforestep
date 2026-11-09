"""Atomic, complete PPO state: weights, optimizer, random streams and physics."""
import json
from pathlib import Path
import uuid

import numpy as np

from . import ppo


def physical_state(environment):
    # mj_step integrates qpos after computing contacts. Synchronize those derived
    # quantities at the checkpoint boundary so both uninterrupted and restored
    # runs start the next soil/servo step from the same physical state.
    import mujoco
    mujoco.mj_forward(environment.model, environment.data)
    return environment.save_state()


def save(path, params, best, optimizer, generators, metadata):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {f'params_{k}': v for k, v in params.items()}
    arrays.update({f'best_{k}': v for k, v in best.items()})
    arrays.update({f'adam_m_{k}': v for k, v in optimizer.m.items()})
    arrays.update({f'adam_v_{k}': v for k, v in optimizer.v.items()})
    state = {**metadata, 'schema': 'beforestep-complete-ppo-checkpoint/v1',
             'optimizer': {'lr': optimizer.lr, 'b1': optimizer.b1, 'b2': optimizer.b2,
                           'eps': optimizer.eps, 't': optimizer.t},
             'generators': {name: generator.bit_generator.state for name, generator in generators.items()}}
    arrays['metadata'] = np.frombuffer(json.dumps(state, sort_keys=True).encode(), dtype=np.uint8)
    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    with temporary.open('wb') as stream:
        np.savez_compressed(stream, **arrays)
        stream.flush()
        __import__('os').fsync(stream.fileno())
    temporary.replace(path)


def load(path):
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(archive['metadata'].tobytes())
        if metadata['schema'] != 'beforestep-complete-ppo-checkpoint/v1':
            raise ValueError('Unsupported complete training checkpoint')
        keys = (*ppo.ACTOR_KEYS, *ppo.CRITIC_KEYS)
        params = {k: archive['params_'+k].copy() for k in keys}
        best = {k: archive['best_'+k].copy() for k in keys}
        configuration = metadata['optimizer']
        optimizer = ppo.Adam(params, **{k: configuration[k] for k in ('lr', 'b1', 'b2', 'eps')})
        optimizer.t = configuration['t']
        optimizer.m = {k: archive['adam_m_'+k].copy() for k in keys}
        optimizer.v = {k: archive['adam_v_'+k].copy() for k in keys}
    generators = {}
    for name, state in metadata['generators'].items():
        generator = np.random.default_rng()
        generator.bit_generator.state = state
        generators[name] = generator
    return params, best, optimizer, generators, metadata
