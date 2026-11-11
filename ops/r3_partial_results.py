"""Settle already-created IDs when a request stops at the R3 budget/deadline."""
import json
from pathlib import Path

from beforestep.generation import client as C
from r3_known_results import result_for_request
from suite_lux_budget import PendingTask, task_lock


def settle_request(request_path, budget, timeout=3600, scene=None):
    request_path = Path(request_path)
    request = json.loads(request_path.read_text())
    records = []
    pending = False
    for item in request['items']:
        identity = C.request_identity(request, item)
        client_path = C.LEDGER / 'tasks' / (identity + '.json')
        if not client_path.exists():
            continue
        with task_lock(identity):
            record = json.loads(client_path.read_text())
            if not record.get('task_id') and record['status'] != 'uncertain':
                continue
            old = json.loads(budget.path.read_text())['tasks'].get(identity, {})
            metadata = {'scene': scene or old['scene'],
                        'sample': item['id'], 'request': str(request_path.relative_to(C.ROOT)),
                        'request_sha256': C.sha(request_path), 'input_sha256': item['sha256']}
            budget.reserve(identity, metadata, record)
            try:
                if record['status'] not in ('ok', 'failed'):
                    record = C.poll(record, timeout=timeout)
            finally:
                if client_path.exists():
                    budget.sync(identity, json.loads(client_path.read_text()))
        if record['status'] in ('ok', 'failed'):
            records.append(result_for_request(request, record))
        else:
            records.append(record)
            pending = True
    missing = [item['id'] for item in request['items'] if item['id'] not in {row['id'] for row in records}]
    result = {'schema': 'beforestep-r3-partial-lux-result/v1', 'tasks': records,
              'incomplete_request': True, 'missing_item_ids': missing,
              'scope': 'Known task IDs queried after creation stopped. Missing samples are not created or treated as provider failures or self-check rejections.'}
    if records:
        C.atomic_json(request_path.parent / 'lux_result.partial.json', result)
    if pending:
        raise PendingTask('Known cloud identities remain pending or uncertain; only query on recovery')
    return result
