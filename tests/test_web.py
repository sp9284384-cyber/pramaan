import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from evidence_tools import web
from tests._fakes import fake_result


class TestWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self._orig = web.CHECK

    def tearDown(self):
        web.CHECK = self._orig

    def req(self, method, path, body=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request(method, path, body=body, headers={"Content-Type": "application/json"} if body else {})
        r = c.getresponse()
        return r.status, r.read().decode("utf-8")

    def test_index_served(self):
        status, body = self.req("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Pramaan", body)

    def test_check_ok(self):
        web.CHECK = lambda claim: fake_result()
        status, body = self.req("POST", "/api/check", json.dumps({"claim": "haldi se sugar control hoti hai"}))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["summary"]["status"], "supported")

    def test_bad_input(self):
        self.assertEqual(self.req("POST", "/api/check", "not json")[0], 400)
        self.assertEqual(self.req("POST", "/api/check", json.dumps({"claim": "  "}))[0], 400)
        self.assertEqual(self.req("POST", "/api/check", json.dumps({"claim": "x" * 501}))[0], 400)
        self.assertEqual(self.req("POST", "/nope", "{}")[0], 404)

    def test_errors_do_not_leak_details(self):
        def boom(claim):
            raise RuntimeError("secret api_key=abc123 https://serpapi.com/?api_key=abc123")
        web.CHECK = boom
        status, body = self.req("POST", "/api/check", json.dumps({"claim": "x"}))
        self.assertEqual(status, 500)
        self.assertNotIn("abc123", body)
        self.assertIn("RuntimeError", body)


if __name__ == "__main__":
    unittest.main()
