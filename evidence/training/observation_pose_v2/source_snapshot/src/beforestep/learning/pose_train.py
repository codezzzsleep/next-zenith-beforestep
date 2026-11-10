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
    parser.add_argument('--demonstrations-from', help='Reuse preserved physical demonstrations without resampling dynamics')
    parser.add_argument('--goal-augmentation', type=int, default=0,
                        help='Counterfactual nearby yaw supervision; counted separately from dynamics')
    parser.add_argument('--near-yaw-weight', type=float, default=1.)
    args = parser.parse_args(argv)
    if args.episodes < 1 or args.epochs < 1 or args.goal_augmentation < 0 or args.near_yaw_weight <= 0:
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
    if args.demonstrations_from:
        source = ROOT/args.demonstrations_from
        with np.load(source/'demonstrations.npz', allow_pickle=False) as data:
            X = list(data['observations']); Y = list(data['actions']); states = list(data['physical_states'])
        if np.asarray(X).shape[1:] != (2,) or np.asarray(Y).shape != (len(X), 4):
            raise ValueError('Reused demonstrations do not match the terminal pose contract')
        manifest = json.loads((source/'demonstration_manifest.json').read_text())
        shutil.copy2(source/'demonstrations.npz', out/'demonstrations.npz')
        shutil.copy2(source/'demonstration_manifest.json', out/'demonstration_manifest.json')
        identity['demonstrations_source'] = {'path': args.demonstrations_from,
            'sha256': hashlib.sha256((source/'demonstrations.npz').read_bytes()).hexdigest()}
    for episode in range(0 if args.demonstrations_from else args.episodes):
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
    identity['new_physical_transitions'] = 0 if args.demonstrations_from else len(X)
    identity['physical_steps'] = sum(r['physical_steps'] for r in manifest)
    identity['demonstrations_sha256'] = hashlib.sha256((out/'demonstrations.npz').read_bytes()).hexdigest()
    if args.goal_augmentation:
        count = args.goal_augmentation
        augmented = X[rng.integers(0, len(X), size=count)].copy()
        errors = rng.uniform(-.2, .2, count)
        augmented[:, 0] = errors/.1
        turn = np.where(np.abs(errors)<np.radians(1.5), 0.,
                        np.sign(errors)*np.maximum(.85, np.minimum(3., 6.*np.abs(errors))))
        labels = np.zeros((count, 4)); labels[:, 3] = turn/4.
        X = np.concatenate((X, augmented)); Y = np.concatenate((Y, labels))
        identity['goal_augmentation'] = {'rows': count, 'physical_state_source': 'Preserved measured yaw rates',
            'yaw_error_range_rad': .2, 'kind': 'Counterfactual target supervision, not new physical transitions'}
    # Symmetry adds supervision, never additional physical transition counts.
    X, Y = np.concatenate((X, -X)), np.concatenate((Y, -Y))
    identity['symmetry_supervision_rows'] = len(X)//2
    near_yaw = (np.abs(X[:, 0]) >= np.radians(2.)/.1) & (np.abs(X[:, 0]) <= np.radians(10.)/.1)
    weights = np.where(near_yaw, args.near_yaw_weight, 1.)
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
            grads, loss = bc_grads(params, X[indices], Y[indices], weights[indices])
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
               'new_physical_transitions': identity['new_physical_transitions'],
               'physical_steps': identity['physical_steps'],
               'demonstration_successes': sum(r['success'] for r in manifest),
               'symmetry_supervision_rows': identity['symmetry_supervision_rows'],
               'counterfactual_goal_rows': args.goal_augmentation,
               'epochs': args.epochs, 'final_loss': history[-1]['loss'],
               'checkpoint_sha256': hashlib.sha256((out/'checkpoints/pose.npz').read_bytes()).hexdigest(),
               'wall_seconds': time.monotonic()-started,
               'independent_task_evaluation': 'Pending; demonstration success is not model task success'}
    atomic_json(out/'summary.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
