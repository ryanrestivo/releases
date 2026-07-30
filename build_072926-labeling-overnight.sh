#!/bin/bash
set -e

REPO_DIR="/Users/ryanrestivo/Sites/releases"
BRANCH="072926-labeling-overnight"
cd "$REPO_DIR"

# Ensure we're on the right branch
git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH" main
echo "✅ On branch: $(git branch --show-current)"

# Check for a working labeling script
if [ ! -f "scripts/build_072926-labeling-overnight.py" ]; then
    echo "🛑 No labelling script found. Create it at scripts/build_072926-labeling-overnight.py first."
    exit 1
fi

echo "✅ Script exists at: scripts/build_072926-labeling-overnight.py"
echo "Running the labeling pipeline..."


