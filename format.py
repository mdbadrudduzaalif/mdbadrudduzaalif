import re
with open('tests/test_update_readme.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Fix the specific lines reported by flake8
    if i + 1 == 284:
        new_lines.append(line.replace('        mock_response.read.return_value = b\'{"message": "API rate limit"}\' # noqa', '        mock_response.read.return_value = b\'{"message": "API rate limit"}\'  # noqa'))
    elif i + 1 == 318:
        new_lines.append(line.replace('        mock_fetch.return_value = [{"type": "PushEvent", "repo": { # noqa', '        mock_fetch.return_value = [{"type": "PushEvent", "repo": {  # noqa'))
    else:
        new_lines.append(line)

with open('tests/test_update_readme.py', 'w') as f:
    f.writelines(new_lines)
