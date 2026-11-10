"""Task/result contract, input identity and target matching."""
import hashlib, json, pathlib
import numpy as np
from beforestep.paths import ROOT

def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def rel(p):
    return str(pathlib.Path(p).resolve().relative_to(ROOT))


def items_first(tstate):
    return [{'id': k, 'path': v['path'], 'sha256': v['sha256']} for k, v in sorted(tstate['crops'].items())]


def items_second(t1state, t2state):
    p1, p2 = t1state['crops']['A1'], t2state['crops']['A1']
    return [{'id': f'M{i}', 'paths': [p1['path'], p2['path']], 'sha256': [p1['sha256'], p2['sha256']]} for i in (1, 2, 3)]


def items_for_look(k, reference, current):
    if k > 1 and reference is not current and reference.get('native_ok') and current.get('native_ok'):
        return 'imgs', items_second(reference, current)
    return 'img', items_first(current)


def pending_request(tdir):
    tdir = pathlib.Path(tdir)
    if _read_single_result(tdir) is None:
        return tdir / 'lux_request.json'
    retry = tdir / 'retry'
    if (retry / 'lux_request.json').exists() and _read_single_result(retry) is None:
        return retry / 'lux_request.json'
    return None


def prepare_second_batch(tdir, decision, look):
    """R1 preregistered one-time retry, preserving the original request and result."""
    import shutil
    tdir = pathlib.Path(tdir)
    request = json.loads((tdir / 'lux_request.json').read_text())
    if look != 2 or request['mode'] != 'img' or decision['admitted_ids']:
        return None
    if {it['id'] for it in request['items']} != {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}:
        raise ValueError('R1 second-look batch must contain exactly the six original sample IDs')
    retry = tdir / 'retry'
    if (retry / 'lux_request.json').exists():
        return None
    if pending_request(tdir) is not None:
        raise ValueError('Cannot retry an incomplete or uncertain first batch')
    retry.mkdir(parents=True, exist_ok=True)
    frozen = tdir / 'decide_before_retry'
    if (tdir / 'decide').exists():
        shutil.copytree(tdir / 'decide', frozen, dirs_exist_ok=True)
    items = [{**it, 'id': it['id'] + 'b'} for it in request['items']]
    preregistration = {'schema': 'beforestep-r1-retry/v1', 'look': 2, 'additional_tasks': 6,
        'total_tasks_limit': 12, 'first_request_sha256': sha(tdir / 'lux_request.json'),
        'first_result_sha256': sha(tdir / 'lux_result.json'),
        'first_admitted_ids': decision['admitted_ids'],
        'first_decision': {k: v for k, v in decision.items() if k not in ('footprint', 'footprints')},
        'expected': 'At least one admitted candidate: plan/rehearse/execute. Zero across twelve tasks: safe stop; enter review section 2.4.'}
    (retry / 'preregistration.json').write_text(json.dumps(preregistration, indent=2) + '\n')
    write_request(retry, 'img', items)
    return retry / 'lux_request.json'


def write_request(tdir, mode, items):
    from PIL import Image
    import copy
    items = copy.deepcopy(items)
    conversions = []
    for item in items:
        original_paths = item['paths'] if mode == 'imgs' else [item['path']]
        paths, hashes = [], []
        for relative in original_paths:
            source = ROOT / relative
            actual = source
            if source.stat().st_size > 1_048_576:
                actual = source.with_name(source.stem + '_upload.jpg')
                image = Image.open(source).convert('RGB')
                image.save(actual, quality=95, subsampling=0)
                if actual.stat().st_size > 1_048_576:
                    raise ValueError('Upload JPEG exceeds the block limit; keep the original and prepare a documented input')
                conversions.append({'source':relative,'source_sha256':sha(source),'path':rel(actual),
                                    'sha256':sha(actual),'encoding':'JPEG95, no resize, 4:4:4',
                                    'reason':'Provider single-upload block limit; original PNG retained'})
            paths.append(rel(actual)); hashes.append(sha(actual))
        if mode == 'imgs':
            item.update(paths=paths,sha256=hashes)
        else:
            item.update(path=paths[0],sha256=hashes[0])
    req = {'schema': 'v8-lux-request/v1', 'mode': mode, 'version': 'G1-Turbo', 'faceCount': 30000, 'items': items,
           'input_conversions':conversions,
           'result_file': rel(pathlib.Path(tdir) / 'lux_result.json'),
           'result_schema': {'tasks': [{'id': 'A1', 'task_id': '...', 'status': 'ok|failed', 'submitted_at': '...', 'finished_at': '...',
                                        'fetched_at': '...', 'glb': 'repo-relative path of tex_mesh.glb', 'glb_sha256': '...',
                                        'inputs': ['repo-relative input image paths'],
                                        **({'api_field': 'imgs', 'n_images': 2} if mode == 'imgs' else {})}]}}
    if mode == 'imgs':
        req['imgs_rule'] = ('Each item is ONE Lux3D task whose request body carries the field imgs = [url of paths[0], url of paths[1]] '
                            'in this order (beforestep.generation.client). Never stitch the two images into one picture. '
                            'Items with identical paths are independent samples: give each its own sample id so they are not cache hits.')
    (pathlib.Path(tdir) / 'lux_request.json').write_text(json.dumps(req, indent=2, ensure_ascii=False))
    return req


def _read_single_result(tdir):
    """返回 [{'id', 'glb'}]；结果不存在返回 None；不合规（两图不是真两图、输入图对不上、GLB 校验不过）抛错。"""
    tdir = pathlib.Path(tdir)
    p = tdir / 'lux_result.json'
    if not p.exists():
        return None
    res = json.loads(p.read_text()); req = json.loads((tdir / 'lux_request.json').read_text())
    want = {it['id']: it for it in req['items']}
    tasks = res.get('tasks') or []
    ids = [t.get('id') for t in tasks]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f'{p}: duplicate task sample ids')
    if set(ids) - set(want):
        raise RuntimeError(f'{p}: unexpected task sample ids')
    if set(ids) != set(want) or any(t.get('status') not in ('ok', 'failed') for t in tasks):
        return None
    out = []
    for t in tasks:
        it = want.get(t['id'])
        if it is None:
            raise RuntimeError(f'{p}: task {t["id"]} is not in the request')
        if req['mode'] == 'imgs' and t.get('status') == 'ok' and not (t.get('api_field') == 'imgs' and t.get('n_images') == 2):
            raise RuntimeError(f'{p}: task {t["id"]} is not a real two-image call (need api_field=imgs, n_images=2)')
        paths = it['paths'] if req['mode'] == 'imgs' else [it['path']]
        hashes = it.get('sha256')
        hashes = hashes if isinstance(hashes, list) else [hashes]
        for i, path in enumerate(paths):
            image = ROOT / path
            if not image.is_file() or (i < len(hashes) and hashes[i] and sha(image) != hashes[i]):
                raise RuntimeError(f'{p}: task {t["id"]} input bytes changed or missing')
        if [str(x) for x in (t.get('inputs') or [])] != paths:
            raise RuntimeError(f'{p}: task {t["id"]} inputs {t.get("inputs")} != request {paths}')
        if t.get('status') == 'ok' and not t.get('glb'):
            raise RuntimeError(f'{p}: successful task {t["id"]} has no GLB')
        if t.get('status') == 'ok' and t.get('glb'):
            g = ROOT / t['glb']
            if not g.exists() or sha(g) != t.get('glb_sha256'):
                raise RuntimeError(f'{p}: task {t["id"]} glb missing or sha256 mismatch')
            out.append({'id': t['id'], 'glb': str(g)})
    return out


def read_result(tdir):
    tdir = pathlib.Path(tdir)
    first = _read_single_result(tdir)
    if first is None:
        return None
    retry = tdir / 'retry'
    if not (retry / 'lux_request.json').exists():
        return first
    second = _read_single_result(retry)
    if second is None:
        return None
    combined = first + second
    if len({c['id'] for c in combined}) != len(combined):
        raise ValueError('Retry sample IDs overlap with the original batch')
    return combined


def same_inputs(old_state, new_state):
    """重放检查：两次拍到的观测与 Lux3D 输入图逐字节相同。"""
    a, b = old_state.get('observation_sha256', {}), new_state.get('observation_sha256', {})
    if a != b:
        return False
    return {k: v['sha256'] for k, v in old_state['crops'].items()} == {k: v['sha256'] for k, v in new_state['crops'].items()}


def match_target(cells, prev_targets):
    """第二眼的目标对应到第一眼的哪一块：地图格子重叠最多的那块。"""
    best, score = None, 0
    for t in prev_targets:
        s = int((np.asarray(t['cells']) & cells).sum())
        if s > score:
            best, score = t, s
    return best
