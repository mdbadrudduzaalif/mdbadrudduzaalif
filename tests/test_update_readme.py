import unittest
import datetime
from update_readme import calculate_streaks_stats, render_progress_bar

class TestUpdateReadme(unittest.TestCase):

    def test_calculate_streaks_stats(self):
        today_str = (datetime.datetime.now(datetime.timezone.utc)).date().strftime("%Y-%m-%d")
        yesterday_str = ((datetime.datetime.now(datetime.timezone.utc)).date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        log_entries = [
            {"topic": "SQL", "date": "2024-06-20"},
            {"topic": "SQL", "date": "2024-06-21"},
            {"topic": "SQL", "date": "2024-06-25"},
            {"topic": "Python", "date": today_str},
            {"topic": "Python", "date": yesterday_str},
            {"topic": "Python", "date": ((datetime.datetime.now(datetime.timezone.utc)).date() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")}
        ]

        stats = calculate_streaks_stats(log_entries)

        # Test SQL (gap in dates)
        self.assertEqual(stats["SQL"]["longest"], 2)
        self.assertEqual(stats["SQL"]["current"], 0)

        # Test Python (active streak)
        self.assertEqual(stats["Python"]["longest"], 3)
        self.assertEqual(stats["Python"]["current"], 3)

        # Test empty
        stats_empty = calculate_streaks_stats([])
        self.assertEqual(stats_empty, {})

        # Test missing topic or date
        stats_invalid = calculate_streaks_stats([{"date": "2024-06-20"}, {"topic": "SQL"}, {"topic": "SQL", "date": "invalid"}])
        self.assertEqual(stats_invalid, {})

    def test_render_progress_bar(self):
        # 50%
        self.assertEqual(render_progress_bar(5, 10, length=10), "`█████░░░░░ 50%`")

        # 0 total
        self.assertEqual(render_progress_bar(0, 0, length=10), "`░░░░░░░░░░ 0%`")

        # 100%
        self.assertEqual(render_progress_bar(10, 10, length=10), "`██████████ 100%`")

        # 33%
        self.assertEqual(render_progress_bar(1, 3, length=10), "`███░░░░░░░ 33%`")

if __name__ == '__main__':
    unittest.main()
