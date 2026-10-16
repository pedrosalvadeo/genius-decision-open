"""Loopback-only lab transport. Peer reads cannot invoke operator mutations."""
import argparse
import hmac
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import sys

from .core import MAX_BYTES, MAX_PEERS, Node, canonical, decode, fields, identifier, integer


def secret(value):
    if not isinstance(value, str) or not 32 <= len(value) <= 128 or not value.isascii():
        raise ValueError('INVALID_SECRET')
    return value


def request(port, token, method, path, payload=None):
    integer(port, 65535)
    if port == 0:
        raise ValueError('INVALID_PORT')
    conn = HTTPConnection('127.0.0.1', port, timeout=2)
    try:
        conn.request(method, path, body=None if payload is None else canonical(payload),
                     headers={'Authorization': 'Bearer '+secret(token), 'Content-Type': 'application/json'})
        response = conn.getresponse()
        raw = response.read(MAX_BYTES+1)
        if response.status != 200:
            raise ValueError('PEER_HTTP_'+str(response.status))
        return decode(raw)
    finally:
        conn.close()


class LabServer(HTTPServer):
    allow_reuse_address = False

    def __init__(self, node, config):
        fields(config, 'admin_token read_token')
        self.node = node
        self.admin_token = secret(config['admin_token'])
        self.read_token = secret(config['read_token'])
        if hmac.compare_digest(self.admin_token, self.read_token):
            raise ValueError('SEPARATE_CREDENTIALS_REQUIRED')
        self.peers = {}
        super().__init__(('127.0.0.1', 0), Handler)

    def get_request(self):
        conn, address = super().get_request()
        conn.settimeout(3)
        return conn, address

    def enroll(self, peers):
        if type(peers) is not list or len(peers) > MAX_PEERS:
            raise ValueError('PEER_LIMIT')
        checked = {}
        for peer in peers:
            fields(peer, 'node_id port read_token')
            name = identifier(peer['node_id'])
            integer(peer['port'], 65535)
            secret(peer['read_token'])
            if name in checked or name == self.node.node_id or peer['port'] == 0:
                raise ValueError('INVALID_PEER')
            checked[name] = peer
        self.peers = checked
        return dict(enrolled=sorted(checked))

    def sync(self, name):
        peer = self.peers.get(identifier(name))
        if not peer:
            raise ValueError('UNENROLLED_PEER')
        try:
            hello = request(peer['port'], peer['read_token'], 'GET', '/hello')
            if (hello.get('format') != 'genius-node-hello/1' or hello.get('node_id') != name or
                'observation_exchange_v1' not in hello.get('capabilities', [])):
                raise ValueError('PEER_IDENTITY_OR_PROTOCOL')
            packet = request(peer['port'], peer['read_token'], 'GET', '/experiences')
            fields(packet, 'node_id records')
            if packet['node_id'] != name or type(packet['records']) is not list:
                raise ValueError('PEER_IDENTITY_OR_PROTOCOL')
            outcome = self.node.ingest(packet['records'], via=name) if packet['records'] else dict(inserted=0, duplicates=0)
            return dict(status='EXCHANGED', peer=name, hello=hello, **outcome)
        except (OSError, ValueError, KeyError, TypeError, RecursionError):
            # Failed discovery/import leaves prior memory intact. Never interpret
            # silence as an empty environment or erase prior knowledge.
            return dict(status='UNAVAILABLE_OR_REJECTED', peer=name, memory_preserved=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # No headers, credentials, observations or personal payloads in logs.

    def authorized(self, write):
        value = self.headers.get('Authorization', '')
        allowed = [self.server.admin_token] if write else [self.server.admin_token, self.server.read_token]
        return any(hmac.compare_digest(value.encode(), ('Bearer '+token).encode()) for token in allowed)

    def reply(self, status, value):
        raw = canonical(value)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if not self.authorized(False):
            return self.reply(401, dict(error='UNAUTHORIZED'))
        if self.path == '/hello':
            return self.reply(200, self.server.node.hello())
        if self.path == '/experiences':
            return self.reply(200, dict(node_id=self.server.node.node_id, records=self.server.node.export()))
        self.reply(404, dict(error='UNKNOWN_ROUTE'))

    def do_POST(self):
        if not self.authorized(True):
            return self.reply(401, dict(error='UNAUTHORIZED'))
        try:
            if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Encoding'):
                raise ValueError('ENCODING_NOT_SUPPORTED')
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_BYTES:
                raise ValueError('MESSAGE_LIMIT')
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError('INCOMPLETE_MESSAGE')
            body = decode(raw)
            node = self.server.node
            if self.path == '/observe':
                fields(body, 'records')
                result = node.ingest(body['records'])
            elif self.path == '/peers':
                fields(body, 'peers')
                result = self.server.enroll(body['peers'])
            elif self.path == '/sync':
                fields(body, 'node_id')
                result = self.server.sync(body['node_id'])
            elif self.path == '/predict':
                fields(body, 'id context mode target_after target_before')
                result = node.predict(body['id'], body['context'], body['mode'], body['target_after'], body['target_before'])
            elif self.path == '/target':
                fields(body, 'id target')
                result = node.observe_target(body['id'], body['target'])
            else:
                return self.reply(404, dict(error='UNKNOWN_ROUTE'))
            self.reply(200, result)
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError, UnicodeError):
            self.reply(422, dict(error='INVALID_REQUEST'))


def main():
    parser = argparse.ArgumentParser(description='Private loopback Genius node laboratory')
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--node-id', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    # Secrets arrive via the parent pipe, never through arguments or environment.
    config = decode(sys.stdin.buffer.readline(1024))
    server = LabServer(Node(args.state, args.node_id), config)
    print(json.dumps(dict(node_id=args.node_id, port=server.server_port)), flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
