"""R3-only paid reservations; prior R1/R2 identities remain read-only reuse."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path

from beforestep.generation import client as C
from suite_lux_budget import BudgetExhausted

LIMIT = 170


class R3Budget:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.locked():
            pass

    @staticmethod
    def usage(data):
        return sum(row['new_r3_task'] and
                   (bool(row.get('task_id')) or row['status'] in ('reserved', 'uncertain'))
                   for row in data['tasks'].values())

    @contextmanager
    def locked(self):
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self.path.exists():
                data = json.loads(self.path.read_text())
            else:
                # Take this immutable snapshot before the first R3 creation.
                prior = []
                for path in sorted((C.LEDGER / 'tasks').glob('*.json')):
                    row = json.loads(path.read_text())
                    if row.get('task_id') or row.get('status') == 'uncertain':
                        prior.append(path.stem)
                data = {'schema': 'beforestep-r3-paid-budget/v1', 'limit': LIMIT,
                        'r2_new_tasks': 168, 'prior_identities': prior, 'tasks': {},
                        'started_at': datetime.now(timezone.utc).isoformat()}
            assert data['schema'] == 'beforestep-r3-paid-budget/v1' and data['limit'] == LIMIT
            yield data
            assert self.usage(data) <= LIMIT
            C.atomic_json(self.path, data)

    def reserve(self, identity, metadata, existing=None):
        with self.locked() as data:
            old = data['tasks'].get(identity)
            if old and (old.get('task_id') or old['status'] == 'uncertain'):
                return old
            is_new = identity not in data['prior_identities']
            if existing and (existing.get('task_id') or existing.get('status') == 'uncertain'):
                row = {**metadata, 'identity': identity, 'new_r3_task': is_new,
                       'status': existing['status'], 'task_id': existing.get('task_id')}
            else:
                if not is_new:
                    raise RuntimeError('A pre-R3 identity lost its client record; never recreate it')
                if not (old and old['status'] == 'reserved') and self.usage(data) >= LIMIT:
                    raise BudgetExhausted('R3 reached 170 new tasks; no new create allowed')
                row = {**metadata, 'identity': identity, 'new_r3_task': True,
                       'status': 'reserved', 'task_id': None,
                       'reserved_at': datetime.now(timezone.utc).isoformat()}
            data['tasks'][identity] = row
            return row

    def sync(self, identity, record):
        with self.locked() as data:
            data['tasks'][identity].update(
                status=record['status'], task_id=record.get('task_id'),
                client_ledger=str((C.LEDGER / 'tasks' / (identity + '.json')).relative_to(C.ROOT)))

