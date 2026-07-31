#!/bin/bash
# Install git hooks from scripts/ to .git/hooks/
cp "$(dirname "$0")/pre-commit" "$(git rev-parse --git-dir)/hooks/pre-commit"
chmod +x "$(git rev-parse --git-dir)/hooks/pre-commit"
echo "Git hooks installed."
