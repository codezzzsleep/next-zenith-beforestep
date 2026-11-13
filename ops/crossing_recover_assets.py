"""Download missing assets for existing task IDs; never create a cloud task."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT))
from beforestep.generation import client as C
from experimental.crossing.budget import CrossingBudget
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--timeout',type=int,default=3600);args=parser.parse_args()
    budget=CrossingBudget();data=json.loads(budget.path.read_text());restored=[];waiting=[]
    for row in data['tasks']:
        if row['status'] in ['failed','not_submitted']:continue
        if not row.get('task_id'):raise RuntimeError('Reserved or uncertain identity needs provider reconciliation; never recreate it')
        if row['status']=='ok':
            path=ROOT/row['glb']
            if path.exists():
                assert hashlib.sha256(path.read_bytes()).hexdigest()==row['glb_sha256'],'Existing asset differs; preserve evidence'
                continue
        ledger=ROOT/row['client_ledger'];record=json.loads(ledger.read_text());assert record['task_id']==row['task_id']
        if record['status']=='ok':
            task=C.api('GET',f'/lux3d/v1/generate/task/get?taskid={row["task_id"]}')
            assert task.get('status') in (3,'success','SUCCESS'),'Existing task no longer returns a successful asset'
            glb,digest=C.fetch_glb(task,record);assert digest==row['glb_sha256'],'Provider asset differs from the saved checksum'
            restored.append(row['task_id'])
        else:
            record=budget.poll(record,timeout=args.timeout)
            (restored if record['status']=='ok' else waiting).append(row['task_id'])
    print(json.dumps({'restored_task_ids':restored,'pending_task_ids':waiting,'created_tasks':0}))
