"""Stock Anatomy static site (GitHub Pages, https://9yurrr.github.io/stockanatomy/).

posts/*.json, pages/*.json -> _site/. Paths mirror the old Blogspot URLs (/2026/10/slug.html, /p/about.html)
under BASE, so the old blog can redirect path-for-path.

  python site.py
  python site.py new <html-file> "<title>" "Label1,Label2"   # add a post dated now (KST), then git push
"""
import html, json, re, shutil, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "_site"
SITE = "https://9yurrr.github.io"
BASE = "/stockanatomy"
NAME = "Stock Anatomy"
DESC = "Korean stocks, part by part. We take products apart and find the listed Korean companies that make each component."
GA = "G-9Z2Z1F6EN5"
KST = timezone(timedelta(hours=9))
NAV = ["Market Close", "Korea Brief", "Teardown", "Congress Trades"]
esc = html.escape
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def text_of(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def localize(c):
    """Old blog links -> this site under BASE."""
    c = re.sub(r"https?://stockanatomykr\.blogspot\.com/", "/", c)
    return re.sub(r'href=(["\'])/(?!/)', lambda m: f"href={m[1]}{BASE}/", c)


def load_posts():
    posts = []
    for f in (HERE / "posts").glob("*.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        c = localize(p["content"])
        img = re.search(r'<img[^>]+src="([^"]+)"', c)
        first = re.search(r"<p>(.*?)</p>", c, re.S)
        p.update(content=c, img=img.group(1) if img else "", summary=text_of(first.group(1) if first else c)[:160],
                 date=datetime.fromisoformat(p["published"]).astimezone(KST))
        posts.append(p)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def page(title, body, path, desc=DESC, image="", og_type="website", extra_head=""):
    canon = SITE + BASE + path
    full = title if title == NAME else f"{title} | {NAME}"
    nav = "".join(f'<a href="{BASE}/label/{slug(l)}.html">{esc(l)}</a>' for l in NAV)
    image = image or f"{SITE}{BASE}/assets/og.jpg"
    og_img = f'<meta property="og:image" content="{image}">'
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="max-image-preview:large">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">{og_img}
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="{BASE}/feed.xml">
<link rel="icon" type="image/png" sizes="48x48" href="{BASE}/assets/favicon-48.png"><link rel="apple-touch-icon" href="{BASE}/assets/apple-touch-icon.png">
<link rel="stylesheet" href="{BASE}/style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA}');</script>
{extra_head}</head><body>
<header class="hd"><div class="wrap"><a class="logo" href="{BASE}/"><img src="{BASE}/assets/logo-art-96.png" alt="" height="38">{NAME}</a><nav>{nav}</nav></div></header>
{body}
<footer class="ft"><div class="wrap"><div class="links"><a href="{BASE}/p/about.html">About</a><a href="{BASE}/p/disclaimer.html">Disclaimer</a><a href="{BASE}/archive.html">All posts</a><a href="{BASE}/feed.xml">RSS</a></div>
<small>{esc(DESC)} Not investment advice.</small><small>© {NAME}</small></div></footer>
</body></html>
"""


def card(p):
    thumb = f'<span class="thumb"><img src="{p["img"]}" alt="" loading="lazy"></span>' if p["img"] else ""
    return (f'<a class="card" href="{BASE}{p["path"]}">{thumb}<time>{p["date"]:%b %d, %Y}</time>'
            f'<b>{esc(p["title"])}</b><span class="sum">{esc(p["summary"])}</span></a>')


def write(path, s):
    f = OUT / path.lstrip("/")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(s, encoding="utf-8")


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(HERE / "style.css", OUT / "style.css")
    shutil.copytree(HERE / "assets", OUT / "assets")
    posts = load_posts()
    grid = lambda ps: f'<div class="grid">{"".join(card(p) for p in ps)}</div>'

    for p in posts:
        same = [q for q in posts if q is not p and set(q["labels"]) & set(p["labels"])][:4]
        more = ("<h2>Related</h2><ul>" + "".join(f'<li><a href="{BASE}{q["path"]}">{esc(q["title"])}</a></li>' for q in same) + "</ul>") if same and "related-links" not in p["content"] else ""
        tags = " · ".join(f'<a href="{BASE}/label/{slug(l)}.html">{esc(l)}</a>' for l in p["labels"])
        ld = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": p["title"],
                         "image": [p["img"]] if p["img"] else [], "datePublished": p["published"],
                         "dateModified": p.get("updated", p["published"]), "author": {"@type": "Organization", "name": NAME},
                         "publisher": {"@type": "Organization", "name": NAME}})
        body = (f'<main class="wrap post"><article><h1>{esc(p["title"])}</h1>'
                f'<p class="meta"><time datetime="{p["published"]}">{p["date"]:%B %d, %Y}</time>{" · " + tags if tags else ""}</p>'
                f'<div class="body">{p["content"]}{more}</div></article></main>')
        write(p["path"], page(p["title"], body, p["path"], p["summary"], p["img"], "article",
                              f'<script type="application/ld+json">{ld}</script>\n'))

    home = (f'<section class="hero"><div class="wrap"><p class="kick">Daily Korea market close · Component teardowns</p><h1>Korean stocks,<br>part by part.</h1><p>We take products apart and find the listed Korean companies that make each component, and close every trading day with a short Korea market recap.</p><p class="cta"><a href="{BASE}/label/market-close.html">Latest market close →</a><a href="{BASE}/label/teardown.html">Teardowns →</a></p><img class="art" src="{BASE}/assets/logo-art-600.png" alt="A phone taken apart, with the chip inside highlighted" width="271" height="300"></div></section>'
            f'<main class="wrap"><h2 class="sec">Latest</h2>{grid(posts[:30])}'
            f'<p class="more"><a href="{BASE}/archive.html">All {len(posts)} posts →</a></p></main>')
    write("/index.html", page(NAME, home, "/"))

    labels = sorted({l for p in posts for l in p["labels"]})
    for l in labels:
        ps = [p for p in posts if l in p["labels"]]
        thin = '<meta name="robots" content="noindex,follow">\n' if len(ps) < 3 else ""  # 1-2 post tag pages are thin: keep out of search
        write(f"/label/{slug(l)}.html", page(l, f'<main class="wrap post"><h1>{esc(l)}</h1><p class="meta">{len(ps)} posts</p>{grid(ps)}</main>',
                                            f"/label/{slug(l)}.html", f"{NAME} posts on {l}", extra_head=thin))

    for f in (HERE / "pages").glob("*.json"):
        pg = json.loads(f.read_text(encoding="utf-8"))
        write(pg["path"], page(pg["title"], f'<main class="wrap post"><article><h1>{esc(pg["title"])}</h1><div class="body">{localize(pg["content"])}</div></article></main>', pg["path"]))

    rows = "".join(f'<li><time>{p["date"]:%Y-%m-%d}</time> <a href="{BASE}{p["path"]}">{esc(p["title"])}</a></li>' for p in posts)
    write("/archive.html", page("All posts", f'<main class="wrap post"><h1>All posts ({len(posts)})</h1><ul class="archive">{rows}</ul></main>', "/archive.html"))

    urls = ["/", "/archive.html"] + [f"/label/{slug(l)}.html" for l in labels if sum(l in p["labels"] for p in posts) >= 3] + [p["path"] for p in posts]
    lm = {p["path"]: p.get("updated", p["published"]) for p in posts}
    write("/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{SITE}{BASE}{u}</loc>" + (f"<lastmod>{lm[u]}</lastmod>" if u in lm else "") + "</url>" for u in urls) + "</urlset>\n")
    items = "".join(f"<item><title>{esc(p['title'])}</title><link>{SITE}{BASE}{p['path']}</link><guid>{SITE}{BASE}{p['path']}</guid>"
                    f"<pubDate>{p['date']:%a, %d %b %Y %H:%M:%S %z}</pubDate><description>{esc(p['summary'])}</description></item>" for p in posts[:30])
    write("/feed.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{NAME}</title><link>{SITE}{BASE}/</link>'
          f"<description>{esc(DESC)}</description><language>en</language>{items}</channel></rss>\n")
    (OUT / ".nojekyll").write_text("")
    print(f"built {len(posts)} posts, {len(labels)} labels -> {OUT}")


def new_post(html_file, title, labels):
    """Add a post the way Blogger did: /YYYY/MM/<first ~40 chars of title as slug>.html."""
    now = datetime.now(KST)
    s = slug(title)[:40].rstrip("-")
    s = s[: s.rfind("-")] if len(slug(title)) > 40 and "-" in s else s
    taken = {json.loads(f.read_text(encoding="utf-8"))["path"] for f in (HERE / "posts").glob("*.json")}
    path, i = f"/{now:%Y/%m}/{s}.html", 2
    while path in taken:
        path, i = f"/{now:%Y/%m}/{s}_{i}.html", i + 1
    d = {"title": title, "path": path, "published": now.isoformat(timespec="seconds"), "updated": now.isoformat(timespec="seconds"),
         "labels": [l.strip() for l in labels.split(",") if l.strip()], "content": Path(html_file).read_text(encoding="utf-8")}
    (HERE / "posts" / f"{Path(path).stem}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("added", SITE + BASE + path)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "new":
        new_post(*sys.argv[2:5])
    else:
        build()
