"""Read original candidate metrics and reapply every frozen production gate.

No registration, generation, simulation or source file is changed. This is a
standalone audit of the recorded metrics, not a claim of newly measured geometry.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from beforestep.geometry.admission import ADM,admitted
ROOT=Path(__file__).resolve().parents[1]
METRICS=('scale_ratio','hidden_frac','shell_contact','free_intrusion_frac','contour_iou')
def inspect_candidate(run,target,sample,look=1):
 run=Path(run);run=run if run.is_absolute() else ROOT/run
 path=run/f'looks/look{look}/{target}/decide/target_decision.json'
 decision=json.loads(path.read_text());row=next((c for c in decision['candidates'] if c['id']==sample),None)
 if row is None:raise ValueError('No returned candidate with that sample; supplier failures are not admissions or rejections')
 thresholds=decision.get('thresholds',ADM);assert thresholds==ADM,'Recorded thresholds differ from the frozen production gate'
 def finite(value):return isinstance(value,(int,float,np.number)) and bool(np.isfinite(value))
 checks=[]
 for key in METRICS:
  value=row.get(key);valid=finite(value)
  if key=='scale_ratio':lower,upper=ADM[key]['min'],ADM[key]['max'];passed=valid and lower<=value<=upper
  elif key=='free_intrusion_frac':lower,upper=None,ADM['free_intrusion_max'];passed=valid and value<=upper
  else:lower,upper=ADM[key+'_min'],None;passed=valid and value>=lower
  checks.append({'metric':key,'value':value,'finite':valid,'min_inclusive':lower,'max_inclusive':upper,'passed':bool(passed)})
 result=all(c['passed'] for c in checks);assert result==admitted(row),'Checker disagrees with production predicate'
 assert result==row['admitted'],'Recorded decision differs from current frozen predicate'
 tasks=[]
 for result_path in [path.parent.parent/'lux_result.json',path.parent.parent/'retry/lux_result.json']:
  if result_path.exists():tasks+=json.loads(result_path.read_text())['tasks']
 task=next(t for t in tasks if t['id']==sample)
 return {'schema':'beforestep-readonly-candidate-check/v1','run':str(run),'target':target,'sample':sample,'look':look,'task_id':task['task_id'],'metrics':{k:v for k,v in row.items() if k not in ('id','glb','M','admitted')},'thresholds':thresholds,'checks':checks,'admitted':result,'production_admitted':row['admitted'],'production_exact':True,'scope':'Recomputed frozen gates from unchanged recorded metrics; no new geometric measurement','source_decision':str(path),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True);parser.add_argument('--target',required=True);parser.add_argument('--sample',required=True);parser.add_argument('--look',type=int,default=1);a=parser.parse_args()
 print(json.dumps(inspect_candidate(a.run,a.target,a.sample,a.look),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
