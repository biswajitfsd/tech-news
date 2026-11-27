"""Fetch tech news from the last 24 hours via public RSS/Atom feeds.

Writes a Markdown digest to news/YYYY-MM-DD.md and refreshes LATEST.md.
Standard library only, so the GitHub Actions job needs no installs.
"""
from __future__ import annotations

import datetime as dt
import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = {
    "Hacker News (front page)": "https://hnrss.org/frontpage",
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Wired": "https://www.wired.com/feed/rss",
    "Engadget": "https://www.engadget.com/rss.xml",
}
WINDOW = dt.timedelta(hours=24)
MAX_PER_FEED = 15
ATOM = "{http://www.w3.org/2005/Atom}"
ROOT = Path(__file__).resolve().parent


def parse_date(text: str | None) -> dt.datetime | None:
    if not text:
        return None
    text = text.strip()
    try:
        d = parsedate_to_datetime(text)  # RFC 822 (RSS)
    except (TypeError, ValueError):
        try:
            d = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))  # ISO 8601 (Atom)
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def clean(text: str | None) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", "", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def fetch(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "tech-news-digest/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    items = []
    for it in root.iter("item"):  # RSS 2.0
        items.append({
            "title": clean(it.findtext("title")),
            "link": (it.findtext("link") or "").strip(),
            "date": parse_date(it.findtext("pubDate")),
        })
    for e in root.iter(f"{ATOM}entry"):  # Atom
        link_el = e.find(f"{ATOM}link[@rel='alternate']")
        if link_el is None:  # Elements without children are falsy, so no `or`
            link_el = e.find(f"{ATOM}link")
        items.append({
            "title": clean(e.findtext(f"{ATOM}title")),
            "link": link_el.get("href", "") if link_el is not None else "",
            "date": parse_date(e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated")),
        })
    return items


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - WINDOW
    lines = [
        f"# Tech News — {now:%Y-%m-%d}",
        "",
        f"Stories published between {cutoff:%Y-%m-%d %H:%M} and {now:%Y-%m-%d %H:%M} UTC.",
        "",
    ]
    total, failures = 0, []
    for name, url in FEEDS.items():
        try:
            items = fetch(url)
        except Exception as exc:  # one bad feed shouldn't sink the digest
            failures.append(f"{name}: {exc}")
            continue
        recent = [i for i in items if i["date"] and i["date"] >= cutoff and i["title"] and i["link"]]
        recent.sort(key=lambda i: i["date"], reverse=True)
        recent = recent[:MAX_PER_FEED]
        if not recent:
            continue
        lines += [f"## {name}", ""]
        for i in recent:
            title = i["title"].replace("[", "(").replace("]", ")")
            lines.append(f"- [{title}]({i['link']}) — {i['date']:%H:%M} UTC")
        lines.append("")
        total += len(recent)

    if failures:
        lines += ["## Feeds that failed", ""] + [f"- {f}" for f in failures] + [""]
    lines.append(f"_{total} stories from {len(FEEDS) - len(failures)} of {len(FEEDS)} feeds._")
    body = "\n".join(lines) + "\n"

    out_dir = ROOT / "news"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{now:%Y-%m-%d}.md").write_text(body, encoding="utf-8")
    (ROOT / "LATEST.md").write_text(body, encoding="utf-8")
    print(f"Wrote {total} stories; {len(failures)} feed(s) failed.")
    for f in failures:
        print("  failed:", f, file=sys.stderr)
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
