"""The separately authorized 400-task budget, reserved before any HTTP create."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
from beforestep.generation import client as C


class PhysicalGatePending(RuntimeError):
    pass


class CrossingBudgetExhausted(RuntimeError):
    pass


class CrossingStopped(RuntimeError):
    pass


class CrossingBudget:
    def __init__(self, path=None, gate=None):
        self.path = Path(path or C.ROOT / 'outputs/generation/crossing-budget.json')
        self.gate = Path(gate or C.ROOT / 'evidence/crossing/calibration/gate.json')

    @staticmethod
    def usage(data):
        return sum(bool(row.get('task_id')) or row['status'] in ('reserved', 'uncertain')
                   for row in data['tasks'])

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text())
            assert data['schema'] == 'beforestep-crossing-budget/v1'
            assert data['authorized_max_new_tasks'] == 400
            yield data
            assert self.usage(data) <= 400
            data['created'] = sum(bool(row.get('task_id')) for row in data['tasks'])
            data['reserved_or_created'] = self.usage(data)
            data['updated_at'] = datetime.now(timezone.utc).isoformat()
            C.atomic_json(self.path, data)

    def reserve(self, identity, metadata):
        if not self.gate.exists() or not json.loads(self.gate.read_text())['physical_gate_passed']:
            raise PhysicalGatePending('The measured physical gate has not passed; no HTTP create allowed')
        with self.locked() as data:
            if data.get('stop', {}).get('new_creation_stopped'):
                raise CrossingStopped('A SPEC stopping condition is recorded; collect known tasks only')
            old = next((row for row in data['tasks'] if row['identity'] == identity), None)
            if old:
                return old
            if self.usage(data) >= 400:
                raise CrossingBudgetExhausted('Crossing reached its separately authorized 400-task limit')
            row = {**metadata, 'identity': identity, 'status': 'reserved', 'task_id': None,
                   'reserved_at': datetime.now(timezone.utc).isoformat(),
                   'client_ledger': str((C.LEDGER / 'tasks' / (identity + '.json')).relative_to(C.ROOT))}
            data['tasks'].append(row)
            data['status'] = 'physical_gate_passed_generation_active'
            return row

    def sync(self, identity, record):
        with self.locked() as data:
            row = next(row for row in data['tasks'] if row['identity'] == identity)
            row.update({key: record[key] for key in
                        ['status', 'task_id', 'glb', 'glb_sha256', 'finished_at', 'rejection_code'] if key in record})

    def submit(self, request, item, *, scene, observation):
        assert item['id'].startswith('crossing_'), 'Crossing must use new, distinct task identities'
        identity = C.request_identity(request, item)
        reservation = self.reserve(identity, {'scene': scene, 'observation': observation,
                                               'sample': item['id'], 'inputs': item.get('paths') or [item['path']]})
        if reservation['status'] == 'not_submitted':
            raise RuntimeError('A previous provider rejection is terminal under Crossing SPEC §12; do not resubmit')
        client_path = C.LEDGER / 'tasks' / (identity + '.json')
        if reservation.get('task_id') or reservation['status'] == 'uncertain':
            if not client_path.exists():
                raise RuntimeError('Known or uncertain client record missing; never recreate the task')
            return json.loads(client_path.read_text())
        try:
            record = C.submit(request, item)
        except Exception:
            if client_path.exists():
                self.sync(identity, json.loads(client_path.read_text()))
            raise
        # C.submit already fsyncs the returned ID before this budget sync.
        self.sync(identity, record)
        return record

    def poll(self, record, timeout=3600):
        completed = C.poll(record, timeout=timeout)
        self.sync(record['identity'], completed)
        return completed
