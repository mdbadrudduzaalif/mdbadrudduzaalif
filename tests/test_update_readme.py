import unittest
import datetime
import os
from update_readme import _calculate_longest_streak, _calculate_current_streak, render_progress_bar

class TestUpdateReadme(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("TZ_OFFSET_HOURS", None)

    def test_longest_streak(self):
        dates = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 2),
            datetime.date(2023, 1, 4),
            datetime.date(2023, 1, 5),
            datetime.date(2023, 1, 6),
        ]
        self.assertEqual(_calculate_longest_streak(dates), 3)
        self.assertEqual(_calculate_longest_streak([]), 0)
        self.assertEqual(_calculate_longest_streak([datetime.date(2023, 1, 1)]), 1)

    def test_calculate_current_streak(self):
        os.environ["TZ_OFFSET_HOURS"] = "6"
        tz_offset = datetime.timezone(datetime.timedelta(hours=6))
        today = datetime.datetime.now(tz_offset).date()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)
        three_days_ago = today - datetime.timedelta(days=3)

        self.assertEqual(_calculate_current_streak(set()), 0)
        self.assertEqual(_calculate_current_streak({two_days_ago}), 0)
        self.assertEqual(_calculate_current_streak({yesterday}), 1)
        self.assertEqual(_calculate_current_streak({today}), 1)
        self.assertEqual(_calculate_current_streak({yesterday, today}), 2)
        self.assertEqual(_calculate_current_streak({two_days_ago, yesterday}), 2)
        self.assertEqual(_calculate_current_streak({three_days_ago, two_days_ago, yesterday, today}), 4)

    def test_render_progress_bar(self):
        self.assertEqual(render_progress_bar(0, 0), "`░░░░░░░░░░ 0%`")
        self.assertEqual(render_progress_bar(0, 10), "`░░░░░░░░░░ 0%`")
        self.assertEqual(render_progress_bar(5, 10), "`█████░░░░░ 50%`")
        self.assertEqual(render_progress_bar(10, 10), "`██████████ 100%`")
        self.assertEqual(render_progress_bar(3, 10), "`███░░░░░░░ 30%`")

if __name__ == "__main__":
    unittest.main()
