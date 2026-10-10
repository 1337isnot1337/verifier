import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import smoke
import submissions as s

class SmokeTests(unittest.TestCase):
    def test_only_exact_legacy_fixture_can_be_enabled(self):
        sub={'schema_version':1,'problem':'dft','repo_url':smoke.REPO,'commit':smoke.PIN,'bound':smoke.BOUND,'authors':[]}
        selected={'test_only':True,'live_smoke':smoke.TAG,'submission':smoke.issue_submission(sub)}
        self.assertTrue(smoke.active(selected))
        for field,value in [('test_only',False),('live_smoke','anything')]:
            self.assertFalse(smoke.active(dict(selected,**{field:value})))
        with self.assertRaises(ValueError):smoke.issue_submission(dict(sub,commit='a'*40))

    def test_pr_smoke_has_fixed_problem_bound_and_test_folder(self):
        selected={'test_only':True,'live_smoke':smoke.TAG,'route':'pull_request',
                  'submission':{'problem':'dft','bound':smoke.BOUND},'source_subdir':'submissions/dft/nmamano-smoke-dft-837dc31'}
        self.assertTrue(smoke.active(selected))
        self.assertFalse(smoke.active(dict(selected,source_subdir='submissions/dft/nmamano-real-proof')))

if __name__=='__main__':unittest.main()
