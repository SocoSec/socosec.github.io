# Personal portfolio + automated AI & security news digest

A Jekyll site for GitHub Pages, plus a GitHub Actions agent that publishes a
short daily digest of AI and cybersecurity news from an allowlist of trusted
sources — every item linked to its original publisher.

## Deploy in 5 steps

1. **Create the repo.** For a `https://<username>.github.io` address, name the
   repo exactly `<username>.github.io`. Any other name works too (the site
   lives at `https://<username>.github.io/<repo>` — set `baseurl` in
   `_config.yml` to `/<repo>` in that case).

2. **Push these files.**
   ```bash
   git init && git add . && git commit -m "initial site"
   git branch -M main
   git remote add origin https://github.com/<username>/<repo>.git
   git push -u origin main
   ```

3. **Turn on GitHub Pages.** Repo → Settings → Pages → Source: *Deploy from a
   branch* → Branch: `main`, folder `/ (root)`. GitHub builds Jekyll for you;
   the site is live a minute later.

4. **(Optional but recommended) Add your Anthropic API key** so summaries are
   written by Claude instead of using the publishers' raw excerpts:
   Settings → Secrets and variables → Actions → New repository secret →
   name `ANTHROPIC_API_KEY`. Without it, the agent still works — it falls back
   to the feeds' own summary text.

5. **Test the agent.** Actions tab → *Daily news digest* → *Run workflow*.
   It commits a new post to `_posts/` and Pages rebuilds automatically.
   After that it runs daily at 06:30 UTC (edit the cron in
   `.github/workflows/news-agent.yml`).

## Make it yours

- `_config.yml` — your name, email, GitHub/LinkedIn handles
- `index.html` — replace the three placeholder project cards and the About text
- `agent/sources.yml` — add or remove trusted sources; the agent refuses any
  link that isn't on a listed domain
- `assets/css/style.css` — colors and fonts are all CSS variables at the top

## Run the agent locally

```bash
pip install -r agent/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # optional
python agent/news_agent.py            # writes a post into _posts/
```

`agent/posted.json` tracks which article URLs have already been covered so the
digest never repeats a story.
