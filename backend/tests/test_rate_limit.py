"""The public API bills an OpenAI call per request, so the limits matter.

The pipeline is patched out here: these tests must never make a model call.
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from order_generator import api
from order_generator.rate_limit import PER_CLIENT_LIMITS


PER_MINUTE_ALLOWANCE = int(PER_CLIENT_LIMITS.split("/")[0])


class RateLimitTests(unittest.TestCase):
    def setUp(self) -> None:
        api.limiter.reset()
        # These tests cover burst control only; the Postgres-backed cap has
        # its own tests and must not be reached from here.
        cap_patch = patch("order_generator.api.check_and_record")
        cap_patch.start()
        self.addCleanup(cap_patch.stop)
        # ALLOWED_HOSTS does not include the test client's default host.
        self.client = TestClient(api.app, base_url="http://localhost")

    def post(self, client_ip: str = "203.0.113.1"):
        return self.client.post(
            "/api/order-generator",
            params={"text": "2 sample orders"},
            headers={"x-forwarded-for": client_ip},
        )

    @patch("order_generator.api.text_to_orders", return_value=[])
    def test_requests_are_allowed_up_to_the_per_client_limit(self, _mock) -> None:
        for attempt in range(PER_MINUTE_ALLOWANCE):
            with self.subTest(attempt=attempt):
                self.assertEqual(self.post().status_code, 200)

    @patch("order_generator.api.text_to_orders", return_value=[])
    def test_exceeding_the_limit_returns_429_without_calling_the_model(
        self, mock_pipeline
    ) -> None:
        for _ in range(PER_MINUTE_ALLOWANCE):
            self.post()

        response = self.post()

        self.assertEqual(response.status_code, 429)
        self.assertIn("Too many order requests", response.json()["detail"])
        self.assertEqual(mock_pipeline.call_count, PER_MINUTE_ALLOWANCE)

    @patch("order_generator.api.text_to_orders", return_value=[])
    def test_clients_are_limited_separately(self, _mock) -> None:
        for _ in range(PER_MINUTE_ALLOWANCE):
            self.post(client_ip="203.0.113.1")

        self.assertEqual(self.post(client_ip="203.0.113.1").status_code, 429)
        self.assertEqual(self.post(client_ip="198.51.100.7").status_code, 200)


if __name__ == "__main__":
    unittest.main()
