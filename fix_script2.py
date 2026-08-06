import os

filepath = "update_readme.py"
with open(filepath, "r") as f:
    content = f.read()

search_block = """            url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}/commit/{sha}"
            commits.append(
                f"- **{repo_name}**: {message} ([`{sha}`]({url}))"
            )  # noqa: E501"""

replace_block = """            url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}/commit/{sha}"
            commits.append(
                f"- **{repo_name}**: {message} ([`{sha}`]({url}))"
            )"""

if search_block in content:
    content = content.replace(search_block, replace_block)
    with open(filepath, "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Block not found!")
