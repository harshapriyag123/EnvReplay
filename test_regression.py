"""Regression checks for the deployment path and route isolation."""

import unittest
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from app import serve, validate_base_path
from replay import check


class HealthRouteTests(unittest.TestCase):
    def test_ci_route(self):
        self.assertEqual(check("ci"), 0)

    def test_deployment_route(self):
        self.assertEqual(check("deployment"), 0)

    def test_prefixed_server_does_not_serve_root_route(self):
        server = serve(base_path="/service")
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(HTTPError) as error:
                urlopen(f"http://127.0.0.1:{server.server_port}/api/health", timeout=3)
            self.assertEqual(error.exception.code, 404)
            error.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_invalid_base_paths_fail_before_server_starts(self):
        for path in ("service", "/service/", "/service//api", "/service?x=1"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate_base_path(path)


if __name__ == "__main__":
    unittest.main()
