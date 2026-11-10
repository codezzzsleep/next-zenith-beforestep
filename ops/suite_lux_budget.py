"""Reserve R2 task identities before paid creation, with a hard 360 task cap.

The client task ledgers remain authoritative for cloud IDs and uncertain
responses. This ledger stores no upload URLs, authentication or secret values.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import time

from beforestep.generation import client as C

LIMIT = 360
R2_STARTED_AT = datetime(2026, 11, 10, 13, 51, tzinfo=timezone.utc).timestamp()


class BudgetExhausted(RuntimeError):
    pass


class PendingTask(RuntimeError):
    pass


class Budget:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text()) if self.path.exists() else {
                'schema': 'beforestep-r2-paid-budget/v1', 'limit': LIMIT, 'tasks': {}}
            assert data['limit'] == LIMIT
            yield data
            C.atomic_json(self.path, data)

    @staticmethod
    def usage(data):
        return sum(bool(row.get('task_id')) or row['status'] in ('reserved', 'uncertain')
                   for row in data['tasks'].values() if row.get('new_r2_task', True))

    def reserve(self, identity, metadata, existing=None):
        with self.locked() as data:
            old = data['tasks'].get(identity)
            if old and (old.get('task_id') or old['status'] == 'uncertain'):
                return old
            if existing and (existing.get('task_id') or existing.get('status') == 'uncertain'):
                # Pre-existing client identity is restored, never newly created.
                submitted = existing.get('submitted_at')
                if isinstance(submitted, str):
                    try:
                        submitted = datetime.fromisoformat(submitted.replace('Z', '+00:00')).timestamp()
                    except ValueError:
                        submitted = None
                new_task = bool(old) or not isinstance(submitted, (int, float)) or submitted >= R2_STARTED_AT
                row = {**metadata, 'identity': identity, 'new_r2_task': new_task,
                       'status': existing['status'], 'task_id': existing.get('task_id')}
                data['tasks'][identity] = row
                return row
            already_reserved = old and old['status'] == 'reserved'
            if not already_reserved and self.usage(data) >= LIMIT:
                raise BudgetExhausted('R2 paid task capacity reached 360; no create allowed')
            row = {**metadata, 'identity': identity, 'new_r2_task': True, 'status': 'reserved',
                   'task_id': None, 'reserved_at': datetime.now(timezone.utc).isoformat()}
            data['tasks'][identity] = row
            return row

    def sync(self, identity, record):
        with self.locked() as data:
            row = data['tasks'][identity]
            row.update(status=record['status'], task_id=record.get('task_id'),
                       client_ledger=str((C.LEDGER / 'tasks' / (identity + '.json')).relative_to(C.ROOT)))
            assert self.usage(data) <= LIMIT


@contextmanager
def task_lock(identity):
    lock_path = C.LEDGER / 'locks' / (identity + '.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def generate_request(request_path, budget, scene, timeout=3600):
    """Complete one immutable request; known and uncertain IDs are never created twice."""
    request_path = Path(request_path)
    request = json.loads(request_path.read_text())
    if (request_path.parent / 'lux_result.json').exists():
        old = json.loads((request_path.parent / 'lux_result.json').read_text())
        if old.get('not_real_lux') or old.get('provider') == 'offline_standin':
            raise ValueError('Offline results cannot enter paid generation')
    records = []
    for item in request['items']:
        identity = C.request_identity(request, item)
        ledger = C.LEDGER / 'tasks' / (identity + '.json')
        metadata = {'scene': scene, 'sample': item['id'],
                    'request': str(request_path.relative_to(C.ROOT)),
                    'request_sha256': C.sha(request_path), 'input_sha256': item['sha256']}
        while True:
            with task_lock(identity):
                existing = json.loads(ledger.read_text()) if ledger.exists() else None
                budget.reserve(identity, metadata, existing)
                if existing and (existing.get('task_id') or existing.get('status') == 'uncertain'):
                    record = existing
                    budget.sync(identity, record)
                    break
                try:
                    record = C.submit(request, item)
                    budget.sync(identity, record)
                    break
                except C.ProviderRejected as error:
                    if ledger.exists():
                        budget.sync(identity, json.loads(ledger.read_text()))
                    if error.code != 'GENERATION_CONCURRENCY_LIMIT_EXCEEDED':
                        raise
                except Exception:
                    if ledger.exists():
                        budget.sync(identity, json.loads(ledger.read_text()))
                    raise
            time.sleep(10)
        records.append(record)
    from concurrent.futures import ThreadPoolExecutor

    def poll(record):
        ledger = C.LEDGER / 'tasks' / (record['identity'] + '.json')
        with task_lock(record['identity']):
            try:
                current = json.loads(ledger.read_text()) if ledger.exists() else record
                return C.poll(current, timeout=timeout)
            finally:
                if ledger.exists():
                    budget.sync(record['identity'], json.loads(ledger.read_text()))

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(poll, records))
    C.atomic_json(request_path.parent / 'lux_result.json', {
        'schema': 'beforestep-lux-result/v1', 'tasks': records})
    if any(record['status'] not in ('ok', 'failed') for record in records):
        raise PendingTask('Existing cloud identities still pending or uncertain; only query on recovery')
    return records
