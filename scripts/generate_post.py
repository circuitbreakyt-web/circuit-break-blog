#!/usr/bin/env python3
"""
Generate SEO-optimized blog posts with affiliate links using Claude Haiku via AWS Bedrock.
"""

import boto3
import json
import os
import sys
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

# AI & Tech topics pool
TOPICS = [
    "AI model efficiency breakthroughs",
    "Edge computing and AI deployment",
    "Transformer architecture innovations",
    "AI safety and alignment",
    "Open source AI models",
    "Multi-modal AI systems",
    "AI in healthcare diagnostics",
    "Automated coding assistants",
    "AI chip design and hardware",
    "Synthetic data generation",
    "AI regulation and policy",
    "Robotics and embodied AI",
    "AI-powered search engines",
    "Neural network optimization",
    "AI for climate modeling",
    "Quantum machine learning",
    "AI ethics and bias mitigation",
    "Generative AI for creativity",
    "AI in drug discovery",
    "Edge AI and IoT devices"
]

# Relevant affiliate products (books/tech)
AFFILIATE_PRODUCTS = [
    {
        "name": "The Alignment Problem: Machine Learning and Human Values",
        "asin": "0393868338",
        "context": "AI safety, alignment, ethics"
    },
    {
        "name": "Superintelligence: Paths, Dangers, Strategies",
        "asin": "0198739834",
        "context": "AI futures, AGI, existential risk"
    },
    {
        "name": "Life 3.0: Being Human in the Age of Artificial Intelligence",
        "asin": "1101970316",
        "context": "AI impact, society, future"
    },
    {
        "name": "Deep Learning (Adaptive Computation and Machine Learning series)",
        "asin": "0262035618",
        "context": "neural networks, technical foundations"
    },
    {
        "name": "Artificial Intelligence: A Modern Approach",
        "asin": "0134610997",
        "context": "AI fundamentals, algorithms, theory"
    },
    {
        "name": "Grokking Deep Learning",
        "asin": "1617293709",
        "context": "neural networks, practical learning"
    },
    {
        "name": "The Master Algorithm: How the Quest for the Ultimate Learning Machine Will Remake Our World",
        "asin": "0465094279",
        "context": "machine learning, AI history"
    }
]


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


def get_topic() -> str:
    """Get topic from ai-news queue or generate random."""
    ai_news_queue = Path.home() / "Projects/youtube-channels/ai-news/queue"

    # Try to get from queue
    if ai_news_queue.exists():
        queue_files = sorted(ai_news_queue.glob("*.txt"))
        if queue_files:
            with open(queue_files[0]) as f:
                content = f.read().strip()
                # Extract title from queue file
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('Title:'):
                        return line.replace('Title:', '').strip()

    # Fall back to random topic
    return random.choice(TOPICS)


def choose_affiliate_product(topic: str) -> dict:
    """Choose relevant affiliate product based on topic."""
    topic_lower = topic.lower()

    # Try to match context
    for product in AFFILIATE_PRODUCTS:
        context_words = product["context"].lower().split(", ")
        if any(word in topic_lower for word in context_words):
            return product

    # Default to random product
    return random.choice(AFFILIATE_PRODUCTS)


def generate_blog_post(topic: str) -> dict:
    """Generate SEO blog post with affiliate link."""

    # Choose affiliate product
    product = choose_affiliate_product(topic)
    affiliate_link = f"https://www.amazon.com/dp/{product['asin']}?tag={AFFILIATE_TAG}"

    # Prompt for blog post
    prompt = f"""Write a 600-900 word SEO-optimized blog post about: {topic}

Requirements:
- Write for a general tech-curious audience (not just experts)
- Use clear H2 headers to structure the content (use ## markdown)
- Include 2-3 bullet point lists for readability
- Natural, engaging tone - not overly formal
- Include 1-2 specific examples or case studies
- Naturally mention the book "{product['name']}" as a recommended resource for readers who want to dive deeper
- End with a brief "What's Next" or "Key Takeaway" section
- Use SEO-friendly language without keyword stuffing

DO NOT include a main H1 title at the start (Hugo will add that).
Start directly with an engaging intro paragraph."""

    content = invoke_claude(prompt)

    # Insert affiliate link
    book_mention = product['name'].split(':')[0]  # Get first part before colon
    if book_mention in content:
        # Replace first mention with linked version
        content = content.replace(
            book_mention,
            f"[{book_mention}]({affiliate_link})",
            1
        )
    else:
        # Append recommendation at end
        content += f"\n\n*For a deeper dive into this topic, check out [{product['name']}]({affiliate_link}).*\n"

    # Generate metadata
    prompt_meta = f"""Based on this topic: "{topic}"

Generate:
1. A catchy, SEO-friendly title (60 chars max) — do NOT include a year like "2024" or "2025" in the title
2. A compelling meta description (150 chars max)
3. 3-5 relevant tags (comma-separated, lowercase)
4. URL-friendly slug (lowercase, hyphens)

Format as JSON:
{{"title": "...", "description": "...", "tags": ["tag1", "tag2"], "slug": "..."}}"""

    meta_json = invoke_claude(prompt_meta, max_tokens=500)

    # Parse JSON from response
    try:
        # Extract JSON from markdown code blocks if present
        if "```json" in meta_json:
            meta_json = meta_json.split("```json")[1].split("```")[0]
        elif "```" in meta_json:
            meta_json = meta_json.split("```")[1].split("```")[0]

        metadata = json.loads(meta_json.strip())
    except:
        # Fallback metadata
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
        metadata = {
            "title": topic[:60],
            "description": f"Exploring {topic} and its implications for AI and tech.",
            "tags": ["ai", "tech"],
            "slug": slug
        }

    return {
        "content": content,
        "metadata": metadata,
        "affiliate_product": product['name']
    }


def save_post(post_data: dict) -> Path:
    """Save post as Hugo markdown file."""
    date = datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    slug = post_data["metadata"]["slug"]

    # Create filename
    filename = f"{date_str}-{slug}.md"
    output_path = Path.home() / "Projects/youtube-channels/blog-engine/content/posts" / filename

    # Create front matter
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

    # Write file
    with open(output_path, 'w') as f:
        f.write(front_matter)
        f.write(post_data['content'])

    print(f"✓ Post saved: {output_path}")
    print(f"  Title: {post_data['metadata']['title']}")
    print(f"  Affiliate product: {post_data['affiliate_product']}")

    return output_path


def main():
    print("=== Circuit Break Blog Post Generator ===\n")

    # Get topic
    topic = get_topic()
    print(f"Topic: {topic}\n")

    # Generate post
    print("Generating blog post with Claude Haiku...")
    post_data = generate_blog_post(topic)

    # Save post
    output_path = save_post(post_data)

    print(f"\n✓ Done! Run ./deploy.sh to publish.")
    return output_path


if __name__ == "__main__":
    main()
