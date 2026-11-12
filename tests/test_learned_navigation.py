"""New navigation contracts: information boundary, seeds, geometry and learning."""
import unittest
import importlib.util
import numpy as np
from experimental.navigation.world import ROOT,DIRECTIONS,World,read,shortest_paths,safe_transition
from experimental.navigation.llm import validate


class NavigationContracts(unittest.TestCase):
    def test_seed_disjoint(self):
        cfg=read(ROOT/'config/training/navigation_v1.json');seen=set()
        for key in ['train','validation','test','ood','physical']:
            p=cfg[key];seeds=set(range(p['seed_start'],p['seed_start']+p['count']))
            self.assertFalse(seen & seeds);seen|=seeds

    def test_diagonal_corner_is_blocked(self):
        blocked=np.zeros((5,5),bool);blocked[2,1]=blocked[1,2]=True
        self.assertFalse(safe_transition(blocked,np.array([1,1]),1))
        d,a=shortest_paths(blocked,[3,3]);self.assertNotEqual(int(a[1,1]),1)

    def test_advisor_cannot_invent_candidate(self):
        with self.assertRaises(ValueError):validate({'action':'move','candidate_id':9},[{'id':1}])
        with self.assertRaises(ValueError):validate({'action':'move','candidate_id':True},[{'id':1}])
        self.assertEqual(validate({'action':'look'},[]),{'action':'look'})

    def test_truth_not_an_input_channel(self):
        cfg=read(ROOT/'config/training/navigation_v1.json')
        pair={'task_id':1,'source':'fixture','source_sha256':'fixture','height_m':.4,
              'truth_polygon':[[-.4,-.3],[.4,-.3],[.4,.3],[-.4,.3]],
              'prior_polygon':[[-.3,-.3],[.3,-.3],[.3,.3],[-.3,.3]]}
        world=World(cfg,{'pairs':[pair]},'test',3100000)
        x,known=world.observe(world.start,0.,prior_enabled=False)
        self.assertEqual(x.shape,(4,*cfg['grid']))
        self.assertFalse(x[2].any());self.assertFalse(x[3].any())
        self.assertTrue(np.array_equal(x[0],world.raw & known))

    @unittest.skipUnless(importlib.util.find_spec('torch'), 'optional CPU training dependencies')
    def test_model_gradients_and_no_teacher_at_inference(self):
        import torch
        from unittest.mock import patch
        from experimental.navigation.model import NavigationNet,infer
        torch.set_num_threads(1);m=NavigationNet(3)
        x=torch.zeros(1,4,8,8);g=torch.zeros(1,8,8);g[0,6,6]=1.
        q,b=m(x,g);(q.mean()+b.square().mean()).backward()
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters()))
        with patch('experimental.navigation.world.shortest_paths',side_effect=AssertionError('teacher leaked')):
            scores,risk=infer(m,np.zeros((4,8,8),np.float32),np.array([6,6]))
        self.assertEqual(scores.shape,(8,8,8))


if __name__=='__main__':unittest.main()
