"""Evaluate frozen controllers on the same held-out physical tasks and limits."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import uuid

import numpy as np

from beforestep.generation.client import atomic_json
from beforestep.paths import ROOT
from beforestep.navigation.controller import yaw_of
from .policy import GoalPolicy, apply_action, completed, expert_action
from .train import environment, reset_task, sample_task


def main(argv=None):
    parser = argparse.ArgumentParser(prog='beforestep evaluate-controller')
    parser.add_argument('--model', action='append', required=True,
                        help='LABEL=checkpoint path, or LABEL=rules for the demonstration expert')
    parser.add_argument('--out', required=True)
    parser.add_argument('--episodes', type=int, default=32)
    parser.add_argument('--seed-start', type=int, default=940001)
    parser.add_argument('--max-seconds', type=float, default=65.)
    parser.add_argument('--slope', type=float, default=0.)
    parser.add_argument('--roughness', type=float, default=0.)
    args = parser.parse_args(argv)
    if args.episodes < 1 or args.max_seconds <= 0:
        parser.error('Episodes and time limit must be positive')
    out = ROOT / args.out
    if out.exists() and any(out.iterdir()):
        parser.error('Evaluation output must be new to preserve independent trials')
    controllers = []
    for item in args.model:
        label, path = item.split('=', 1)
        if not label or any(label == c['label'] for c in controllers):
            parser.error('Controller labels must be nonempty and unique')
        checkpoint = None if path == 'rules' else ROOT / path
        policy = None if checkpoint is None else GoalPolicy(checkpoint)
        controllers.append({'label': label, 'path': path, 'policy': policy,
                            'sha256': None if checkpoint is None else hashlib.sha256(checkpoint.read_bytes()).hexdigest()})
    rng = np.random.default_rng(args.seed_start)
    tasks = [sample_task(rng, args.seed_start+i) for i in range(args.episodes)]
    out.mkdir(parents=True)
    identity = {'schema': 'beforestep-controller-evaluation/v1', 'run_id': uuid.uuid4().hex,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'tasks': tasks, 'max_seconds_per_episode': args.max_seconds,
                'terrain': {'slope_degrees': args.slope, 'roughness_m': args.roughness},
                'gravity_mps2': 1.62, 'navigation_base': False,
                'acceptance': {'position_error_m': .075, 'specified_yaw_error_degrees': 4.,
                               'linear_speed_mps': .035, 'yaw_rate_rps': .08, 'stable_control_frames': 5},
                'controllers': [{k: c[k] for k in ('label', 'path', 'sha256')} for c in controllers],
                'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((ROOT/'src/beforestep').rglob('*.py'))}}
    atomic_json(out/'run_identity.json', identity)
    env = environment('held_out_controller_evaluation', slope=args.slope, roughness=args.roughness)
    started = time.monotonic()
    summary = {'schema': identity['schema'], 'run_id': identity['run_id'], 'controllers': {}}
    for controller in controllers:
        trials = []
        policy = controller['policy']
        for task in tasks:
            reset_task(env, task)
            if policy is not None:
                policy.previous = np.zeros(4)
            t0 = env.t
            stable = steps = 0
            while env.t-t0 < args.max_seconds:
                action = expert_action(env, task['goal'], task['goal_yaw']) if policy is None else policy.action(env, task['goal'], task['goal_yaw'])
                apply_action(env, action)
                steps += 1
                stable = stable+1 if completed(env, task['goal'], task['goal_yaw']) else 0
                if stable >= 5 or env.terminated or env.truncated:
                    break
            goal_yaw = task['goal_yaw']
            record = {**task, 'success': stable >= 5,
                      'goal_error_m': float(np.linalg.norm(np.asarray(task['goal'])-env.data.qpos[:2])),
                      'specified_yaw_error_degrees': None if goal_yaw is None else float(np.degrees(abs((goal_yaw-yaw_of(env.data.qpos)+np.pi)%(2*np.pi)-np.pi))),
                      'sim_seconds': env.t-t0, 'control_steps': steps, 'physical_steps': env.n_physics,
                      'failure': None if stable >= 5 else env.last_termination.get('reason', 'time_limit')}
            trials.append(record)
            result = {'checkpoint_sha256': controller['sha256'], 'episodes': len(trials),
                      'successes': sum(r['success'] for r in trials),
                      'success_rate': float(np.mean([r['success'] for r in trials])),
                      'mean_goal_error_m': float(np.mean([r['goal_error_m'] for r in trials])),
                      'per_episode': trials}
            atomic_json(out/f"{controller['label']}.json", result)
            with (out/'episodes.jsonl').open('a') as stream:
                stream.write(json.dumps({'controller': controller['label'], **record})+'\n')
            print(json.dumps({'controller': controller['label'], 'episodes': len(trials),
                              'successes': result['successes'], 'last_success': record['success'],
                              'goal_error_m': record['goal_error_m']}), flush=True)
        summary['controllers'][controller['label']] = {k:v for k,v in result.items() if k != 'per_episode'}
    summary['wall_seconds'] = time.monotonic()-started
    atomic_json(out/'summary.json', summary)
    print(json.dumps(summary), flush=True)

