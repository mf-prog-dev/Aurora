from __future__ import annotations

import unittest
from datetime import date, timedelta

from aurora_chaser.config import UTC
from aurora_chaser.models import HourlyWeather, KpRecord
from aurora_chaser.scoring import assess_night
from aurora_chaser.time_windows import build_aurora_night


class ScoringTests(unittest.TestCase):
    def test_clouds_block_go_even_with_strong_kp(self) -> None:
        night = build_aurora_night(date(2026, 1, 15))
        weather = [
            HourlyWeather(window.start_utc + timedelta(hours=1), 90, 10, 10)
            for window in night.dark_windows_utc
        ]
        kp = [KpRecord(night.start_utc + timedelta(hours=3), 7, "test")]
        result = assess_night(night, weather, kp, now_utc=night.start_utc.astimezone(UTC))
        self.assertNotEqual(result.recommendation, "Go")
        self.assertTrue(any("Cloud cover" in blocker for blocker in result.blockers))

    def test_good_near_term_conditions_can_go(self) -> None:
        night = build_aurora_night(date(2026, 1, 15))
        weather = [
            HourlyWeather(window.start_utc + timedelta(hours=1), 5, 0, 5)
            for window in night.dark_windows_utc
        ]
        kp = [KpRecord(night.start_utc + timedelta(hours=3), 7, "test")]
        result = assess_night(night, weather, kp, now_utc=night.start_utc - timedelta(days=1))
        if result.moon_illumination <= 80:
            self.assertEqual(result.recommendation, "Go")

    def test_far_out_forecast_blocks_go(self) -> None:
        night = build_aurora_night(date(2026, 1, 15))
        weather = [
            HourlyWeather(window.start_utc + timedelta(hours=1), 5, 0, 5)
            for window in night.dark_windows_utc
        ]
        kp = [KpRecord(night.start_utc + timedelta(hours=3), 7, "test")]
        result = assess_night(night, weather, kp, now_utc=night.start_utc - timedelta(days=5))
        self.assertNotEqual(result.recommendation, "Go")
        self.assertTrue(any("too far out" in blocker for blocker in result.blockers))


if __name__ == "__main__":
    unittest.main()

