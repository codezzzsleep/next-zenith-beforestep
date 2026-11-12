import tempfile
import unittest
from pathlib import Path
import numpy as np
from experimental.navigation.world import ROOT,World,read
from experimental.navigation.physics import scene_spec as original
from experimental.navigation_physics_start_v2 import scene_spec as repaired


class StartAdapterTests(unittest.TestCase):
    def test_start_is_declared_before_reset_and_rock_meshes_are_identical(self):
        world=World(read(ROOT/'config/training/navigation_v1.json'),
                    read(ROOT/'assets/training/navigation_v1/shape-library.json'),'validation',2100063)
        with tempfile.TemporaryDirectory() as d:
            a=original(world,Path(d)/'a');b=repaired(world,Path(d)/'b')
            self.assertEqual(a['start'],[0.,0.])
            self.assertEqual(b['start'],(world.start*world.res).tolist())
            self.assertFalse(world.blocked[tuple(world.start)])
            self.assertEqual(len(a['objects']),len(b['objects']))
            for x,y in zip(a['objects'],b['objects']):
                self.assertEqual({k:v for k,v in x.items() if k!='mesh_file'},
                                 {k:v for k,v in y.items() if k!='mesh_file'})
                self.assertEqual(Path(x['mesh_file']).read_bytes(),Path(y['mesh_file']).read_bytes())
