"""The award archive retains raw task bytes and interrupted scene evidence."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'ops/preserve_suite_scene.py'
spec = importlib.util.spec_from_file_location('award_custody', MODULE)
custody = importlib.util.module_from_spec(spec)
spec.loader.exec_module(custody)


class AwardCustodyTests(unittest.TestCase):
    def test_complete_archive_keeps_raw_task_and_interruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / 'repository'
            scene = 'fixed_scene'
            run = root / 'outputs/award' / scene / 'imagination'
            run.mkdir(parents=True)
            (run / 'summary.json').write_text(json.dumps({'scene_id': scene, 'result': 'stuck'}))
            (run / 'run_identity.json').write_text(json.dumps({'run_id': 'retained-run'}))
            interrupted = run.parent / 'interrupted/attempt.log'
            interrupted.parent.mkdir()
            interrupted.write_bytes(b'partial rehearsal output\n')
            raw = root / 'assets/candidates/12345/tex_mesh.glb'
            raw.parent.mkdir(parents=True)
            raw.write_bytes(b'original generated model bytes')
            (root / 'runs.json').write_text(json.dumps({'imagination': str(run.relative_to(root))}))
            extras = [str(run.parent.relative_to(root)), str(raw.parent.relative_to(root))]
            (root / 'extras.json').write_text(json.dumps(extras))
            args = argparse.Namespace(scene=scene, runs='runs.json', extras='extras.json',
                archive_dir=str(base / 'archives'), out='evidence/award', reuse_public_objects=False)
            previous = custody.ROOT
            try:
                custody.ROOT = root
                custody.preserve(args)
            finally:
                custody.ROOT = previous
            manifest = json.loads((root / 'evidence/award' / scene / 'manifest.json').read_text())
            entries = {row['path']: row for row in manifest['files']}
            self.assertIn(str(raw.relative_to(root)), entries)
            self.assertIn(str(interrupted.relative_to(root)), entries)
            self.assertLess(manifest['public_bytes'], 150_000_000)
            with tarfile.open(manifest['complete_archive']['path']) as archive:
                for relative, row in entries.items():
                    content = archive.extractfile('repo/' + relative).read()
                    self.assertEqual(hashlib.sha256(content).hexdigest(), row['sha256'])
                    self.assertEqual(len(content), row['bytes'])
                    if row.get('public_object'):
                        self.assertEqual(gzip.decompress((root / row['public_object']).read_bytes()), content)

    def test_rejects_unrelated_supplementary_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'repository'
            root.mkdir()
            (root / 'runs.json').write_text('{}')
            for relative in ['assets/models', 'assets/candidates/not-a-task', 'outputs/another_scene']:
                (root / 'extras.json').write_text(json.dumps([relative]))
                args = argparse.Namespace(scene='fixed_scene', runs='runs.json', extras='extras.json')
                previous = custody.ROOT
                try:
                    custody.ROOT = root
                    with self.assertRaisesRegex(AssertionError, 'Invalid supplementary'):
                        custody.preserve(args)
                finally:
                    custody.ROOT = previous


if __name__ == '__main__':
    unittest.main()
