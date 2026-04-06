#!/bin/bash
# Deploy Circuit Break blog to GitHub Pages

set -e

REPO_DIR="/Users/sam.painter/Projects/youtube-channels/blog-engine"
cd "$REPO_DIR"

echo "=== Deploying Circuit Break Blog ==="
echo ""

# Build Hugo site
echo "Building Hugo site..."
hugo --minify

# Initialize gh-pages branch if needed
if ! git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git reset --hard
    git commit --allow-empty -m "Initial gh-pages commit"
    git checkout master
fi

# Copy public/ contents to gh-pages
echo "Preparing gh-pages content..."
git checkout gh-pages
rsync -av --delete --exclude='.git' public/ .
rm -rf public

# Commit and push
echo "Committing and pushing to gh-pages..."
git add -A
if git diff --staged --quiet; then
    echo "No changes to commit"
else
    git commit -m "Deploy blog - $(date +%Y-%m-%d\ %H:%M)"
    git push origin gh-pages --force
fi

# Return to master
git checkout master

# Ensure GitHub Pages is configured (idempotent)
echo "Configuring GitHub Pages..."
gh api repos/samfoy/circuit-break-blog/pages -X PUT \
  --field source[branch]=gh-pages \
  --field source[path]=/ 2>/dev/null || echo "GitHub Pages already configured"

echo ""
echo "✓ Deployment complete!"
echo "  Site: https://samfoy.github.io/circuit-break-blog"
echo "  (May take 1-2 minutes to update)"
