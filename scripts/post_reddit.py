#!/usr/bin/env python3
"""
Auto-post new Circuit Break blog posts to relevant Reddit subreddits.
Reads the latest post from content/posts/, checks if already posted, posts if not.
"""

import os
import json
import re
import sys
import time
import random
from pathlib import Path
from datetime import datetime, timezone

# Reddit API via PRAW
try:
    import praw
except ImportError:
    print("Installing praw...")
    os.system(f"{sys.executable} -m pip install praw -q")
    import praw

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "CircuitBreakYT")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT = "CircuitBreakBot/1.0 by CircuitBreakYT"

BLOG_BASE = "https://circuitbreakyt-web.github.io/circuit-break-blog"
REPO_DIR = Path.home() / "Projects/youtube-channels/blog-engine"
STATE_FILE = REPO_DIR / "scripts/reddit_posted.json"

# Subreddit routing by topic keywords
SUBREDDIT_MAP = [
    (["safety", "alignment", "ethics", "bias", "responsible"], ["r/artificial", "r/singularity"]),
    (["open source", "open-source", "llama", "mistral", "local"], ["r/LocalLLaMA", "r/artificial"]),
    (["regulation", "policy", "government", "law"], ["r/artificial", "r/Futurology"]),
    (["chip", "hardware", "gpu", "semiconductor", "nvidia", "tpu"], ["r/artificial", "r/MachineLearning"]),
    (["drug", "healthcare", "medical", "biology", "protein"], ["r/artificial", "r/MachineLearning"]),
    (["quantum"], ["r/QuantumComputing", "r/artificial"]),
    (["robotics", "robot", "embodied"], ["r/artificial", "r/Futurology"]),
    (["transformer", "attention", "architecture"], ["r/MachineLearning", "r/artificial"]),
    (["edge", "iot", "deployment", "inference"], ["r/artificial", "r/MachineLearning"]),
]
DEFAULT_SUBREDDITS = ["r/artificial", "r/AITech"]

# Flair/title templates to avoid looking spammy
TITLE_TEMPLATES = [
    "{title} — full breakdown",
    "{title}",
    "Deep dive: {title}",
    "{title} [blog post]",
]


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"posted": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_latest_posts(limit=3):
    """Get the most recent markdown posts."""
    posts_dir = REPO_DIR / "content/posts"
    files = sorted(posts_dir.glob("*.md"), reverse=True)[:limit]
    results = []
    for f in files:
        text = f.read_text()
        title_match = re.search(r'^title:\s*"(.+)"', text, re.MULTILINE)
        desc_match = re.search(r'^description:\s*"(.+)"', text, re.MULTILINE)
        slug_match = re.search(r'^slug:\s*"(.+)"', text, re.MULTILINE)
        tags_match = re.search(r'^tags:\s*(\[.+\])', text, re.MULTILINE)
        if title_match and slug_match:
            results.append({
                "file": f.name,
                "title": title_match.group(1),
                "description": desc_match.group(1) if desc_match else "",
                "slug": slug_match.group(1),
                "tags": tags_match.group(1) if tags_match else "[]",
                "url": f"{BLOG_BASE}/posts/{slug_match.group(1)}/",
            })
    return results


def pick_subreddits(title, description):
    """Pick 1-2 relevant subreddits based on post content."""
    text = (title + " " + description).lower()
    for keywords, subs in SUBREDDIT_MAP:
        if any(k in text for k in keywords):
            return subs[:2]
    return DEFAULT_SUBREDDITS[:1]


def post_to_reddit(post, reddit):
    """Post a single blog post to Reddit. Returns list of submission URLs."""
    state = load_state()
    if post["slug"] in state["posted"]:
        print(f"Already posted: {post['slug']}")
        return []

    subreddits = pick_subreddits(post["title"], post["description"])
    title = random.choice(TITLE_TEMPLATES).format(title=post["title"])
    submitted = []

    for sub_name in subreddits:
        sub_name = sub_name.lstrip("r/")
        try:
            subreddit = reddit.subreddit(sub_name)
            submission = subreddit.submit(
                title=title,
                url=post["url"],
                resubmit=False,
            )
            print(f"✓ Posted to r/{sub_name}: {submission.shortlink}")
            submitted.append(submission.shortlink)
            time.sleep(10)  # rate limit
        except Exception as e:
            print(f"✗ Failed r/{sub_name}: {e}")

    if submitted:
        state["posted"].append(post["slug"])
        save_state(state)

    return submitted


def main():
    if not REDDIT_CLIENT_ID or not REDDIT_PASSWORD:
        print("⚠️  Reddit credentials not set. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD.")
        print("Get credentials at https://www.reddit.com/prefs/apps (script app)")
        sys.exit(1)

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=REDDIT_USER_AGENT,
    )

    posts = get_latest_posts(limit=3)
    if not posts:
        print("No posts found.")
        return

    all_links = []
    for post in posts:
        links = post_to_reddit(post, reddit)
        all_links.extend(links)

    if all_links:
        print(f"\n✓ Posted {len(all_links)} submissions to Reddit")
    else:
        print("Nothing new to post.")


if __name__ == "__main__":
    main()
