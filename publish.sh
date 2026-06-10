#!/bin/bash

# Exit on error
set -e

echo "=== GitHub Profile README Publisher ==="

# Initialize git repository if it doesn't exist
if [ ! -d .git ]; then
    echo "Initializing local Git repository..."
    git init
    git branch -M main
else
    echo "Git repository already initialized."
fi

# Add README.md
echo "Staging README.md..."
git add README.md

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit (README.md is already up to date in Git)."
else
    echo "Committing README.md..."
    git commit -m "docs: create professional profile README"
fi

echo ""
echo "=========================================================="
echo " README setup complete!"
echo "=========================================================="
echo "To publish this to your GitHub profile:"
echo "1. Go to https://github.com/new"
echo "2. Create a repository named exactly: mdbadrudduzaalif"
echo "   - Make sure it is PUBLIC."
echo "   - Do NOT initialize it with README, .gitignore, or license."
echo "3. Run the following commands in this directory:"
echo "   git remote add origin https://github.com/mdbadrudduzaalif/mdbadrudduzaalif.git"
echo "   git push -u origin main"
echo "=========================================================="
