#!/bin/bash
# Generate one blog post and deploy

set -e

# Load shared env vars (API keys etc)
if [ -f "$(dirname "$0")/../.env" ]; then
  export $(grep -v '^#' "$(dirname "$0")/../.env" | xargs)
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="/Users/sam.painter/Projects/youtube-channels/scary-stories/.venv/bin/python"

echo "=== Circuit Break Blog - Run Once ==="
echo ""

# Generate post
echo "Generating post..."
$PYTHON "$SCRIPT_DIR/scripts/generate_post.py"
echo ""

# Deploy
echo "Deploying to GitHub Pages..."
bash "$SCRIPT_DIR/deploy.sh"
echo ""

# Promote on Reddit (if credentials set)
if [ -n "$REDDIT_CLIENT_ID" ]; then
    echo "Posting to Reddit..."
    $PYTHON "$SCRIPT_DIR/scripts/post_reddit.py" || echo "Reddit post failed (non-fatal)"
else
    echo "⚠️  REDDIT_CLIENT_ID not set — skipping Reddit promotion"
fi

# Promote on Pinterest (if credentials set)
if [ -n "$PINTEREST_ACCESS_TOKEN" ]; then
    echo "Pinning to Pinterest..."
    $PYTHON "$SCRIPT_DIR/scripts/post_pinterest.py" || echo "Pinterest post failed (non-fatal)"
else
    echo "⚠️  PINTEREST_ACCESS_TOKEN not set — skipping Pinterest"
fi

echo ""
echo "✓ Complete! Check https://circuitbreakyt-web.github.io/circuit-break-blog"
