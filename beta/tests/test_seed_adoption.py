"""Anonymous adoption is read-only and retains existing hosting boundaries."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from genius_beta.app import create_app


class SeedAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        env = patch.dict(os.environ, {'GENIUS_R2_BACKUP_ENABLED':'false'})
        env.start(); self.addCleanup(env.stop)
        self.app = create_app(dict(DATA_DIR=root, DATABASE=root/'db.sqlite3',
            SUSPEND_FILE=root/'SUSPENDED', PUBLIC_URL='https://hub.example', TESTING=True))
        self.client = self.app.test_client(use_cookies=False)

    def test_public_page_and_assets_without_account(self):
        for path in ('/adopt','/static/adopt.js','/static/adopt.css'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertNotIn('Set-Cookie', response.headers)
            response.close()
        with self.client.get('/adopt') as response:
            page = response.text
        for text in ('DEMO LOCAL', 'DATOS SINTÉTICOS', 'un nacimiento total',
                     'policy-consent', 'HABITATS.md', 'HOSTING.md', 'role="status"'):
            self.assertIn(text, page)
        self.assertEqual(self.client.post('/adopt').status_code, 405)

    def test_entry_points(self):
        for path in ('/lab', '/es/lab', '/network', '/organisms'):
            with self.client.get(path) as response:
                self.assertIn('href="/adopt"', response.text, path)

    def test_no_account_or_network_mutation_in_local_demo(self):
        with self.client.get('/static/adopt.js') as response:
            script = response.text
        for prohibited in ('fetch(', 'XMLHttpRequest', 'localStorage', 'innerHTML', '/api/'):
            self.assertNotIn(prohibited, script)
        self.assertIn('max_births:1', script)
        self.assertIn("$('policy-consent').checked = false", script)

    def test_machine_readable_adoption(self):
        with self.client.get('/adopt/manifest.json') as response:
            self.assertEqual(response.status_code, 200)
            data = response.json
        self.assertFalse(data['demo']['creates_identity'])
        self.assertFalse(data['demo']['executes_kernel'])
        self.assertEqual(data['paths'][2]['starter_max_births_total'], 1)
        with self.client.get('/llms.txt') as response:
            self.assertIn('/adopt/manifest.json', response.text)
