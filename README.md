# socosec.github.io

Personal portfolio of **Esmail Abdullah** — cybersecurity engineer, M.S.
Cybersecurity student at Óbuda University, Budapest.

**Live site → https://socosec.github.io**

Alongside the portfolio, this repo runs an autonomous news agent: every
morning a Python script on GitHub Actions reads a fixed allowlist of trusted
publications (MIT Technology Review, Ars Technica, The Verge, Reuters, Krebs
on Security, BleepingComputer, The Hacker News, Schneier on Security, CISA),
summarizes the day's AI and cybersecurity stories, and publishes a short
digest — with every item linked to its source.

## How the agent stays trustworthy

- **Allowlist only** — links not on a listed domain are dropped, even if they
  appear inside a trusted feed (`agent/sources.yml`)
- **No repeats** — covered URLs are tracked in `agent/posted.json`
- **Source on every item** — each summary names and links the publisher
- **No invention** — summaries are constrained to the original headline and
  excerpt; if AI summarization is unavailable, the publisher's own excerpt
  is used

## Stack

- **Site:** Jekyll on GitHub Pages (no build setup — Pages compiles it)
- **Agent:** Python (`agent/news_agent.py`), scheduled by GitHub Actions
  daily at 06:30 UTC (`.github/workflows/news-agent.yml`)
- **Summaries:** Anthropic API (optional, via `ANTHROPIC_API_KEY` secret),
  with a graceful fallback to feed excerpts

## Run the agent locally

    pip install -r agent/requirements.txt
    python agent/news_agent.py
