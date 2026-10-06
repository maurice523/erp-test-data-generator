"""The global cap is what bounds OpenAI spend, so its refusals matter.

Every test here patches the database out, or is skipped unless the D1
settings are set. Nothing in this file may make a model call.
"""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from order_generator import api, d1, usage_limit


def batch_returning(inserted_rows):
    """A d1.batch stand-in: the prune result, then the insert's RETURNING rows."""
    return [d1.Result(columns=[], rows=[]), d1.Result(columns=["called_at"], rows=inserted_rows)]


class CheckAndRecordTests(unittest.TestCase):
    def test_allows_when_the_insert_returns_a_row(self) -> None:
        with patch("order_generator.d1.batch", return_value=batch_returning([[1]])):
            usage_limit.check_and_record()  # does not raise

    def test_refuses_when_the_insert_records_nothing(self) -> None:
        # No row back means the WHERE clause rejected it: a limit is spent.
        with patch("order_generator.d1.batch", return_value=batch_returning([])):
            with self.assertRaises(usage_limit.UsageLimitExceeded):
                usage_limit.check_and_record()

    def test_database_errors_propagate(self) -> None:
        with patch("order_generator.d1.batch", side_effect=d1.D1Error("no database")):
            with self.assertRaises(d1.D1Error):
                usage_limit.check_and_record()

    def test_missing_table_is_created_then_retried(self) -> None:
        with (
            patch(
                "order_generator.d1.batch",
                side_effect=[
                    d1.D1Error("no such table: api_usage: SQLITE_ERROR"),
                    batch_returning([[1]]),
                ],
            ),
            patch("order_generator.d1.query") as query,
        ):
            usage_limit.check_and_record()  # does not raise

        query.assert_called_once_with(usage_limit.CREATE_TABLE_SQL)

    def test_limits_are_passed_to_the_query(self) -> None:
        with patch(
            "order_generator.d1.batch", return_value=batch_returning([[1]])
        ) as batch:
            usage_limit.check_and_record()

        statements = batch.call_args[0][0]
        _sql, params = statements[-1]
        self.assertEqual(params, [usage_limit.HOURLY_LIMIT, usage_limit.DAILY_LIMIT])


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
    os.getenv("CF_API_TOKEN"), "needs a live database; no model calls involved"
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
        d1.query(
            "DELETE FROM api_usage WHERE rowid = (SELECT max(rowid) FROM api_usage)"
        )


if __name__ == "__main__":
    unittest.main()
