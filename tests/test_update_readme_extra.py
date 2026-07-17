"""Extra tests for update_readme.py."""
import unittest
# pylint: disable=protected-access,import-outside-toplevel,line-too-long
from unittest.mock import patch, MagicMock
from update_readme import _fetch_github_api, main

class TestUpdateReadmeExtra(unittest.TestCase):
    """Test Update Readme Extra cases."""
    @patch('urllib.request.urlopen')
    def test_fetch_github_api_http_error(self, mock_urlopen):
        """Test fetch github api http error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError("http://test", 404, "Not Found", {}, None)
        res = _fetch_github_api("http://test")
        self.assertEqual(res, "*(Failed API request: HTTP Error 404: Not Found)*")

    @patch('update_readme.os.environ.get')
    @patch('update_readme.load_yaml')
    @patch('update_readme.fetch_recent_commits')
    @patch('update_readme.fetch_open_tasks')
    @patch('builtins.open')
    @patch('builtins.print')
    # pylint: disable=too-many-arguments,too-many-positional-arguments,unused-argument
    def test_main_not_found_old_content(self, mock_print, mock_open, mock_tasks, mock_commits, mock_yaml, mock_env):
        """Test main not found old content."""
        mock_env.return_value = "TOKEN"
        mock_yaml.side_effect = [
            {"log": [{"date": "2023-01-01", "topic": "A"}]},
            {"projects": {}},
            {"agents": []}
        ]
        mock_commits.return_value = ""
        mock_tasks.return_value = ""

        # We need builtins.open to throw FileNotFoundError on the second read
        # Let's mock a sequence
        mock_file = MagicMock()
        mock_file.read.return_value = "content"
        mock_file.__enter__.return_value = mock_file

        # the read calls are 1. read README, 2. read README inside try
        def open_side_effect(path, mode="r", **kwargs):
            if path.endswith("README.md"):
                if mode == 'w':
                    return mock_file
                if not hasattr(open_side_effect, 'called'):
                    open_side_effect.called = True
                    return mock_file
                raise FileNotFoundError
            return mock_file  # pragma: no cover

        mock_open.side_effect = open_side_effect
        main()

    @patch('update_readme.os.environ.get')
    @patch('update_readme.load_yaml')
    @patch('update_readme.fetch_recent_commits')
    @patch('update_readme.fetch_open_tasks')
    @patch('builtins.open')
    @patch('builtins.print')
    # pylint: disable=too-many-arguments,too-many-positional-arguments,unused-argument
    def test_main_no_rewrite_needed(self, mock_print, mock_open, mock_tasks, mock_commits, mock_yaml, mock_env):
        """Test main no rewrite needed."""
        mock_env.return_value = "TOKEN"
        mock_yaml.side_effect = [
            {"log": [{"date": "2023-01-01", "topic": "A"}]},
            {"projects": {}},
            {"agents": []}
        ]
        mock_commits.return_value = ""
        mock_tasks.return_value = ""

        # The content needs to match the new_content. We can just mock the write check by ensuring old_content == content
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        # To make old_content == content we have to see what new content is produced.
        # Let's just patch update_block to return "SAME" and the file read to return "SAME"
        with patch('update_readme.update_block') as mock_block:
            mock_block.return_value = "SAME"
            mock_file.read.return_value = "SAME"
            mock_open.return_value = mock_file
            main()
            mock_print.assert_called_with("README content is already up-to-date. No rewrite needed.")


    @patch('update_readme._parse_log_dates')
    def test_calculate_streaks_stats_empty_set(self, mock_parse):
        """Test calculate streaks stats empty set."""
        mock_parse.return_value = {"A": set()}
        stats = __import__('update_readme').calculate_streaks_stats([])
        self.assertEqual(stats["A"]["longest"], 0)
        self.assertEqual(stats["A"]["current"], 0)

    @patch('update_readme.os.environ.get')
    def test_fetch_github_api_with_token(self, mock_env):
        """Test fetch github api with token."""
        mock_env.return_value = "TOKEN"
        # We need to test line 251, so we mock urlopen to just return something
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b'{"key": "value"}'
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            __import__('update_readme')._fetch_github_api("http://test")

    def test_main_with_agent_inactive(self):
        """Test main with agent inactive."""
        with patch('update_readme.os.environ.get') as mock_env, \
             patch('update_readme.load_yaml') as mock_yaml, \
             patch('update_readme.fetch_recent_commits') as mock_commits, \
             patch('update_readme.fetch_open_tasks') as mock_tasks, \
             patch('builtins.open') as mock_open, \
             patch('builtins.print') as _mock_print:
            mock_env.return_value = "TOKEN"
            mock_yaml.side_effect = [
                {"log": [{"date": "2023-01-01", "topic": "A"}]},
                {"projects": {}},
                {"agents": [{"name": "A", "status": "Inactive", "purpose": "T"}]}
            ]
            mock_commits.return_value = ""
            mock_tasks.return_value = ""
            mock_file = MagicMock()
            mock_file.read.return_value = "SAME"
            mock_file.__enter__.return_value = mock_file
            mock_open.return_value = mock_file
            __import__('update_readme').main()

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
