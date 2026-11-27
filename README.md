# Tech News Digest

A GitHub Actions workflow that collects tech news from the last 24 hours once a day and commits it as Markdown.

- **Schedule:** daily at 00:30 UTC (06:00 IST). See `.github/workflows/daily-news.yml`.
- **Sources:** Hacker News front page, TechCrunch, The Verge, Ars Technica, Wired and Engadget, read from their public RSS feeds. No API keys needed.
- **Output:** `LATEST.md` always holds the newest digest, and `news/YYYY-MM-DD.md` keeps one file per day. Each run also shows the digest in its Actions run summary.

Run it locally:

```
python fetch_news.py
```

Run it on GitHub now:

```
gh workflow run daily-news.yml
```
