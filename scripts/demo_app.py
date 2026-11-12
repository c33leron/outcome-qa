#!/usr/bin/env python3
"""Synthetic loopback-only booking lab; not a production app or an LLM."""
import argparse
import datetime
import hmac
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HTML = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Outcome QA — Booking Lab</title>
<style>body{font:18px system-ui;max-width:740px;margin:60px auto;padding:0 24px;color:#17202a;background:#f5f6f8}main{background:white;padding:28px;border:1px solid #ccd2d8;border-radius:12px}label{display:block;margin:20px 0 8px}input,button{font:inherit;padding:10px}button{margin-top:18px;cursor:pointer}li{padding:6px}small{color:#566573}</style>
<main><h1>Booking Lab</h1><p>Reserve one room. Edit the date, submit, then reopen the page to inspect saved bookings.</p>
<small>Synthetic local data. Nothing is booked or charged outside this process.</small>
<form id="booking"><label for="day">Booking date (YYYY-MM-DD)</label>
<input id="day" name="day" value="2031-05-10" required pattern="[0-9]{4}-[0-9]{2}-[0-9]{2}">
<br><button id="reserve" type="submit" disabled>Reserve room</button></form>
<p id="status" role="status" aria-live="polite">Ready</p>
<h2>Saved bookings</h2><ul id="saved"></ul></main>
<script>
const day=document.querySelector('#day'), status=document.querySelector('#status');
const initialDate=day.value;
let requestId=crypto.randomUUID();
let labToken=null;
day.addEventListener('input',()=>{requestId=crypto.randomUUID()});
async function refresh(){const r=await fetch('/api/bookings');if(!r.ok)throw Error('Read failed');const data=await r.json();const ul=document.querySelector('#saved');ul.replaceChildren();for(const b of data.bookings){const li=document.createElement('li');li.textContent=b.id+' — '+b.date;ul.append(li)}}
document.querySelector('#booking').addEventListener('submit',async event=>{
 event.preventDefault();status.textContent='Saving…';
 try {if(!labToken)throw Error('Lab session is not ready');const r=await fetch('/api/bookings',{method:'POST',headers:{'Content-Type':'application/json','X-Lab-Token':labToken},body:JSON.stringify({date:__DATE_EXPRESSION__,request_id:requestId})});
 const data=await r.json();if(!r.ok)throw Error(data.error||'Save failed');status.textContent='Reservation saved';await refresh()}
 catch(error){status.textContent='Unable to complete: '+error.message}
});
async function init(){const r=await fetch('/api/session');if(!r.ok)throw Error('Session failed');labToken=(await r.json()).token;document.querySelector('#reserve').disabled=false;await refresh()}
init().catch(()=>{status.textContent='Unable to initialize lab'});
</script></html>'''


class GuardedLabServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, variant, handler):
        if address[0] != '127.0.0.1':
            raise ValueError('Lab binds only to 127.0.0.1.')
        if variant not in ('buggy', 'fixed'):
            raise ValueError('Unknown lab variant.')
        self.variant = variant
        self.lab_token = secrets.token_urlsafe(32)
        super().__init__(address, handler)
        self.expected_host = f'127.0.0.1:{self.server_port}'
        self.expected_origin = f'http://{self.expected_host}'


class LabServer(GuardedLabServer):
    def __init__(self, address, variant):
        self.bookings = []
        self.keys = {}
        self.lock = threading.Lock()
        super().__init__(address, variant, Handler)


class GuardedHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, status, data, mime='application/json'):
        raw = (json.dumps(data) if mime == 'application/json' else data).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(raw)

    def valid_host(self):
        if self.headers.get('Host') != self.server.expected_host:
            self.send(421, {'error': 'Invalid lab host'})
            return False
        return True

    def authorize_write(self):
        if not self.valid_host():
            return False
        origin = self.headers.get('Origin')
        if origin is not None and origin != self.server.expected_origin:
            self.send(403, {'error': 'Cross-origin lab write rejected'})
            return False
        media_type = self.headers.get('Content-Type', '').partition(';')[0].strip().lower()
        if media_type != 'application/json':
            self.send(415, {'error': 'Expected application/json'})
            return False
        supplied = self.headers.get('X-Lab-Token', '')
        if not hmac.compare_digest(supplied, self.server.lab_token):
            self.send(403, {'error': 'Invalid lab token'})
            return False
        return True

    def read_json_object(self, maximum=8192):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or length > maximum:
                self.send(413, {'error': 'Body too large'})
                return None
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Expected object')
            return data
        except (ValueError, TypeError):
            self.send(400, {'error': 'Invalid request'})
            return None


class Handler(GuardedHandler):

    def do_GET(self):
        if not self.valid_host():
            return
        if self.path == '/':
            expression = 'initialDate' if self.server.variant == 'buggy' else 'day.value'
            self.send(200, HTML.replace('__DATE_EXPRESSION__', expression), 'text/html')
        elif self.path == '/api/session':
            self.send(200, {'token': self.server.lab_token})
        elif self.path == '/api/bookings':
            with self.server.lock:
                data = [dict(x) for x in self.server.bookings]
            self.send(200, {'bookings': data})
        else:
            self.send(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path not in ('/api/bookings', '/api/reset'):
            self.send(404, {'error': 'Not found'})
            return
        if not self.authorize_write():
            return
        data = self.read_json_object()
        if data is None:
            return
        try:
            if self.path == '/api/reset':
                with self.server.lock:
                    self.server.bookings.clear()
                    self.server.keys.clear()
                self.send(200, {'reset': True})
                return
            date = data.get('date')
            key = data.get('request_id')
            if not isinstance(date, str) or datetime.date.fromisoformat(date).isoformat() != date:
                raise ValueError('Expected an ISO calendar date')
            if not isinstance(key, str) or not 1 <= len(key) <= 128:
                raise ValueError('Expected request_id')
        except (ValueError, TypeError):
            self.send(400, {'error': 'Invalid request'})
            return
        with self.server.lock:
            previous = self.server.keys.get(key)
            if self.server.variant == 'fixed' and previous:
                if previous['date'] != date:
                    status, result = 409, {'error': 'Request ID already used for different data'}
                else:
                    status, result = 200, dict(previous)
            else:
                result = {'id': 'booking-' + str(len(self.server.bookings) + 1), 'date': date}
                self.server.bookings.append(result)
                self.server.keys[key] = result
                status = 201
        self.send(status, result)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant', choices=['buggy', 'fixed'], default='buggy')
    p.add_argument('--port', type=int, default=0, help='0 chooses a free port')
    args = p.parse_args()
    server = LabServer(('127.0.0.1', args.port), args.variant)
    print(json.dumps({'url': 'http://127.0.0.1:' + str(server.server_port),
                      'synthetic': True, 'variant': args.variant}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
