"""Tests for update_readme.py."""
import unittest
from unittest.mock import patch, MagicMock
import datetime
import os
import json
import urllib.error
from update_readme import (
    _calculate_longest_streak,
    _calculate_current_streak,
    render_progress_bar,
    process_learning_journey,
    process_project_portfolio,
    _extract_commits,
    _fetch_github_api,
    update_block
)


class TestUpdateReadme(unittest.TestCase):
    """Test cases for update_readme.py."""

    def test_calculate_current_streak_head(self):
        """Test calculate current streak head."""
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
        self.assertEqual(
            _calculate_current_streak({two_days_ago, yesterday}), 2)
        self.assertEqual(
            _calculate_current_streak(
                {three_days_ago, two_days_ago, yesterday, today}), 4)

        if "TZ_OFFSET_HOURS" in os.environ:
            del os.environ["TZ_OFFSET_HOURS"]

    def test_longest_streak(self):
        """Test longest streak."""
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
        """Test current streak."""
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
        """Test current streak timezone."""
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
        """Test render progress bar."""
        self.assertEqual(render_progress_bar(0, 0), "`░░░░░░░░░░ 0%`")
        self.assertEqual(render_progress_bar(0, 10), "`░░░░░░░░░░ 0%`")
        self.assertEqual(render_progress_bar(5, 10), "`█████░░░░░ 50%`")
        self.assertEqual(render_progress_bar(10, 10), "`██████████ 100%`")
        self.assertEqual(render_progress_bar(3, 10), "`███░░░░░░░ 30%`")

    def test_longest_streak_with_missing_dates(self):
        """Test longest streak with missing dates."""
        dates_with_gap = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 3),
        ]
        self.assertEqual(_calculate_longest_streak(dates_with_gap), 1)

    def test_longest_streak_all_consecutive(self):
        """Test longest streak all consecutive."""
        dates_consecutive = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 2),
            datetime.date(2023, 1, 3),
        ]
        self.assertEqual(_calculate_longest_streak(dates_consecutive), 3)

    def test_longest_streak_duplicate_dates(self):
        """Test longest streak duplicate dates."""
        dates_duplicate = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 2),
        ]
        self.assertEqual(_calculate_longest_streak(dates_duplicate), 2)

    def test_render_progress_bar_edge_cases(self):
        """Test render progress bar edge cases."""
        # Test edge cases
        self.assertEqual(render_progress_bar(15, 10), "`██████████ 100%`")

    def test_process_learning_journey(self):
        """Test process learning journey."""
        skills = {
            "SQL": {
                "completed": ["SELECT"],
                "in_progress": ["JOIN"],
                "planned": ["Trigger"]
            }
        }
        prog, path = process_learning_journey(skills)
        self.assertIn("SQL", prog)
        self.assertIn("SELECT", path)
        self.assertIn("JOIN", path)
        self.assertIn("Trigger", path)

    def test_process_project_portfolio(self):
        """Test process project portfolio."""
        projects = {
            "TestProject": {
                "features": [{"name": "A", "completed": True},
                             {"name": "B", "completed": False}],
                "emoji": "🧪"
            }
        }
        res = process_project_portfolio(projects)
        self.assertIn("TestProject", res)
        self.assertIn("🧪", res)

    def test_extract_commits(self):
        """Test extract commits."""
        events = [
            {
                "type": "PushEvent",
                "repo": {"name": "mdbadrudduzaalif/test-repo"},
                "payload": {
                    "commits": [
                        {"message": "feat: add something",
                         "sha": "1234567890abcdef"}
                    ]
                }
            }
        ]
        res = _extract_commits(events)
        self.assertTrue(len(res) == 1)
        self.assertIn("test-repo", res[0])
        self.assertIn("feat: add something", res[0])
        self.assertIn("1234567", res[0])

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_success(self, mock_urlopen):
        """Test fetch github API success."""

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([{"id": 1}])\
            .encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = _fetch_github_api("http://test.com")
        self.assertEqual(res, [{"id": 1}])

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_error(self, mock_urlopen):
        """Test fetch github API error."""

        mock_urlopen.side_effect = urllib.error.URLError("test error")
        res = _fetch_github_api("http://test.com")
        self.assertTrue(res.startswith("*(Failed API request:"))

    def test_update_block(self):
        """Test update block."""
        content = "hello\n<!-- START_TEST -->\nold "
        content += "value\n<!-- END_TEST -->\nworld"
        res = update_block(content, "TEST", "new value")
        self.assertIn("new value", res)
        self.assertNotIn("old value", res)


if __name__ == "__main__":
    unittest.main()
