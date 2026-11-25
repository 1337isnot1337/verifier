import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))


def _load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v = _load_module('verifier_hardening_sut', 'scripts/verifier.py')
verdicts = _load_module('verdicts_hardening_sut', 'scripts/verdicts.py')


class IsolationHardeningTests(unittest.TestCase):
    def test_sandbox_args_supports_isolated_phase_mounts_and_ro_audit(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        (work / 'control').mkdir(parents=True)
        (work / 'control/request.json').write_text(json.dumps({
            'request': {'lean_toolchain': 'leanprover/lean4:v4.34.1'},
            'profile': {'solution_module': 'Submission'},
            'names': ['Race.bound'],
        }))
        with mock.patch.object(v, 'WORK', work):
            lean_args = v.sandbox_args(
                build_dir=work / 'build-lean',
                build_ro=False,
                scratch_dir=work / 'scratch-lean',
            )
            audit_args = v.sandbox_args(
                build_dir=work / 'build-lean',
                build_ro=True,
                scratch_dir=work / 'scratch-audit',
            )
            nanoda_args = v.sandbox_args(
                build_dir=work / 'build-nanoda',
                build_ro=False,
                scratch_dir=work / 'scratch-nanoda',
            )
        stage_build = str(work / 'stage/.lake/build')
        idx_lean = lean_args.index(stage_build)
        self.assertEqual(lean_args[idx_lean - 2:idx_lean + 1], ['--bind', str(work / 'build-lean'), stage_build])
        idx_audit = audit_args.index(stage_build)
        self.assertEqual(audit_args[idx_audit - 2:idx_audit + 1], ['--ro-bind', str(work / 'build-lean'), stage_build])
        idx_nanoda = nanoda_args.index(stage_build)
        self.assertEqual(nanoda_args[idx_nanoda - 2:idx_nanoda + 1], ['--bind', str(work / 'build-nanoda'), stage_build])
        self.assertNotEqual(str(work / 'build-lean'), str(work / 'build-nanoda'))
        self.assertIn(str(work / 'scratch-lean'), lean_args)
        self.assertIn(str(work / 'scratch-audit'), audit_args)
        self.assertIn(str(work / 'scratch-nanoda'), nanoda_args)

    def test_default_sandbox_args_uses_prepare_created_dirs_for_dependency_check(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name) / 'work'
        art = Path(tmp.name) / 'art'
        src_repo = Path(tmp.name) / 'src_repo'
        src_repo.mkdir(parents=True)
        (src_repo / 'Submission.lean').write_text('theorem bound : 1 = 1 := rfl\n', encoding='utf-8')
        req_file = Path(tmp.name) / 'request.json'
        req_file.write_text(json.dumps({
            'test_only': True,
            'inputs': {
                'repo_url': 'https://github.com/openai/math',
                'commit': 'fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb',
                'challenge_file': 'challenges/matrix-multiplication/MatrixMultiplication.lean',
                'theorem_names': 'OAI.MatrixMultiplication.complex_omega_le_nine_quarters',
                'lean_toolchain': 'leanprover/lean4:v4.34.1',
            },
        }), encoding='utf-8')

        def _fake_clone(_url, _sha, dest, label, **_kw):
            files = (
                {'lean/OAI/LinearAlgebra/MatrixMultiplication/Main.lean': 'import FixedPointTheorems.brouwer\n'}
                if label == 'submission'
                else {'FixedPointTheorems/brouwer.lean': 'import Mathlib\n'}
            )
            for rel, content in files.items():
                p = dest / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding='utf-8')

        def _fake_check_output(cmd, **_kw):
            loc = Path(cmd[2])
            entries = []
            for p in sorted(loc.rglob('*.lean')):
                rel = p.relative_to(loc).as_posix().encode('utf-8')
                entries.append(b'100644 blob deadbeef\t' + rel)
            return b'\0'.join(entries) + b'\0'

        with mock.patch.object(v, 'WORK', work), \
                mock.patch.object(v, 'ART', art), \
                mock.patch.dict('os.environ', {'BOS_REQUEST_PATH': str(req_file)}, clear=False), \
                mock.patch.object(v, 'clone', side_effect=_fake_clone), \
                mock.patch.object(v, 'command', return_value=None), \
                mock.patch.object(v.subprocess, 'check_output', side_effect=_fake_check_output):
            v.prepare()
            (work / 'cache/.lake/packages').mkdir(parents=True, exist_ok=True)
            default_args = v.sandbox_args()

        self.assertTrue((work / 'build-setup').is_dir())
        self.assertTrue((work / 'scratch-setup').is_dir())
        self.assertFalse((work / 'build-lean').exists())
        stage_build = str(work / 'stage/.lake/build')
        idx_default = default_args.index(stage_build)
        self.assertEqual(
            default_args[idx_default - 2:idx_default + 1],
            ['--bind', str(work / 'build-setup'), stage_build],
        )
        self.assertNotIn(str(work / 'build-lean'), default_args)
        # Every WORK-rooted source path bound by default sandbox_args() must exist after prepare() + cache init
        for i, tok in enumerate(default_args):
            if tok in ('--bind', '--ro-bind'):
                src_path = Path(default_args[i + 1])
                if src_path.is_relative_to(work):
                    self.assertTrue(src_path.exists(), f'missing sandbox bind source: {src_path}')

    def test_prioritize_toolchain_lean_path_blocks_stdlib_shadowing(self):
        inside = _load_module('inside_hardening_sut', 'scripts/inside.py')
        tc_lib = '/work/tools/elan/toolchains/lean4/lib/lean'
        mathlib = '/work/stage/.lake/packages/mathlib/.lake/build/lib/lean'
        stage_build = '/work/stage/.lake/build/lib/lean'
        env = {'LEAN_PATH': f'{mathlib}:{stage_build}:{tc_lib}'}
        updated = inside.prioritize_toolchain_lean_path(env, tc_lib)
        parts = updated['LEAN_PATH'].split(':')
        self.assertEqual(parts, [tc_lib, mathlib, stage_build])
        self.assertLess(parts.index(tc_lib), parts.index(stage_build))
        self.assertLess(parts.index(mathlib), parts.index(stage_build))

    def test_phase_dirs_enforces_fresh_directories_and_ro_audit_prereq(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        with mock.patch.object(v, 'WORK', work):
            with self.assertRaises(FileNotFoundError):
                v._phase_dirs('audit')
            lean_build, lean_scratch = v._phase_dirs('lean')
            self.assertEqual(lean_build, work / 'build-lean')
            self.assertEqual(lean_scratch, work / 'scratch-lean')
            self.assertTrue(lean_build.is_dir())
            self.assertTrue(lean_scratch.is_dir())
            with self.assertRaises(FileExistsError):
                v._phase_dirs('lean')

            audit_build, audit_scratch = v._phase_dirs('audit')
            self.assertEqual(audit_build, work / 'build-lean')
            self.assertEqual(audit_scratch, work / 'scratch-audit')
            with self.assertRaises(FileExistsError):
                v._phase_dirs('audit')

            nanoda_build, nanoda_scratch = v._phase_dirs('nanoda')
            self.assertEqual(nanoda_build, work / 'build-nanoda')
            self.assertEqual(nanoda_scratch, work / 'scratch-nanoda')
            self.assertNotEqual(lean_build, nanoda_build)
            with self.assertRaises(FileExistsError):
                v._phase_dirs('nanoda')

    def test_inside_audit_uses_trusted_audit_axioms_script(self):
        audit_script = (ROOT / 'scripts/AuditAxioms.lean').read_text(encoding='utf-8')
        self.assertIn('Lean.importModules', audit_script)
        self.assertIn('loadExts := false', audit_script)
        self.assertIn('Lean.collectAxioms', audit_script)
        self.assertNotIn('#print axioms', audit_script)

        inside = _load_module('inside_exec_sut', 'scripts/inside.py')
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        (work / 'control').mkdir(parents=True)
        (work / 'control/request.json').write_text(json.dumps({
            'request': {'lean_toolchain': 'leanprover/lean4:v4.34.1'},
            'profile': {'solution_module': 'Submission'},
            'names': ['Race.bound'],
        }))
        captured = {}

        class _ExecCalled(BaseException):
            pass

        def fake_execve(path, argv, env):
            captured['path'] = path
            captured['argv'] = argv
            captured['env'] = env
            raise _ExecCalled()

        tc_lib = str(work / 'tools/elan/toolchains/leanprover--lean4---v4.34.1/lib/lean')
        stage_lib = str(work / 'stage/.lake/build/lib/lean')
        with mock.patch.object(sys, 'argv', ['inside.py', str(work), 'audit-exec']), \
                mock.patch.dict('os.environ', {'LEAN_PATH': f'{stage_lib}:{tc_lib}', 'PATH': '/usr/bin'}, clear=True), \
                mock.patch.object(inside.os, 'execve', side_effect=fake_execve):
            with self.assertRaises(_ExecCalled):
                inside.main()
        self.assertTrue(captured['path'].endswith('/bin/lean'))
        self.assertEqual(captured['argv'][1:5], ['--run', str(work / 'control/AuditAxioms.lean'), 'Submission', 'Race.bound'])
        self.assertEqual(captured['env']['LEAN_PATH'].split(':')[0], tc_lib)

    def test_verify_wires_ro_audit_mount_quiet_systemd_run_and_systemd_log_parsing(self):
        def _run_verify(audit_log_text):
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            work = Path(tmp.name) / 'work'
            art = Path(tmp.name) / 'art'
            (work / 'control').mkdir(parents=True)
            art.mkdir(parents=True)
            (work / 'control/request.json').write_text(json.dumps({
                'request': {'lean_toolchain': 'leanprover/lean4:v4.34.1'},
                'profile': {'solution_module': 'Submission'},
                'names': ['Race.bound'],
            }))
            (art / 'receipt.json').write_text(json.dumps({
                'started_unix': int(v.time.time()),
                'theorem_names': ['Race.bound'],
                'kernels': {},
                'steps': [],
            }))
            popen_calls = []

            class _FakeProc:
                def __init__(self, args, stdout):
                    popen_calls.append(list(args))
                    kernel = args[-1]
                    if kernel == 'lean':
                        stdout.write(
                            'Lean default kernel accepts the solution\n'
                            'Your solution is okay!\n'
                        )
                    elif kernel == 'audit':
                        stdout.write(audit_log_text)
                    stdout.flush()

                def poll(self):
                    return 0

                def wait(self):
                    return 0

            def _fake_run(args, **_kw):
                return mock.Mock(returncode=0, stdout='success\n')

            with mock.patch.object(v, 'WORK', work), \
                    mock.patch.object(v, 'ART', art), \
                    mock.patch.object(v, 'command', return_value=None), \
                    mock.patch.object(v.subprocess, 'Popen', side_effect=lambda args, stdout=None, **_kw: _FakeProc(args, stdout)), \
                    mock.patch.object(v.subprocess, 'run', side_effect=_fake_run):
                v.verify(['lean', 'audit'])
            return work, json.loads((art / 'receipt.json').read_text()), popen_calls

        systemd_wrapped_ok = (
            'Running as unit: bos-verifier-audit.service; invocation ID: 0123456789abcdef0123456789abcdef\n'
            "'Race.bound' does not depend on any axioms\n"
            'Finished with result: success\n'
            'Main processes terminated with: code=exited/status=0\n'
            'Service runtime: 1.234s\n'
            'Memory peak: 42.1M\n'
            'Memory swap peak: 0B\n'
            'CPU time consumed: 980ms\n'
        )
        work, rec_ok, calls = _run_verify(systemd_wrapped_ok)
        self.assertEqual(len(calls), 2)
        stage_build = str(work / 'stage/.lake/build')
        lean_cmd, audit_cmd = calls
        for cmd in (lean_cmd, audit_cmd):
            self.assertEqual(cmd[:5], ['sudo', 'systemd-run', '--quiet', '--wait', '--pipe'])
        idx_lean = lean_cmd.index(stage_build)
        self.assertEqual(lean_cmd[idx_lean - 2:idx_lean + 1], ['--bind', str(work / 'build-lean'), stage_build])
        idx_audit = audit_cmd.index(stage_build)
        self.assertEqual(audit_cmd[idx_audit - 2:idx_audit + 1], ['--ro-bind', str(work / 'build-lean'), stage_build])
        self.assertEqual(rec_ok['status'], 'passed')
        self.assertEqual(rec_ok['axiom_audit']['status'], 'passed')
        self.assertEqual(rec_ok['axiom_audit']['reported_axioms'], {'Race.bound': []})

        systemd_wrapped_warn = (
            'Running as unit: bos-verifier-audit.service; invocation ID: 0123456789abcdef0123456789abcdef\n'
            "warning: declaration uses 'sorry'\n"
            "'Race.bound' does not depend on any axioms\n"
            'Finished with result: success\n'
        )
        _work2, rec_bad, _calls2 = _run_verify(systemd_wrapped_warn)
        self.assertEqual(rec_bad['axiom_audit']['status'], 'invalid_output')
        self.assertEqual(rec_bad['status'], 'not_verified')


class AxiomAuditHardeningTests(unittest.TestCase):
    def test_zero_axiom_theorem_accepted_and_admitted(self):
        out = "'Race.bound' does not depend on any axioms\n"
        reported, ok = v.parse_axiom_audit(out, ['Race.bound'])
        self.assertTrue(ok)
        self.assertEqual(reported, {'Race.bound': []})
        receipt = {
            'verification_stage': 'final',
            'kernels': {
                'lean': {'status': 'passed'},
                'nanoda': {'status': 'passed'},
            },
            'axiom_audit': {'status': 'passed', 'reported_axioms': reported},
            'theorems': {
                'Race.bound': {
                    'lean_kernel': 'passed',
                    'nanoda_kernel': 'passed',
                    'reported_axioms': [],
                }
            },
        }
        status, reason = verdicts.admission(receipt, ['Race.bound'])
        self.assertEqual((status, reason), ('passed', 'lean_and_axiom_passed'))

    def test_mixed_zero_and_standard_axioms_accepted(self):
        out = (
            "'A.thm1' does not depend on any axioms\n"
            "'A.thm2' depends on axioms: [Classical.choice, Quot.sound, propext]\n"
        )
        reported, ok = v.parse_axiom_audit(out, ['A.thm1', 'A.thm2'])
        self.assertTrue(ok)
        self.assertEqual(reported['A.thm1'], [])
        self.assertEqual(reported['A.thm2'], ['Classical.choice', 'Quot.sound', 'propext'])

    def test_duplicate_or_spoofed_extra_lines_rejected(self):
        spoof_dup = (
            "'Race.bound' depends on axioms: [sorryAx]\n"
            "'Race.bound' depends on axioms: [propext]\n"
        )
        _rep, ok = v.parse_axiom_audit(spoof_dup, ['Race.bound'])
        self.assertFalse(ok)

        unanchored = "noise 'Race.bound' depends on axioms: [propext]\n"
        _rep2, ok2 = v.parse_axiom_audit(unanchored, ['Race.bound'])
        self.assertFalse(ok2)

        extra_line = (
            "warning: declaration uses 'sorry'\n"
            "'Race.bound' depends on axioms: [propext]\n"
        )
        _rep3, ok3 = v.parse_axiom_audit(extra_line, ['Race.bound'])
        self.assertFalse(ok3)

        unpermitted = "'Race.bound' depends on axioms: [sorryAx]\n"
        _rep4, ok4 = v.parse_axiom_audit(unpermitted, ['Race.bound'])
        self.assertFalse(ok4)

        missing = "'Other.thm' does not depend on any axioms\n"
        _rep5, ok5 = v.parse_axiom_audit(missing, ['Race.bound'])
        self.assertFalse(ok5)

    def test_indented_empty_list_and_malformed_axiom_lines_rejected(self):
        bad_outputs = [
            "  'Race.bound' does not depend on any axioms\n",
            "\t'Race.bound' depends on axioms: [propext]\n",
            "'Race.bound' does not depend on any axioms \n",
            "   \n'Race.bound' does not depend on any axioms\n",
            "'Race.bound' depends on axioms: []\n",
            "'Race.bound' depends on axioms: [ ]\n",
            "'Race.bound' depends on axioms: [propext, ]\n",
            "'Race.bound' depends on axioms: [propext,Quot.sound]\n",
        ]
        for out in bad_outputs:
            with self.subTest(out=out):
                _rep, ok = v.parse_axiom_audit(out, ['Race.bound'])
                self.assertFalse(ok)

    def test_systemd_run_status_lines_accepted_while_non_success_and_spoofs_rejected(self):
        v255_zero = (
            'Running as unit: bos-verifier-audit.service; invocation ID: 0123456789abcdef0123456789abcdef\n'
            "'Race.bound' does not depend on any axioms\n"
            'Finished with result: success\n'
            'Main processes terminated with: code=exited/status=0\n'
            'Service runtime: 1.234s\n'
            'Memory peak: 42.1M\n'
            'Memory swap peak: 0B\n'
            'CPU time consumed: 980ms\n'
        )
        reported, ok = v.parse_axiom_audit(v255_zero, ['Race.bound'])
        self.assertTrue(ok)
        self.assertEqual(reported, {'Race.bound': []})

        v252_std = (
            'Running as unit: bos-verifier-audit.service\n'
            "'Race.bound' depends on axioms: [Classical.choice, propext]\n"
            'Finished with result: success\n'
            'Main processes terminated with: code=exited/status=0\n'
            'Service runtime: 1min 2.345s\n'
            'Memory peak: 12.3M\n'
            'Memory swap peak: 4.0K\n'
            'CPU time consumed: 85ms\n'
            'IP traffic received: 0B\n'
            'IP traffic sent: 0B\n'
            'IO bytes read: 0B\n'
            'IO bytes written: 0B\n'
        )
        reported2, ok2 = v.parse_axiom_audit(v252_std, ['Race.bound'])
        self.assertTrue(ok2)
        self.assertEqual(reported2, {'Race.bound': ['Classical.choice', 'propext']})

        bad_systemd_logs = [
            (
                'Running as unit: bos-verifier-audit.service\n'
                'Finished with result: success\n'
            ),
            (
                'Running as unit: bos-verifier-audit.service\n'
                "'Race.bound' does not depend on any axioms\n"
                'Finished with result: exit-code\n'
            ),
            (
                'Running as unit: bos-verifier-audit.service\n'
                "'Race.bound' does not depend on any axioms\n"
                'Finished with result: timeout\n'
            ),
            (
                'Running as unit: bos-verifier-audit.service\n'
                "'Race.bound' does not depend on any axioms\n"
                'Finished with result: signal\n'
            ),
            (
                'Running as unit: bos-verifier-audit.service\n'
                "'Race.bound' does not depend on any axioms\n"
                'Finished with result: resources\n'
            ),
            (
                'Running as unit: bos-verifier-audit.service\n'
                "'Race.bound' does not depend on any axioms\n"
                'Main processes terminated with: code=exited/status=1\n'
            ),
            (
                'Running as unit: bos-verifier-audit.service\n'
                "'Race.bound' does not depend on any axioms\n"
                'Main processes terminated with: code=killed/status=KILL\n'
            ),
            (
                '  Running as unit: bos-verifier-audit.service\n'
                "'Race.bound' does not depend on any axioms\n"
            ),
            (
                'Running as unit: bos-verifier-audit.service\n'
                "warning: declaration uses 'sorry'\n"
                "'Race.bound' does not depend on any axioms\n"
                'Finished with result: success\n'
            ),
        ]
        for out in bad_systemd_logs:
            with self.subTest(out=out):
                _rep, bad_ok = v.parse_axiom_audit(out, ['Race.bound'])
                self.assertFalse(bad_ok)


class LexerAndImportHardeningTests(unittest.TestCase):
    def _stage(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        for name, text in files.items():
            p = root / (name.replace('.', '/') + '.lean')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')
        return root

    def test_body_literals_and_syntax_do_not_break_plan_sources(self):
        src = (
            'import Mathlib\n'
            'def s1 : String := "/- not a comment"\n'
            'def s2 : String := "-- also not a comment"\n'
            'def c1 : Char := \'"\'\n'
            'def c2 : Char := \'\\\'\'\n'
            'def c3 : Char := \'\\\\\'\n'
            'def r1 : String := r#"/- raw " string"#\n'
            'def r2 : String := r"\\"\n'
            'def x\' : String := "prime ident ok /-" \n'
            'def y\'\' : Nat := 1\n'
            'def «/-» : Nat := 0\n'
            'def «a"b» : Nat := 0\n'
            'def interp (n : Nat) : String := s!"val {n} /- ok"\n'
            'def b1 : Bool := !"{" == "x"\n'
            'def b2 : Bool := !!"{" == "x"\n'
            'def b3 : Bool := (!"{") == "x"\n'
            'def b4 : String := get!"{"\n'
            'def b5 : String := x.r"\\""\n'
            'def interp2 (n : Nat) : String := s!"val { !"{" == "x" } {n}"\n'
            'def m_interp (n : Nat) : String := m!"msg {n}"\n'
            'theorem t : 1 = 1 := rfl\n'
        )
        self.assertEqual(v.parse_imports(src), ['Mathlib'])
        root = self._stage({'Submission': src})
        self.assertEqual(v.plan_sources(root, 'Submission'), [['Submission']])

    def test_unclosed_header_comments_and_guillemets_rejected(self):
        for bad in [
            '/- unclosed block comment\nimport Mathlib\n',
            'import\n  /- nested /- unclosed -/\n  Mathlib\n',
            'import«VerifierChallenge\n',
            'import «VerifierChallenge\n',
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    v.parse_imports(bad)

    def test_multiline_and_module_imports_cannot_bypass_plan_sources(self):
        bypass_cases = [
            {'Submission': 'import\n  VerifierChallenge\ntheorem t : True := trivial\n'},
            {'Submission': 'import\n  /- comment -/\n  VerifierChallenge\n'},
            {'Submission': 'import\n  Helper\nimport VerifierChallenge\n', 'Helper': 'def h := 1\n'},
            {'Submission': 'public\n  import\n  all\n  VerifierChallenge\n'},
            {'Submission': 'prelude import VerifierChallenge\n'},
            {'Submission': 'module import VerifierChallenge\n'},
            {'Submission': 'module prelude public import VerifierChallenge\n'},
            {'Submission': 'import Helper import VerifierChallenge\n', 'Helper': 'def h := 1\n'},
            {'Submission': 'import Helper public import VerifierChallenge\n', 'Helper': 'def h := 1\n'},
            {'Submission': 'import/-c-/VerifierChallenge\n'},
            {'Submission': 'prelude/-c-/import/-c-/VerifierChallenge\n'},
            {'Submission': '\ufeffimport VerifierChallenge\n'},
            {'Submission': 'import «VerifierChallenge»\n'},
            {'Submission': 'import«VerifierChallenge»\n'},
            {'Submission': 'import Helper\nimport«VerifierChallenge»\n', 'Helper': 'def h := 1\n'},
            {'Submission': 'public import«VerifierChallenge»\n'},
            {'Submission': 'prelude\nimport«VerifierChallenge»\n'},
            {'Submission': 'module\nimport«VerifierChallenge»\n'},
            {'Submission': 'import all«VerifierChallenge»\n'},
            {'Submission': 'import«Submission.Hidden»\n', 'Submission.Hidden': 'import VerifierChallenge\n'},
            {'Submission': 'import«Submission».«Hidden»\n', 'Submission.Hidden': 'import VerifierChallenge\n'},
            {'Submission': 'import Submission.«Hidden»\n', 'Submission.Hidden': 'import VerifierChallenge\n'},
            {'Submission': 'import Helper import«VerifierChallenge»\n', 'Helper': 'def h := 1\n'},
            {'Submission': 'import Helper«VerifierChallenge»\n', 'Helper': 'def h := 1\n'},
            {'Submission': 'import»VerifierChallenge\n'},
            {'Submission': 'import\n  VerifierAudit\n'},
            {'Submission': 'import\n'},
            {'Submission': 'import all\n'},
            {'Submission': 'import all all VerifierChallenge\n'},
            {'Submission': 'import public\n'},
            {'Submission': 'import Helper import\n', 'Helper': 'def h := 1\n'},
            {'Submission': 'import Helper; import VerifierChallenge\n', 'Helper': 'def h := 1\n'},
            {'Submission': '/- unclosed header comment\nimport VerifierChallenge\n'},
            {'Submission': 'import\n  B\n', 'B': 'import Submission\n'},
        ]
        for files in bypass_cases:
            with self.subTest(files=files):
                with self.assertRaises(ValueError):
                    v.plan_sources(self._stage(files), 'Submission')

    def test_multiline_valid_local_imports_and_private_decls_work(self):
        root = self._stage({
            'Submission.A': 'import Mathlib\nprivate\ntheorem helper : True := trivial\n',
            'Submission': 'import\n  Submission.A\ndef marker : String := "/-"\ntheorem t : True := trivial\n',
        })
        self.assertEqual(v.plan_sources(root, 'Submission'), [['Submission.A', 'Submission']])

        root_all = self._stage({
            'Submission.A': 'def a := 1\n',
            'Submission': 'module\npublic import all Submission.A\n',
        })
        self.assertEqual(v.plan_sources(root_all, 'Submission'), [['Submission.A', 'Submission']])

    def test_oneline_prelude_module_multi_import_and_header_only_scanning(self):
        self.assertEqual(v.parse_imports('import A import B\n'), ['A', 'B'])
        self.assertEqual(v.parse_imports('prelude import A\n'), ['A'])
        self.assertEqual(v.parse_imports('module import A\n'), ['A'])
        self.assertEqual(v.parse_imports('import A public import B\n'), ['A', 'B'])
        self.assertEqual(v.parse_imports('import A\ndef f : Bool := !"{" == "x"\n'), ['A'])
        self.assertEqual(
            v.parse_imports('import Mathlib\ndef body_not_scanned := "unterminated\n'),
            ['Mathlib'],
        )
        root = self._stage({
            'Submission.A': 'def a := 1\n',
            'Submission.B': 'def b := 2\n',
            'Submission': 'import Submission.A import Submission.B\ntheorem t : True := trivial\n',
        })
        self.assertEqual(
            v.plan_sources(root, 'Submission'),
            [['Submission.A'], ['Submission.B', 'Submission']],
        )


if __name__ == '__main__':
    unittest.main()
