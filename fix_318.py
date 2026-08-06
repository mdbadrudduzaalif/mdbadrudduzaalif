with open('tests/test_update_readme.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i + 1 == 317:
        new_lines.append(line.replace('        mock_fetch.return_value = [{"type": "PushEvent", "repo": {  # noqa', '        mock_fetch.return_value = [{"type": "PushEvent",\n                                    "repo": {'))
    elif i + 1 == 318:
        new_lines.append(line.replace('            "name": "r"}, "payload": {"commits": [{"message": "m", "sha": "s"}]}}]', '                                        "name": "r"},\n                                    "payload": {"commits": [{"message": "m", "sha": "s"}]}}]'))
    else:
        new_lines.append(line)

with open('tests/test_update_readme.py', 'w') as f:
    f.writelines(new_lines)
