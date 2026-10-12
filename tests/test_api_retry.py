import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, call, patch
from urllib.error import HTTPError, URLError
from http.client import IncompleteRead

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import submissions as s
import pr_submissions as p


def response(body=b'{"ok":true}'):
    result = io.BytesIO(body)
    result.headers = {}
    return result


def http_error(code):
    return HTTPError('https://api.github.com/test', code, 'test', {}, None)


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, GH_TOKEN='test-token')
        self.env.start()
        self.budget = patch.object(s, 'SCAN_BUDGET', None)
        self.budget.start()
        self.sleep = patch.object(s.time, 'sleep')
        self.wait = self.sleep.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.budget.stop)
        self.addCleanup(self.sleep.stop)

    def invoke(self, module, effects, **kwargs):
        opener = Mock(side_effect=effects)
        if module is s:
            context = patch.object(s.urllib.request, 'urlopen', opener)
        else:
            context = patch.object(p.urllib.request, 'build_opener', return_value=Mock(open=opener))
        with context:
            result = module.api('issues/4', **kwargs)
        return result, opener

    def test_get_recovers_from_502_and_connection_failure(self):
        for module in (s, p):
            with self.subTest(module=module.__name__):
                self.wait.reset_mock()
                result, opener = self.invoke(module, [http_error(502), URLError('connection'), response()])
                self.assertEqual(result, {'ok': True})
                self.assertEqual(opener.call_count, 3)
                self.assertEqual(self.wait.call_args_list, [call(1), call(2)])

    def test_attempts_stop_at_three(self):
        for module in (s, p):
            for error in (http_error(503), ConnectionResetError(), TimeoutError()):
                with self.subTest(module=module.__name__, error=type(error).__name__):
                    self.wait.reset_mock()
                    opener = Mock(side_effect=error)
                    with patch.object(s.urllib.request, 'urlopen', opener), patch.object(p.urllib.request, 'build_opener', return_value=Mock(open=opener)):
                        with self.assertRaises(type(error)):
                            module.api('issues/4')
                    self.assertEqual(opener.call_count, 3)
                    self.assertEqual(self.wait.call_args_list, [call(1), call(2)])

    def test_no_retry_for_writes_or_client_errors(self):
        for module in (s, p):
            for kwargs in ({'data': {'body': 'comment'}}, {'data': {}, 'method': 'PUT'}, {'data': {}, 'method': 'PATCH'}, {'method': 'DELETE'}, {}):
                errors = [http_error(502), URLError('lost response')] if kwargs else [http_error(403), http_error(404), http_error(429)]
                for error in errors:
                    with self.subTest(module=module.__name__, kwargs=kwargs, error=error):
                        self.wait.reset_mock()
                        opener = Mock(side_effect=error)
                        with patch.object(s.urllib.request, 'urlopen', opener), patch.object(p.urllib.request, 'build_opener', return_value=Mock(open=opener)):
                            with self.assertRaises(type(error)):
                                module.api('issues/4', **kwargs)
                        self.assertEqual(opener.call_count, 1)
                        self.wait.assert_not_called()

    def test_stream_failure_restarts_bounded_download(self):
        broken = Mock()
        broken.__enter__ = Mock(return_value=broken)
        broken.__exit__ = Mock(return_value=False)
        broken.headers = {}
        broken.read.side_effect = [b'partial', IncompleteRead(b'')]
        result, opener = self.invoke(p, [broken, response(b'complete')], raw=True)
        self.assertEqual(result, b'complete')
        self.assertEqual(opener.call_count, 2)

    def test_validation_errors_are_not_retried(self):
        oversized = response()
        oversized.headers = {'Content-Length': str(p.MAX_ARCHIVE + 1)}
        with self.assertRaises(ValueError):
            self.invoke(p, [oversized], raw=True)
        with self.assertRaises(json.JSONDecodeError):
            self.invoke(s, [response(b'not json')])
        self.wait.assert_not_called()

    def test_retries_consume_scan_budget(self):
        opener = Mock(side_effect=http_error(502))
        with patch.object(s, 'SCAN_BUDGET', {'calls': 399, 'deadline': float('inf')}), patch.object(s.urllib.request, 'urlopen', opener):
            with self.assertRaises(s.ScanLimit):
                s.api('issues/4')
        self.assertEqual(opener.call_count, 1)


if __name__ == '__main__':
    unittest.main()
