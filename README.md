# Circuit Break Blog

Hugo static blog deployed to GitHub Pages at https://samfoy.github.io/circuit-break-blog

## Quick Start

```bash
# Generate a new blog post (auto-selects topic from ai-news queue or random)
./run_once.sh

# Or generate and deploy manually
python scripts/generate_post.py
bash deploy.sh
```

## Scripts

### `scripts/generate_post.py`
Generates SEO-optimized blog posts with Amazon Associates affiliate links.
- Auto-pulls topics from `~/Projects/youtube-channels/ai-news/queue/` if available
- Falls back to curated AI/tech topics
- Uses Claude Haiku via AWS Bedrock to generate 600-900 word posts
- Weaves in relevant Amazon book affiliate links
- Saves to `content/posts/YYYY-MM-DD-slug.md`

### `scripts/youtube_to_blog.py`
Converts YouTube video scripts to expanded blog posts.

```bash
python scripts/youtube_to_blog.py \
  --title "Video Title" \
  --script-file ~/path/to/script.txt
```

Expands 400-word scripts to 800-word blog posts with:
- SEO structure (H2 headers, bullet lists)
- Affiliate book recommendations
- Hugo front matter

### `deploy.sh`
Builds Hugo site and deploys to GitHub Pages.
- Builds with `hugo --minify`
- Pushes to `gh-pages` branch
- Configures GitHub Pages via `gh` CLI

### `run_once.sh`
One-command workflow: generate post + deploy.

## Configuration

- **hugo.toml**: Hugo config (theme, SEO, analytics)
- **Affiliate tag**: `circuitbreak-20` (hardcoded in scripts)
- **AWS Profile**: `openclaw-bedrock` (Claude Haiku)
- **Python**: Uses `~/Projects/youtube-channels/scary-stories/.venv/bin/python`

## Theme

PaperMod theme (cloned from https://github.com/adityatelange/hugo-PaperMod)

## GitHub Pages

- **Repo**: samfoy/circuit-break-blog
- **Branch**: gh-pages
- **URL**: https://samfoy.github.io/circuit-break-blog

## Requirements

- Hugo (installed via Homebrew)
- GitHub CLI (`gh`)
- Python 3 with boto3
- AWS credentials for Bedrock (profile: openclaw-bedrock)
