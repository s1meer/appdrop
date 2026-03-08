#!/bin/bash
# AppDrop — Create GitHub repo + push in one command
# Usage: ./setup_github.sh
# Requires: gh CLI installed (brew install gh)

set -e

REPO_NAME="appdrop"
GITHUB_USER="s1meer"
DESCRIPTION="Turn any GitHub repo into a running app — no terminal, no code, no setup."

echo ""
echo "▼ AppDrop GitHub Setup"
echo "────────────────────────────────────"

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌  GitHub CLI (gh) not found."
    echo "    Install it: brew install gh"
    echo "    Then run: gh auth login"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "🔐  Not logged in. Running: gh auth login"
    gh auth login
fi

echo "✓  GitHub CLI ready"

# Create the repo on GitHub
echo "📦  Creating github.com/$GITHUB_USER/$REPO_NAME ..."
gh repo create "$REPO_NAME" \
    --public \
    --description "$DESCRIPTION" \
    --source=. \
    --remote=origin \
    --push \
    2>/dev/null || {
        echo "⚠️  Repo may already exist. Adding remote and pushing..."
        git remote remove origin 2>/dev/null || true
        git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
        git push -u origin main
    }

echo ""
echo "✅  Done!"
echo "   🔗  https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "Next steps:"
echo "  1. Go to the link above and add a README cover image"
echo "  2. Add topics: ai, desktop-app, github-launcher, open-source"  
echo "  3. Enable GitHub Actions in Settings → Actions"
