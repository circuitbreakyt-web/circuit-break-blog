#!/bin/bash
# Deploy Circuit Break blog to GitHub Pages

set -e

REPO_DIR="/Users/sam.painter/Projects/youtube-channels/blog-engine"
cd "$REPO_DIR"

echo "=== Deploying Circuit Break Blog ==="
echo ""

# Ensure PaperMod theme is present (submodule can be empty after clone)
if [ ! -f "themes/PaperMod/theme.toml" ] && [ ! -f "themes/PaperMod/layouts/index.html" ]; then
    echo "PaperMod theme missing — cloning..."
    rm -rf themes/PaperMod
    git clone https://github.com/adityatelange/hugo-PaperMod themes/PaperMod --depth=1 --quiet
fi

# Commit any new posts to master before building
echo "Committing new posts to master..."
git add content/posts/
if ! git diff --staged --quiet; then
    git commit -m "Add blog post - $(date +%Y-%m-%d)"
    git push origin master
else
    echo "No new posts to commit"
fi

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

# Copy public/ to temp location
echo "Preparing gh-pages content..."
TEMP_DIR=$(mktemp -d)
cp -R public/* "$TEMP_DIR/"
echo "Copied build to temp: $TEMP_DIR"

# Switch to gh-pages and deploy
git checkout gh-pages
rsync -av --delete --exclude='.git' "$TEMP_DIR/" .
touch .nojekyll  # Prevent GitHub Pages from running Jekyll on Hugo output
rm -rf "$TEMP_DIR"

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
gh api repos/circuitbreakyt-web/circuit-break-blog/pages -X PUT \
  --field source[branch]=gh-pages \
  --field source[path]=/ 2>/dev/null || echo "GitHub Pages already configured"

echo ""
echo "✓ Deployment complete!"
echo "  Site: https://circuitbreakyt-web.github.io/circuit-break-blog"
echo "  (May take 1-2 minutes to update)"
