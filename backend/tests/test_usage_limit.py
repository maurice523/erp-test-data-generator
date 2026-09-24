"""The global cap is what bounds OpenAI spend, so its refusals matter.

Every test here patches the database out, or is skipped unless DATABASE_URL is
set. Nothing in this file may make a model call.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from order_generator import api, usage_limit


def fake_connection(fetchone_result, side_effect=None):
    """A psycopg.connect stand-in whose cursor returns one canned row."""
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_result
    if side_effect is not None:
        cursor.execute.side_effect = side_effect

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    return connection


class CheckAndRecordTests(unittest.TestCase):
    def test_allows_when_the_insert_returns_a_row(self) -> None:
        with patch("psycopg.connect", return_value=fake_connection(("now",))):
            usage_limit.check_and_record()  # does not raise

    def test_refuses_when_the_insert_records_nothing(self) -> None:
        # No row back means the WHERE clause rejected it: a limit is spent.
        with patch("psycopg.connect", return_value=fake_connection(None)):
            with self.assertRaises(usage_limit.UsageLimitExceeded):
                usage_limit.check_and_record()

    def test_database_errors_propagate(self) -> None:
        connection = fake_connection(None, side_effect=RuntimeError("no database"))
        with patch("psycopg.connect", return_value=connection):
            with self.assertRaises(RuntimeError):
                usage_limit.check_and_record()

    def test_limits_are_passed_to_the_query(self) -> None:
        connection = fake_connection(("now",))
        with patch("psycopg.connect", return_value=connection):
            usage_limit.check_and_record()

        cursor = connection.cursor.return_value.__enter__.return_value
        _sql, params = cursor.execute.call_args[0]
        self.assertEqual(params["hourly_limit"], usage_limit.HOURLY_LIMIT)
        self.assertEqual(params["daily_limit"], usage_limit.DAILY_LIMIT)


class EndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        api.limiter.reset()
        # ALLOWED_HOSTS does not include the test client's default host.
        self.client = TestClient(api.app, base_url="http://localhost")

    def post(self):
        return self.client.post(
            "/api/order-generator",
            params={"text": "2 sample orders"},
            headers={"x-forwarded-for": "203.0.113.9"},
        )

    @patch("order_generator.api.text_to_orders", return_value=[])
    @patch("order_generator.api.check_and_record")
    def test_allowed_request_reaches_the_pipeline(self, _cap, pipeline) -> None:
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(pipeline.call_count, 1)

    @patch("order_generator.api.text_to_orders", return_value=[])
    @patch(
        "order_generator.api.check_and_record",
        side_effect=usage_limit.UsageLimitExceeded,
    )
    def test_capped_request_returns_429_without_calling_the_model(
        self, _cap, pipeline
    ) -> None:
        response = self.post()

        self.assertEqual(response.status_code, 429)
        self.assertIn("daily limit", response.json()["detail"])
        self.assertEqual(pipeline.call_count, 0)

    @patch("order_generator.api.text_to_orders", return_value=[])
    @patch(
        "order_generator.api.check_and_record",
        side_effect=RuntimeError("no database"),
    )
    def test_database_failure_fails_closed(self, _cap, pipeline) -> None:
        response = self.post()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(pipeline.call_count, 0)


@unittest.skipUnless(
    os.getenv("DATABASE_URL"), "needs a live database; no model calls involved"
)
class LiveDatabaseTests(unittest.TestCase):
    def test_recording_increments_the_window_counts(self) -> None:
        usage_limit.ensure_usage_table()
        before = usage_limit.current_usage()

        usage_limit.check_and_record()
        self.addCleanup(self.remove_newest_row)
        after = usage_limit.current_usage()

        self.assertEqual(after["last_hour"], before["last_hour"] + 1)
        self.assertEqual(after["last_day"], before["last_day"] + 1)

    def remove_newest_row(self) -> None:
        """Keep the suite from spending slots out of the real daily cap."""
        import psycopg

        from order_generator.extract.extract_orders import get_database_url

        with psycopg.connect(get_database_url()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM api_usage WHERE called_at = "
                    "(SELECT max(called_at) FROM api_usage)"
                )


if __name__ == "__main__":
    unittest.main()
