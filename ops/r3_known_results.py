"""Reuse settled real task identities across byte-identical request paths."""
import json
from pathlib import Path
import shutil

from beforestep.generation import client as C, records as LX


def result_for_request(request, record):
    item = next(i for i in request['items'] if i['id'] == record['id'])
    paths = item.get('paths') or [item['path']]
    hashes = [C.sha(C.ROOT / p) for p in paths]
    expected = item['sha256'] if isinstance(item['sha256'], list) else [item['sha256']]
    if hashes != expected or hashes != record.get('input_sha256'):
        raise ValueError('Known task input bytes differ from the current request')
    if record.get('identity') != C.request_identity(request, item):
        raise ValueError('Known task identity differs from the current request')
    if request['mode'] == 'imgs' and (record.get('api_field') != 'imgs' or record.get('n_images') != 2):
        raise ValueError('Known multi-view task was not a verified two-image call')
    if record['status'] == 'ok':
        glb = C.ROOT / record['glb']
        if not glb.is_file() or C.sha(glb) != record['glb_sha256']:
            raise ValueError('Known task GLB is missing or changed')
    return {**record, 'inputs': paths, 'original_task_inputs': record['inputs'],
            'reused_known_task': True}


def old_target(paths):
    for relative in reversed(paths):
        for parent in (C.ROOT / relative).parents:
            if not parent.is_relative_to(C.ROOT):
                break
            if (parent / 'state.json').is_file() and (parent / 'decide').is_dir():
                return parent
    return None


def without_paths(value):
    if isinstance(value, dict):
        return {k: '<same-image-path>' if k == 'path' else without_paths(v) for k, v in value.items()}
    if isinstance(value, list):
        return [without_paths(v) for v in value]
    return value


def reuse_decision(target, previous):
    """Reuse old metadata only if the fresh observation and full pose are equal."""
    from beforestep.geometry import imagination as IM
    if previous is None or previous.resolve() == target.resolve():
        return False
    current_state = json.loads((target / 'state.json').read_text())
    old_state = json.loads((previous / 'state.json').read_text())
    if not LX.same_inputs(old_state, current_state) or without_paths(old_state) != without_paths(current_state):
        return False
    names = ('observation.json', 'camera_world.json', 'rgb.png', 'depth.npy', 'mask.png', 'dark.png', 'visible_points.npy')
    if any(not (previous / name).is_file() or C.sha(previous / name) != C.sha(target / name) for name in names):
        return False
    glbs = LX.read_result(target)
    if glbs is None:
        return False
    expected = IM.decision_identity(previous, glbs)
    source = None
    for folder in ('decide', 'decide_before_retry'):
        path = previous / folder / 'target_decision.json'
        if path.exists() and json.loads(path.read_text()).get('cache_identity') == expected:
            source = path.parent
            break
    if source is None:
        return False
    # The metadata differs only in crop paths, never pose, time or sensor bytes.
    # Match the original cache using genuine identical metadata, not a forged ID.
    shutil.copy2(previous / 'state.json', target / 'state.json')
    shutil.copytree(source, target / 'decide', dirs_exist_ok=True)
    assert IM.decision_identity(target, glbs) == expected
    C.atomic_json(target / 'known_decision_reuse.json', {
        'source': str(previous.relative_to(C.ROOT)), 'same_fresh_observation_bytes': True,
        'same_pose_time_and_state_except_image_paths': True, 'same_geometry_implementation': True,
        'cache_identity': expected})
    return True


def complete_known_request(path):
    """No network or creation; incomplete/uncertain IDs remain pending."""
    path = Path(path)
    request = json.loads(path.read_text())
    rows, previous = [], None
    for item in request['items']:
        identity = C.request_identity(request, item)
        ledger = C.LEDGER / 'tasks' / (identity + '.json')
        if not ledger.exists():
            return False
        record = json.loads(ledger.read_text())
        if (record.get('status') not in ('ok', 'failed') or not record.get('task_id') or
                record.get('not_real_lux') or record.get('provider') == 'offline_standin' or
                str(record['task_id']).startswith('OFFLINE:')):
            return False
        rows.append(result_for_request(request, record))
        previous = previous or old_target(record['inputs'])
    C.atomic_json(path.parent / 'lux_result.json', {
        'schema': 'beforestep-lux-result/v1', 'tasks': rows,
        'known_task_reuse': True, 'new_tasks_created': 0})
    target = path.parent.parent if path.parent.name == 'retry' else path.parent
    if (target / 'state.json').exists():
        reuse_decision(target, previous)
    return True

