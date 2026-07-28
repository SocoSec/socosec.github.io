---
layout: post
title: "How this digest works"
date: 2026-07-28 08:00:00 +0000
tags: [AI, SEC]
---

*This is a sample post — the agent will replace it with real digests. Delete it once the first automated post lands.*

Every morning, a small Python agent runs on GitHub Actions. It reads a fixed allowlist of well-known publications (MIT Technology Review, Ars Technica, The Verge, Reuters, Krebs on Security, BleepingComputer, The Hacker News, Schneier on Security, and CISA), keeps only stories from the last day, summarizes each one in two or three neutral sentences, and files a short post here.

Three rules keep it trustworthy:

**Allowlist only.** Any item whose link is not on a listed domain is dropped, even if it appears inside a trusted feed.

**Source on every item.** Each summary links directly to the original report and names the publisher.

**No invention.** Summaries are constrained to the information in the original headline and excerpt — if summarization fails, the publisher's own excerpt is used instead.
