import importlib.util
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

spec = importlib.util.spec_from_file_location('crew', Path(__file__).with_name('app.py'))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class LoginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        app.DB = Path(cls.temp.name) / 'test.sqlite3'
        app.init_db()
        cls.server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.port = cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def setUp(self):
        app.ATTEMPTS.clear()
        app.SESSIONS.clear()

    def request(self, path, data=None, cookie=None, origin=True):
        connection = HTTPConnection('127.0.0.1', self.port)
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = f'http://127.0.0.1:{self.port}'
        if cookie:
            headers['Cookie'] = cookie
        connection.request('POST' if data is not None else 'GET', path, json.dumps(data) if data is not None else None, headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_success_session_logout(self):
        status, headers, body = self.request('/api/login', {'registration': ' crew001 ', 'phone': '98765 43210'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['name'], 'Red')
        cookie = headers['Set-Cookie'].split(';')[0]
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertEqual(self.request('/api/me', cookie=cookie)[0], 200)
        self.assertEqual(self.request('/api/logout', {}, cookie)[0], 200)
        self.assertEqual(self.request('/api/me', cookie=cookie)[0], 401)

    def test_bad_credentials_and_input(self):
        for registration, phone in [('CREW001', '1111111111'), ('CREW999', '9876543210')]:
            self.assertEqual(self.request('/api/login', {'registration': registration, 'phone': phone})[0], 401)
        for data in [{}, [], {'registration': "' OR 1=1 --", 'phone': '9876543210'}, {'registration': 'CREW001', 'phone': 'bad-number'}]:
            self.assertEqual(self.request('/api/login', data)[0], 400)

    def test_restrictions(self):
        self.assertEqual(self.request('/api/me')[0], 401)
        self.assertEqual(self.request('/crew.sqlite3')[0], 404)
        self.assertEqual(self.request('/../app.py')[0], 404)
        self.assertEqual(self.request('/api/login', {}, origin=False)[0], 403)
        for _ in range(8):
            self.assertEqual(self.request('/api/login', {})[0], 400)
        self.assertEqual(self.request('/api/login', {})[0], 429)

    def test_custom_user_and_expiry(self):
        app.add_user('REG-42', '+91 90000 00000', 'Test Crewmate')
        status, headers, _ = self.request('/api/login', {'registration': 'reg-42', 'phone': '+91 (90000) 00000'})
        self.assertEqual(status, 200)
        cookie = headers['Set-Cookie'].split(';')[0]
        token = cookie.split('=', 1)[1]
        app.SESSIONS[token]['expires'] = 0
        self.assertEqual(self.request('/api/me', cookie=cookie)[0], 401)

    def test_assets(self):
        for path in ['/', '/style.css', '/mobile.css', '/app.js', '/favicon.svg']:
            status, headers, body = self.request(path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertIn('Content-Security-Policy', headers)


if __name__ == '__main__':
    unittest.main(verbosity=2)
