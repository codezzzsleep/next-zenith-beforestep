"""Joint mapping and calibrated stance targets."""
import mujoco


LEG = ['FR', 'FL', 'RR', 'RL']
STANCE = {'hip': 0.0, 'thigh': 0.85, 'calf': -1.65}
STANCE_HIGH = {'hip': 0.0, 'thigh': 0.55, 'calf': -1.05}
def ids(m):
    d = {}
    for leg in LEG:
        for part in ('hip', 'thigh', 'calf', 'wheel'):
            jn = f'{leg}_{part}_joint'
            d[jn] = dict(
                qadr=m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jn)],
                vadr=m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jn)],
                act=mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, f'{leg}_{part}'),
            )
    return d
