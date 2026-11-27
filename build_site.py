"""Turn news/*.md digests into a static site in site/ for GitHub Pages.

The digests are written by fetch_news.py in a small, known Markdown subset,
so this converts them directly instead of pulling in a Markdown library.
"""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEWS = ROOT / "news"
SITE = ROOT / "site"
LINK = re.compile(r"^- \[(.+?)\]\((\S+?)\)(?: — (.+))?$")

CSS = """
:root{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--line:#e7e5e4;--accent:#2563eb;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#0c0a09;--fg:#e7e5e4;--muted:#a8a29e;--line:#292524;--accent:#60a5fa;--card:#1c1917}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:760px;margin:0 auto;padding:32px 16px 64px}
header nav{display:flex;gap:16px;font-size:14px;margin-bottom:24px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
h1{font-size:28px;margin:0 0 4px}
h2{font-size:18px;margin:32px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
p.meta,p.note,.time{color:var(--muted);font-size:14px}
ul{list-style:none;padding:0;margin:0}
li{padding:8px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:16px}
li a{color:var(--fg)}li a:hover{color:var(--accent)}
.time{white-space:nowrap}
.archive li{justify-content:flex-start}
"""


def page(title: str, body: str, nav_prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{nav_prefix}style.css"></head>
<body><main>
<header><nav><a href="{nav_prefix}index.html">Latest</a><a href="{nav_prefix}archive.html">Archive</a></nav></header>
{body}
</main></body></html>
"""


def md_to_html(md: str) -> str:
    out, in_list = [], False
    for line in md.splitlines():
        m = LINK.match(line)
        if m:
            if not in_list:
                out.append("<ul>")
                in_list = True
            title, url, when = m.groups()
            out.append(
                f'<li><a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(title)}</a>'
                + (f'<span class="time">{html.escape(when)}</span>' if when else "")
                + "</li>"
            )
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if line.startswith("- "):
            out.append(f"<p class=\"note\">{html.escape(line[2:])}</p>")
        elif line.startswith("## "):
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("_") and line.endswith("_"):
            out.append(f"<p class=\"note\">{html.escape(line.strip('_'))}</p>")
        elif line.strip():
            out.append(f"<p class=\"meta\">{html.escape(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "days").mkdir(parents=True)
    (SITE / "style.css").write_text(CSS, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    days = sorted(NEWS.glob("*.md"), reverse=True)
    for f in days:
        body = md_to_html(f.read_text(encoding="utf-8"))
        (SITE / "days" / f"{f.stem}.html").write_text(page(f"Tech News {f.stem}", body, "../"), encoding="utf-8")

    latest = md_to_html(days[0].read_text(encoding="utf-8")) if days else "<h1>Tech News</h1><p>No digests yet.</p>"
    (SITE / "index.html").write_text(page("Tech News — Latest", latest), encoding="utf-8")

    items = "\n".join(f'<li><a href="days/{f.stem}.html">{f.stem}</a></li>' for f in days)
    archive = f"<h1>Archive</h1><p class=\"meta\">{len(days)} daily digests</p><ul class=\"archive\">{items}</ul>"
    (SITE / "archive.html").write_text(page("Tech News — Archive", archive), encoding="utf-8")
    print(f"Built site with {len(days)} day(s).")


if __name__ == "__main__":
    main()
