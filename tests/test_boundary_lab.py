import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import boundary_lab


class BoundaryLabTests(unittest.TestCase):
    def run_lab(self, variant):
        server = boundary_lab.BoundaryServer(('127.0.0.1', 0), variant)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server

    def request(self, server, path, data=None, *, actor=None, token=True,
                origin=None, content_type='application/json'):
        headers = {'Content-Type': content_type}
        if actor is not None:
            headers['X-Actor'] = actor
        if data is not None and token:
            headers['X-Lab-Token'] = server.lab_token if token is True else token
        if origin is not None:
            headers['Origin'] = origin
        raw = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(f'http://127.0.0.1:{server.server_port}{path}',
                                         data=raw, headers=headers)
        try:
            response = urllib.request.urlopen(request, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def owner_read(self, server):
        return self.request(server, '/api/records/note-1', actor='alice')

    def test_owner_can_read_and_update(self):
        server = self.run_lab('fixed')
        self.assertEqual(boundary_lab.INITIAL_TEXT, self.owner_read(server)[1]['text'])
        status, _ = self.request(server, '/api/records/note-1', {'text': 'OWNER-UPDATE'}, actor='alice')
        self.assertEqual(200, status)
        self.assertEqual('OWNER-UPDATE', self.owner_read(server)[1]['text'])

    def test_nonowner_cannot_read(self):
        server = self.run_lab('fixed')
        status, data = self.request(server, '/api/records/note-1', actor='bob')
        self.assertEqual(403, status)
        self.assertNotIn('text', data)

    def test_fixed_denial_has_no_hidden_write(self):
        server = self.run_lab('fixed')
        status, _ = self.request(server, '/api/records/note-1', {'text': 'BOB-WAS-HERE'}, actor='bob')
        self.assertEqual(403, status)
        self.assertEqual(boundary_lab.INITIAL_TEXT, self.owner_read(server)[1]['text'])

    def test_buggy_denial_mutates_before_deny(self):
        server = self.run_lab('buggy')
        status, _ = self.request(server, '/api/records/note-1', {'text': 'BOB-WAS-HERE'}, actor='bob')
        self.assertEqual(403, status)
        self.assertEqual('BOB-WAS-HERE', self.owner_read(server)[1]['text'])

    def test_guard_rejects_foreign_origin_and_wrong_token_without_mutation(self):
        server = self.run_lab('buggy')
        payload = {'text': 'SHOULD-NOT-LAND'}
        self.assertEqual(403, self.request(server, '/api/records/note-1', payload,
                                           actor='bob', origin='https://attacker.example')[0])
        self.assertEqual(403, self.request(server, '/api/records/note-1', payload,
                                           actor='bob', token='wrong')[0])
        self.assertEqual(boundary_lab.INITIAL_TEXT, self.owner_read(server)[1]['text'])

    def test_reset_restores_only_synthetic_record(self):
        server = self.run_lab('buggy')
        self.request(server, '/api/records/note-1', {'text': 'BOB-WAS-HERE'}, actor='bob')
        self.assertEqual(200, self.request(server, '/api/reset', {})[0])
        self.assertEqual(boundary_lab.INITIAL_TEXT, self.owner_read(server)[1]['text'])

    def test_unauthorized_reset_cannot_clear_state(self):
        server = self.run_lab('fixed')
        self.request(server, '/api/records/note-1', {'text': 'OWNER-UPDATE'}, actor='alice')
        self.assertEqual(403, self.request(server, '/api/reset', {}, token='wrong')[0])
        self.assertEqual('OWNER-UPDATE', self.owner_read(server)[1]['text'])

    def test_non_loopback_rejected(self):
        with self.assertRaises(ValueError):
            boundary_lab.BoundaryServer(('0.0.0.0', 0), 'fixed')
