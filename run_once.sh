#!/bin/bash
# Generate one blog post and deploy

set -e

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

echo "✓ Complete! Check https://samfoy.github.io/circuit-break-blog"
