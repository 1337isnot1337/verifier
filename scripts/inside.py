#!/usr/bin/python3
"""Trusted entrypoint, executed only inside the outer offline namespace."""
import json
import os
from pathlib import Path
import sys

work = Path(sys.argv[1])
phase = sys.argv[2]
request = json.loads((work / 'control/request.json').read_text())
stage = work / 'stage'
lean = work / 'tools/elan/toolchains/leanprover--lean4---v4.34.1/bin/lake'
if phase == 'audit':
    args = [str(lean), 'env', 'lean', str(stage / 'VerifierAudit.lean')]
else:
    # Submission code can write build products. Never trust its copy of the
    # challenge .olean/trace on a later run. Removal itself stays sandboxed,
    # so hostile output symlinks cannot reach the host checkout or receipts.
    for facet in ['lib/lean', 'ir']:
        parent = stage / '.lake/build' / facet
        if parent.exists():
            for path in parent.glob('VerifierChallenge.*'):
                if path.is_dir() and not path.is_symlink():
                    raise RuntimeError('unexpected challenge output directory')
                path.unlink()
    args = [str(lean), 'env', str(work / 'tools/comparator/.lake/build/bin/comparator'),
            str(work / f'control/{phase}.json')]
os.execve(str(lean), args, dict(os.environ, LEAN_NUM_THREADS='4'))
