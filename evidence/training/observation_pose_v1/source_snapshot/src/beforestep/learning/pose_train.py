"""Collect actual rotation dynamics and train a small terminal pose network."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
import uuid

import numpy as np

from beforestep.generation.client import atomic_json
from beforestep.navigation.controller import yaw_of
from beforestep.paths import ROOT
from . import ppo
from .policy import apply_action, completed
from .pose import SCHEMA, observation
from .train import bc_grads, checkpoint, environment, reset_task


def teacher_action(env, goal_yaw):
    """Training-only expert, including low-speed traction and stopping samples."""
    error = (goal_yaw-yaw_of(env.data.qpos)+np.pi) % (2*np.pi)-np.pi
    turn = 0. if abs(error) < np.radians(1.5) else np.sign(error)*max(.85, min(3., 6.*abs(error)))
    return np.array([0., 0., 0., turn/4.])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    parser.add_argument('--episodes', type=int, default=64)
    parser.add_argument('--epochs', type=int, default=40)
    parser.add_argument('--seed', type=int, default=130001)
    args = parser.parse_args(argv)
    if args.episodes < 1 or args.epochs < 1:
        parser.error('Episodes and epochs must be positive')
    out = ROOT / args.out
    if out.exists() and any(out.iterdir()):
        parser.error('Training output must be new; preserved runs cannot be overwritten')
    out.mkdir(parents=True)
    started = time.monotonic()
    rng = np.random.default_rng(args.seed)
    identity = {'schema': SCHEMA, 'run_id': uuid.uuid4().hex,
                'started_at': datetime.now(timezone.utc).isoformat(), 'arguments': vars(args),
                'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((ROOT/'src/beforestep').rglob('*.py'))},
                'training': 'Behavior cloning of actual MuJoCo rotation demonstrations; no new PPO',
                'observation': 'Wrapped yaw error / 0.1 and measured yaw rate * 5, clipped',
                'actions': 'Four network outputs through existing leg and wheel servos',
                'gravity_mps2': 1.62, 'navigation_base': False,
                'acceptance': {'position_m': .075, 'yaw_degrees': 4., 'stable_frames': 5}}
    atomic_json(out/'run_identity.json', identity)
    for relative, digest in identity['source_sha256'].items():
        source = ROOT/relative
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise RuntimeError('Training source changed during preservation')
        target = out/'source_snapshot'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    atomic_json(out/'source_snapshot/manifest.json', identity['source_sha256'])
    env = environment('terminal_pose_demonstrations')
    X, Y, states, manifest = [], [], [], []
    for episode in range(args.episodes):
        initial = float(rng.uniform(-np.pi, np.pi))
        angle = float(rng.uniform(-np.pi, np.pi))
        # Include precise stopping and small corrections in actual dynamics.
        if episode % 4 == 0:
            angle = float(rng.uniform(-.15, .15))
        task = {'seed': args.seed+episode, 'goal': [0., 0.],
                'initial_yaw': initial, 'goal_yaw': initial+angle}
        reset_task(env, task)
        start = env.t
        first = len(X)
        stable = 0
        hold_until = None
        while env.t-start < 25.:
            obs = observation(env, task['goal_yaw'])
            action = teacher_action(env, task['goal_yaw'])
            X.append(obs); Y.append(action)
            states.append([episode, env.t, *env.data.qpos, *env.data.qvel])
            apply_action(env, action)
            stable = stable+1 if completed(env, task['goal'], task['goal_yaw']) else 0
            if stable >= 5 and hold_until is None:
                hold_until = env.t+3.
            if (hold_until is not None and env.t >= hold_until) or env.terminated or env.truncated:
                break
        manifest.append({**task, 'row_start': first, 'row_end': len(X),
                         'success': bool(completed(env, task['goal'], task['goal_yaw'])),
                         'sim_seconds': env.t-start, 'physical_steps': env.n_physics,
                         'position_error_m': float(np.linalg.norm(env.data.qpos[:2])),
                         'yaw_error_degrees': float(np.degrees(abs((task['goal_yaw']-yaw_of(env.data.qpos)+np.pi) % (2*np.pi)-np.pi)))})
        if (episode+1) % 8 == 0 or episode+1 == args.episodes:
            with (out/'demonstrations.npz').open('wb') as f:
                np.savez_compressed(f, observations=np.asarray(X), actions=np.asarray(Y),
                                    physical_states=np.asarray(states))
            atomic_json(out/'demonstration_manifest.json', manifest)
            print(json.dumps({'stage': 'physical_demonstrations', 'episodes': episode+1,
                              'transitions': len(X), 'successes': sum(r['success'] for r in manifest)}), flush=True)
    X, Y = np.asarray(X), np.asarray(Y)
    identity['physical_transitions'] = len(X)
    identity['physical_steps'] = sum(r['physical_steps'] for r in manifest)
    identity['demonstrations_sha256'] = hashlib.sha256((out/'demonstrations.npz').read_bytes()).hexdigest()
    # Symmetry adds supervision, never additional physical transition counts.
    X, Y = np.concatenate((X, -X)), np.concatenate((Y, -Y))
    identity['symmetry_supervision_rows'] = len(X)//2
    atomic_json(out/'run_identity.json', identity)
    params = ppo.init_params(rng, obs_dim=2, act_dim=4, hidden=32)
    # Zero-initialized output channels retain the demonstrated zero stance and
    # forward speed exactly; all four commands still come from network weights.
    params['Wm'][:, :3] = 0.
    checkpoint(out/'checkpoints/initial.npz', {**params, 'schema': np.array(SCHEMA)})
    optimizer = ppo.Adam(params, lr=.001)
    history = []
    for epoch in range(args.epochs):
        losses = []
        for indices in np.array_split(rng.permutation(len(X)), max(1, len(X)//256)):
            grads, loss = bc_grads(params, X[indices], Y[indices])
            grads, _ = ppo.clip_grads(grads, 1.)
            optimizer.step(params, grads)
            losses.append(loss)
        row = {'epoch': epoch+1, 'loss': float(np.mean(losses)), 'actor_sha': ppo.actor_checksum(params)}
        history.append(row)
        atomic_json(out/'behavior_cloning.json', history)
        checkpoint(out/'checkpoints/pose.npz', {**params, 'schema': np.array(SCHEMA)})
        if (epoch+1) % 5 == 0:
            print(json.dumps({'stage': 'behavior_cloning', **row}), flush=True)
    summary = {'run_id': identity['run_id'], 'physical_demonstrations': len(manifest),
               'physical_transitions': identity['physical_transitions'],
               'physical_steps': identity['physical_steps'],
               'demonstration_successes': sum(r['success'] for r in manifest),
               'symmetry_supervision_rows': identity['symmetry_supervision_rows'],
               'epochs': args.epochs, 'final_loss': history[-1]['loss'],
               'checkpoint_sha256': hashlib.sha256((out/'checkpoints/pose.npz').read_bytes()).hexdigest(),
               'wall_seconds': time.monotonic()-started,
               'independent_task_evaluation': 'Pending; demonstration success is not model task success'}
    atomic_json(out/'summary.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
