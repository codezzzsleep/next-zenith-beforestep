"""A separate, durable paid ledger for the labelled post-result demonstration."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path

from beforestep.generation import client as C
from r3_lux_budget import ExperimentDeadline, R3Budget
from suite_lux_budget import BudgetExhausted

END = datetime(2026, 11, 18, 0, 0, tzinfo=timezone.utc)


class AwardBudget:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.locked():
            pass

    @staticmethod
    def usage(data):
        return sum(bool(row.get('new_award_task')) and
                   (bool(row.get('task_id')) or row['status'] in ('reserved', 'uncertain'))
                   for row in data['tasks'].values())

    @contextmanager
    def locked(self):
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self.path.exists():
                data = json.loads(self.path.read_text())
            else:
                prior = [p.stem for p in (C.LEDGER / 'tasks').glob('*.json')
                         if (lambda r: r.get('task_id') or r.get('status') == 'uncertain')(json.loads(p.read_text()))]
                r3 = json.loads((C.LEDGER / 'r3-budget.json').read_text())
                data = {'schema': 'beforestep-award-paid-budget/v1', 'limit': 30,
                        'cumulative_limit': 316, 'prior_r2_tasks': r3['r2_new_tasks'],
                        'prior_r3_tasks': R3Budget.usage(r3), 'prior_identities': sorted(prior),
                        'tasks': {}, 'started_at': datetime.now(timezone.utc).isoformat(),
                        'scope': 'Post-result supplemental demonstration; excluded from R1/R2/R3 conclusions.'}
            assert data['schema'] == 'beforestep-award-paid-budget/v1'
            yield data
            assert self.usage(data) <= data['limit']
            assert data['prior_r2_tasks'] + data['prior_r3_tasks'] + self.usage(data) <= data['cumulative_limit']
            C.atomic_json(self.path, data)

    def reserve(self, identity, metadata, existing=None):
        with self.locked() as data:
            old = data['tasks'].get(identity)
            if old and (old.get('task_id') or old['status'] == 'uncertain'):
                return old
            is_new = identity not in data['prior_identities']
            if existing and (existing.get('task_id') or existing.get('status') == 'uncertain'):
                row = {**metadata, 'identity': identity, 'new_award_task': is_new,
                       'new_r3_task': is_new, 'status': existing['status'], 'task_id': existing.get('task_id')}
            else:
                if not is_new:
                    raise RuntimeError('Known identity lost its client record; do not recreate it')
                if datetime.now(timezone.utc) >= END:
                    raise ExperimentDeadline('Award deadline reached; no new create')
                usage = self.usage(data)
                if not (old and old['status'] == 'reserved') and (
                        usage >= data['limit'] or data['prior_r2_tasks'] + data['prior_r3_tasks'] + usage >= data['cumulative_limit']):
                    raise BudgetExhausted('Award task or cumulative cap reached; only query existing IDs')
                row = {**metadata, 'identity': identity, 'new_award_task': True, 'new_r3_task': True,
                       'status': 'reserved', 'task_id': None, 'reserved_at': datetime.now(timezone.utc).isoformat()}
            data['tasks'][identity] = row
            return row

    def sync(self, identity, record):
        with self.locked() as data:
            data['tasks'][identity].update(status=record['status'], task_id=record.get('task_id'),
                client_ledger=str((C.LEDGER / 'tasks' / (identity + '.json')).relative_to(C.ROOT)))

