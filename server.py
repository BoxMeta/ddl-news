#!/usr/bin/env python3
"""DDL.NEWS — archive of the Squarespace run, plus a publish API for nightly posts."""

import json
import os
import re
import html
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "posts.json")
PUBLIC = os.path.join(ROOT, "public")
SECRET = os.environ.get("PUBLISH_SECRET", "change-me")
PORT = int(os.environ.get("PORT", "8080"))

DISCLAIMER = (
    "DDL.NEWS is an independent, fan-run resource covering Doginal Dogs Legends. "
    "It is not affiliated with, endorsed by, or operated by Doginal Dogs. "
    "Written by Box Meta, a crypto investor since 2017, Doginal Dogs holder since May 2024, "
    "creative director at Crypto Spaces Network, and a Legends beta tester."
)

def load_posts():
    if not os.path.exists(DATA):
        return []
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)

def save_posts(posts):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA)

def esc(s):
    return html.escape(s or "", quote=True)

def slugify(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or datetime.now().strftime("%Y-%m-%d-recap")

def paragraphs(body):
    body = body or ""
    if "<p" in body.lower() or "<h" in body.lower():
        return body  # trusted publisher html
    chunks = [c.strip() for c in re.split(r"\n\s*\n", body) if c.strip()]
    out = []
    for c in chunks:
        if len(c) < 80 and not c.endswith(".") and not c.startswith("http"):
            out.append(f"<h2>{esc(c)}</h2>")
        else:
            out.append("<p>" + esc(c).replace("\n", "<br>") + "</p>")
    return "\n".join(out)

def fmt_date(iso):
    try:
        d = datetime.strptime(iso[:10], "%Y-%m-%d")
        return d.strftime("%b %-d, %Y").replace(" 0", " ")
    except Exception:
        return iso or ""

def page(title, body, description=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description or 'Independent fan coverage of Doginal Dogs Legends.')}">
<link rel="alternate" type="application/rss+xml" title="DDL.NEWS" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,680&family=Outfit:wght@380;520&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:#17140f; --paper:#f6f1e7; --gold:#c9842a; --line:#e4d9c6; --mute:#6f675c;
    --bg:#100e0c; --card:#1a1714;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--paper); font-family:Outfit, sans-serif; }}
  a {{ color:inherit; }}
  header {{
    display:flex; justify-content:space-between; align-items:center; gap:16px;
    padding:18px 7vw; border-bottom:1px solid #2a241c;
  }}
  .mark {{ font-family:Fraunces, serif; letter-spacing:.08em; font-size:22px; text-decoration:none; }}
  .mark span {{ color:var(--gold); }}
  nav a {{ color:#cfc6b8; text-decoration:none; margin-left:18px; font-size:14px; letter-spacing:.06em; text-transform:uppercase; }}
  main {{ width:min(980px, 88vw); margin:0 auto; padding:42px 0 80px; }}
  .kicker {{ color:var(--gold); letter-spacing:.16em; text-transform:uppercase; font-size:12px; }}
  h1 {{ font-family:Fraunces, serif; font-weight:560; font-size:clamp(36px, 6vw, 68px); line-height:.95; margin:10px 0 18px; }}
  .lead {{ font-size:20px; color:#ddd4c6; max-width:640px; }}
  .grid {{ display:grid; gap:18px; margin-top:36px; }}
  article.card {{
    display:grid; grid-template-columns: 148px 1fr; gap:18px; align-items:center;
    background:var(--card); border:1px solid #2c261e; padding:14px; text-decoration:none;
  }}
  article.card img, .ph {{ width:148px; height:110px; object-fit:cover; background:#2a241c; }}
  article.card h2 {{ font-family:Fraunces, serif; font-size:26px; margin:4px 0 6px; line-height:1.05; }}
  .meta {{ color:var(--mute); font-size:13px; letter-spacing:.04em; text-transform:uppercase; }}
  .story {{ background:var(--paper); color:var(--ink); padding:clamp(22px, 4vw, 48px); }}
  .story h1 {{ font-size:clamp(34px, 5vw, 58px); }}
  .story .meta {{ color:#8a7d6c; }}
  .story p {{ font-size:18px; line-height:1.55; }}
  .story h2 {{ font-family:Fraunces, serif; font-size:28px; margin:28px 0 8px; }}
  .story img {{ width:100%; height:auto; margin:12px 0 18px; }}
  footer {{ padding:28px 7vw 48px; color:#8d8376; font-size:13px; line-height:1.5; border-top:1px solid #2a241c; }}
  .archive {{ display:inline-block; border:1px solid var(--gold); color:var(--gold); font-size:11px; letter-spacing:.12em; text-transform:uppercase; padding:3px 7px; }}
  @media (max-width:700px) {{
    article.card {{ grid-template-columns:1fr; }}
    article.card img, .ph {{ width:100%; height:180px; }}
    header {{ padding:16px 5vw; }}
  }}
</style>
</head>
<body>
<header>
  <a class="mark" href="/">DDL<span>.NEWS</span></a>
  <nav>
    <a href="https://ddltcg.com">TCG</a>
    <a href="https://shop.doginaldogs.com/products/doginal-dogs-legends-rise-of-the-pack-booster-box">Buy</a>
    <a href="https://ddltcg.com/play">Play</a>
    <a href="/news">News</a>
    <a href="/about">About</a>
    <a href="https://x.com/BoxMetaAlt">@BoxMeta</a>
  </nav>
</header>
<main>{body}</main>
</body>
</html>"""

def home(posts):
    if not posts:
        inner = "<p class='lead'>No posts yet.</p>"
    else:
        lead = posts[0]
        rest = posts[1:]
        cards = "\n".join(card(p) for p in rest)
        inner = f"""
        <p class="kicker">Doginal Dogs Legends</p>
       <h1>Daily coverage of Doginal Dogs Legends News!</h1>
        <div class="grid">
          {card(lead, featured=True)}
          {cards}
        </div>"""
    return page("DDL.NEWS — Doginal Dogs Legends", inner, "Independent fan coverage of Doginal Dogs Legends TCG.")

def card(p, featured=False):
    img = p["images"][0] if p.get("images") else ""
    thumb = f'<img src="{esc(img)}" alt="">' if img else '<div class="ph"></div>'
    flag = '<span class="archive">Archive</span>' if p.get("archived") else '<span class="archive">New</span>'
    return f"""<a class="card" href="/news/{esc(p['slug'])}">
      {thumb}
      <div>
        <div class="meta">{esc(fmt_date(p.get('date','')))} · {flag}</div>
        <h2>{esc(p['title'])}</h2>
        <div class="meta">{esc((p.get('description') or p.get('body') or '')[:140])}</div>
      </div>
    </a>"""

def story(p):
    imgs = "\n".join(f'<img src="{esc(i)}" alt="">' for i in p.get("images") or [])
    note = ""
    if p.get("original_url"):
        note = f'<p class="meta">Archived from Squarespace · {esc(p["original_url"])}</p>'
    inner = f"""<article class="story">
      <p class="kicker">{'Squarespace archive' if p.get('archived') else 'DDL.NEWS'}</p>
      <h1>{esc(p['title'])}</h1>
      <p class="meta">{esc(fmt_date(p.get('date','')))} · Box Meta</p>
      {imgs}
      {paragraphs(p.get('body',''))}
      {note}
      <p class="meta">{esc(DISCLAIMER)}</p>
    </article>"""
    return page(p["title"] + " — DDL.NEWS", inner, (p.get("description") or "")[:180])

def about():
    inner = """
    <p class="kicker">About</p>
    <h1>Box Meta</h1>
    <div class="story">
      <p>Box Meta is a Doginal Dogs holder and community member. A crypto investor since 2017 and a Doginal Dogs holder since May 2024, he's played close to 250 games of Doginal Dogs Legends. He runs Wizard Wednesday, producing custom profile pictures for Wizard Doginal Dog holders.</p>
      <p>DDL.NEWS is independent and not affiliated with, endorsed by, or operated by Doginal Dogs.</p>
      <p>More at boxmeta.xyz · @BoxMetaAlt</p>
    </div>"""
    return page("About — DDL.NEWS", inner)

def rss(posts):
    items = []
    for p in posts[:30]:
        items.append(f"""<item>
      <title>{esc(p['title'])}</title>
      <link>https://ddl.news/news/{esc(p['slug'])}</link>
      <pubDate>{esc(p.get('date',''))}</pubDate>
      <description>{esc((p.get('description') or p.get('body') or '')[:300])}</description>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>DDL.NEWS</title><link>https://ddl.news</link>
<description>Independent Doginal Dogs Legends coverage</description>
{''.join(items)}
</channel></rss>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(fmt % args)

    def send(self, code, body, content_type="text/html; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        posts = load_posts()
        if path in ("/", "/index.html"):
            return self.send(200, home(posts))
        if path in ("/news", "/news/"):
            return self.send(200, home(posts))
        if path == "/about":
            return self.send(200, about())
        if path == "/feed.xml":
            return self.send(200, rss(posts), "application/rss+xml; charset=utf-8")
        if path == "/feed.json":
            slim = [{"title": p["title"], "slug": p["slug"], "date": p.get("date"), "url": f"/news/{p['slug']}"} for p in posts]
            return self.send(200, json.dumps(slim), "application/json")
        if path.startswith("/news/"):
            slug = path[len("/news/"):].strip("/")
            for p in posts:
                if p["slug"] == slug:
                    return self.send(200, story(p))
            return self.send(404, page("Not found", "<h1>Not found</h1>"))
        if path.startswith("/images/"):
            fp = os.path.normpath(os.path.join(PUBLIC, path.lstrip("/")))
            if not fp.startswith(PUBLIC) or not os.path.isfile(fp):
                return self.send(404, "missing", "text/plain")
            ext = os.path.splitext(fp)[1].lower()
            ctype = {".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg", ".webp":"image/webp"}.get(ext, "application/octet-stream")
            with open(fp, "rb") as f:
                return self.send(200, f.read(), ctype)
        return self.send(404, page("Not found", "<h1>Not found</h1>"))

    def do_POST(self):
        if urlparse(self.path).path != "/api/publish":
            return self.send(404, "nope", "text/plain")
        auth = self.headers.get("Authorization", "")
        if auth != f"Bearer {SECRET}":
            return self.send(401, json.dumps({"error":"unauthorized"}), "application/json")
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            return self.send(400, json.dumps({"error":"bad json"}), "application/json")
        title = (payload.get("title") or "").strip()
        body = payload.get("body") or payload.get("html") or ""
        if not title or not body:
            return self.send(400, json.dumps({"error":"title and body required"}), "application/json")
        slug = slugify(payload.get("slug") or title)
        posts = load_posts()
        posts = [p for p in posts if p.get("slug") != slug]
        post = {
            "slug": slug,
            "title": title,
            "description": (payload.get("excerpt") or body[:160]).strip(),
            "date": (payload.get("date") or datetime.now().strftime("%Y-%m-%d"))[:10],
            "author": "Box Meta",
            "images": payload.get("images") or [],
            "body": body,
            "archived": False,
            "source": "grok-nightly",
        }
        posts.insert(0, post)
        posts.sort(key=lambda p: p.get("date",""), reverse=True)
        save_posts(posts)
        return self.send(201, json.dumps({"ok": True, "url": f"/news/{slug}"}), "application/json")

if __name__ == "__main__":
    print(f"DDL.NEWS on :{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
