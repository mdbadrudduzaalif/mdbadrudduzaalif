import os
import yaml
import urllib.request
import json
import datetime
import re

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(BASE_DIR, "README.md")
LEARNING_LOG_PATH = os.path.join(BASE_DIR, "data", "learning_log.yml")
PROJECTS_PATH = os.path.join(BASE_DIR, "data", "takaa.yml")
AGENTS_PATH = os.path.join(BASE_DIR, "data", "agents.yml")

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# 1. Streak & Longest Streak Calculation
def _parse_log_dates(log_entries):
    topic_dates = {}
    for entry in log_entries:
        date_str = entry.get("date")
        topic = entry.get("topic")
        if date_str and topic:
            try:
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                topic_dates.setdefault(topic, set()).add(date_obj)
            except ValueError:
                continue
    return topic_dates

def _calculate_longest_streak(sorted_dates):
    longest = 0
    current_longest = 0
    prev_date = None
    for d in sorted_dates:
        if prev_date is None:
            current_longest = 1
        elif (d - prev_date).days == 1:
            current_longest += 1
        elif (d - prev_date).days > 1:
            if current_longest > longest:
                longest = current_longest
            current_longest = 1
        prev_date = d
    if current_longest > longest:
        longest = current_longest
    return longest

def _calculate_current_streak(dates_set):
    tz_offset_hours = os.environ.get("TZ_OFFSET_HOURS")
    if tz_offset_hours is not None:
        try:
            offset = int(tz_offset_hours)
            tz = datetime.timezone(datetime.timedelta(hours=offset))
            today = datetime.datetime.now(tz).date()
        except ValueError:
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

def calculate_streaks_stats(log_entries):
    topic_dates = _parse_log_dates(log_entries)
    stats = {}
    
    for topic, dates_set in topic_dates.items():
        sorted_dates = sorted(dates_set)
        if not sorted_dates:
            stats[topic] = {"current": 0, "longest": 0}
            continue
        
        longest = _calculate_longest_streak(sorted_dates)
        current = _calculate_current_streak(dates_set)
        
        stats[topic] = {"current": current, "longest": longest}

    return stats


def render_streaks_md(streaks_stats):
    if not streaks_stats:
        return "No active streaks."
    
    sorted_stats = sorted(streaks_stats.items())

    lines = ["**🔥 Active Study Streaks**"]
    for topic, s in sorted_stats:
        emoji = "🔥" if s["current"] > 0 else "❄️"
        lines.append(f"- **{topic}**: {emoji} {s['current']} day{'s' if s['current'] != 1 else ''}")
    
    lines.append("\n**🏆 Longest Streak**")
    for topic, s in sorted_stats:
        lines.append(f"- **{topic}**: {s['longest']} day{'s' if s['longest'] != 1 else ''}")

    return "\n".join(lines)

# 2. Render ASCII Progress Bar
def render_progress_bar(completed, total, length=10):
    if total == 0:
        return "`░░░░░░░░░░ 0%`"
    percentage = int((completed / total) * 100)
    filled_length = int(length * completed // total)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"`{bar} {percentage}%`"

# 3. Learning Progress and Path Logic
def process_learning_journey(skills):
    progress_lines = []
    path_lines = []
    
    category_icons = {
        "SQL": "🗄️ Database Development (SQL)",
        "React Native": "📱 Mobile Development (React Native)",
        "C#": "💻 C# Development (C#)",
        "Algorithms": "🧠 Algorithms & Data Structures (C++)"
    }
    
    for topic, sections in skills.items():
        completed = sections.get("completed", [])
        in_progress = sections.get("in_progress", [])
        planned = sections.get("planned", [])
        
        total = len(completed) + len(in_progress) + len(planned)
        bar = render_progress_bar(len(completed), total, length=10)
        progress_lines.append(f"- **{topic}**: {bar}")
        
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
def process_project_portfolio(projects):
    lines = []
    for name, data in projects.items():
        features = data.get("features", [])
        completed = sum(1 for f in features if f.get("completed"))
        remaining = sum(1 for f in features if not f.get("completed"))
        
        emoji = "💰" if name == "Takaa" else "🏠"
        lines.append(f"### {emoji} {name}")
        lines.append(f"- **{data.get('label_completed', 'Modules Implemented')}**: {completed}")
        lines.append(f"- **{data.get('label_remaining', 'Major Features Remaining')}**: {remaining}")
        lines.append(f"- **Current Milestone**: {data.get('milestone', 'MVP')}")
        lines.append("- **Current Focus**:")
        for item in data.get("focus", []):
            lines.append(f"  - {item}")
        lines.append("")
    return "\n".join(lines)

def _extract_commits(events):
    commits = []
    seen_commits = set()
    for event in events:
        if event.get('type') != 'PushEvent':
            continue
        repo_name = event.get('repo', {}).get('name', '').split('/')[-1]
        for commit in event.get('payload', {}).get('commits', []):
            message = commit.get('message', '').split('\n')[0]
            sha = commit.get('sha', '')[:7]
            if not message or message.startswith("Merge") or sha in seen_commits:
                continue
            seen_commits.add(sha)
            commits.append(f"- **{repo_name}**: {message} ([`{sha}`](https://github.com/mdbadrudduzaalif/{repo_name}/commit/{sha}))")
            if len(commits) >= 5:
                return commits
    return commits

# 5. Fetch GitHub Commits
def fetch_recent_commits():
    url = "https://api.github.com/users/mdbadrudduzaalif/events"
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers['Authorization'] = f"token {token}"
    else:
        print("Warning: GITHUB_TOKEN not found. API rate limits may apply for unauthenticated requests.")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            events = json.loads(response.read().decode())
            commits = _extract_commits(events)
            if not commits:
                return "No recent public commits found."
            return "\n".join(commits)
    except Exception as e:
        return f"*(Failed to fetch recent commits: {str(e)})*"

# 6. Fetch Open Issues (Tasks)
def fetch_open_tasks():
    url = "https://api.github.com/repos/mdbadrudduzaalif/mdbadrudduzaalif/issues?state=open"
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers['Authorization'] = f"token {token}"
    else:
        print("Warning: GITHUB_TOKEN not found. API rate limits may apply for unauthenticated requests.")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            issues = json.loads(response.read().decode())
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
                return "*No active tasks from projects. Create a GitHub Issue in this repository to track your next task!*"
            return "\n".join(tasks)
    except Exception as e:
        return f"*(Failed to fetch tasks from issues: {str(e)})*"

def update_block(content, tag, new_value):
    start_tag = f"<!-- START_{tag} -->"
    end_tag = f"<!-- END_{tag} -->"
    pattern = re.escape(start_tag) + r"(.*?)" + re.escape(end_tag)
    replacement = f"{start_tag}\n{new_value}\n{end_tag}"
    return re.sub(pattern, lambda m: replacement, content, flags=re.DOTALL)

def main():
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
    for a in agents_data.get("agents", []):
        emoji = "🟢" if a.get("status") == "Active" else "🟡"
        agent_lines.append(f"- **{a.get('name')}** ({emoji} {a.get('status')}): {a.get('purpose')}")
    agents_md = "\n".join(agent_lines)
    
    # Process reflections from dates studied
    today_refl = learning_log.get("log", [])[:3]
    completed_today_lines = []
    for r in today_refl:
        completed_today_lines.append(f"- Logged study for {r.get('topic')} ({r.get('date')})")
    reflections_md = "**Completed Today**:\n" + "\n".join(completed_today_lines)
    
    # API Fetches
    recent_commits = fetch_recent_commits()
    open_tasks = fetch_open_tasks()
    
    # Read README
    with open(README_PATH, "r") as f:
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
    with open(README_PATH, "w") as f:
        f.write(content)

    print("README updated successfully.")

if __name__ == "__main__":
    main()
