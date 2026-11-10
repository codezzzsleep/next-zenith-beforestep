"""Optional learned terminal rotation, separate from goal translation."""
from pathlib import Path

import numpy as np

from beforestep.navigation.controller import yaw_of
from . import ppo

SCHEMA = 'beforestep-pose-controller/v1'


def observation(env, goal_yaw):
    error = (goal_yaw-yaw_of(env.data.qpos)+np.pi) % (2*np.pi)-np.pi
    return np.array([np.clip(error/.1, -5., 5.),
                     np.clip(env.data.qvel[5]*5., -2., 2.)])


class PosePolicy:
    def __init__(self, checkpoint):
        self.checkpoint = Path(checkpoint)
        with np.load(self.checkpoint, allow_pickle=False) as data:
            if str(data['schema']) != SCHEMA:
                raise ValueError('Unknown terminal pose checkpoint contract')
            self.params = {k: data[k].copy() for k in (*ppo.ACTOR_KEYS, *ppo.CRITIC_KEYS)}
        hidden = self.params['b1'].size
        expected = ppo.init_params(np.random.default_rng(0), obs_dim=2, act_dim=4, hidden=hidden)
        if any(self.params[k].shape != expected[k].shape or not np.isfinite(self.params[k]).all()
               for k in expected):
            raise ValueError('Terminal pose checkpoint has invalid dimensions or values')

    def action(self, env, goal_yaw):
        return ppo.deterministic_action(self.params, observation(env, goal_yaw))
