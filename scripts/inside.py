#!/usr/bin/python3
"""Trusted entrypoint, executed only inside the outer offline namespace."""
import json
import os
from pathlib import Path
import sys


def prioritize_toolchain_lean_path(env, toolchain_lib):
    """Prepend the toolchain stdlib dir ahead of stage build dirs in LEAN_PATH."""
    tc = str(toolchain_lib)
    parts = [p for p in env.get('LEAN_PATH', '').split(':') if p and p != tc]
    env['LEAN_PATH'] = ':'.join([tc] + parts)
    return env


def main():
    work = Path(sys.argv[1])
    phase = sys.argv[2]
    request = json.loads((work / 'control/request.json').read_text())
    stage = work / 'stage'
    toolchain = work / 'tools/elan/toolchains' / request['request']['lean_toolchain'].replace('/', '--').replace(':', '---')
    lake = toolchain / 'bin/lake'
    lean = toolchain / 'bin/lean'
    toolchain_lib = toolchain / 'lib/lean'
    if phase == 'audit-exec':
        env = prioritize_toolchain_lean_path(dict(os.environ, LEAN_NUM_THREADS='4'), toolchain_lib)
        args = [str(lean), '--run', str(work / 'control/AuditAxioms.lean'),
                request['profile']['solution_module'], *request['names']]
        os.execve(str(lean), args, env)
    if phase.endswith('-exec'):
        # `lake env` has been observed to prepend its toolchain bin to PATH.
        # Restore the reviewed adapter and prepend toolchain lib/lean in the child environment.
        kernel = phase.removesuffix('-exec')
        if kernel not in ['lean', 'nanoda']:
            raise ValueError('invalid kernel phase')
        env = prioritize_toolchain_lean_path(dict(os.environ, LEAN_NUM_THREADS='4'), toolchain_lib)
        env['PATH'] = str(work / 'control/bin') + ':' + env['PATH']
        comparator = work / 'tools/comparator/.lake/build/bin/comparator'
        os.execve(str(comparator), [str(comparator), str(work / f'control/{kernel}.json')], env)
    if phase == 'audit':
        args = [str(lake), 'env', '/usr/bin/python3', str(work / 'control/inside.py'),
                str(work), 'audit-exec']
    else:
        # Defense in depth alongside separate per-phase build mounts: remove
        # any stale challenge .olean/trace inside the sandbox build directory.
        for facet in ['lib/lean', 'ir']:
            parent = stage / '.lake/build' / facet
            if parent.exists():
                for path in parent.glob('VerifierChallenge.*'):
                    if path.is_dir() and not path.is_symlink():
                        raise RuntimeError('unexpected challenge output directory')
                    path.unlink()
        args = [str(lake), 'env', '/usr/bin/python3', str(work / 'control/inside.py'),
                str(work), phase + '-exec']
    os.execve(str(lake), args, dict(os.environ, LEAN_NUM_THREADS='4'))


if __name__ == '__main__':
    main()
