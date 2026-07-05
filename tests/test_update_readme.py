import unittest
import datetime
import os
from unittest.mock import patch
import json
import urllib.error
from update_readme import (
    _calculate_longest_streak,
    _calculate_current_streak,
    render_progress_bar,
    _parse_log_dates,
    calculate_streaks_stats,
    render_streaks_md,
    _fetch_github_api
)

class TestUpdateReadme(unittest.TestCase):
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
        self.assertEqual(render_progress_bar(-5, 10), "`░░░░░░░░░░ 0%`")


    def test_parse_log_dates(self):
        log_entries = [
            {"date": "2023-01-01", "topic": "SQL"},
            {"date": "2023-01-02", "topic": "SQL"},
            {"date": "2023-01-02", "topic": "C#"},
            {"date": "invalid-date", "topic": "SQL"},
            {"topic": "SQL"}  # missing date
        ]
        parsed = _parse_log_dates(log_entries)
        self.assertIn("SQL", parsed)
        self.assertIn("C#", parsed)
        self.assertEqual(len(parsed["SQL"]), 2)
        self.assertEqual(len(parsed["C#"]), 1)

    def test_parse_log_dates_invalid_input(self):
        self.assertEqual(_parse_log_dates(None), {})
        self.assertEqual(_parse_log_dates("not a list"), {})
        self.assertEqual(_parse_log_dates(["not a dict"]), {})

    @patch('update_readme._calculate_current_streak')
    @patch('update_readme._calculate_longest_streak')
    def test_calculate_streaks_stats(self, mock_longest, mock_current):
        mock_current.return_value = 2
        mock_longest.return_value = 5
        log_entries = [
            {"date": "2023-01-01", "topic": "SQL"},
        ]
        stats = calculate_streaks_stats(log_entries)
        self.assertIn("SQL", stats)
        self.assertEqual(stats["SQL"]["current"], 2)
        self.assertEqual(stats["SQL"]["longest"], 5)

    def test_render_streaks_md(self):
        stats = {
            "SQL": {"current": 2, "longest": 5},
            "C#": {"current": 0, "longest": 1}
        }
        md = render_streaks_md(stats)
        self.assertIn("- **SQL**: 🔥 2 days", md)
        self.assertIn("- **C#**: ❄️ 0 days", md)
        self.assertIn("- **SQL**: 5 days", md)
        self.assertIn("- **C#**: 1 day", md)

    def test_render_streaks_md_empty(self):
        self.assertEqual(render_streaks_md({}), "No active streaks.")

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_success(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps([{"id": 1}]).encode()
        data, error = _fetch_github_api("http://test.com")
        self.assertIsNone(error)
        self.assertEqual(data, [{"id": 1}])

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_api_error(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps({"message": "Not Found"}).encode()
        data, error = _fetch_github_api("http://test.com")
        self.assertIsNone(data)
        self.assertEqual(error, "*(API Error: Not Found)*")

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError("http://test.com", 404, "Not Found", {}, None)
        data, error = _fetch_github_api("http://test.com")
        self.assertIsNone(data)
        self.assertIn("Failed API request", error)


if __name__ == "__main__":
    unittest.main()
