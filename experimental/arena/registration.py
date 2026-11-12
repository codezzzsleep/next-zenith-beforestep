"""Require the committed preregistration before any scored data are generated."""
import subprocess
from .common import ROOT, OUT, read, sha


def require_registration():
    gate = read(OUT / 'prechecks/final.json')
    assert gate['passed'], 'Development and transplant prechecks must pass'
    record = read(OUT / 'protocol.json')
    for relative, expected in record['frozen_files_sha256'].items():
        assert sha(ROOT / relative) == expected, f'Frozen registration file changed: {relative}'
    commit = record['commit']
    committed = subprocess.check_output(['git', 'show', f'{commit}:docs/arena-protocol.md'], cwd=ROOT)
    assert committed == (ROOT / 'docs/arena-protocol.md').read_bytes(), 'Protocol must be committed before evaluation'
    return record
