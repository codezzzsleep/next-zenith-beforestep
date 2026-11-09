"""Resolve the collision parts actually loaded by the environment."""
import hashlib, json, pathlib
from beforestep.paths import ROOT

def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def resolve_asset(asset_dir):
    """
    读取 manifest、解析 parts 路径、预检，返回实际参与仿真的文件列表。

    返回 dict: ok, reason, manifest, part_paths(abs, 顺序同 manifest),
               collision_sha, path_mode, missing
    """
    d = pathlib.Path(asset_dir)
    base = {'ok': False, 'manifest': None, 'part_paths': [], 'collision_sha': None,
            'path_mode': None, 'missing': []}
    if not d.exists():
        return {**base, 'reason': 'asset_dir_missing'}
    mf = d / 'manifest.json'
    if not mf.exists():
        return {**base, 'reason': 'manifest_missing'}
    try:
        man = json.loads(mf.read_text())
    except Exception:
        return {**base, 'reason': 'manifest_unreadable'}
    if not isinstance(man, dict):
        return {**base, 'reason': 'manifest_not_object'}

    raw_parts = man.get('parts')
    if not isinstance(raw_parts, list) or not raw_parts:
        return {**base, 'reason': 'no_collision_parts', 'manifest': man}

    resolved, missing, modes = [], [], set()
    for p in raw_parts:
        if not isinstance(p, str) or not p.strip():
            missing.append(repr(p))
            continue
        pp = pathlib.Path(p)
        if pp.is_absolute():
            if pp.exists():
                resolved.append(pp.resolve())
                modes.add('absolute_compat')
                continue
            cand = d / 'parts' / pp.name     # 兼容：绝对路径失效时按命名回退
            if cand.exists():
                resolved.append(cand.resolve())
                modes.add('absolute_compat_fallback')
                continue
            missing.append(str(pp))
        else:
            # 约定：相对 manifest 所在目录；兼容旧数据里"相对仓库根"的写法
            cand = d / pp
            if cand.exists():
                resolved.append(cand.resolve())
                modes.add('relative')
                continue
            legacy = ROOT / pp
            if legacy.exists():
                resolved.append(legacy.resolve())
                modes.add('root_relative_compat')
                continue
            tail = d / 'parts' / pp.name
            if tail.exists():
                resolved.append(tail.resolve())
                modes.add('basename_fallback')
                continue
            missing.append(str(cand))

    if missing:
        return {**base, 'reason': 'missing_part', 'manifest': man,
                'part_paths': resolved, 'path_mode': '+'.join(sorted(modes)) or None,
                'missing': missing}

    # 哈希必须对应实际参与仿真的文件，顺序与 manifest 一致，
    # 未被 manifest 引用的残留 STL 不参与
    h = hashlib.sha256()
    for p in resolved:
        h.update(p.name.encode())
        h.update(sha256_file(p).encode())
    collision_sha = h.hexdigest()[:32]
    mode = '+'.join(sorted(modes))

    try:
        height = float(man['height_m'])
        rel_w = float(man['rel_width'])
    except Exception:
        return {**base, 'reason': 'bad_dimensions', 'manifest': man,
                'part_paths': resolved, 'collision_sha': collision_sha, 'path_mode': mode}
    if not (height > 0) or not (rel_w > 0):
        return {**base, 'reason': 'nonpositive_dimensions', 'manifest': man,
                'part_paths': resolved, 'collision_sha': collision_sha, 'path_mode': mode}
    if man.get('pass', True) is False:
        return {**base, 'reason': 'manifest_pass_false', 'manifest': man,
                'part_paths': resolved, 'collision_sha': collision_sha, 'path_mode': mode}

    return {'ok': True, 'reason': 'ok', 'manifest': man, 'part_paths': resolved,
            'collision_sha': collision_sha, 'path_mode': mode, 'missing': []}
