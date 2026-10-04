#!/usr/bin/env python3
"""Run linters and formatters on the codebase."""

import subprocess
import sys


def main():
    """Run isort, black, and flake8."""
    print("Running isort...")
    subprocess.run(["isort", "."], check=False)

    print("\nRunning black...")
    subprocess.run(["black", "."], check=False)

    print("\nRunning flake8...")
    result = subprocess.run(["flake8", "."], check=False)

    if result.returncode != 0:
        print("\nflake8 found issues.")
        sys.exit(result.returncode)

    print("\nFormatting and linting complete.")


if __name__ == "__main__":
    main()
