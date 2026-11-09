"""Observation, imagination, rehearsal, decision and independent truth execution."""
import argparse, json, pathlib, sys, time
import numpy as np
from scipy import ndimage
from . import scene as S
from .navigation import map as N, controller as F

IMAG_MARGIN_CELLS = 1


MAX_EXTRA_LOOKS = 2


class Recorder:
    def __init__(self):
        self.t, self.q, self.phase = [], [], []
        self.monitor = None

    def frame(self, env, kind, phase):
        self.t.append(float(env.t)); self.q.append(np.asarray(env.data.qpos, float).copy()); self.phase.append(str(phase))

    def hold(self, env, phase, seconds):
        if self.monitor is not None and self.monitor(env):
            return False
        n = int(seconds * env.control_hz)
        for _ in range(n):
            env.step_command(joint_targets_rad=F.BASE_POSE, wheel_brake=np.ones(4, bool))
            self.frame(env, 'HOLD', phase)
            if self.monitor is not None and self.monitor(env):
                return False
        return True

    def save(self, path):
        np.savez_compressed(path, t=np.array(self.t), qpos=np.array(self.q), phase=np.array(self.phase))


def true_footprints(env, meta):
    import mujoco
    from matplotlib.path import Path as MP
    from scipy.spatial import ConvexHull
    m, d = env.model, env.data
    out = {}
    for key, r in meta['rocks'].items():
        bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, r['body']); P = []
        for g in range(m.ngeom):
            if m.geom_bodyid[g] == bid and m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
                mid = m.geom_dataid[g]; V = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
                P.append(V @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g])
        P = np.concatenate(P); h = ConvexHull(P[:, :2])
        out[key] = MP(P[h.vertices, :2]).contains_points(np.c_[N.GX.ravel(), N.GY.ravel()]).reshape(N.GX.shape)
    return out


def pose(env):
    q = env.data.qpos
    return float(q[0]), float(q[1]), F.yaw_of(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--policy', required=True, choices=['conservative', 'optimistic', 'imagination'])
    ap.add_argument('--scene', default='gate_passage_001', help='Named configuration in config/scenes')
    ap.add_argument('--out', required=True); ap.add_argument('--imagine', choices=['lux', 'truth'], default='lux')
    ap.add_argument('--see-dark', action='store_true', help='对照实验：假设相机在黑影里也能测出深度')
    ap.add_argument('--max-looks', type=int, default=None, help='最多看几眼（想象策略最多两眼；保守策略默认五眼）')
    ap.add_argument('--reuse-lux', default=None, help='已有想象运行：只复用逐字节相同的观测与生成结果，不复用旧决策')
    ap.add_argument('--recorded-observations', help='显式使用记录的传感器观测；核对姿态和时刻，不冒充本次实时输入')
    ap.add_argument('--tag', default=None, help='输出子目录名（默认等于策略名）')
    ap.add_argument('--trust', default=None, help='反事实：T1=A2,T2=B1 —— 这几块石头只用指定的那份想象，不管自检结论，也不看第二眼')
    a = ap.parse_args()
    scene_definition = S.configure(a.scene)
    if a.recorded_observations:
        fixture = pathlib.Path(a.recorded_observations) / 'scene.json'
        if not fixture.is_file() or S.physical_identity(json.loads(fixture.read_text())) != S.physical_identity(scene_definition):
            ap.error('Recorded observations must match the selected physical scene')
    if a.recorded_observations and (a.policy != 'imagination' or a.imagine != 'lux' or a.reuse_lux):
        ap.error('--recorded-observations仅用于Lux3D记录观测复现，不能与--reuse-lux混用')
    a.max_looks = a.max_looks if a.max_looks is not None else (2 if a.policy == 'imagination' else 5)
    if a.max_looks < 1 or (a.policy == 'imagination' and a.max_looks > 2):
        ap.error('想象策略允许一至两眼；其他策略的观察次数必须为正数')
    out = pathlib.Path(a.out) / (a.tag or a.policy); out.mkdir(parents=True, exist_ok=True)
    import hashlib
    from .paths import ROOT
    identity = {'schema':'beforestep-run-identity/v1', 'arguments':vars(a), 'scene':scene_definition,
                'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted((ROOT/'src/beforestep').rglob('*.py'))},
                'config_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted((ROOT/'config').glob('*.json'))}}
    (out/'run_identity.json').write_text(json.dumps(identity,ensure_ascii=False,indent=2))
    (out/'scene.json').write_text(json.dumps(scene_definition,ensure_ascii=False,indent=2))
    dark_thr = 0.0 if a.see_dark else 0.10
    trust = dict(kv.split('=') for kv in a.trust.split(',')) if a.trust else None
    (out / 'looks').mkdir(exist_ok=True)
    if a.reuse_lux:
        import shutil
        source = pathlib.Path(a.reuse_lux).resolve() / 'looks'
        if not source.is_dir():
            ap.error(f'复用源不存在：{source}')
        if source.resolve() != (out / 'looks').resolve():
            shutil.copytree(source, out / 'looks', dirs_exist_ok=True)
    if a.trust:                     # 反事实：复用想象那台车已有的观测、Lux3D 结果与自检结果，不产生新的调用
        import shutil
        src = out.parent / 'imagination' / 'looks'
        if not src.exists():
            raise SystemExit(f'--trust needs {src}')
        for ld in sorted(src.glob('look*')):
            if ld.is_dir() and not ld.name.endswith('_replay'):
                shutil.copytree(ld, out / 'looks' / ld.name, dirs_exist_ok=True)
    events = []
    (out / 'events.jsonl').write_text('')
    def ev(kind, **kw):
        e = {'kind': kind, **kw}; events.append(e)
        line = json.dumps(e, ensure_ascii=False)
        with (out / 'events.jsonl').open('a') as f:
            f.write(line + '\n')
        print(line, flush=True)
        return e

    from .visualization import camera as VZ
    t0 = time.time()
    spec, rb, meta = S.scene_spec(pathlib.Path(a.out) / 'scene')
    env = S.make_env(spec); S.place(env, *S.START); S.settle(env)
    lux = a.policy == 'imagination' and a.imagine == 'lux'
    vm = VZ.video_model(env, rb, width=1600, height=1200, off=VZ.HI)
    vm.hi_sensor = True                # 三台车用同一条传感器链：一个 4040×3030 渲染器，缩到 1600×1200 建图
    rec = Recorder(); rec.frame(env, 'START', 'start')
    bodies = [r['body'] for r in meta['rocks'].values()] + meta['walls']
    watch = N.contact_watch(env, bodies)
    crash = {}
    def on_step(env):
        hit, info = watch(env)
        if hit:
            crash.update(info); return True
        return False
    rec.monitor = on_step
    truth = true_footprints(env, meta)
    truth_union = np.logical_or.reduce(list(truth.values()))
    truth_objs = []
    if a.policy == 'imagination' and a.imagine == 'truth':
        import trimesh
        import mujoco
        for key, r_ in meta['rocks'].items():
            bid = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, r_['body']); Vs, Fs, off_ = [], [], 0
            for g in range(env.model.ngeom):
                if env.model.geom_bodyid[g] == bid and env.model.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
                    mid = env.model.geom_dataid[g]
                    V = env.model.mesh_vert[env.model.mesh_vertadr[mid]:env.model.mesh_vertadr[mid] + env.model.mesh_vertnum[mid]]
                    Fc = env.model.mesh_face[env.model.mesh_faceadr[mid]:env.model.mesh_faceadr[mid] + env.model.mesh_facenum[mid]]
                    Vs.append(V @ env.data.geom_xmat[g].reshape(3, 3).T + env.data.geom_xpos[g]); Fs.append(Fc + off_); off_ += len(V)
            p_ = out / 'truth_standin' / f'{key}.obj'; p_.parent.mkdir(parents=True, exist_ok=True)
            trimesh.Trimesh(np.concatenate(Vs), np.concatenate(Fs), process=False).export(str(p_)); truth_objs.append(p_)

    looks = []
    # ---- 0. 出发前在起点拍一张（相机一直开着；这一张让地图里有起点附近的地面）
    ob0 = N.observe(vm, env, dark_thr=dark_thr)
    base_maps = [ob0['state']]
    # ---- 1. 开到第一次停车点
    try:
        _, stopped = F.drive_to(env, *S.STOP1, log=rec, phase='approach', on_step=on_step)
        if not stopped:
            F.turn_to(env, 0.0, log=rec, phase='approach', on_step=on_step)
    except F.MotionInterrupted:
        pass
    rec.hold(env, 'look1', 1.0)

    def look(label):
        ob = N.observe(vm, env, dark_thr=dark_thr)
        k = len(looks) + 1
        from PIL import Image
        Image.fromarray(ob['rgb']).save(out / 'looks' / f'look{k}_rgb.png')
        np.save(out / 'looks' / f'look{k}_state.npy', ob['state']); np.save(out / 'looks' / f'look{k}_depth.npy', ob['depth'].astype(np.float32))
        np.save(out / 'looks' / f'look{k}_dark.npy', ob['dark'])
        looks.append(ob)
        st = N.fuse(base_maps + [l['state'] for l in looks])
        x, y, yaw = pose(env)
        ev('look', k=k, label=label, pose=[round(x, 3), round(y, 3), round(float(np.degrees(yaw)), 2)], t=round(env.t, 2),
           cells={N.NAMES[i]: int((st == i).sum()) for i in range(6)}, cam_pos=[round(v, 4) for v in ob['cam_pos']])
        return st

    state = look('first')

    tlooks = []                       # 每一眼的目标石头 [{'target','dir','cells','state'}]
    imagined_meshes = {}              # 目标 -> [被采纳候选的世界坐标 OBJ]（用于在想象里预演）
    focus = {'cells': None}           # 第二眼要看的地方：想象全被拒绝的石头周围
    why = {'reason': None, 'admitted': {}}   # 为什么看下一眼；每块（第一眼编号的）石头当前是否有被采纳的想象

    def capture_targets(k, state):
        """想象的车：这一眼的每块目标石头写观测目录；重放时核对与上次逐字节相同。"""
        import shutil
        from .observation import capture as O
        from .generation import records as LX
        ld = (out / 'looks' / f'look{k}').resolve()
        if a.recorded_observations:
            source = pathlib.Path(a.recorded_observations).resolve() / 'looks' / f'look{k}'
            if not source.is_dir():
                raise RuntimeError(f'Recorded observation missing: {source}')
            tg = []
            for td in sorted(source.glob('T*')):
                st = json.loads((td / 'state.json').read_text())
                if not np.allclose(st['robot_qpos_world'], env.data.qpos, atol=1e-6, rtol=0) or abs(st['t_sim'] - env.t) > 1e-6:
                    raise RuntimeError(f'Recorded observation pose/time mismatch: look{k}/{td.name}')
                destination = ld / td.name
                shutil.copytree(td, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns('decide','lux_cache'))
                tg.append({'target': td.name, 'dir': destination,
                           'cells': np.load(td / 'cells.npy'), 'state': st})
            ev('recorded_sensor', look=k, source=str(source), verified_pose=True, verified_time=True,
               note='Frozen recorded RGB-D and Lux3D inputs; current live render is a separate observation.')
            tlooks.append(tg)
            return tg
        if not ld.exists():
            tg = O.capture(vm, env, ld, f'look{k}', state, dark_thr=dark_thr)
        else:
            # 重放：拍到临时目录，与上次逐字节核对；一致就用上次的目录（里面有 Lux3D 请求与结果）
            tmp = (out / 'looks' / f'look{k}_replay').resolve()
            if tmp.exists():
                shutil.rmtree(tmp)
            tg_new = O.capture(vm, env, tmp, f'look{k}', state, dark_thr=dark_thr)
            tg = []
            for t in tg_new:
                old = ld / t['target'] / 'state.json'
                if not old.exists() or not LX.same_inputs(json.loads(old.read_text()), t['state']):
                    ev('replay_mismatch', look=k, target=t['target'])
                    raise SystemExit(11)
                tg.append(dict(t, dir=ld / t['target'], state=json.loads(old.read_text())))
            shutil.rmtree(tmp)
        tlooks.append(tg)
        return tg

    def imagined_mask():
        if a.policy != 'imagination':
            return None
        if a.imagine == 'truth':
            return truth_union
        from .geometry import imagination as IM
        from .generation import records as LX
        k = len(looks)
        tg = tlooks[-1]
        missing = []
        for t in tg:
            ref = t if k == 1 else (LX.match_target(t['cells'], tlooks[0]) or t)
            t['ref'] = ref['target']
            # 第二眼只为"想象全被拒绝"的石头（或新出现的石头）再调 Lux3D；已经有被采纳想象的石头沿用原结论。
            # 留不出余量或预演碰撞时，所有拍到的石头都重新想象。
            t['skip'] = (k > 1 and why['reason'] == 'rejected' and why['admitted'].get(ref['target'], False))
            if t['skip'] or (t['dir'] / 'lux_request.json').exists():
                continue
            if k == 1 or ref is t:
                LX.write_request(t['dir'], 'img', LX.items_first(t['state']))
            else:
                LX.write_request(t['dir'], 'imgs', LX.items_second(ref['state'], t['state']))
        for t in tg:
            if not t['skip'] and LX.read_result(t['dir']) is None:
                missing.append(LX.rel(t['dir'] / 'lux_request.json'))
        if missing:
            ev('need_lux3d', look=k, requests=missing)
            (out / 'NEED_LUX3D.json').write_text(json.dumps({'look': k, 'requests': missing}, indent=2))
            raise SystemExit(10)
        mask = np.zeros((N.NX, N.NY), bool)
        per = []
        focus['cells'] = None
        VZ.release(vm)                 # 配准前释放渲染上下文（省约 1.4 GB）
        # 每块石头用它最近一次被拍到时的想象（第二眼没拍到的石头，沿用第一眼的结论）
        latest = {}
        for kk, tl in enumerate(tlooks):
            for t in tl:
                if t.get('skip'):
                    continue
                latest[t.get('ref', t['target'])] = t
        for t in latest.values():
            dd = t['dir'] / 'decide'
            glbs = LX.read_result(t['dir'])
            identity = IM.decision_identity(t['dir'], glbs)
            saved = dd / 'target_decision.json'
            res = json.loads(saved.read_text()) if saved.is_file() else {}
            if res.get('cache_identity') == identity and (dd / 'footprint_union.npy').is_file():
                fp = np.load(dd / 'footprint_union.npy')
            else:
                res = IM.decide_target(t['dir'], glbs, dd); fp = res['footprint']
            if trust and t['target'] in trust:
                cid = trust[t['target']]
                fp = np.load(dd / f'footprint_{cid}.npy')
                c = next(c for c in res['candidates'] if c['id'] == cid)
                imagined_meshes[t.get('ref', t['target'])] = [IM.candidate_world_mesh(c['glb'], c['M'], t['state']['local_frame'], dd / f'world_{cid}.obj')]
                mask |= fp
                per.append({'target': t['target'], 'trusted': cid, 'admitted_by_self_check': c['admitted']})
                continue
            n_adm = len(res['admitted_ids'])
            objs = []
            for c in res['candidates']:
                if c['admitted']:
                    objs.append(IM.candidate_world_mesh(c['glb'], c['M'], t['state']['local_frame'], dd / f'world_{c["id"]}.obj'))
            imagined_meshes[t.get('ref', t['target'])] = objs
            why['admitted'][t.get('ref', t['target'])] = n_adm > 0
            if n_adm == 0:
                focus['cells'] = (focus['cells'] if focus['cells'] is not None else np.zeros_like(t['cells'])) | ndimage.binary_dilation(t['cells'], iterations=int(1.0 / N.RES))
                # 这块石头的想象全被自检拒绝：它背后与周围看不见的格子按保守处理
                near = ndimage.binary_dilation(t['cells'], iterations=int(1.5 / N.RES))
                fp = near & np.isin(state, (N.DARK, N.HIDDEN, N.UNSEEN))
            mask |= fp
            per.append({'target': t['target'], 'n_candidates': len(res['candidates']), 'admitted': res['admitted_ids'],
                        'rejected': [c['id'] for c in res['candidates'] if not c['admitted']]})
        ev('imagination', look=k, targets=per)
        return mask

    def rehearse(path, k):
        """在想象里先走一遍：把规划好的路线放进只有想象石块的场景里，每份想象一格；任何一格碰了就不执行。"""
        from .geometry import imagination as IM
        if a.imagine == 'truth':
            panes = [[str(p) for p in truth_objs]]
        else:
            from itertools import product
            lists = [v for v in imagined_meshes.values() if v]
            if not lists:
                return False, []
            panes = [[str(p) for p in combination] for combination in product(*lists)]
        results = []
        q0, v0 = env.data.qpos.copy(), env.data.qvel.copy()
        for i, objs in enumerate(panes):
            pd = out / 'rehearsal' / f'look{k}' / f'pane{i}'
            spec_r = IM.rehearsal_spec(spec, objs, pd)
            env_r = S.make_env(spec_r)
            import mujoco
            env_r.data.qpos[:] = q0; env_r.data.qvel[:] = v0; mujoco.mj_forward(env_r.model, env_r.data)
            w = N.contact_watch(env_r, [f'obstacle{j}' for j in range(len(objs) + 1)])
            hit = {}
            def stop(e):
                h, info = w(e)
                if h:
                    hit.update(info); return True
                return False
            rr = Recorder(); rr.frame(env_r, 'START', 'rehearsal')
            motion = F.run_waypoints(env_r, path, log=rr, phase='rehearsal', on_step=stop, final_yaw=None)
            rr.save(pd / 'traj.npz')
            record = {'objects': objs, 'collided': motion.collision, 'completed': motion.completed,
                      'reason': motion.reason, 'waypoint_errors_m': motion.errors, 'contact': hit or None}
            (pd / 'pane.json').write_text(json.dumps(record, indent=2))
            results.append({'pane': i, **record})
            del env_r
        ev('rehearsal', look=k, panes=results)
        return bool(results) and all(r['completed'] and not r['collided'] for r in results), results

    def go_to_viewpoint(state, occ):
        x, y, _ = pose(env)
        unknown = np.isin(state, (N.DARK, N.HIDDEN, N.UNSEEN)) & ~N.prior_nogo()
        need = unknown & (N.GX > x + 1.0) & (N.GX < x + 4.5)
        if focus['cells'] is not None and (unknown & focus['cells']).sum() > 50:
            need = unknown & focus['cells']          # 想象的车：去看想象被拒绝的那块石头
        path = None
        for vx, vy, vyaw, score, n in N.choose_second_look(state, (x, y), need, occ)[:40]:
            if n < 20:
                break
            path = N.plan(occ, (x, y), (vx, vy))
            if path is not None:
                break
        if path is None:
            return None
        ev('second_look_plan', viewpoint=[round(vx, 2), round(vy, 2), round(float(np.degrees(vyaw)), 1)], expected_new_cells=n,
           path=None if path is None else [[round(p[0], 3), round(p[1], 3)] for p in path])
        if path is None:
            return None
        motion = F.run_waypoints(env, path, log=rec, phase=f'to_look{len(looks) + 1}', on_step=on_step, final_yaw=vyaw)
        return 'crash' if motion.collision else ('ok' if motion.completed else 'motion_failed')

    if lux and not crash:
        capture_targets(1, state)
    result = None
    extra = 0
    last_im = None
    while True:
        if crash:
            result = 'collision'
            break
        x, y, yaw = pose(env)
        im = imagined_mask()
        last_im = im
        if a.policy == 'imagination':
            occ_m = N.occupancy(state, 'imagination', ndimage.binary_dilation(im, iterations=IMAG_MARGIN_CELLS))
            path = N.plan(occ_m, (x, y), S.GOAL)
            if path is None:
                raw = N.plan(N.occupancy(state, 'imagination', im), (x, y), S.GOAL)
                reason = 'low_margin' if raw is not None else 'imagined_blocked'
                if trust and raw is not None:
                    path, reason = raw, 'trusted_without_margin'
            else:
                reason = None
            occ = occ_m
        else:
            occ = N.occupancy(state, a.policy, known_free=N.swept(np.array(rec.q)[:, :2]))
            path = N.plan(occ, (x, y), S.GOAL)
            reason = None if path is not None else 'no_path'
        ev('plan', policy=a.policy, look=len(looks), path=None if path is None else [[round(p[0], 3), round(p[1], 3)] for p in path],
           reason=reason, margin_vs_truth=None if path is None else N.path_clearance(path, (x, y), N.clearance(truth_union | N.prior_nogo())))
        if path is not None and a.policy == 'imagination' and not trust:
            ok, _ = rehearse(path, len(looks))
            if not ok:
                ev('plan_rejected_by_rehearsal', look=len(looks)); path = None; reason = 'rehearsal_collision'
        if path is not None:
            motion = F.run_waypoints(env, path, log=rec, phase='execute', on_step=on_step, final_yaw=None)
            if motion.collision:
                ev('collision', **crash); rec.hold(env, 'crash', 2.0); result = 'collision'
            else:
                xg, yg, _ = pose(env)
                result = 'arrived' if motion.completed and np.hypot(xg - S.GOAL[0], yg - S.GOAL[1]) < 0.3 else 'stopped_short'
                rec.hold(env, result, 1.5)
            break
        if len(looks) >= a.max_looks or trust:
            result = 'stuck'; rec.hold(env, 'stuck', 2.0); break
        if a.policy == 'imagination':
            why['reason'] = 'rejected' if focus['cells'] is not None else reason
        occ_safe = N.occupancy(state, 'conservative', known_free=N.swept(np.array(rec.q)[:, :2]))   # 去第二眼的位置只走看得见、开过的地方
        r = go_to_viewpoint(state, occ_safe)
        if r is None:
            result = 'stuck'; ev('no_viewpoint'); rec.hold(env, 'stuck', 2.0); break
        if r == 'crash':
            ev('collision', **crash); result = 'collision'; break
        if r == 'motion_failed':
            result = 'stopped_short'; ev('viewpoint_not_reached'); break
        rec.hold(env, f'look{len(looks) + 1}', 1.0)
        state = look(f'extra{extra + 1}'); extra += 1
        if lux:
            capture_targets(len(looks), state)

    x, y, yaw = pose(env)
    if crash:
        result = 'collision'
    summ = {'policy': a.policy, 'tag': a.tag or a.policy, 'see_dark': bool(a.see_dark), 'imagine': a.imagine if a.policy == 'imagination' else None, 'result': result,
            'scene_id':S.SCENE_ID,
            'sensor_mode': 'recorded' if a.recorded_observations else 'live',
            'looks': len(looks), 'final_pose': [round(x, 3), round(y, 3), round(float(np.degrees(yaw)), 2)],
            'sim_time_s': round(env.t, 2), 'wall_s': round(time.time() - t0, 1), 'collision': crash or None}
    ev('result', **summ)
    rec.save(out / 'traj.npz')
    np.save(out / 'state_final.npy', state)
    (out / 'events.jsonl').write_text('\n'.join(json.dumps(e, ensure_ascii=False) for e in events) + '\n')
    (out / 'summary.json').write_text(json.dumps(summ, indent=2, ensure_ascii=False))
    N.save_map_png(state, out / 'map_final.png',
                   paths=[([tuple(S.START), tuple(S.STOP1)] + [tuple(p) for p in []], (255, 255, 0))],
                   marks=[(S.GOAL, (0, 255, 0))], imagined=last_im)
    VZ.release(vm)
