import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import queue_lease as q
import submissions as s


class QueueSecurityTests(unittest.TestCase):
    def test_active_batch_cannot_be_replaced(self):
        def api(path, data=None, method=None):
            if path.startswith('git/ref/'):return {'object':{'sha':'old'}}
            if path=='git/commits/old':return {'message':json.dumps({'run_id':'12','run_attempt':'1','page':2,'offset':4}),'tree':{'sha':'tree'}}
            if path=='actions/runs/12':return {'status':'in_progress'}
            self.fail('Active lease must not write '+path)
        with patch.dict(os.environ,GITHUB_RUN_ID='13',GITHUB_RUN_ATTEMPT='1'),patch.object(s,'api',side_effect=api):
            self.assertIsNone(q.acquire())

    def test_cas_loser_cannot_launch_batch(self):
        writes=[]
        def api(path,data=None,method=None):
            if path.startswith('git/ref/'):return {'object':{'sha':'old'}}
            if path=='git/commits/old':return {'message':json.dumps({'run_id':'12','run_attempt':'1','page':2,'offset':4}),'tree':{'sha':'tree'}}
            if path=='actions/runs/12':return {'status':'completed'}
            if path=='git/commits':
                self.assertEqual(data['parents'],['old']);return {'sha':'contender'}
            if path.startswith('git/refs/'):
                writes.append(data)
                raise urllib.error.HTTPError('local',422,'not fast forward',{},None)
            self.fail(path)
        with patch.dict(os.environ,GITHUB_RUN_ID='13',GITHUB_RUN_ATTEMPT='1'),patch.object(s,'api',side_effect=api):
            self.assertIsNone(q.acquire())
        self.assertEqual(writes,[{'sha':'contender','force':False}])

    def test_scan_resumes_after_bounded_invalid_candidates(self):
        lease=Mock(state={'page':1,'offset':0})
        items=[{'number':i,'user':{'login':str(i)},'state':'open','title':'not a submission'} for i in range(1,51)]
        calls=[]
        def api(path,data=None,method=None):
            calls.append(path)
            return items if path.startswith('issues?') else []
        with tempfile.TemporaryDirectory() as tmp:
            old=Path.cwd();os.chdir(tmp)
            try:
                with patch.dict(os.environ,GITHUB_OUTPUT=str(Path(tmp)/'output')),patch.object(q,'acquire',return_value=lease),patch.object(s,'api',side_effect=api):
                    s.select()
                    self.assertEqual(lease.state,{'page':1,'offset':40})
                    self.assertLessEqual(len(calls),41)
                    self.assertIn('selected=false',Path('output').read_text())
                    s.select()
                    self.assertEqual(lease.state['page'],2)
            finally:os.chdir(old)

    def test_network_budget_rejects_before_another_request(self):
        with patch.object(s,'SCAN_BUDGET',{'calls':400,'deadline':float('inf')}),self.assertRaises(s.ScanLimit):
            s.scan_check('issues/4/comments')

    def test_old_attempt_cannot_restart_after_lease_changes(self):
        replies=[{'object':{'sha':'state'}},{'message':json.dumps({'run_id':'13','run_attempt':'2'})}]
        with patch.dict(os.environ,GITHUB_RUN_ID='13',GITHUB_RUN_ATTEMPT='1'),patch.object(s,'api',side_effect=replies),self.assertRaisesRegex(ValueError,'another run/attempt'):
            q.assert_owner()

    def test_no_trusted_workflow_uses_fork_named_concurrency_groups(self):
        workflows=Path(__file__).resolve().parents[1]/'.github/workflows'
        self.assertFalse((workflows/'pr-verify.yml').exists())
        for path in workflows.glob('*.yml'):
            text=path.read_text()
            self.assertNotIn('concurrency:',text)
            self.assertNotIn('pull_request:',text)
            self.assertNotIn('pull_request_target:',text)


if __name__=='__main__':unittest.main()
