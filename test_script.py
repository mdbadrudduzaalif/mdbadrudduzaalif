import datetime
import os
import sys

def _calculate_current_streak(dates_set):
    """Calculate current streak."""
    tz_offset_hours = os.environ.get("TZ_OFFSET_HOURS")
    if tz_offset_hours is not None:
        try:
            offset = int(tz_offset_hours)
            tz_offset = datetime.timezone(datetime.timedelta(hours=offset))
            today = datetime.datetime.now(tz_offset).date()
        except ValueError:
            # Fallback to local time if invalid value
            today = datetime.date.today()
    else:
        today = datetime.date.today()

    yesterday = today - datetime.timedelta(days=1)
    current = 0

    if today in dates_set:
        start_date = today
    elif yesterday in dates_set:
        start_date = yesterday
    else:
        start_date = None

    if start_date:
        current_date = start_date
        while current_date in dates_set:
            current += 1
            current_date -= datetime.timedelta(days=1)

    return current

print("Testing _calculate_current_streak")
today = datetime.date.today()
print(f"Today is {today}")
print(f"Yesterday is {today - datetime.timedelta(days=1)}")

dates_set = {today, today - datetime.timedelta(days=1)}
print(f"Set: {dates_set}")
print(f"Current streak: {_calculate_current_streak(dates_set)}")
