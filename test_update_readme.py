import datetime
from update_readme import calculate_streaks_stats

def test_calculate_streaks_stats():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    day_before_yesterday = today - datetime.timedelta(days=2)

    log_entries = [
        {"topic": "A", "date": "2023-10-01"},
        {"topic": "A", "date": "2023-10-02"},
        {"topic": "A", "date": "2023-10-04"},
        {"topic": "B", "date": str(today)},
        {"topic": "B", "date": str(yesterday)},
        {"topic": "C", "date": str(yesterday)},
        {"topic": "C", "date": str(day_before_yesterday)},
        {"topic": "D", "date": "invalid-date"},
    ]

    stats = calculate_streaks_stats(log_entries)

    assert stats["A"]["longest"] == 2
    assert stats["A"]["current"] == 0

    assert stats["B"]["longest"] == 2
    assert stats["B"]["current"] == 2

    assert stats["C"]["longest"] == 2
    assert stats["C"]["current"] == 2 # Yesterday and day before makes current 2

    assert "D" not in stats
