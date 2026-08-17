from __future__ import annotations

import unittest

from aurora_chaser.app import render_dashboard


class DashboardRenderTests(unittest.TestCase):
    def test_dashboard_explains_fairbanks_kp_four(self) -> None:
        html = render_dashboard([], [])
        self.assertIn("Kp 4 can be meaningful", html)
        self.assertIn("Fetch Fresh Data", html)


if __name__ == "__main__":
    unittest.main()

