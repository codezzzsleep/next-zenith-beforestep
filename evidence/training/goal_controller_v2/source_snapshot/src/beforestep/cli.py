"""One public command for running, evaluating and checking BeforeStep."""
import argparse
import importlib
import json
import os
import sys
from pathlib import Path

from .paths import ROOT


def main():
    parser = argparse.ArgumentParser(prog='beforestep')
    parser.add_argument('command', choices=['run', 'evaluate', 'admit', 'check', 'resources', 'generate', 'build', 'serve', 'train'])
    args, remaining = parser.parse_known_args()
    if args.command == 'run':
        from . import pipeline
        sys.argv = ['beforestep run', *remaining]
        pipeline.main()
    elif args.command == 'evaluate':
        from . import evaluation
        sys.argv = ['beforestep evaluate', *remaining]
        evaluation.main()
    elif args.command == 'check':
        packages = {}
        for name in ['mujoco', 'numpy', 'scipy', 'trimesh', 'PIL', 'matplotlib', 'rtree', 'coacd', 'manifold3d']:
            try:
                m = importlib.import_module(name)
                packages[name] = getattr(m, '__version__', 'installed')
            except ImportError:
                packages[name] = None
        from .simulation.robot_model import model_available
        rocks = Path(os.environ.get('BEFORESTEP_ROCK_ROOT', ROOT / 'assets/rocks'))
        missing = [f'{rid}/{part}' for rid in ('rock_07','rock_09','moon_rock_03','moon_rock_04','moon_rock_06','moon_rock_07')
                   for part in ('h1/body_vis.obj','texture.png') if not (rocks / rid / part).is_file()]
        result = {'root': str(ROOT), 'packages': packages, 'robot_model': model_available(),
                  'rock_assets': not missing, 'missing_rocks': missing}
        result['ok'] = all(packages.values()) and result['robot_model'] and result['rock_assets']
        if '--render' in remaining and result['ok']:
            import mujoco
            import numpy as np
            model = mujoco.MjModel.from_xml_string('<mujoco><worldbody><geom type="sphere" size=".2"/></worldbody></mujoco>')
            data = mujoco.MjData(model); mujoco.mj_forward(model, data)
            with mujoco.Renderer(model, 64, 64) as renderer:
                renderer.update_scene(data)
                result['render_ok'] = bool(np.ptp(renderer.render()) > 0)
            result['ok'] = result['ok'] and result['render_ok']
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result['ok'] else 1)
    elif args.command == 'train':
        from .learning.train import main as train
        train(remaining)
    elif args.command == 'generate':
        from .generation.client import main as generate
        generate(remaining)
    elif args.command == 'resources':
        from .resources import main as resources
        resources(remaining)
    elif args.command == 'build':
        from .delivery.artifacts import main as build
        build(remaining)
    elif args.command == 'admit':
        from .generation.evaluate import main as admit
        admit(remaining)
    else:
        from .delivery.server import main as serve
        serve(remaining)
