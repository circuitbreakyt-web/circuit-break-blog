#!/usr/bin/env python3
"""
Auto-post new Circuit Break blog posts to Pinterest.
Creates a pin for each new post using the Pinterest API v5.
"""

import os
import json
import re
import sys
import requests
from pathlib import Path

PINTEREST_ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
PINTEREST_BOARD_ID = os.environ.get("PINTEREST_BOARD_ID", "")  # e.g. "circuitbreakyt/ai-tech-news"

BLOG_BASE = "https://circuitbreakyt-web.github.io/circuit-break-blog"
REPO_DIR = Path.home() / "Projects/youtube-channels/blog-engine"
STATE_FILE = REPO_DIR / "scripts/pinterest_posted.json"

# Default image to use for pins (Circuit Break logo/banner)
DEFAULT_IMAGE = "https://circuitbreakyt-web.github.io/circuit-break-blog/assets/og-image.png"


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"posted": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_latest_posts(limit=3):
    posts_dir = REPO_DIR / "content/posts"
    files = sorted(posts_dir.glob("*.md"), reverse=True)[:limit]
    results = []
    for f in files:
        text = f.read_text()
        title_match = re.search(r'^title:\s*"(.+)"', text, re.MULTILINE)
        desc_match = re.search(r'^description:\s*"(.+)"', text, re.MULTILINE)
        slug_match = re.search(r'^slug:\s*"(.+)"', text, re.MULTILINE)
        if title_match and slug_match:
            results.append({
                "file": f.name,
                "title": title_match.group(1),
                "description": desc_match.group(1) if desc_match else "",
                "slug": slug_match.group(1),
                "url": f"{BLOG_BASE}/posts/{slug_match.group(1)}/",
            })
    return results


def create_pin(post):
    """Create a Pinterest pin for a blog post."""
    state = load_state()
    if post["slug"] in state["posted"]:
        print(f"Already pinned: {post['slug']}")
        return None

    headers = {
        "Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    pin_data = {
        "title": post["title"],
        "description": f"{post['description']}\n\nRead more at Circuit Break 🤖",
        "link": post["url"],
        "board_id": PINTEREST_BOARD_ID,
        "media_source": {
            "source_type": "image_url",
            "url": DEFAULT_IMAGE,
        },
    }

    resp = requests.post(
        "https://api.pinterest.com/v5/pins",
        headers=headers,
        json=pin_data,
        timeout=30,
    )

    if resp.status_code in (200, 201):
        pin = resp.json()
        pin_url = f"https://pinterest.com/pin/{pin.get('id', '')}"
        print(f"✓ Pinned: {post['title']} → {pin_url}")
        state["posted"].append(post["slug"])
        save_state(state)
        return pin_url
    else:
        print(f"✗ Pinterest error {resp.status_code}: {resp.text}")
        return None


def main():
    if not PINTEREST_ACCESS_TOKEN or not PINTEREST_BOARD_ID:
        print("⚠️  Pinterest credentials not set.")
        print("1. Create app at https://developers.pinterest.com/apps/")
        print("2. Get access token with boards:write + pins:write scopes")
        print("3. Set PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID env vars")
        sys.exit(1)

    posts = get_latest_posts(limit=3)
    if not posts:
        print("No posts found.")
        return

    for post in posts:
        create_pin(post)

    print("✓ Pinterest done")


if __name__ == "__main__":
    main()
