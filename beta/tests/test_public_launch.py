"""Exercise launch boundaries, not only the happy-path registration form."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from genius_beta.app import create_app
from genius_beta.config import settings


class PublicLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        data = Path(self.temp.name)
        self.app = create_app(dict(DATA_DIR=data, DATABASE=data/'db.sqlite3',
            SUSPEND_FILE=data/'SUSPENDED', PUBLIC_URL='http://localhost',
            ENV='development', REGISTRATION_OPEN=True, TESTING=True))
        self.client = self.app.test_client()
        self.payload = dict(username='synthetic', password='Synthetic-password-123',
            privacy_accepted=True, privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_project_home_and_account_workspace_are_separate_public_entries(self):
        with self.client.get('/') as response:
            self.assertEqual(response.status_code, 200)
            home = response.get_data(as_text=True)
            self.assertIn('href="/app?next=/twin/"', home)
            self.assertNotIn('id="auth-form"', home)
            self.assertNotIn('/static/app.js', home)
            self.assertNotIn('Set-Cookie', response.headers)
        with self.client.get('/app') as response:
            self.assertEqual(response.status_code, 200)
            workspace = response.get_data(as_text=True)
            for marker in ('id="auth-form"', 'id="workspace"', '/static/app.js', '/static/choice.js'):
                self.assertIn(marker, workspace)
            self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
        self.assertEqual(self.client.get('/api/me').status_code, 401)

    def test_existing_api_access_bookmark_reaches_same_workspace_without_external_redirect(self):
        response = self.client.get('/?access=api&next=https://example.invalid')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/app?access=api')
        with self.client.get(response.headers['Location']) as workspace:
            self.assertEqual(workspace.status_code, 200)
            self.assertIn('id="workspace"', workspace.get_data(as_text=True))

    def test_home_and_workspace_remain_readable_when_registration_is_closed(self):
        self.app.config['REGISTRATION_OPEN'] = False
        self.app.config['SUSPEND_FILE'].touch()
        for path in ('/', '/app', '/static/home.css'):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.get('/api/config').json['registration_open'])

    def test_closing_registration_preserves_existing_access_export_and_deletion(self):
        response = self.client.post('/api/register', json=self.payload)
        self.assertEqual(response.status_code, 201)
        csrf = response.json['csrf_token']
        self.app.config['REGISTRATION_OPEN'] = False
        self.assertFalse(self.client.get('/api/config').json['registration_open'])
        response = self.client.post('/api/register', json={**self.payload, 'username':'other'})
        self.assertEqual((response.status_code,response.json['error']['code']), (503,'registration_closed'))
        self.assertEqual(self.client.get('/api/export').status_code, 200)
        login = self.client.post('/api/login', json=self.payload)
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.delete('/api/me', headers={'X-CSRF-Token':login.json['csrf_token']}).status_code, 204)
        self.assertEqual(self.client.get('/api/me').status_code, 401)

    def test_notice_changed_between_read_and_acceptance(self):
        shown = self.client.get('/api/config').json['privacy']['version']
        self.app.config['PRIVACY_VERSION'] = shown+'-revised'
        response = self.client.post('/api/register', json=self.payload)
        self.assertEqual((response.status_code,response.json['error']['code']), (409,'privacy_version_changed'))
        self.assertEqual(self.client.get('/api/me').status_code, 401)

    def test_adult_confirmation_is_explicit_and_optional_consents_stay_off(self):
        for value in (None, False, 'true', 1):
            response = self.client.post('/api/register', json={**self.payload,'adult_confirmed':value})
            self.assertEqual(response.json['error']['code'], 'adult_required')
        response = self.client.post('/api/register', json=self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json['user']['research_consent'])
        self.assertFalse(response.json['user']['followup_consent'])

    def test_production_defaults_closed_and_keeps_existing_legal_guard(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'Production requires HTTPS origin'):
                settings(dict(ENV='production', PUBLIC_URL='https://example.invalid'))
            cfg = settings(dict(ENV='production', PUBLIC_URL='https://example.invalid',
                PRIVACY_CONTROLLER='Synthetic test only',
                PRIVACY_CONTACT='test@example.invalid'))
            self.assertFalse(cfg['REGISTRATION_OPEN'])
        with patch.dict('os.environ', {'GENIUS_REGISTRATION_OPEN':'tru'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'must be true or false'):
                settings()

    def test_public_routes_never_expose_legacy_controller_address(self):
        self.app.config['PRIVACY_ADDRESS'] = 'PRIVATE-SENTINEL-NOT-FOR-OUTPUT'
        for path in ('/api/config', '/api/meta'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('address', response.json['privacy'])
            self.assertNotIn('PRIVATE-SENTINEL', response.get_data(as_text=True))
        for path in ('/', '/static/app.js', '/static/privacy.html', '/static/privacy.js'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('PRIVATE-SENTINEL', response.get_data(as_text=True))
            response.close()
        with self.client.get('/static/privacy.html') as response:
            notice = response.get_data(as_text=True)
        self.assertNotIn('data-privacy="address"', notice)
        self.assertIn(self.app.config['PRIVACY_VERSION'], notice)

    def test_email_is_a_username_error_and_creates_no_account(self):
        response = self.client.post('/api/register', json={
            **self.payload, 'username': 'synthetic@example.invalid'})
        self.assertEqual((response.status_code, response.json['error']['code']),
                         (400, 'invalid_username'))
        self.assertIn('alias, no un correo', response.json['error']['message'])
        self.assertNotIn('contraseña', response.json['error']['message'].lower())
        self.assertEqual(self.client.get('/api/me').status_code, 401)

    def test_password_symbols_and_spaces_survive_registration_and_login(self):
        password = '  Fictional-only!@#$%_+/=  '
        response = self.client.post('/api/register', json={
            **self.payload, 'password': password})
        self.assertEqual(response.status_code, 201)
        client = self.app.test_client()
        self.assertEqual(client.post('/api/login', json={
            'username': self.payload['username'], 'password': password.strip()}).status_code, 401)
        self.assertEqual(client.post('/api/login', json={
            'username': self.payload['username'], 'password': password}).status_code, 200)

    def test_password_limits_are_reported_as_password_errors(self):
        for password in ('short-12345', 'x' * 129, None):
            with self.subTest(length=len(password) if password is not None else None):
                response = self.client.post('/api/register', json={
                    **self.payload, 'password': password})
                self.assertEqual(response.json['error']['code'], 'invalid_password')
                self.assertIn('Contraseña:', response.json['error']['message'])
        self.assertEqual(self.client.get('/api/me').status_code, 401)


if __name__ == '__main__':
    unittest.main()
