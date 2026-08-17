from __future__ import annotations

import unittest
from datetime import date

from aurora_chaser.time_windows import build_aurora_night, moon_illumination_percent


class TimeWindowTests(unittest.TestCase):
    def test_winter_night_has_darkness(self) -> None:
        night = build_aurora_night(date(2026, 1, 15))
        self.assertGreater(night.dark_hours, 4)
        self.assertEqual(night.start_local.tzinfo.key, "America/Anchorage")
        self.assertEqual(night.start_utc.tzinfo.key, "UTC")

    def test_near_solstice_has_no_astronomical_darkness(self) -> None:
        night = build_aurora_night(date(2026, 6, 21))
        self.assertEqual(night.dark_hours, 0)

    def test_moon_illumination_range(self) -> None:
        illumination = moon_illumination_percent(date(2026, 1, 15))
        self.assertGreaterEqual(illumination, 0)
        self.assertLessEqual(illumination, 100)


if __name__ == "__main__":
    unittest.main()

