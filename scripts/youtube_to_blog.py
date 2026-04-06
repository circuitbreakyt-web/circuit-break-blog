#!/usr/bin/env python3
"""
Convert YouTube video script to expanded blog post.
Usage: python youtube_to_blog.py --title "Video Title" --script-file path/to/script.txt
"""

import boto3
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import re
import random

# AWS Bedrock setup
os.environ.setdefault("AWS_PROFILE", "openclaw-bedrock")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Amazon Associates tag
AFFILIATE_TAG = "circuitbreak-20"

# Relevant affiliate products
AFFILIATE_PRODUCTS = {
    "ai": {"asin": "1101970316", "name": "Life 3.0: Being Human in the Age of Artificial Intelligence"},
    "tech": {"asin": "0134610997", "name": "Artificial Intelligence: A Modern Approach"},
    "general": {"asin": "0465094279", "name": "The Master Algorithm"}
}


def invoke_claude(prompt: str, max_tokens: int = 2500) -> str:
    """Invoke Claude Haiku via AWS Bedrock."""
    try:
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
    except Exception as e:
        print(f"Error invoking Claude: {e}")
        sys.exit(1)


def expand_script_to_blog(title: str, script_content: str) -> dict:
    """Expand 400-word script to 800-word blog post."""

    # Determine affiliate product
    title_lower = title.lower()
    if "ai" in title_lower or "artificial intelligence" in title_lower:
        product = AFFILIATE_PRODUCTS["ai"]
    elif "tech" in title_lower or "technology" in title_lower:
        product = AFFILIATE_PRODUCTS["tech"]
    else:
        product = AFFILIATE_PRODUCTS["general"]

    affiliate_link = f"https://www.amazon.com/dp/{product['asin']}?tag={AFFILIATE_TAG}"

    # Expansion prompt
    prompt = f"""Expand this YouTube video script into an 800-word SEO-optimized blog post.

Video Title: {title}

Original Script:
{script_content}

Requirements:
- Expand to 800-900 words while keeping the core narrative
- Add clear H2 section headers (use ## markdown)
- Include 2-3 bullet point lists for key takeaways
- Add specific examples or details not in the original script
- Write in an engaging, conversational blog tone
- Structure for SEO: clear sections, scannable content
- Naturally mention "{product['name']}" as a recommended resource
- Add a brief "Final Thoughts" or "Key Takeaway" section

DO NOT include H1 title. Start with an engaging intro paragraph."""

    content = invoke_claude(prompt)

    # Insert affiliate link
    book_name_short = product['name'].split(':')[0]
    if book_name_short in content:
        content = content.replace(
            book_name_short,
            f"[{book_name_short}]({affiliate_link})",
            1
        )
    else:
        content += f"\n\n*Want to learn more? Check out [{product['name']}]({affiliate_link}).*\n"

    # Generate metadata
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    description = f"{title} - Expanded insights from our latest video."

    metadata = {
        "title": title[:60],
        "description": description[:150],
        "tags": ["ai", "tech", "video"],
        "slug": slug
    }

    return {
        "content": content,
        "metadata": metadata
    }


def save_post(post_data: dict) -> Path:
    """Save post as Hugo markdown file."""
    date = datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    slug = post_data["metadata"]["slug"]

    filename = f"{date_str}-{slug}.md"
    output_path = Path.home() / "Projects/youtube-channels/blog-engine/content/posts" / filename

    front_matter = f"""---
title: "{post_data['metadata']['title']}"
date: {date.isoformat()}
draft: false
description: "{post_data['metadata']['description']}"
tags: {json.dumps(post_data['metadata']['tags'])}
author: "Circuit Break"
slug: "{slug}"
---

"""

    with open(output_path, 'w') as f:
        f.write(front_matter)
        f.write(post_data['content'])

    print(f"✓ Blog post saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert YouTube script to blog post")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--script-file", required=True, help="Path to script file")
    args = parser.parse_args()

    script_path = Path(args.script_file)

    if not script_path.exists():
        print(f"Error: Script file not found: {script_path}")
        sys.exit(1)

    print(f"=== YouTube to Blog Converter ===")
    print(f"Title: {args.title}")
    print(f"Script: {script_path}\n")

    # Read script
    with open(script_path) as f:
        script_content = f.read()

    print(f"Expanding {len(script_content.split())} words to 800-word blog post...")

    # Convert
    post_data = expand_script_to_blog(args.title, script_content)

    # Save
    output_path = save_post(post_data)
    print(f"\n✓ Done! Run ./deploy.sh to publish.")


if __name__ == "__main__":
    main()
