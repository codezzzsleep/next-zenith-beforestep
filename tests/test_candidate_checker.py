"""Every returned anchor candidate independently reproduces its production gate."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ops'))
from check_candidate import inspect_candidate
class AnchorCandidateChecker(unittest.TestCase):pass
RUN='evidence/reviews/beforestep_r1/lux/original_b'
for target in ['T1','T2']:
 path=ROOT/RUN/f'looks/look1/{target}/decide/target_decision.json'
 for candidate in json.loads(path.read_text())['candidates']:
  def test(self,target=target,candidate=candidate,path=path):
   before=hashlib.sha256(path.read_bytes()).hexdigest();result=inspect_candidate(RUN,target,candidate['id'])
   self.assertEqual(result['admitted'],candidate['admitted']);self.assertEqual(result['production_admitted'],candidate['admitted'])
   self.assertEqual(result['metrics'],{k:v for k,v in candidate.items() if k not in ('id','glb','M','admitted')})
   self.assertEqual(result['thresholds'],json.loads((ROOT/'config/admission.json').read_text()))
   self.assertEqual(result['source_sha256'],before);self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
   self.assertEqual(len(result['checks']),5)
  setattr(AnchorCandidateChecker,f'test_{target}_{candidate["id"]}',test)
if __name__=='__main__':unittest.main()
