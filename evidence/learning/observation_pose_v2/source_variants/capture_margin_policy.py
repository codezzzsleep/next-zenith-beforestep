"""Goal-conditioned neural control: learned actions reach the motor servos."""
from pathlib import Path
import numpy as np

from . import ppo
from beforestep.navigation.controller import BASE_POSE, yaw_of, PathResult

OBS_DIM = 51
ACTION_SCALE = np.array([.12, .12, 4., 4.])

def observation(env, goal, goal_yaw=None, previous=None, dimension=OBS_DIM):
    proprio = np.asarray(env._obs()[:35], dtype=float).copy()
    proprio[3:6] *= .5
    proprio[6] *= 5.
    proprio[7:19] -= BASE_POSE.ravel()
    proprio[19:31] *= .1
    proprio[31:35] /= 6.
    yaw = yaw_of(env.data.qpos)
    dx, dy = np.asarray(goal) - env.data.qpos[:2]
    c, s = np.cos(yaw), np.sin(yaw)
    local = np.array([c*dx+s*dy, -s*dx+c*dy])
    distance = float(np.linalg.norm(local))
    bearing = float(np.arctan2(local[1], local[0]))
    wanted = 0. if goal_yaw is None else (goal_yaw-yaw+np.pi)%(2*np.pi)-np.pi
    task = [*np.clip(local/3., -2., 2.), np.cos(bearing), np.sin(bearing),
            min(distance/(3. if dimension==47 else .2), 2.), np.cos(wanted),
            np.sin(wanted)*(1. if dimension==47 else 4.), float(goal_yaw is not None)]
    if dimension in (49,51):task.extend(np.clip(local/.2,-2.,2.))
    elif dimension!=47:raise ValueError('Unknown goal observation contract')
    if dimension==51:
        terminal = distance < .055
        orientation_only = terminal and goal_yaw is not None
        if orientation_only:
            # Position has met the inner stopping target. Its bearing can be
            # arbitrary near zero; encode the remaining orientation constraint.
            # Motor commands still come entirely from the trained network.
            task[0:2]=[0.,0.];task[2:4]=[1.,0.];task[8:10]=[0.,0.]
        task.extend([float(terminal),float(orientation_only)])
    return np.concatenate([proprio, np.zeros(4) if previous is None else previous, task])

def apply_action(env, action):
    a = np.clip(np.asarray(action, dtype=float), -1., 1.)
    if a.shape != (4,) or not np.isfinite(a).all():
        raise ValueError('Neural controller must output four finite actions')
    stance = BASE_POSE.copy()
    stance[:2, 1] += ACTION_SCALE[0]*a[0]
    stance[2:, 1] += ACTION_SCALE[1]*a[1]
    speed, turn = ACTION_SCALE[2:]*a[2:]
    env.step_command(joint_targets_rad=stance,
                     wheel_omega_rad_s=np.array([speed+turn,speed-turn,speed+turn,speed-turn]),
                     wheel_mode='velocity')

def expert_action(env, goal, goal_yaw=None):
    """Only for collecting physical demonstrations, never policy inference."""
    dx, dy = np.asarray(goal)-env.data.qpos[:2]
    distance = float(np.hypot(dx, dy));yaw=yaw_of(env.data.qpos)
    bearing = (np.arctan2(dy,dx)-yaw+np.pi)%(2*np.pi)-np.pi
    speed = 3.0*np.exp(-(bearing/.22)**2)*min(1., distance/.20)
    turn = float(np.clip(5.*bearing, -3., 3.))
    if distance < .055:
        speed = 0.
        turn = 0. if goal_yaw is None else float(np.clip(6.*((goal_yaw-yaw+np.pi)%(2*np.pi)-np.pi),-3.,3.))
    return np.array([0.,0.,speed/4.,turn/4.])

def completed(env, goal, goal_yaw=None):
    position = float(np.linalg.norm(np.asarray(goal)-env.data.qpos[:2]))
    yaw_error = 0. if goal_yaw is None else abs((goal_yaw-yaw_of(env.data.qpos)+np.pi)%(2*np.pi)-np.pi)
    stable = np.linalg.norm(env.data.qvel[:2])<.035 and abs(env.data.qvel[5])<.08
    return position < .075 and yaw_error < np.radians(4.) and stable

class GoalPolicy:
    def __init__(self, checkpoint, pose_checkpoint=None):
        self.checkpoint = Path(checkpoint)
        with np.load(self.checkpoint, allow_pickle=False) as data:
            self.params = {k:data[k].copy() for k in (*ppo.ACTOR_KEYS,*ppo.CRITIC_KEYS)}
        self.dimension=self.params['W1'].shape[0]
        if self.dimension not in (47,49,51) or self.params['Wm'].shape[1] != 4:
            raise ValueError('Checkpoint is not a goal-conditioned four-action controller')
        self.previous = np.zeros(4)
        self.pose_policy = None
        if pose_checkpoint is not None:
            from .pose import PosePolicy
            self.pose_policy = PosePolicy(pose_checkpoint)
        self._pose_goal = None
        self._pose_rotation = False

    def action(self, env, goal, goal_yaw=None):
        if self.pose_policy is not None:
            key = None if goal_yaw is None else (*map(float, goal), float(goal_yaw))
            if key != self._pose_goal:
                self._pose_goal = key
                self._pose_rotation = False
            if goal_yaw is not None:
                distance = float(np.linalg.norm(np.asarray(goal)-env.data.qpos[:2]))
                if distance < .06:
                    self._pose_rotation = True
                elif distance >= .07:
                    self._pose_rotation = False
                if self._pose_rotation:
                    a = self.pose_policy.action(env, goal_yaw)
                    self.previous = a.copy()
                    env._control_source = 'learned_pose'
                    return a
                # Translation and terminal rotation have separate learned
                # actions. The reach loop still checks the original full pose.
                goal_yaw = None
            env._control_source = 'learned'
        obs = observation(env,goal,goal_yaw,self.previous,self.dimension)
        a = ppo.deterministic_action(self.params,obs)
        self.previous = a.copy()
        return a

    def reach(self, env, goal, goal_yaw=None, log=None, phase='learned', on_step=None, max_seconds=90.):
        t0=env.t;stable=0
        while env.t-t0<max_seconds:
            if on_step is not None and on_step(env):
                return PathResult([],True,False,'collision')
            apply_action(env,self.action(env,goal,goal_yaw))
            if log is not None:log.frame(env,'LEARNED',phase)
            if on_step is not None and on_step(env):
                return PathResult([],True,False,'collision')
            if env.terminated or env.truncated:
                reason = env.last_termination.get('reason','terminated')
                return PathResult([],reason=='collision',False,reason)
            # Leave room for passive yaw drift while the sensor brakes and
            # captures. This is stricter than the unchanged 4-degree task gate.
            capture_margin = (getattr(self, 'pose_policy', None) is None or goal_yaw is None
                              or abs((goal_yaw-yaw_of(env.data.qpos)+np.pi)%(2*np.pi)-np.pi) < np.radians(3.))
            stable=stable+1 if completed(env,goal,goal_yaw) and capture_margin else 0
            if stable>=5:
                error=float(np.linalg.norm(np.asarray(goal)-env.data.qpos[:2]))
                return PathResult([error],False,True,'completed')
        return PathResult([],False,False,'time_limit')

    def run_waypoints(self, env, points, log=None, phase='learned', on_step=None, final_yaw=None):
        errors=[]
        for i,goal in enumerate(points):
            yaw=final_yaw if i==len(points)-1 else None
            result=self.reach(env,goal,yaw,log,phase,on_step)
            errors.extend(result.errors)
            if not result.completed:return PathResult(errors,result.collision,False,result.reason)
        return PathResult(errors,False,True,'completed')
