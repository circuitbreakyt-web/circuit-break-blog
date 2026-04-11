#!/usr/bin/env python3
"""
Generate SEO-optimized blog posts with affiliate links using Claude Haiku via AWS Bedrock.
"""

import boto3
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
import re
import random

# AWS Bedrock setup
os.environ.setdefault("AWS_PROFILE", "openclaw-bedrock")

# Load .env from parent directory if present
_env_file = Path(__file__).parent.parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

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
    },
    {
        "name": "AI Superpowers: China, Silicon Valley, and the New World Order",
        "asin": "132854639X",
        "context": "AI geopolitics, China, industry"
    },
    {
        "name": "The Coming Wave: Technology, Power, and the Twenty-First Century's Greatest Dilemma",
        "asin": "0593593952",
        "context": "AI futures, risk, regulation, society"
    },
    {
        "name": "Co-Intelligence: Living and Working with AI",
        "asin": "059371671X",
        "context": "working with AI, productivity, practical use"
    },
    {
        "name": "Chip War: The Fight for the World's Most Critical Technology",
        "asin": "1982172002",
        "context": "semiconductors, chips, hardware, geopolitics"
    },
    {
        "name": "The Worlds I See: Curiosity, Exploration, and Discovery at the Dawn of AI",
        "asin": "1250897939",
        "context": "AI history, deep learning, Fei-Fei Li"
    }
]

# SaaS/Tool affiliate links (higher commission rates)
SAAS_AFFILIATES = [
    {
        "name": "Jasper AI",
        "url": "https://www.jasper.ai/?fpr=circuitbreak",
        "description": "AI writing assistant used by 100,000+ marketers",
        "context": "writing, content, marketing, productivity",
        "cta": "Try Jasper AI free",
    },
    {
        "name": "ElevenLabs",
        "url": "https://elevenlabs.io/?from=circuitbreak",
        "description": "AI voice generation — realistic text-to-speech",
        "context": "voice, audio, text-to-speech, content creation",
        "cta": "Generate AI voices with ElevenLabs",
    },
    {
        "name": "Perplexity AI",
        "url": "https://perplexity.ai",
        "description": "AI-powered search engine",
        "context": "search, research, AI tools, productivity",
        "cta": "Try Perplexity AI",
    },
    {
        "name": "Midjourney",
        "url": "https://www.midjourney.com",
        "description": "AI image generation",
        "context": "image generation, creative AI, design, art",
        "cta": "Create AI art with Midjourney",
    },
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


def choose_saas_affiliate(topic: str) -> dict | None:
    """Choose a relevant SaaS affiliate based on topic."""
    topic_lower = topic.lower()
    for product in SAAS_AFFILIATES:
        context_words = product["context"].lower().split(", ")
        if any(word in topic_lower for word in context_words):
            return product
    return None


def research_topic(topic: str) -> str:
    """
    Fetch real recent data about the topic using Perplexity API.
    Returns a research brief with facts, stats, recent events, and real tools.
    """
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not perplexity_key:
        print("  [research] No PERPLEXITY_API_KEY — skipping web research")
        return ""

    print(f"  [research] Fetching real data for: {topic}")
    try:
        payload = json.dumps({
            "model": "sonar",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Research brief for a tech blog post about: {topic}\n\n"
                        "Return a concise research brief (400 words max) containing:\n"
                        "1. 3-5 recent news items or events (last 6 months) with approximate dates\n"
                        "2. 3-5 real statistics or data points with sources\n"
                        "3. 3-5 real tools, products, or companies relevant to this topic with URLs\n"
                        "4. 1-2 interesting angles or counterintuitive facts worth exploring\n\n"
                        "Be specific. Name real companies, cite real numbers. No filler."
                    )
                }
            ],
            "max_tokens": 800,
            "search_recency_filter": "month",
            "return_citations": True,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.perplexity.ai/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {perplexity_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            brief = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            if citations:
                brief += "\n\nSources: " + ", ".join(citations[:5])
            print(f"  [research] Got {len(brief)} chars of research data")
            return brief
    except Exception as e:
        print(f"  [research] Failed: {e} — continuing without research")
        return ""


def generate_blog_post(topic: str) -> dict:
    """Generate SEO blog post with affiliate link."""

    # Step 0: Research the topic with real data
    research_brief = research_topic(topic)
    research_section = ""
    if research_brief:
        research_section = f"""

RESEARCH BRIEF (use this real data — cite these facts, link to these tools, reference these events):
---
{research_brief}
---
IMPORTANT: Ground your writing in this research. Use the specific numbers, companies, tools, and events listed above. 
Do NOT invent statistics or make vague claims. If you cite a tool, link to its real URL.
"""

    # Choose affiliate product
    product = choose_affiliate_product(topic)
    affiliate_link = f"https://www.amazon.com/dp/{product['asin']}?tag={AFFILIATE_TAG}"

    # Choose SaaS affiliate if relevant
    saas = choose_saas_affiliate(topic)
    saas_block = ""
    if saas:
        saas_block = f"\n\n---\n\n🔧 **Recommended tool:** [{saas['name']}]({saas['url']}) — {saas['description']}. [{saas['cta']} →]({saas['url']})\n"

    # Prompt for blog post
    prompt = f"""You are a senior technology journalist writing for a publication like TechTalks, MIT Technology Review, or Wired. Your readers are tech-curious professionals — smart, busy, and skeptical of hype.
{research_section}
Write a 900-1200 word blog post about: {topic}

STYLE RULES (study and follow these carefully):
- Open with a concrete, surprising, or counterintuitive hook — a real-world event, a striking statistic, or a tension that grabs attention immediately. NOT a generic "AI is transforming..." opener.
- Write like a journalist, not a marketer. State facts, name companies, cite real examples. Be specific: "OpenAI's GPT-4" not "a leading AI model".
- Have a clear argument or thesis — not just "here's what X is", but "here's what people misunderstand about X" or "here's why X matters more than you think"
- Use concrete numbers and comparisons when making a point — pull from the research brief above
- When mentioning real tools people can use, hyperlink them inline using markdown: [Perplexity](https://perplexity.ai), [Hugging Face](https://huggingface.co), etc.
- 2-3 well-chosen H2 sections that build on each other — each section should advance the argument, not just list facts
- Short, punchy paragraphs (2-4 sentences max). Vary sentence length.
- One tight bullet list is fine; avoid multiple listicles — this isn't a "top 10" post
- End with a forward-looking "what this means for you" paragraph — practical, grounded, not hype
- Mention "{product['name']}" naturally as a recommended deep-dive resource (1 sentence, feels earned not forced)

DO NOT:
- Start with "In today's rapidly evolving..." or any variant
- Use the words "delve", "leverage", "paradigm", "transformative", "game-changer", or "revolutionize"
- Include a main H1 title (Hugo adds it automatically)
- Write a listicle disguised as an article
- Invent statistics — only use numbers from the research brief above

TOPIC: {topic}"""

    content = invoke_claude(prompt, max_tokens=3000)

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

    # Append SaaS affiliate block if relevant
    if saas_block:
        content += saas_block

    # Generate metadata
    prompt_meta = f"""Based on this topic: "{topic}"

Generate:
1. A headline-style title that's specific and intriguing (60 chars max) — think Wired/MIT Tech Review style, NOT clickbait. Do NOT include a year like "2024" or "2025".
2. A compelling meta description that teases the argument (150 chars max)
3. 3-5 relevant tags (comma-separated, lowercase, specific not generic)
4. URL-friendly slug (lowercase, hyphens)

Good title examples:
- "Why AI Won't Kill SaaS"
- "The Hidden Cost of Edge AI"
- "Open Source AI's Quiet Takeover"

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
