#!/usr/bin/env python3
"""Synthetic loopback authorization lab with an owner-side read-back oracle."""
import argparse
import json
import threading

from demo_app import GuardedHandler, GuardedLabServer


INITIAL_TEXT = 'ALICE-OWNED-CANARY'
RECORD_ID = 'note-1'

HTML = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outcome QA — Boundary Lab</title>
<style>body{font:18px system-ui;max-width:740px;margin:60px auto;padding:0 24px;color:#17202a;background:#f5f6f8}main{background:white;padding:28px;border:1px solid #ccd2d8;border-radius:12px}label{display:block;margin:18px 0 6px}input,select,button{font:inherit;padding:9px}button{margin:14px 8px 0 0}</style>
<main><h1>Record boundary lab</h1><p>Alice owns note-1. Bob must neither read nor change it.</p>
<label for="actor">Synthetic actor</label><select id="actor"><option>alice</option><option>bob</option></select>
<label for="text">Record text</label><input id="text" value="">
<br><button id="load" disabled>Load record</button><button id="save" disabled>Save record</button>
<p id="status" role="status">Initializing…</p></main>
<script>
let labToken=null;const actor=document.querySelector('#actor'),text=document.querySelector('#text'),status=document.querySelector('#status');
async function load(){const r=await fetch('/api/records/note-1',{headers:{'X-Actor':actor.value}});const d=await r.json();if(!r.ok)throw Error(d.error||'Load rejected');text.value=d.text;status.textContent='Loaded for '+actor.value}
async function save(){const r=await fetch('/api/records/note-1',{method:'POST',headers:{'Content-Type':'application/json','X-Lab-Token':labToken,'X-Actor':actor.value},body:JSON.stringify({text:text.value})});const d=await r.json();if(!r.ok)throw Error(d.error||'Save rejected');status.textContent='Saved for '+actor.value}
document.querySelector('#load').onclick=()=>load().catch(e=>status.textContent=e.message);
document.querySelector('#save').onclick=()=>save().catch(e=>status.textContent=e.message);
async function init(){const r=await fetch('/api/session');if(!r.ok)throw Error('Session failed');labToken=(await r.json()).token;document.querySelector('#load').disabled=false;document.querySelector('#save').disabled=false;await load()}
init().catch(e=>status.textContent=e.message);
</script></html>'''


class BoundaryServer(GuardedLabServer):
    def __init__(self, address, variant):
        self.lock = threading.Lock()
        self.record = {'id': RECORD_ID, 'owner': 'alice', 'text': INITIAL_TEXT}
        super().__init__(address, variant, BoundaryHandler)


class BoundaryHandler(GuardedHandler):
    def actor(self):
        value = self.headers.get('X-Actor', '')
        return value if value in ('alice', 'bob') else None

    def do_GET(self):
        if not self.valid_host():
            return
        if self.path == '/':
            self.send(200, HTML, 'text/html')
            return
        if self.path == '/api/session':
            self.send(200, {'token': self.server.lab_token})
            return
        if self.path != f'/api/records/{RECORD_ID}':
            self.send(404, {'error': 'Not found'})
            return
        actor = self.actor()
        if actor != 'alice':
            self.send(403, {'error': 'Record access denied'})
            return
        with self.server.lock:
            result = dict(self.server.record)
        self.send(200, result)

    def do_POST(self):
        if self.path not in (f'/api/records/{RECORD_ID}', '/api/reset'):
            self.send(404, {'error': 'Not found'})
            return
        if not self.authorize_write():
            return
        data = self.read_json_object()
        if data is None:
            return
        if self.path == '/api/reset':
            with self.server.lock:
                self.server.record = {'id': RECORD_ID, 'owner': 'alice', 'text': INITIAL_TEXT}
            self.send(200, {'reset': True})
            return
        actor = self.actor()
        text = data.get('text')
        if actor is None or not isinstance(text, str) or not 1 <= len(text) <= 200:
            self.send(400, {'error': 'Invalid synthetic update'})
            return
        with self.server.lock:
            if actor != self.server.record['owner']:
                if self.server.variant == 'buggy':
                    self.server.record['text'] = text
                self.send(403, {'error': 'Record update denied'})
                return
            self.server.record['text'] = text
            result = dict(self.server.record)
        self.send(200, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=['buggy', 'fixed'], default='buggy')
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    server = BoundaryServer(('127.0.0.1', args.port), args.variant)
    print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}',
                      'synthetic': True, 'variant': args.variant}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
