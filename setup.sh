#!/usr/bin/env bash
set -euo pipefail
beforestep_project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$beforestep_project_dir"
beforestep_python="${PYTHON:-python3}"
"$beforestep_python" -c 'import sys; assert sys.version_info[:2] == (3,12), "Python 3.12 required"'
[ -d .venv ] || "$beforestep_python" -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m beforestep resources
MUJOCO_GL="${MUJOCO_GL:-egl}" .venv/bin/python -m beforestep check --render
printf '%s\n' 'Ready: .venv/bin/python -m beforestep serve'
