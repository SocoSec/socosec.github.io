#!/usr/bin/env python3
"""
Daily AI & Cybersecurity digest agent.

Pipeline:
  1. Read agent/sources.yml (allowlist of trusted feeds).
  2. Fetch each RSS/Atom feed; keep only recent items whose link is on an
     allowlisted domain (defense in depth against feed spam/injection).
  3. Skip anything already covered (agent/posted.json).
  4. Summarize each story in 2-3 neutral sentences:
       - with the Anthropic API if ANTHROPIC_API_KEY is set,
       - otherwise fall back to the feed's own summary text.
  5. Write a Jekyll post to _posts/ with a source link on every item.

Run locally:  pip install -r agent/requirements.txt && python agent/news_agent.py
"""

import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import yaml

ROOT = Path(__file__).resolve().parent.parent
POSTED_FILE = ROOT / "agent" / "posted.json"
POSTS_DIR = ROOT / "_posts"
TOPIC_LABELS = {"AI": "AI", "SEC": "Security"}


def load_sources():
    with open(ROOT / "agent" / "sources.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_posted():
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text(encoding="utf-8")))
    return set()


def save_posted(posted):
    # Keep the file bounded
    POSTED_FILE.write_text(
        json.dumps(sorted(posted)[-2000:], indent=0), encoding="utf-8"
    )


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def clean_text(raw: str, limit: int = 600) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit]


def entry_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def collect(config, posted):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=config.get("lookback_hours", 26))
    per_topic = config.get("max_items_per_topic", 4)
    items = {}

    for topic, sources in config["topics"].items():
        bucket = []
        for src in sources:
            allowed = src["domain"].lower()
            try:
                feed = feedparser.parse(src["feed"])
            except Exception as exc:  # network hiccup on one feed shouldn't kill the run
                print(f"[warn] failed to fetch {src['name']}: {exc}", file=sys.stderr)
                continue
            for entry in feed.entries[:15]:
                link = entry.get("link", "")
                if not link or link in posted:
                    continue
                d = domain_of(link)
                if not (d == allowed or d.endswith("." + allowed)):
                    continue  # not on the allowlist -> drop
                when = entry_time(entry)
                if when and when < cutoff:
                    continue
                bucket.append({
                    "title": clean_text(entry.get("title", ""), 200),
                    "link": link,
                    "source": src["name"],
                    "summary": clean_text(entry.get("summary", "")),
                    "time": when or datetime.now(timezone.utc),
                })
        bucket.sort(key=lambda x: x["time"], reverse=True)
        # One item per source first, for variety
        seen_sources, primary, rest = set(), [], []
        for it in bucket:
            (rest if it["source"] in seen_sources else primary).append(it)
            seen_sources.add(it["source"])
        items[topic] = (primary + rest)[:per_topic]
    return items


def summarize_with_claude(items):
    """Ask Claude for tight, neutral 2-3 sentence summaries. Returns None on any failure."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        payload = [
            {"id": i, "title": it["title"], "source": it["source"], "text": it["summary"]}
            for i, it in enumerate(items)
        ]
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": (
                    "Summarize each news item below in 2-3 neutral, factual sentences "
                    "for a tech digest. Only use information present in the given title "
                    "and text; do not add facts or speculation. Respond ONLY with a JSON "
                    "array of objects like {\"id\": 0, \"summary\": \"...\"} and nothing "
                    "else.\n\n" + json.dumps(payload)
                ),
            }],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        by_id = {row["id"]: row["summary"] for row in json.loads(text)}
        return [by_id.get(i, items[i]["summary"]) for i in range(len(items))]
    except Exception as exc:
        print(f"[warn] Claude summarization failed, using feed summaries: {exc}", file=sys.stderr)
        return None


def build_post(items_by_topic):
    now = datetime.now(timezone.utc)
    flat = [it for topic in items_by_topic.values() for it in topic]
    summaries = summarize_with_claude(flat)
    if summaries:
        for it, s in zip(flat, summaries):
            it["summary"] = s

    tags = " ".join(t for t, its in items_by_topic.items() if its)
    lines = [
        "---",
        "layout: post",
        f'title: "AI & Security Digest — {now.strftime("%B %-d, %Y")}"',
        f"date: {now.strftime('%Y-%m-%d %H:%M:%S')} +0000",
        f"tags: [{', '.join(t for t, its in items_by_topic.items() if its)}]",
        "---",
        "",
        "*Auto-curated from trusted sources. Every summary links to the original report.*",
        "",
    ]
    for topic, its in items_by_topic.items():
        if not its:
            continue
        lines.append(f"## {TOPIC_LABELS.get(topic, topic)}")
        lines.append("")
        for it in its:
            summary = it["summary"] or "See the full report at the source."
            lines.append(f"**[{it['title']}]({it['link']})**")
            lines.append("")
            lines.append(summary)
            lines.append("")
            lines.append(f'<span class="source">Source: {it["source"]}</span>')
            lines.append("")
    return now, "\n".join(lines), tags


def main():
    config = load_sources()
    posted = load_posted()
    items_by_topic = collect(config, posted)

    total = sum(len(v) for v in items_by_topic.values())
    if total == 0:
        print("No new items found in the lookback window; skipping post.")
        return

    now, content, _ = build_post(items_by_topic)
    POSTS_DIR.mkdir(exist_ok=True)
    path = POSTS_DIR / f"{now.strftime('%Y-%m-%d')}-ai-security-digest.md"
    if path.exists():
        print(f"{path.name} already exists for today; skipping.")
        return
    path.write_text(content, encoding="utf-8")

    for topic in items_by_topic.values():
        for it in topic:
            posted.add(it["link"])
    save_posted(posted)
    print(f"Wrote {path.relative_to(ROOT)} with {total} items.")


if __name__ == "__main__":
    main()
