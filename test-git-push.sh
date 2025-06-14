#!/bin/bash
set -e
set -x

echo "Starting git push test..."

# Check current directory
pwd

# Check git status
git status --porcelain

# Check if there are any changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Changes found, adding them..."
    git add .
    git commit -m "Test commit for git push fix"
else
    echo "No changes to commit"
fi

# Check remote
git remote -v

# Check current branch
git branch --show-current

# Try to push
git push origin $(git branch --show-current)

echo "Git push test completed successfully!"
