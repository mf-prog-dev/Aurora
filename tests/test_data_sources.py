from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aurora_chaser import data_sources


class CacheTests(unittest.TestCase):
    def test_force_refresh_bypasses_cached_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original_path = data_sources.DB_PATH
            data_sources.DB_PATH = Path(temp_dir) / "cache.sqlite3"
            calls = {"count": 0}

            def fetcher() -> dict[str, int]:
                calls["count"] += 1
                return {"count": calls["count"]}

            try:
                first, first_status = data_sources.cached_json("demo", fetcher)
                second, second_status = data_sources.cached_json("demo", fetcher)
                third, third_status = data_sources.cached_json("demo", fetcher, force_refresh=True)
            finally:
                data_sources.DB_PATH = original_path

        self.assertEqual(first, {"count": 1})
        self.assertEqual(second, {"count": 1})
        self.assertEqual(third, {"count": 2})
        self.assertEqual(calls["count"], 2)
        self.assertIn("Fetched live", first_status.message)
        self.assertIn("Loaded from local cache", second_status.message)
        self.assertIn("manual refresh", third_status.message)


if __name__ == "__main__":
    unittest.main()

