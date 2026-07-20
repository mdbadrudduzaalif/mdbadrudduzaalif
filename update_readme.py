"""Module to update README.md with learning streaks and project info."""
import datetime
import json
import os
import re
import urllib.request
import urllib.error
from typing import Dict, List, Set, Tuple, Any, Union

import yaml

GITHUB_USERNAME = "mdbadrudduzaalif"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(BASE_DIR, "README.md")
LEARNING_LOG_PATH = os.path.join(BASE_DIR, "data", "learning_log.yml")
PROJECTS_PATH = os.path.join(BASE_DIR, "data", "projects.yml")
AGENTS_PATH = os.path.join(BASE_DIR, "data", "agents.yml")


def load_yaml(path: str) -> Dict[str, Any]:
    """Load YAML file safely."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:  # pragma: no cover
        print(f"Warning: File not found at {path}")
        return {}
    except yaml.YAMLError as e:  # pragma: no cover
        print(f"Warning: Error parsing YAML file at {path}: {e}")
        return {}

# 1. Streak & Longest Streak Calculation


def _parse_log_dates(
    log_entries: List[Dict[str, Any]]
) -> Dict[str, Set[datetime.date]]:
    """Parse log dates."""
    topic_dates = {}
    for entry in log_entries:
        date_str = entry.get("date")
        topic = entry.get("topic")
        if date_str and topic:
            try:
                date_obj = datetime.datetime.strptime(
                    date_str, "%Y-%m-%d").date()
                topic_dates.setdefault(topic, set()).add(date_obj)
            except ValueError:  # pragma: no cover
                continue
    return topic_dates


def _calculate_longest_streak(sorted_dates: List[datetime.date]) -> int:
    """Calculate longest streak."""
    longest = 0
    current_longest = 0
    prev_date = None
    for d in sorted_dates:
        if prev_date is None:
            current_longest = 1
        elif (d - prev_date).days == 1:
            current_longest += 1
        elif (d - prev_date).days > 1:
            longest = max(longest, current_longest)
            current_longest = 1
        prev_date = d
    longest = max(longest, current_longest)
    return longest


def _calculate_current_streak(dates_set: Set[datetime.date]) -> int:
    """Calculate current streak."""
    # Try to get timezone offset from environment, default to local system time if not set  # noqa: E501  # pylint: disable=line-too-long
    # Expected format for TZ_OFFSET_HOURS is an integer, e.g. "6"
    tz_offset_hours = os.environ.get("TZ_OFFSET_HOURS")
    if tz_offset_hours is not None:
        try:
            offset = int(tz_offset_hours)
            tz_offset = datetime.timezone(datetime.timedelta(hours=offset))
            today = datetime.datetime.now(tz_offset).date()
        except ValueError:  # pragma: no cover
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


def calculate_streaks_stats(
    log_entries: List[Dict[str, Any]]
) -> Dict[str, Dict[str, int]]:
    """Calculate streak stats."""
    topic_dates = _parse_log_dates(log_entries)
    stats = {}

    for topic, dates_set in topic_dates.items():
        if not dates_set:  # pragma: no cover
            stats[topic] = {"current": 0, "longest": 0}
            continue

        sorted_dates = sorted(dates_set)
        longest = _calculate_longest_streak(sorted_dates)
        current = _calculate_current_streak(dates_set)

        stats[topic] = {"current": current, "longest": longest}

    return stats


def render_streaks_md(streaks_stats: Dict[str, Dict[str, int]]) -> str:
    """Render streaks MD."""
    if not streaks_stats:
        return "No active streaks."

    sorted_stats = sorted(streaks_stats.items())

    lines = ["**🔥 Active Study Streaks**"]
    for topic, s in sorted_stats:
        emoji = "🔥" if s["current"] > 0 else "❄️"
        lines.append(
            f"- **{topic}**: {emoji} {s['current']} day{'s' if s['current'] != 1 else ''}")  # noqa: E501  # pylint: disable=line-too-long

    lines.append("\n**🏆 Longest Streak**")
    for topic, s in sorted_stats:
        lines.append(
            f"- **{topic}**: {s['longest']} day{'s' if s['longest'] != 1 else ''}")  # noqa: E501

    return "\n".join(lines)

# 2. Render ASCII Progress Bar


def render_progress_bar(completed: int, total: int, length: int = 10) -> str:
    """Render progress bar."""
    if total == 0:
        prog_bar = "░" * length
        return f"`{prog_bar} 0%`"
    completed = min(completed, total)
    percentage = int(completed * 100 / total)
    filled_length = int(length * completed // total)
    prog_bar = "█" * filled_length + "░" * (length - filled_length)
    return f"`{prog_bar} {percentage}%`"

# 3. Learning Progress and Path Logic


def process_learning_journey(skills: Dict[str, Any]) -> Tuple[str, str]:
    """Process learning journey."""
    progress_lines = []
    path_lines = []

    category_icons = {
        "SQL": "🗄️ Database Development (SQL)",
        "React Native": "📱 Mobile Development (React Native)",
        "C#": "💻 C# Development (C#)",
        "Algorithms": "🧠 Algorithms & Data Structures (C++)"
    }

    for topic, sections in skills.items():
        if not isinstance(sections, dict):
            sections = {}
        completed = sections.get("completed", [])
        in_progress = sections.get("in_progress", [])
        planned = sections.get("planned", [])

        total = len(completed) + len(in_progress) + len(planned)
        prog_bar = render_progress_bar(len(completed), total, length=10)
        progress_lines.append(f"- **{topic}**: {prog_bar}")

        topic_header = category_icons.get(topic, f"🛠️ {topic}")
        path_lines.append(f"\n#### {topic_header}")

        for item in completed:
            path_lines.append(f"- ✅ {item}")
        for item in in_progress:
            path_lines.append(f"- ⏳ {item}")
        for item in planned:
            path_lines.append(f"- ❌ {item}")

    return "\n".join(progress_lines), "\n".join(path_lines)

# 4. Project Portfolio Generator


def process_project_portfolio(projects: Dict[str, Any]) -> str:
    """Process project portfolio."""
    lines = []
    for name, data in projects.items():
        features = data.get("features", [])
        completed = sum(1 for f in features if f.get("completed"))
        remaining = len(features) - completed

        emoji = data.get("emoji", "🚀")
        lines.append(f"### {emoji} {name}")
        lines.append(
            f"- **{data.get('label_completed', 'Modules Implemented')}**: {completed}")  # noqa: E501  # pylint: disable=line-too-long
        lines.append(f"- **{data.get('label_remaining', 'Major Features Remaining')}**: {remaining}")  # noqa: E501  # pylint: disable=line-too-long
        lines.append(
            f"- **Current Milestone**: {data.get('milestone', 'MVP')}")
        lines.append("- **Current Focus**:")
        for item in data.get("focus", []):
            lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines)


def _extract_commits(events: List[Dict[str, Any]]) -> List[str]:
    """Extract commits."""
    commits = []
    seen_commits = set()
    for event in events:
        if event.get('type') != 'PushEvent':
            continue
        repo_name = event.get('repo', {}).get('name', '').split('/')[-1]
        for commit in event.get('payload', {}).get('commits', []):
            message = commit.get('message', '').split('\n')[0]
            sha = commit.get('sha', '')[:7]
            if not message or message.startswith(
                    "Merge") or sha in seen_commits:
                continue
            seen_commits.add(sha)
            commits.append(
                f"- **{repo_name}**: {message} ([`{sha}`]"
                f"(https://github.com/{GITHUB_USERNAME}/{repo_name}/commit/{sha}))")  # noqa: E501
            if len(commits) >= 5:
                return commits
    return commits


def _fetch_github_api(
    url: str
) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
    """Fetch github API."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = os.environ.get("GITHUB_TOKEN")
    if token:  # pragma: no cover
        headers['Authorization'] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, dict) and "message" in data:
                return f"*(API Error: {data['message']})*"
            return data
    except json.JSONDecodeError as e:  # pragma: no cover
        return f"*(Failed to parse JSON: {str(e)})*"
    except urllib.error.HTTPError as e:  # pragma: no cover
        return f"*(Failed API request: {str(e)})*"
    except urllib.error.URLError as e:  # pragma: no cover
        return f"*(Failed API request: {str(e)})*"

# 5. Fetch GitHub Commits


def fetch_recent_commits() -> str:
    """Fetch recent commits."""
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/events"
    events = _fetch_github_api(url)
    if isinstance(events, str) and events.startswith("*("):
        return events  # return the error string

    commits = _extract_commits(events)
    if not commits:
        return "No recent public commits found."
    return "\n".join(commits)

# 6. Fetch Open Issues (Tasks)


def fetch_open_tasks() -> str:
    """Fetch open tasks."""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_USERNAME}/issues?state=open"  # noqa: E501  # pylint: disable=line-too-long
    issues = _fetch_github_api(url)
    if isinstance(issues, str) and issues.startswith("*("):
        return issues  # return the error string

    tasks = []
    for issue in issues:
        if 'pull_request' not in issue:
            title = issue.get('title', '')
            number = issue.get('number', '')
            html_url = issue.get('html_url', '')
            tasks.append(f"- [ ] {title} ([#{number}]({html_url}))")
        if len(tasks) >= 5:
            break
    if not tasks:
        return ("*No active tasks from projects. Create a GitHub Issue "
                "in this repository to track your next task!*")
    return "\n".join(tasks)


def update_block(content: str, tag: str, new_value: str) -> str:
    """Update block."""
    start_tag = f"<!-- START_{tag} -->"
    end_tag = f"<!-- END_{tag} -->"
    pattern = re.escape(start_tag) + r"(.*?)" + re.escape(end_tag)
    replacement = f"{start_tag}\n{new_value}\n{end_tag}"
    return re.sub(pattern, lambda m: replacement, content, flags=re.DOTALL)


def main() -> None:
    """Main function."""
    # pylint: disable=too-many-locals
    if not os.environ.get("GITHUB_TOKEN"):  # pragma: no cover
        print("Warning: GITHUB_TOKEN environment variable not found. Rate limiting might occur.")  # noqa: E501  # pylint: disable=line-too-long

    # Load YAML databases
    learning_log = load_yaml(LEARNING_LOG_PATH)
    projects_data = load_yaml(PROJECTS_PATH)
    agents_data = load_yaml(AGENTS_PATH)

    # Process Streaks
    streaks_stats = calculate_streaks_stats(learning_log.get("log", []))
    streaks_md = render_streaks_md(streaks_stats)

    # Process Learning Journey (Trees and Paths)
    skills = learning_log.get("skills", {})
    progress_md, path_md = process_learning_journey(skills)

    # Process Project Portfolio
    projects = projects_data.get("projects", {})
    portfolio_md = process_project_portfolio(projects)

    # Process Agent Lab
    agent_lines = []
    for a in agents_data.get("agents", []):  # pragma: no cover
        emoji = "🟢" if a.get("status") == "Active" else "🟡"
        agent_lines.append(
            f"- **{a.get('name')}** ({emoji} {a.get('status')}): {a.get('purpose')}")  # noqa: E501
    agents_md = "\n".join(agent_lines)

    # Process reflections from dates studied
    today_refl = learning_log.get("log", [])[:3]
    completed_today_lines = []
    for r in today_refl:  # pragma: no cover
        completed_today_lines.append(
            f"- Logged study for {r.get('topic')} ({r.get('date')})")
    reflections_md = "**Completed Today**:\n" + \
        "\n".join(completed_today_lines)

    # API Fetches
    recent_commits = fetch_recent_commits()
    open_tasks = fetch_open_tasks()

    # Read README
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace content blocks
    content = update_block(content, "PORTFOLIO", portfolio_md)
    content = update_block(content, "STREAKS", streaks_md)
    content = update_block(content, "LEARNING_PROGRESS", progress_md)
    content = update_block(content, "LEARNING_PATH", path_md)
    content = update_block(content, "COMMITS", recent_commits)
    content = update_block(content, "TASKS", open_tasks)
    content = update_block(content, "AGENTS", agents_md)
    content = update_block(content, "REFLECTION", reflections_md)

    # Write back
    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            old_content = f.read()
    except FileNotFoundError:  # pragma: no cover
        old_content = ""

    if content != old_content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("README updated successfully.")
    else:
        print("README content is already up-to-date. No rewrite needed.")


if __name__ == "__main__":  # pragma: no cover
    main()
