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
