import importlib.util
import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

spec = importlib.util.spec_from_file_location('demo', Path(__file__).resolve().parents[1] / 'scripts/demo_app.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class DemoTests(unittest.TestCase):
    def request(self, server, path, data=None, *, token=True, origin=None,
                content_type='application/json', host=None):
        raw = json.dumps(data).encode() if data is not None else None
        headers = {'Content-Type': content_type}
        if data is not None and token:
            headers['X-Lab-Token'] = server.lab_token if token is True else token
        if origin is not None:
            headers['Origin'] = origin
        if host is not None:
            headers['Host'] = host
        req = urllib.request.Request(f'http://127.0.0.1:{server.server_port}{path}', data=raw,
                                     headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=3)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            return response.status, json.loads(response.read())

    def run_lab(self, variant):
        server = demo.LabServer(('127.0.0.1', 0), variant)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server

    def test_fixed_repeat_has_one_durable_effect(self):
        s = self.run_lab('fixed')
        payload = {'date': '2031-05-17', 'request_id': 'same-intent'}
        self.assertEqual(201, self.request(s, '/api/bookings', payload)[0])
        self.assertEqual(200, self.request(s, '/api/bookings', payload)[0])
        _, result = self.request(s, '/api/bookings')
        self.assertEqual([{'id': 'booking-1', 'date': '2031-05-17'}], result['bookings'])

    def test_buggy_repeat_really_duplicates(self):
        s = self.run_lab('buggy')
        payload = {'date': '2031-05-17', 'request_id': 'same-intent'}
        for _ in range(2):
            self.assertEqual(201, self.request(s, '/api/bookings', payload)[0])
        self.assertEqual(2, len(self.request(s, '/api/bookings')[1]['bookings']))

    def test_fixed_conflicting_replay_rejected_without_mutation(self):
        s = self.run_lab('fixed')
        self.request(s, '/api/bookings', {'date': '2031-05-17', 'request_id': 'k'})
        self.assertEqual(409, self.request(s, '/api/bookings', {'date': '2031-05-18', 'request_id': 'k'})[0])
        self.assertEqual('2031-05-17', self.request(s, '/api/bookings')[1]['bookings'][0]['date'])

    def test_invalid_date_does_not_create(self):
        s = self.run_lab('fixed')
        self.assertEqual(400, self.request(s, '/api/bookings', {'date': '2031-02-30', 'request_id': 'k'})[0])
        self.assertEqual([], self.request(s, '/api/bookings')[1]['bookings'])

    def test_reset_owned_lab_data(self):
        s = self.run_lab('fixed')
        self.request(s, '/api/bookings', {'date': '2031-05-17', 'request_id': 'k'})
        self.assertEqual(200, self.request(s, '/api/reset', {})[0])
        self.assertEqual([], self.request(s, '/api/bookings')[1]['bookings'])

    def test_session_exposes_current_token_to_same_host_client(self):
        s = self.run_lab('fixed')
        status, data = self.request(s, '/api/session')
        self.assertEqual(200, status)
        self.assertEqual(s.lab_token, data['token'])

    def test_foreign_origin_and_simple_content_type_cannot_write(self):
        s = self.run_lab('fixed')
        payload = {'date': '2031-05-17', 'request_id': 'foreign'}
        status, _ = self.request(s, '/api/bookings', payload, token=False,
                                 origin='https://attacker.example', content_type='text/plain')
        self.assertEqual(403, status)
        self.assertEqual([], self.request(s, '/api/bookings')[1]['bookings'])

    def test_foreign_origin_rejected_even_with_token(self):
        s = self.run_lab('fixed')
        payload = {'date': '2031-05-17', 'request_id': 'foreign-token'}
        status, _ = self.request(s, '/api/bookings', payload,
                                 origin='https://attacker.example')
        self.assertEqual(403, status)
        self.assertEqual([], self.request(s, '/api/bookings')[1]['bookings'])

    def test_wrong_token_and_wrong_content_type_do_not_mutate(self):
        s = self.run_lab('fixed')
        payload = {'date': '2031-05-17', 'request_id': 'wrong'}
        self.assertEqual(403, self.request(s, '/api/bookings', payload, token='wrong')[0])
        self.assertEqual(415, self.request(s, '/api/bookings', payload,
                                           content_type='text/plain')[0])
        self.assertEqual([], self.request(s, '/api/bookings')[1]['bookings'])

    def test_unauthorized_reset_does_not_mutate(self):
        s = self.run_lab('fixed')
        self.request(s, '/api/bookings', {'date': '2031-05-17', 'request_id': 'keep'})
        self.assertEqual(403, self.request(s, '/api/reset', {}, token='wrong')[0])
        self.assertEqual(403, self.request(s, '/api/reset', {},
                                           origin='https://attacker.example')[0])
        self.assertEqual(1, len(self.request(s, '/api/bookings')[1]['bookings']))

    def test_wrong_host_rejected(self):
        s = self.run_lab('fixed')
        payload = {'date': '2031-05-17', 'request_id': 'host'}
        self.assertEqual(421, self.request(s, '/api/bookings', payload,
                                           host='attacker.example')[0])
        self.assertEqual([], self.request(s, '/api/bookings')[1]['bookings'])

    def test_non_loopback_rejected(self):
        with self.assertRaises(ValueError):
            demo.LabServer(('0.0.0.0', 0), 'fixed')
