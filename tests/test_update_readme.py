import unittest
import datetime
import os
from update_readme import _calculate_longest_streak, _calculate_current_streak, render_progress_bar, _get_today, load_yaml

class TestUpdateReadme(unittest.TestCase):
    def test_load_yaml_missing(self):
        # Should return empty dict for non-existent file
        self.assertEqual(load_yaml("non_existent_file.yml"), {})

    def test_get_today(self):
        # Test without TZ_OFFSET_HOURS
        if "TZ_OFFSET_HOURS" in os.environ:
            del os.environ["TZ_OFFSET_HOURS"]
        self.assertEqual(_get_today(), datetime.date.today())

        # Test with TZ_OFFSET_HOURS
        os.environ["TZ_OFFSET_HOURS"] = "6"
        tz_offset = datetime.timezone(datetime.timedelta(hours=6))
        expected_today = datetime.datetime.now(tz_offset).date()
        self.assertEqual(_get_today(), expected_today)

        # Test with invalid TZ_OFFSET_HOURS
        os.environ["TZ_OFFSET_HOURS"] = "invalid"
        self.assertEqual(_get_today(), datetime.date.today())

        # Cleanup
        if "TZ_OFFSET_HOURS" in os.environ:
            del os.environ["TZ_OFFSET_HOURS"]

    def test_calculate_current_streak_head(self):
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

        if "TZ_OFFSET_HOURS" in os.environ:
            del os.environ["TZ_OFFSET_HOURS"]

    def test_longest_streak(self):
        dates = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 2),
            datetime.date(2023, 1, 4),
            datetime.date(2023, 1, 5),
            datetime.date(2023, 1, 6),
        ]
        self.assertEqual(_calculate_longest_streak(dates), 3)

        dates_empty = []
        self.assertEqual(_calculate_longest_streak(dates_empty), 0)

        dates_single = [datetime.date(2023, 1, 1)]
        self.assertEqual(_calculate_longest_streak(dates_single), 1)

    def test_current_streak(self):
        if "TZ_OFFSET_HOURS" in os.environ:
            del os.environ["TZ_OFFSET_HOURS"]

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)

        # Test current streak with today
        dates = {today, yesterday, two_days_ago}
        self.assertEqual(_calculate_current_streak(dates), 3)

        # Test current streak ending yesterday
        dates_yesterday = {yesterday, two_days_ago}
        self.assertEqual(_calculate_current_streak(dates_yesterday), 2)

        # Test broken streak
        dates_broken = {two_days_ago}
        self.assertEqual(_calculate_current_streak(dates_broken), 0)

        # Test empty
        self.assertEqual(_calculate_current_streak(set()), 0)

    def test_current_streak_timezone(self):
        os.environ["TZ_OFFSET_HOURS"] = "6"
        tz = datetime.timezone(datetime.timedelta(hours=6))
        today = datetime.datetime.now(tz).date()
        yesterday = today - datetime.timedelta(days=1)

        dates = {today, yesterday}
        self.assertEqual(_calculate_current_streak(dates), 2)
        
        # Clean up
        if "TZ_OFFSET_HOURS" in os.environ:
            del os.environ["TZ_OFFSET_HOURS"]

    def test_render_progress_bar(self):
        self.assertEqual(render_progress_bar(0, 0), "`░░░░░░░░░░ 0%`")
        self.assertEqual(render_progress_bar(0, 10), "`░░░░░░░░░░ 0%`")
        self.assertEqual(render_progress_bar(5, 10), "`█████░░░░░ 50%`")
        self.assertEqual(render_progress_bar(10, 10), "`██████████ 100%`")
        self.assertEqual(render_progress_bar(3, 10), "`███░░░░░░░ 30%`")


    def test_longest_streak_with_missing_dates(self):
        dates_with_gap = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 3),
        ]
        self.assertEqual(_calculate_longest_streak(dates_with_gap), 1)

    def test_longest_streak_all_consecutive(self):
        dates_consecutive = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 2),
            datetime.date(2023, 1, 3),
        ]
        self.assertEqual(_calculate_longest_streak(dates_consecutive), 3)

    def test_longest_streak_duplicate_dates(self):
        dates_duplicate = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 2),
        ]
        self.assertEqual(_calculate_longest_streak(dates_duplicate), 2)

    def test_render_progress_bar_edge_cases(self):
        # Already tests 0,0 and 0,10. Let's test negative maybe? Or completed > total
        self.assertEqual(render_progress_bar(15, 10), "`██████████ 100%`")


if __name__ == "__main__":
    unittest.main()
