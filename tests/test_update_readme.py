"""Tests for update_readme.py."""
import unittest
import datetime
import os
from unittest.mock import patch, mock_open, MagicMock
from update_readme import (
    _calculate_longest_streak,
    _calculate_current_streak,
    render_progress_bar,
    load_yaml,
    process_learning_journey,
    process_project_portfolio,
    _extract_commits,
    _fetch_github_api,
    fetch_recent_commits,
    fetch_open_tasks,
    update_block,
    main,
    calculate_streaks_stats,
    render_streaks_md,
    _parse_log_dates
)


class TestUpdateReadme(unittest.TestCase):
    # pylint: disable=too-many-public-methods
    """Test suite for update_readme."""

    def test_calculate_current_streak_head(self):
        """Test streak head."""
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
        self.assertEqual(_calculate_current_streak(
            {three_days_ago, two_days_ago, yesterday, today}), 4)

        if "TZ_OFFSET_HOURS" in os.environ:
            del os.environ["TZ_OFFSET_HOURS"]

    def test_calculate_current_streak_invalid_tz(self):
        """Test with invalid tz string."""
        os.environ["TZ_OFFSET_HOURS"] = "invalid"
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        self.assertEqual(_calculate_current_streak({today, yesterday}), 2)
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
        # test custom length
        self.assertEqual(render_progress_bar(0, 0, length=5), "`░░░░░ 0%`")

    def test_longest_streak_with_missing_dates(self):
        """Test longest streak missing dates."""
        dates_with_gap = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 1, 3),
        ]
        self.assertEqual(_calculate_longest_streak(dates_with_gap), 1)

    def test_longest_streak_all_consecutive(self):
        """Test longest streak consecutive."""
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
        """Test render progress bar edge."""
        # Edge case test
        self.assertEqual(render_progress_bar(15, 10), "`██████████ 100%`")

    @patch('builtins.open', new_callable=mock_open, read_data="key: value")
    def test_load_yaml_success(self, _mock_file):
        """Test load_yaml success."""
        data = load_yaml("test.yml")
        self.assertEqual(data, {"key": "value"})

    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('builtins.print')
    def test_load_yaml_not_found(self, mock_print, _mock_file):
        """Test load_yaml file not found."""
        data = load_yaml("nonexistent.yml")
        self.assertEqual(data, {})
        mock_print.assert_called_with(
            "Warning: File not found at nonexistent.yml")

    @patch('builtins.open', new_callable=mock_open, read_data="[")
    @patch('builtins.print')
    def test_load_yaml_error(self, mock_print, _mock_file):
        """Test load_yaml parse error."""
        data = load_yaml("bad.yml")
        self.assertEqual(data, {})
        mock_print.assert_called()

    def test_parse_log_dates(self):
        """Test parsing log dates."""
        entries = [
            {"date": "2023-01-01", "topic": "A"},
            {"date": "2023-01-01", "topic": "B"},
            {"date": "invalid", "topic": "A"},
            {"topic": "C"},
        ]
        dates = _parse_log_dates(entries)
        self.assertEqual(len(dates), 2)
        self.assertIn(datetime.date(2023, 1, 1), dates["A"])

    def test_calculate_streaks_stats(self):
        """Test calculating stats."""
        entries = [
            {"date": "2023-01-01", "topic": "A"},
            {"date": "invalid-date", "topic": "B"}
        ]
        stats = calculate_streaks_stats(entries)
        self.assertEqual(stats["A"]["longest"], 1)
        self.assertEqual(stats["A"]["current"], 0)
        self.assertIn("B", stats)
        self.assertEqual(stats["B"]["longest"], 0)
        self.assertEqual(stats["B"]["current"], 0)

    def test_render_streaks_md(self):
        """Test rendering streaks."""
        self.assertEqual(render_streaks_md({}), "No active streaks.")
        stats = {
            "A": {
                "current": 1, "longest": 2}, "B": {
                "current": 0, "longest": 1}}
        md = render_streaks_md(stats)
        self.assertIn("**A**: 🔥 1 day", md)
        self.assertIn("**B**: ❄️ 0 days", md)
        self.assertIn("**A**: 2 days", md)

    def test_process_learning_journey(self):
        """Test processing learning journey."""
        skills = {
            "SQL": {"completed": ["a"], "in_progress": ["b"],
                    "planned": ["c"]},
            "Empty": []
        }
        prog, path = process_learning_journey(skills)
        self.assertIn("- **SQL**:", prog)
        self.assertIn("✅ a", path)
        self.assertIn("⏳ b", path)
        self.assertIn("❌ c", path)
        self.assertIn("- **Empty**:", prog)

    def test_process_project_portfolio(self):
        """Test processing project portfolio."""
        projects = {
            "Proj1": {
                "features": [{"completed": True}, {"completed": False}],
                "focus": ["focus 1"]
            }
        }
        md = process_project_portfolio(projects)
        self.assertIn("### 🚀 Proj1", md)
        self.assertIn("Modules Implemented**: 1", md)
        self.assertIn("Major Features Remaining**: 1", md)
        self.assertIn("- focus 1", md)

    def test_extract_commits(self):
        """Test extracting commits."""
        events = [
            {"type": "PushEvent",
             "repo": {"name": "test/repo"},
             "payload": {"commits": [{"message": "msg1",
                                      "sha": "1234567890"},
                                     {"message": "Merge pull request",
                                      "sha": "abcdef"}]}},
            {"type": "OtherEvent"}
        ]
        commits = _extract_commits(events)
        self.assertEqual(len(commits), 1)
        self.assertIn("msg1", commits[0])

    def test_extract_commits_limit(self):
        """Test extracting commits limit."""
        events = [
            {"type": "PushEvent",
             "repo": {"name": "test/repo"},
             "payload": {"commits": [{"message": f"msg{i}",
                                      "sha": f"sha{i}"} for i in range(10)]}},
        ]
        commits = _extract_commits(events)
        self.assertEqual(len(commits), 5)

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_success(self, mock_urlopen):
        """Test fetch API success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"key": "value"}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = _fetch_github_api("http://test")
        self.assertEqual(res, {"key": "value"})

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_error_response(self, mock_urlopen):
        """Test fetch API error dict."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": "API rate limit"}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = _fetch_github_api("http://test")
        self.assertEqual(res, "*(API Error: API rate limit)*")

    @patch('urllib.request.urlopen')
    @patch('os.environ.get')
    def test_fetch_github_api_success_with_token(self, mock_env, mock_urlopen):
        """Test fetch API with token."""
        mock_env.return_value = "fake-token"
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"success": true}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        res = _fetch_github_api("http://test")
        self.assertEqual(res, {"success": True})

    @patch('urllib.request.urlopen', side_effect=Exception("HTTP error"))
    def test_fetch_github_api_exception(self, mock_urlopen):
        """Test fetch API exception."""
        # Using a generic exception since urllib is complex to mock here
        # Actually _fetch_github_api catches urllib.error.URLError, so let's
        # mock that
        import urllib.error  # pylint: disable=import-outside-toplevel
        mock_urlopen.side_effect = urllib.error.URLError("Error")
        res = _fetch_github_api("http://test")
        self.assertEqual(res, "*(Failed API request: <urlopen error Error>)*")

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_http_error(self, mock_urlopen):
        """Test fetch API HTTPError."""
        import urllib.error  # pylint: disable=import-outside-toplevel
        mock_urlopen.side_effect = urllib.error.HTTPError("http://test", 404, "Not Found", {}, None)
        res = _fetch_github_api("http://test")
        self.assertEqual(res, "*(Failed API request: HTTP Error 404: Not Found)*")

    @patch('urllib.request.urlopen')
    def test_fetch_github_api_json_error(self, mock_urlopen):
        """Test fetch API JSON error."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'not json'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = _fetch_github_api("http://test")
        self.assertTrue(res.startswith("*(Failed to parse JSON"))

    @patch('update_readme._fetch_github_api')
    def test_fetch_recent_commits(self, mock_fetch):
        """Test fetch recent commits."""
        # Error case
        mock_fetch.return_value = "*(Error)*"
        self.assertEqual(fetch_recent_commits(), "*(Error)*")

        # Empty case
        mock_fetch.return_value = []
        self.assertEqual(
            fetch_recent_commits(),
            "No recent public commits found.")

        # Success case
        mock_fetch.return_value = [{"type": "PushEvent", "repo": {
            "name": "r"},
            "payload": {"commits": [{"message": "m", "sha": "s"}]}}]
        self.assertIn("m", fetch_recent_commits())

    @patch('update_readme._fetch_github_api')
    def test_fetch_open_tasks(self, mock_fetch):
        """Test fetch open tasks."""
        # Error case
        mock_fetch.return_value = "*(Error)*"
        self.assertEqual(fetch_open_tasks(), "*(Error)*")

        # Empty case
        mock_fetch.return_value = []
        self.assertIn("No active tasks", fetch_open_tasks())

        # Success case
        mock_fetch.return_value = [{"title": "task1",
                                    "number": 1,
                                    "html_url": "url",
                                    "pull_request": {}},
                                   {"title": "task2",
                                    "number": 2,
                                    "html_url": "url2"}]
        res = fetch_open_tasks()
        self.assertIn("task2", res)
        self.assertNotIn("task1", res)

    @patch('update_readme._fetch_github_api')
    def test_fetch_open_tasks_limit(self, mock_fetch):
        """Test fetch open tasks limit."""
        mock_fetch.return_value = [
            {"title": f"task{i}", "number": i,
             "html_url": f"url{i}"} for i in range(10)]
        res = fetch_open_tasks()
        self.assertEqual(len(res.split('\n')), 5)

    def test_update_block(self):
        """Test update block."""
        content = "before\n<!-- START_TAG -->\nold\n<!-- END_TAG -->\nafter"
        new_content = update_block(content, "TAG", "new")
        self.assertIn("new", new_content)
        self.assertNotIn("old", new_content)

    @patch('update_readme.load_yaml')
    @patch('update_readme.fetch_recent_commits')
    @patch('update_readme.fetch_open_tasks')
    @patch('builtins.open', new_callable=mock_open,
           read_data="<!-- START_PORTFOLIO --><!-- END_PORTFOLIO -->\n"
           "<!-- START_STREAKS --><!-- END_STREAKS -->\n"
           "<!-- START_LEARNING_PROGRESS --><!-- END_LEARNING_PROGRESS -->\n"
           "<!-- START_LEARNING_PATH --><!-- END_LEARNING_PATH -->\n"
           "<!-- START_COMMITS --><!-- END_COMMITS -->\n"
           "<!-- START_TASKS --><!-- END_TASKS -->\n"
           "<!-- START_AGENTS --><!-- END_AGENTS -->\n"
           "<!-- START_REFLECTION --><!-- END_REFLECTION -->")
    @patch('os.environ.get')
    def test_main(self, mock_env, mock_file, mock_fetch_tasks,
                  mock_fetch_commits, mock_load):
        """Test main function."""
        mock_env.return_value = None
        mock_load.return_value = {
            "projects": {},
            "skills": {},
            "log": [{"topic": "A", "date": "2023-10-01"}],
            "agents": [{"name": "Agent1", "status": "Active", "purpose": "Test"},
                       {"name": "Agent2", "status": "Inactive", "purpose": "Test2"}]}
        mock_fetch_commits.return_value = "commits"
        mock_fetch_tasks.return_value = "tasks"

        # Provide different file contents on read to force a rewrite
        mock_read_data = (
            "<!-- START_PORTFOLIO --><!-- END_PORTFOLIO -->\n"
            "<!-- START_STREAKS --><!-- END_STREAKS -->\n"
            "<!-- START_LEARNING_PROGRESS --><!-- END_LEARNING_PROGRESS -->\n"
            "<!-- START_LEARNING_PATH --><!-- END_LEARNING_PATH -->\n"
            "<!-- START_COMMITS --><!-- END_COMMITS -->\n"
            "<!-- START_TASKS --><!-- END_TASKS -->\n"
            "<!-- START_AGENTS --><!-- END_AGENTS -->\n"
            "<!-- START_REFLECTION --><!-- END_REFLECTION -->"
        )
        file_handles = [
            mock_open(read_data=mock_read_data).return_value,
            mock_open(read_data="something old").return_value,
            mock_open().return_value
        ]
        mock_file.side_effect = file_handles

        main()

        # Check that files were written
        file_handles[2].write.assert_called()

    @patch('update_readme.load_yaml')
    @patch('update_readme._fetch_github_api')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.environ.get')
    def test_main_no_change(self, mock_env, mock_file, mock_fetch, mock_load):
        """Test main function no change."""
        mock_env.return_value = None
        mock_load.return_value = {}
        mock_fetch.return_value = []

        # Mock file handling logic precisely to throw FileNotFoundError on the second open call
        # the first call is read README, the second is read old_content
        mock_file_instance = mock_open(read_data="some content").return_value

        def open_side_effect(*args, **kwargs):
            if open_side_effect.call_count == 1:
                open_side_effect.call_count += 1
                raise FileNotFoundError()
            open_side_effect.call_count += 1
            return mock_file_instance

        open_side_effect.call_count = 0
        mock_file.side_effect = open_side_effect

        main()

    @patch('update_readme.load_yaml')
    @patch('update_readme._fetch_github_api')
    @patch('builtins.open')
    @patch('os.environ.get')
    def test_main_no_change_real(self, mock_env, mock_file, mock_fetch, mock_load):
        """Test main function really no change to trigger branch."""
        mock_env.return_value = None
        mock_load.return_value = {}
        mock_fetch.return_value = []

        # we need content == old_content
        # Let's mock a specific content that wouldn't change
        from update_readme import update_block
        test_content = (
            "<!-- START_PORTFOLIO -->\n\n<!-- END_PORTFOLIO -->\n"
            "<!-- START_STREAKS -->\nNo active streaks.\n<!-- END_STREAKS -->\n"
            "<!-- START_LEARNING_PROGRESS -->\n\n<!-- END_LEARNING_PROGRESS -->\n"
            "<!-- START_LEARNING_PATH -->\n\n<!-- END_LEARNING_PATH -->\n"
            "<!-- START_COMMITS -->\nNo recent public commits found.\n<!-- END_COMMITS -->\n"
            "<!-- START_TASKS -->\n*No active tasks from projects. Create a GitHub Issue in this repository to track your next task!*\n<!-- END_TASKS -->\n"
            "<!-- START_AGENTS -->\n\n<!-- END_AGENTS -->\n"
            "<!-- START_REFLECTION -->\n**Completed Today**:\n\n<!-- END_REFLECTION -->"
        )

        mock_file.side_effect = [
            mock_open(read_data=test_content).return_value,
            mock_open(read_data=test_content).return_value,
        ]

        main()

if __name__ == "__main__":
    unittest.main()
