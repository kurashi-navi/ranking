#!/usr/bin/env python3
"""ペット用品 楽天アフィリエイトサイト 自動生成 (標準ライブラリのみ)
内容の追加・変更は content.json を編集してください。"""
import os, sys, json, time, html, datetime, urllib.request, urllib.parse

HITS = 12
APP_ID = os.environ.get("RAKUTEN_APP_ID", "")
ACCESS_KEY = os.environ.get("RAKUTEN_ACCESS_KEY", "")
AFF_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "")
owner, name = os.environ.get("GITHUB_REPOSITORY", "user/repo").split("/")
SITE_URL = os.environ.get("SITE_URL") or f"https://{owner}.github.io/{name}/"
API = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
STAMP = NOW.strftime("%Y年%m月%d日")

if not (APP_ID and ACCESS_KEY and AFF_ID):
    sys.exit("RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY / RAKUTEN_AFFILIATE_ID が未設定です")

CONF = json.load(open("content.json", encoding="utf-8"))
SITE = CONF["site_name"]
e = html.escape


# ---------- 楽天API ----------
def search(kw):
    q = {"applicationId": APP_ID, "accessKey": ACCESS_KEY, "affiliateId": AFF_ID,
         "keyword": kw, "hits": HITS, "sort": "-reviewCount", "imageFlag": 1,
         "format": "json", "formatVersion": 2}
    url = API + "?" + urllib.parse.urlencode(q)
    last = None
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers={"Referer": SITE_URL, "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            items = [i.get("Item", i) for i in data.get("Items", [])]
            return [i for i in items if int(i.get("itemPrice") or 0) > 0]
        except Exception as ex:  # noqa
            last = ex
            time.sleep(3)
    raise RuntimeError(f"{kw}: {last}")


# ---------- 表示用ヘルパー ----------
def num(v, d=0):
    try:
        return float(v)
    except Exception:  # noqa
        return d


def yen(v):
    return f"{int(num(v)):,}円"


def stars(avg):
    n = max(0, min(5, round(num(avg))))
    return "★" * n + "☆" * (5 - n)


def img_of(it):
    imgs = it.get("mediumImageUrls") or []
    if not imgs:
        return ""
    u = imgs[0] if isinstance(imgs[0], str) else imgs[0].get("imageUrl", "")
    return u.split("?")[0] + "?_ex=300x300" if u else ""


def short(s, n=58):
    return s if len(s) <= n else s[:n] + "…"


def link_of(it):
    return it.get("affiliateUrl") or it.get("itemUrl") or "#"


def badges(items):
    b = {}
    if not items:
        return b
    top = max(range(len(items)), key=lambda i: num(items[i].get("reviewCount")))
    b.setdefault(top, []).append("レビュー件数 No.1")
    rated = [(num(it.get("reviewAverage")), i) for i, it in enumerate(items) if num(it.get("reviewCount")) >= 30]
    if rated:
        b.setdefault(max(rated)[1], []).append("高評価（30件以上）")
    return b


CSS = """:root{--bg:#fffaf3;--fg:#2b2622;--mut:#7a6f66;--card:#fff;--line:#f0e4d4;--ac:#e8590c;--ac2:#fff1e6;--hero1:#ffe8cc;--hero2:#fff4e6}
@media(prefers-color-scheme:dark){:root{--bg:#1b1815;--fg:#f4ece4;--mut:#b5a89b;--card:#26221e;--line:#3a332c;--ac:#ff8f4d;--ac2:#33261c;--hero1:#3a2a1d;--hero2:#26221e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.8 -apple-system,'Hiragino Sans','Noto Sans JP',sans-serif}
a{color:var(--ac)}main{max-width:720px;margin:0 auto;padding:0 16px 24px}
header.top{background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
header.top div{max-width:720px;margin:0 auto;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
header.top a.logo{font-weight:800;color:var(--fg);text-decoration:none}header.top nav a{margin-left:14px;text-decoration:none;font-size:14px;font-weight:600}
.pr{font-size:12px;color:var(--mut);background:var(--ac2);border-radius:8px;padding:6px 10px;margin:12px 0}
.hero{background:linear-gradient(135deg,var(--hero1),var(--hero2));border-radius:20px;padding:28px 20px;margin:16px 0;text-align:center}
.hero h1{margin:0 0 8px;font-size:24px;line-height:1.4}.hero p{margin:0 0 16px;color:var(--mut)}
.pill{display:inline-block;background:var(--ac);color:#fff!important;text-decoration:none;font-weight:700;padding:12px 22px;border-radius:999px;margin:4px}
.pill.o{background:transparent;color:var(--ac)!important;border:2px solid var(--ac)}
h1{font-size:23px;line-height:1.45}h2{font-size:19px;margin:32px 0 10px;padding-left:10px;border-left:5px solid var(--ac)}
.m{font-size:13px;color:var(--mut)}.lead{font-size:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px;text-decoration:none;color:var(--fg);display:block}
.tile img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:10px}
.tile b{display:block;font-size:13px;line-height:1.5;margin-top:6px}.tile span{color:var(--ac);font-weight:700;font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin:14px 0;display:flex;gap:12px}
.card img{width:104px;height:104px;object-fit:contain;border-radius:10px;background:#fff;flex:none}
.card.best{border:2px solid var(--ac);flex-direction:column;align-items:center;text-align:center}.card.best img{width:200px;height:200px}
.rank{font-weight:800;color:var(--ac)}.price{font-weight:800;font-size:18px}.st{color:#f59f00;letter-spacing:1px}
.bd{display:inline-block;font-size:11px;font-weight:700;background:var(--ac);color:#fff;border-radius:6px;padding:1px 8px;margin:0 4px 4px 0}
.btn{display:block;text-align:center;background:var(--ac);color:#fff!important;font-weight:800;padding:12px 16px;border-radius:12px;text-decoration:none;margin-top:8px}
.tips{list-style:none;counter-reset:t;padding:0}.tips li{counter-increment:t;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px 10px 48px;margin:8px 0;position:relative}
.tips li:before{content:counter(t);position:absolute;left:12px;top:10px;width:26px;height:26px;border-radius:50%;background:var(--ac);color:#fff;text-align:center;font-weight:800;line-height:26px}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;min-width:420px}th,td{border:1px solid var(--line);padding:8px;text-align:left}th{background:var(--ac2)}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:8px 0}summary{font-weight:700;cursor:pointer}
.chips a{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:4px 14px;margin:4px 4px 0 0;font-size:14px;text-decoration:none}
footer{font-size:12px;color:var(--mut);margin:36px 0 12px;border-top:1px solid var(--line);padding-top:14px}"""


def layout(title, body, desc="", path=""):
    gv = CONF.get("google_verification", "")
    meta_gv = f'<meta name="google-site-verification" content="{e(gv)}">' if gv else ""
    cats = "".join(f'<a href="g-{c["slug"]}.html">{c["emoji"]}{e(c["name"])}</a>' for c in CONF["categories"])
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website">
<meta name="theme-color" content="#e8590c">{meta_gv}<style>{CSS}</style></head><body>
<header class="top"><div><a class="logo" href="index.html">🐾 {e(SITE)}</a><nav>{cats}<a href="about.html">運営方針</a></nav></div></header>
<main><p class="pr">【PR】本ページは広告（楽天アフィリエイト）を含みます。</p>{body}
<footer>価格・在庫・レビュー数は{STAMP}時点に自動取得した情報です。最新情報は楽天市場の各商品ページでご確認ください。<br>
<a href="about.html">運営方針・広告表示について</a></footer></main></body></html>"""


def product_card(it, n, bd, best=False):
    img = img_of(it)
    im = f'<img src="{e(img)}" alt="{e(short(it.get("itemName", ""), 40))}" loading="lazy">' if img else ""
    bs = "".join(f'<span class="bd">{e(x)}</span>' for x in bd)
    label = "レビュー件数がいちばん多い商品" if best else f"{n}位"
    return f"""<div class="card{' best' if best else ''}">{im}<div style="flex:1;width:100%">
<div class="rank">{label}</div>{bs}<div>{e(short(it.get('itemName', '')))}</div>
<div class="price">{yen(it.get('itemPrice'))}</div>
<div class="m"><span class="st">{stars(it.get('reviewAverage'))}</span> {num(it.get('reviewAverage')):.2f}（{int(num(it.get('reviewCount')))}件）｜{e(it.get('shopName', ''))}</div>
<a class="btn" href="{e(link_of(it))}" rel="nofollow sponsored noopener" target="_blank">楽天市場で価格・在庫を見る</a></div></div>"""


def render(cat, p, items, siblings):
    bd = badges(items)
    top_i = max(range(len(items)), key=lambda i: num(items[i].get("reviewCount")))
    prices = [int(num(i.get("itemPrice"))) for i in items]
    o = [f"<p class='m'><a href='index.html'>トップ</a> › <a href='g-{cat['slug']}.html'>{cat['emoji']}{e(cat['name'])}</a></p>",
         f"<h1>{e(p['h1'])} 人気ランキング</h1>",
         f"<p class='lead'>{e(p.get('lead', ''))}</p>",
         f"<p class='m'>{STAMP}更新｜掲載{len(items)}商品｜価格帯 {min(prices):,}円〜{max(prices):,}円（容量・入数はそれぞれ異なります）</p>",
         "<h2>レビュー件数がいちばん多い商品</h2>", product_card(items[top_i], 1, bd.get(top_i, []), best=True)]
    if p.get("tips"):
        o.append("<h2>失敗しない選び方</h2><ol class='tips'>" + "".join(f"<li>{e(t)}</li>" for t in p["tips"]) + "</ol>")
    if len(items) >= 3:
        rows = "".join(f"<tr><td>{n}位 {e(short(it.get('itemName', ''), 26))}</td><td>{yen(it.get('itemPrice'))}</td>"
                       f"<td>{num(it.get('reviewAverage')):.2f}</td><td>{int(num(it.get('reviewCount')))}</td></tr>"
                       for n, it in enumerate(items[:3], 1))
        o.append("<h2>上位3商品の比較</h2><div class='tw'><table><tr><th>商品</th><th>価格</th><th>評価</th><th>レビュー数</th></tr>"
                 + rows + "</table></div>")
    o.append(f"<h2>人気ランキング TOP{len(items)}</h2><p class='m'>楽天市場のレビュー件数が多い順です。</p>")
    for n, it in enumerate(items, 1):
        o.append(product_card(it, n, bd.get(n - 1, [])))
    if p.get("faq"):
        o.append("<h2>よくある質問</h2>" + "".join(
            f"<details><summary>{e(f['q'])}</summary><p>{e(f['a'])}</p></details>" for f in p["faq"]))
    rel = [x for x in siblings if x["slug"] != p["slug"]][:5]
    if rel:
        o.append("<h2>あわせてチェック</h2><div class='chips'>" + "".join(
            f"<a href='{x['slug']}.html'>{e(x['h1'])}</a>" for x in rel) + "</div>")
    return "".join(o)


def write(path, text):
    open(f"_site/{path}", "w", encoding="utf-8").write(text)


def main():
    os.makedirs("_site", exist_ok=True)
    made, failed, urls, picks = {}, [], [SITE_URL, SITE_URL + "about.html"], []
    for c in CONF["categories"]:
        for p in c["pages"]:
            try:
                items = search(p["kw"])
            except Exception as ex:  # noqa
                print("WARN", ex)
                failed.append(p["kw"])
                continue
            time.sleep(1.2)  # 1秒あたり1リクエスト程度に抑える
            if len(items) < 2:
                failed.append(p["kw"])
                continue
            made.setdefault(c["slug"], []).append((p, items))
            top = max(items, key=lambda i: num(i.get("reviewCount")))
            picks.append((num(top.get("reviewCount")), top, p))
    if not made:
        sys.exit("全ページの取得に失敗しました（キー/Referer/URL登録を確認）")

    for c in CONF["categories"]:
        pages = made.get(c["slug"], [])
        sib = [p for p, _ in pages]
        for p, items in pages:
            write(f"{p['slug']}.html", layout(f"{p['h1']} 人気ランキング｜{SITE}", render(c, p, items, sib),
                  p.get("lead", "")))
            urls.append(f"{SITE_URL}{p['slug']}.html")
        if pages:
            cards = "".join(f"<div class='card' style='display:block'><b><a href='{p['slug']}.html'>{e(p['h1'])} 人気ランキング</a></b>"
                            f"<div class='m'>{e(p.get('lead', ''))}</div></div>" for p, _ in pages)
            write(f"g-{c['slug']}.html", layout(f"{c['name']}の人気ランキング｜{SITE}",
                  f"<h1>{c['emoji']}{e(c['name'])}の人気ランキング</h1><p class='lead'>{e(c.get('desc', ''))}</p>{cards}", c.get("desc", "")))
            urls.append(f"{SITE_URL}g-{c['slug']}.html")

    picks.sort(key=lambda x: -x[0])
    tiles = "".join(f"<a class='tile' href='{p['slug']}.html'><img src='{e(img_of(it))}' alt='' loading='lazy'>"
                    f"<b>{e(short(it.get('itemName', ''), 34))}</b><span>{yen(it.get('itemPrice'))}</span>"
                    f"<div class='m'>{e(p['h1'])}</div></a>" for _, it, p in picks[:6])
    btns = "".join(f"<a class='pill{'' if i == 0 else ' o'}' href='g-{c['slug']}.html'>{c['emoji']}{e(c['name'])}</a>"
                   for i, c in enumerate(CONF["categories"]) if made.get(c["slug"]))
    sections = ""
    for c in CONF["categories"]:
        if made.get(c["slug"]):
            chips = "".join(f"<a href='{p['slug']}.html'>{e(p['h1'])}</a>" for p, _ in made[c["slug"]])
            sections += f"<h2>{c['emoji']}{e(c['name'])}</h2><div class='chips'>{chips}</div>"
    write("index.html", layout(f"{SITE}", f"""<div class="hero"><h1>{e(CONF['hero_title']).replace(chr(10), '<br>')}</h1>
<p>{e(CONF['hero_sub'])}</p>{btns}</div><h2>いま人気の商品ピックアップ</h2>
<p class='m'>各ランキングで、レビュー件数が特に多い商品です（毎日自動更新）。</p><div class='grid'>{tiles}</div>{sections}""",
        CONF["hero_sub"]))
    about = "".join(f"<p>{e(t)}</p>" for t in CONF["about"])
    write("about.html", layout(f"運営方針・広告表示｜{SITE}", f"<h1>運営方針・広告表示について</h1>{about}"))
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{u}</loc><lastmod>{NOW.date()}</lastmod></url>" for u in urls) + "</urlset>")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    print(f"OK {sum(len(v) for v in made.values())} pages / failed: {failed}")


main()
