"""A failing regression check for the deployment path before the repair."""

import unittest
from replay import check


class HealthRouteTests(unittest.TestCase):
    def test_ci_route(self):
        self.assertEqual(check("ci"), 0)

    def test_deployment_route(self):
        self.assertEqual(check("deployment"), 0)


if __name__ == "__main__":
    unittest.main()
