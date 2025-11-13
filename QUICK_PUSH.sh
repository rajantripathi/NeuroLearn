#!/bin/bash
# Quick GitHub Push Script

echo "🚀 NeuroLearn - GitHub Push Helper"
echo ""

# Check if GitHub username is provided
if [ -z "$1" ]; then
    echo "Usage: ./QUICK_PUSH.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "Example: ./QUICK_PUSH.sh johndoe"
    echo ""
    echo "This will:"
    echo "  1. Set GitHub remote to https://github.com/YOUR_USERNAME/NeuroLearn.git"
    echo "  2. Rename branch to 'main'"
    echo "  3. Push to GitHub"
    echo ""
    echo "⚠️  Make sure you've created the repository on GitHub first!"
    echo "    Go to: https://github.com/new"
    exit 1
fi

USERNAME=$1
REPO_URL="https://github.com/$USERNAME/NeuroLearn.git"

echo "GitHub Username: $USERNAME"
echo "Repository URL: $REPO_URL"
echo ""

# Check if remote already exists
if git remote | grep -q "origin"; then
    echo "⚠️  Remote 'origin' already exists. Removing..."
    git remote remove origin
fi

echo "📡 Adding GitHub remote..."
git remote add origin "$REPO_URL"

echo "🌿 Renaming branch to 'main'..."
git branch -M main

echo "⬆️  Pushing to GitHub..."
echo ""
echo "You may be prompted for GitHub credentials:"
echo "  Username: Your GitHub username"
echo "  Password: Your Personal Access Token (NOT your password)"
echo ""
echo "Get token at: https://github.com/settings/tokens"
echo ""

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🌐 View your repository at:"
    echo "   https://github.com/$USERNAME/NeuroLearn"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Add repository description"
    echo "   2. Add topics/tags"
    echo "   3. Consider adding a LICENSE file"
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "Common issues:"
    echo "  1. Repository doesn't exist on GitHub"
    echo "     → Create it at: https://github.com/new"
    echo "  2. Authentication failed"
    echo "     → Use Personal Access Token, not password"
    echo "  3. Wrong username"
    echo "     → Check your GitHub username"
fi
