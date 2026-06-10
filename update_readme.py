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
TAKAA_PATH = os.path.join(BASE_DIR, "data", "takaa.yml")
AGENTS_PATH = os.path.join(BASE_DIR, "data", "agents.yml")

def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# 1. Streak Calculation Logic
def calculate_streaks(log_entries):
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
    
    streaks = {}
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    
    for topic, dates in topic_dates.items():
        if today in dates:
            start_date = today
        elif yesterday in dates:
            start_date = yesterday
        else:
            streaks[topic] = 0
            continue
            
        streak = 0
        current_date = start_date
        while current_date in dates:
            streak += 1
            current_date -= datetime.timedelta(days=1)
        streaks[topic] = streak
        
    return streaks

def render_streaks_md(streaks):
    if not streaks:
        return "No active streaks."
    lines = []
    for topic, count in sorted(streaks.items()):
        emoji = "🔥" if count > 0 else "❄️"
        lines.append(f"- **{topic}**: {emoji} {count} day{'s' if count != 1 else ''}")
    return "\n".join(lines)

# 2. Knowledge Tree Logic
def render_skills_tree(skills):
    lines = []
    for category, subskills in skills.items():
        lines.append(f"**{category}**")
        for idx, subskill in enumerate(subskills):
            connector = "└── " if idx == len(subskills) - 1 else "├── "
            lines.append(f"&nbsp;&nbsp;{connector}{subskill}")
    return "\n".join(lines)

# 3. Progress Bar Logic
def render_progress_bar(completed, total, length=12):
    if total == 0:
        return "`░░░░░░░░░░░░ 0%`"
    percentage = int((completed / total) * 100)
    filled_length = int(length * completed // total)
    bar = "█" * filled_length + "░" * (length - filled_length)
    return f"`{bar} {percentage}%`"

# 4. Fetch GitHub Commits
def fetch_recent_commits():
    url = "https://api.github.com/users/mdbadrudduzaalif/events"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            events = json.loads(response.read().decode())
            commits = []
            seen_commits = set()
            for event in events:
                if event.get('type') == 'PushEvent':
                    repo_name = event.get('repo', {}).get('name', '').split('/')[-1]
                    for commit in event.get('payload', {}).get('commits', []):
                        message = commit.get('message', '').split('\n')[0]
                        sha = commit.get('sha', '')[:7]
                        # De-duplicate identical commits in the list
                        if message and not message.startswith("Merge") and sha not in seen_commits:
                            seen_commits.add(sha)
                            commits.append(f"- **{repo_name}**: {message} ([`{sha}`](https://github.com/mdbadrudduzaalif/{repo_name}/commit/{sha}))")
                        if len(commits) >= 5:
                            break
                if len(commits) >= 5:
                    break
            if not commits:
                return "No recent public commits found."
            return "\n".join(commits)
    except Exception as e:
        return f"*(Failed to fetch recent commits: {str(e)})*"

# 5. Fetch Open Issues (Tasks)
def fetch_open_tasks():
    url = "https://api.github.com/repos/mdbadrudduzaalif/mdbadrudduzaalif/issues?state=open"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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
                return "*No active tasks from issues. Create a GitHub Issue in this repository to track your next goals!*"
            return "\n".join(tasks)
    except Exception as e:
        return f"*(Failed to fetch tasks from issues: {str(e)})*"

def update_block(content, tag, new_value):
    start_tag = f"<!-- START_{tag} -->"
    end_tag = f"<!-- END_{tag} -->"
    pattern = re.escape(start_tag) + r"(.*?)" + re.escape(end_tag)
    replacement = f"{start_tag}\n{new_value}\n{end_tag}"
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

def main():
    # Load YAML databases
    learning_log = load_yaml(LEARNING_LOG_PATH)
    takaa_data = load_yaml(TAKAA_PATH)
    agents_data = load_yaml(AGENTS_PATH)
    
    # Process Streaks
    streaks = calculate_streaks(learning_log.get("log", []))
    streaks_md = render_streaks_md(streaks)
    
    # Process Skills Tree
    skills_tree_md = render_skills_tree(learning_log.get("skills", {}))
    
    # Process Takaa Roadmap & Progress
    features = takaa_data.get("features", [])
    completed_features = sum(1 for f in features if f.get("completed"))
    total_features = len(features)
    progress_bar = render_progress_bar(completed_features, total_features)
    
    roadmap_items = []
    for f in features:
        box = "[x]" if f.get("completed") else "[ ]"
        roadmap_items.append(f"- {box} {f.get('name')}")
    roadmap_md = "\n".join(roadmap_items)
    
    milestone_md = f"**Current Milestone**: {takaa_data.get('metrics', {}).get('target_milestone', 'MVP')}"
    takaa_stats_md = f"Progress: {progress_bar}\n\n{milestone_md}"
    
    # Process Snapshot Tasks
    focus = learning_log.get("log", [{}])[0].get("topic", "Coding") if learning_log.get("log") else "Development"
    latest_task = learning_log.get("log", [{}])[0].get("topic", "Practice") if learning_log.get("log") else "Practice"
    
    # Process Agent Lab
    agent_lines = []
    for a in agents_data.get("agents", []):
        emoji = "🟢" if a.get("status") == "Active" else "🟡"
        agent_lines.append(f"- **{a.get('name')}** ({emoji} {a.get('status')}): {a.get('purpose')}")
    agents_md = "\n".join(agent_lines)
    
    # Process Reflections
    # Use standard summaries from agents.yml or learning_log.yml
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
        
    # Replace contents
    content = update_block(content, "STREAKS", streaks_md)
    content = update_block(content, "LEARNING_TREE", skills_tree_md)
    content = update_block(content, "TAKAA_STATS", takaa_stats_md)
    content = update_block(content, "TAKAA_ROADMAP", roadmap_md)
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
