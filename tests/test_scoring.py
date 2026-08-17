from __future__ import annotations

import unittest
from datetime import date, timedelta

from aurora_chaser.config import UTC
from aurora_chaser.models import HourlyWeather, KpRecord
from aurora_chaser.scoring import assess_night, kp_for_hour, score_aurora
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

    def test_kp_four_is_meaningful_at_fairbanks(self) -> None:
        night = build_aurora_night(date(2026, 1, 15))
        weather = [
            HourlyWeather(window.start_utc + timedelta(hours=1), 5, 0, 5)
            for window in night.dark_windows_utc
        ]
        kp = [KpRecord(night.start_utc + timedelta(hours=3), 4, "test")]
        result = assess_night(night, weather, kp, now_utc=night.start_utc - timedelta(days=1))
        self.assertGreaterEqual(score_aurora(4), 60)
        self.assertFalse(any("Kp signal" in blocker for blocker in result.blockers))

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

    def test_no_darkness_gets_seasonal_note(self) -> None:
        night = build_aurora_night(date(2026, 6, 21))
        weather = [HourlyWeather(night.start_utc + timedelta(hours=1), 5, 0, 50)]
        kp = [KpRecord(night.start_utc + timedelta(hours=1), 7, "test")]
        result = assess_night(night, weather, kp, now_utc=night.start_utc)
        self.assertIsNotNone(result.seasonal_note)
        self.assertEqual(result.recommendation, "Skip")

    def test_hourly_details_include_weather_and_darkness(self) -> None:
        night = build_aurora_night(date(2026, 1, 15))
        weather = [
            HourlyWeather(night.start_utc + timedelta(hours=hour), 10 + hour, 0, 5)
            for hour in range(3)
        ]
        kp = [KpRecord(night.start_utc, 6, "test")]
        result = assess_night(night, weather, kp, now_utc=night.start_utc)
        self.assertEqual(len(result.hourly_details), 3)
        self.assertEqual(result.hourly_details[0].kp, 6)
        self.assertIsInstance(result.hourly_details[0].is_dark, bool)

    def test_kp_for_hour_uses_three_hour_block(self) -> None:
        moment = build_aurora_night(date(2026, 1, 15)).start_utc
        records = [KpRecord(moment, 5, "test")]
        self.assertEqual(kp_for_hour(moment + timedelta(hours=2), records), 5)
        self.assertIsNone(kp_for_hour(moment + timedelta(hours=4), records))

    def test_assessment_lists_overlapping_kp_blocks(self) -> None:
        night = build_aurora_night(date(2026, 1, 15))
        weather = [HourlyWeather(night.start_utc + timedelta(hours=1), 5, 0, 5)]
        kp = [
            KpRecord(night.start_utc - timedelta(hours=3), 3, "test"),
            KpRecord(night.start_utc, 4, "test"),
            KpRecord(night.end_utc, 5, "test"),
        ]
        result = assess_night(night, weather, kp, now_utc=night.start_utc)
        self.assertEqual(len(result.kp_blocks), 1)
        self.assertIn("UTC", result.kp_blocks[0].utc_label)


if __name__ == "__main__":
    unittest.main()
