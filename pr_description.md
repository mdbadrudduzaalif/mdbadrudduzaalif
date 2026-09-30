🔒 Escape HTML and markdown in commit messages to prevent injection

🎯 **What:** The vulnerability fixed
Commit messages fetched from the GitHub API were being directly embedded into the README string without sanitization. This allowed unescaped characters like `<`, `>`, `&`, `[`, `]`, and ``` ` ``` to be injected, making the repository susceptible to XSS attacks or Markdown formatting injection.

⚠️ **Risk:** The potential impact if left unfixed
An attacker could craft a malicious commit message that, once processed, could break the layout of the repository's README or execute malicious scripts depending on how the Markdown file is rendered, affecting anyone viewing the README.

🛡️ **Solution:** How the fix addresses the vulnerability
The `update_readme.py` file was updated to use `html.escape()` for standard HTML characters. Additionally, `[`, `]`, and ``` ` ``` were replaced with their respective HTML entities to prevent malicious Markdown links and code block injections. A corresponding test was added to verify sanitization.
