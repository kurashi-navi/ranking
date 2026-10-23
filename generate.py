#!/usr/bin/env python3
"""ペット用品 楽天アフィリエイトサイト 自動生成 (標準ライブラリのみ)
内容の追加・変更は content.json を編集してください。"""
import os, re, sys, json, time, html, datetime
import urllib.request, urllib.parse, urllib.error

HITS = 12
APP_ID = os.environ.get("RAKUTEN_APP_ID", "")
ACCESS_KEY = os.environ.get("RAKUTEN_ACCESS_KEY", "")
AFF_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "")
owner, name = os.environ.get("GITHUB_REPOSITORY", "user/repo").split("/")
SITE_URL = os.environ.get("SITE_URL") or f"https://{owner}.github.io/{name}/"
_u = urllib.parse.urlsplit(SITE_URL)
ORIGIN = f"{_u.scheme}://{_u.netloc}"
API = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
STAMP = NOW.strftime("%Y年%m月%d日")
STAMP_T = NOW.strftime("%Y年%m月%d日 %H:%M")

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
            req = urllib.request.Request(url, headers={"Referer": SITE_URL, "Origin": ORIGIN, "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            items = [i.get("Item", i) for i in data.get("Items", [])]
            return [i for i in items if int(i.get("itemPrice") or 0) > 0]
        except urllib.error.HTTPError as ex:
            body = ex.read().decode("utf-8", "replace")[:300]
            last = f"HTTP {ex.code} {body}"
            if ex.code in (400, 401, 403, 404):
                break  # 設定ミスはリトライしても直らない
            time.sleep(3)
        except Exception as ex:  # noqa
            last = ex
            time.sleep(3)
    raise RuntimeError(f"{kw}: {last}")


# ---------- 表示用ヘルパー ----------
PROMO = re.compile(
    r"楽天[0-9０-９]*位|楽天ランキング[0-9０-９]*位|クーポン(?:配布中|利用|適用)?|送料無料|"
    r"ポイント[0-9０-９]+倍|[Pp][0-9０-９]+倍|あす楽|半額|セール|SALE|Sale|最安値?|"
    r"数量限定|期間限定|限定|[0-9０-９]+[%％]\s?OFF|OFF|お買い物マラソン|ポイント(?:UP|アップ)")
BRACKET = re.compile(r"[【\[［《〈][^】\]］》〉]*[】\]］》〉]|★[^★]*★|☆[^☆]*☆")


def clean_name(n):
    """商品名から販促文言を取り除く（商品の特徴を示す【】は残す）"""
    s = BRACKET.sub(lambda m: " " if PROMO.search(m.group(0)) else m.group(0), n)
    s = PROMO.sub(" ", s)
    s = re.sub(r"[\s　]+", " ", s)
    s = re.sub(r"^[\s/・\-＼／!！]+|[\s/・\-＼／!！]+$", "", s)
    return s if len(s) >= 6 else n


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


def short(s, n=64):
    return s if len(s) <= n else s[:n] + "…"


def link_of(it):
    return it.get("affiliateUrl") or it.get("itemUrl") or "#"


def nm(it, n=64):
    return short(clean_name(it.get("itemName", "")), n)


def badges(items):
    b = {}
    if not items:
        return b
    top = max(range(len(items)), key=lambda i: num(items[i].get("reviewCount")))
    b.setdefault(top, []).append("レビュー件数 No.1")
    rated = [(num(it.get("reviewAverage")), i) for i, it in enumerate(items) if num(it.get("reviewCount")) >= 30]
    if rated:
        b.setdefault(max(rated)[1], []).append("評価が高い（レビュー30件以上）")
    return b


CSS = """:root{--bg:#fffaf3;--fg:#2b2622;--mut:#7a6f66;--card:#fff;--line:#f0e4d4;--ac:#e8590c;--ac2:#fff1e6;--hero1:#ffe8cc;--hero2:#fff4e6}
@media(prefers-color-scheme:dark){:root{--bg:#1b1815;--fg:#f4ece4;--mut:#b5a89b;--card:#26221e;--line:#3a332c;--ac:#ff8f4d;--ac2:#33261c;--hero1:#3a2a1d;--hero2:#26221e}}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:64px}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.8 -apple-system,'Hiragino Sans','Noto Sans JP',sans-serif}
a{color:var(--ac)}main{max-width:720px;margin:0 auto;padding:0 16px 24px}
header.top{background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
header.top div{max-width:720px;margin:0 auto;padding:8px 16px;display:flex;justify-content:space-between;align-items:center;gap:6px;flex-wrap:wrap}
header.top a.logo{font-weight:800;color:var(--fg);text-decoration:none}
header.top nav a{display:inline-block;padding:8px 8px;text-decoration:none;font-size:14px;font-weight:600}
.pr{font-size:12px;color:var(--mut);background:var(--ac2);border-radius:8px;padding:6px 10px;margin:12px 0}
.hero{background:linear-gradient(135deg,var(--hero1),var(--hero2));border-radius:20px;padding:24px 16px;margin:16px 0;text-align:center}
.hero h1{margin:0 0 8px;font-size:23px;line-height:1.45}.hero p{margin:0 0 14px;color:var(--mut);font-size:14px}
.big{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.big a{display:block;background:var(--card);border:2px solid var(--ac);border-radius:16px;padding:14px 8px;text-decoration:none;color:var(--fg);font-weight:800;font-size:17px}
.big a small{display:block;font-weight:500;font-size:12px;color:var(--mut)}.big a span{display:block;font-size:30px;line-height:1.3}
h1{font-size:23px;line-height:1.45}h2{font-size:19px;margin:30px 0 10px;padding-left:10px;border-left:5px solid var(--ac)}h3{font-size:16px;margin:20px 0 6px}
.m{font-size:13px;color:var(--mut)}.lead{font-size:16px}
.box{background:var(--ac2);border-radius:12px;padding:10px 14px;margin:12px 0;font-size:14px;line-height:1.7}
.toc{margin:10px 0}.toc a,.chips a{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:8px 14px;margin:4px 4px 0 0;font-size:14px;text-decoration:none;min-height:40px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px;text-decoration:none;color:var(--fg);display:block}
.tile img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:10px}
.tile .tg{font-size:11px;color:var(--ac);font-weight:700;margin-top:6px;display:block}
.tile b{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-size:13px;line-height:1.5}
.tile .pc{color:var(--ac);font-weight:800;font-size:15px;display:block}.tile .m{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin:14px 0;display:flex;gap:12px}
.card img{width:104px;height:104px;object-fit:contain;border-radius:10px;background:#fff;flex:none}
.card .body{flex:1;min-width:0}.card.best{border:2px solid var(--ac);flex-direction:column;align-items:center;text-align:center}.card.best img{width:200px;height:200px}
.card.best .body{width:100%}
.rank{font-weight:800;color:var(--ac)}.price{font-weight:800;font-size:19px;line-height:1.5}.st{color:#f59f00;letter-spacing:1px}
.nm{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;line-height:1.55;margin:2px 0}
.rv{font-size:13px;color:var(--mut);line-height:1.6}.rv b{color:var(--fg)}
.bd{display:inline-block;font-size:11px;font-weight:700;background:var(--ac);color:#fff;border-radius:6px;padding:1px 8px;margin:0 4px 4px 0}
.btn{display:block;text-align:center;background:var(--ac);color:#fff!important;font-weight:800;padding:13px 16px;border-radius:12px;text-decoration:none;margin-top:10px;min-height:48px}
.prt{font-size:10px;font-weight:700;border:1px solid #fff;border-radius:4px;padding:0 4px;margin-left:6px;vertical-align:middle}
.tips{list-style:none;counter-reset:t;padding:0}.tips li{counter-increment:t;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px 10px 48px;margin:8px 0;position:relative}
.tips li:before{content:counter(t);position:absolute;left:12px;top:10px;width:26px;height:26px;border-radius:50%;background:var(--ac);color:#fff;text-align:center;font-weight:800;line-height:26px}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.5}th,td{border:1px solid var(--line);padding:6px;text-align:left;vertical-align:top}th{background:var(--ac2)}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:8px 0}summary{font-weight:700;cursor:pointer;min-height:32px}
.cc{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:10px 0;text-decoration:none;color:var(--fg)}
.cc b{display:block;font-size:17px}.cc .go{color:var(--ac);font-weight:700;font-size:14px;display:block;margin-top:4px}
.tgt{display:inline-block;font-size:11px;font-weight:700;color:var(--ac);border:1px solid var(--ac);border-radius:999px;padding:0 8px;margin-bottom:4px}
.up{text-align:center;margin:24px 0 0}.up a{display:inline-block;padding:10px 20px;border:1px solid var(--line);border-radius:999px;text-decoration:none;background:var(--card)}
footer{font-size:12px;color:var(--mut);margin:36px 0 12px;border-top:1px solid var(--line);padding-top:14px}"""


def layout(title, body, desc=""):
    gv = CONF.get("google_verification", "")
    meta_gv = f'<meta name="google-site-verification" content="{e(gv)}">' if gv else ""
    nav = "".join(f'<a href="g-{c["slug"]}.html">{c["emoji"]}{e(c["name"])}</a>' for c in CONF["categories"])
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website">
<meta name="theme-color" content="#e8590c">{meta_gv}<style>{CSS}</style></head><body id="top">
<header class="top"><div><a class="logo" href="index.html">🐾 {e(SITE)}</a><nav>{nav}<a href="about.html">運営方針</a></nav></div></header>
<main><p class="pr">【PR】本ページは広告（楽天アフィリエイト）を含みます。</p>{body}
<p class="up"><a href="#top">↑ ページ上部へ</a></p>
<footer>価格・在庫・レビュー件数は{STAMP_T}（日本時間）に自動取得した情報です。購入前に、楽天市場の各商品ページで最新の情報をご確認ください。<br>
<a href="about.html">選定基準・広告について（運営方針）</a></footer></main></body></html>"""


def product_card(it, n, bd, best=False):
    img = img_of(it)
    im = f'<img src="{e(img)}" alt="{e(nm(it, 40))}" loading="lazy">' if img else ""
    bs = "".join(f'<span class="bd">{e(x)}</span>' for x in bd if not (best and x == "レビュー件数 No.1"))
    label = "レビュー件数 No.1" if best else f"{n}位"
    avg, cnt = num(it.get("reviewAverage")), int(num(it.get("reviewCount")))
    rv = (f'<span class="st">{stars(avg)}</span> 評価：<b>{avg:.2f}点</b>' if avg > 0 else "評価：なし") + \
         f' ／ レビュー件数：<b>{cnt:,}件</b>'
    return f"""<div class="card{' best' if best else ''}">{im}<div class="body">
<div class="rank">{label}</div>{bs}<div class="nm">{e(nm(it))}</div>
<div class="price">{yen(it.get('itemPrice'))}</div>
<div class="rv">{rv}<br>{e(it.get('shopName', ''))}</div>
<a class="btn" href="{e(link_of(it))}" rel="nofollow sponsored noopener" target="_blank">楽天市場で価格・在庫を見る<span class="prt">PR</span></a></div></div>"""


def render(cat, p, items, siblings):
    bd = badges(items)
    top_i = max(range(len(items)), key=lambda i: num(items[i].get("reviewCount")))
    prices = [int(num(i.get("itemPrice"))) for i in items]
    o = [f"<p class='m'><a href='index.html'>トップ</a> › <a href='g-{cat['slug']}.html'>{cat['emoji']}{e(cat['name'])}</a></p>",
         f"<h1>{e(p['h1'])} 人気ランキング</h1>",
         f"<p class='lead'>{e(p.get('lead', ''))}</p>",
         f"<div class='box'>📊 <b>ランキングの見方</b><br>楽天市場で「{e(p['kw'])}」を検索し、<b>レビュー件数が多い順</b>に表示しています。"
         "順位は人気の目安で、評価の高さや価格の安さを示すものではありません。評価点とレビュー件数は、商品ごとに別々に表示しています。"
         " <a href='about.html'>選定基準・広告について</a></div>",
         f"<p class='m'>情報取得：{STAMP_T}｜掲載{len(items)}商品｜価格帯 {min(prices):,}円〜{max(prices):,}円（容量・入数は商品ごとに異なります）</p>"]
    toc = [("pick", "レビュー1位")]
    if p.get("tips"):
        toc.append(("tips", "選び方"))
    if len(items) >= 3:
        toc.append(("compare", "上位3商品の比較"))
    toc.append(("rank", "ランキング"))
    if p.get("faq"):
        toc.append(("faq", "よくある質問"))
    o.append("<div class='toc'>" + "".join(f"<a href='#{a}'>{t}</a>" for a, t in toc) + "</div>")
    o.append("<h2 id='pick'>レビュー件数がいちばん多い商品</h2>" + product_card(items[top_i], 1, bd.get(top_i, []), best=True))
    if p.get("tips"):
        o.append("<h2 id='tips'>失敗しない選び方</h2><ol class='tips'>" + "".join(f"<li>{e(t)}</li>" for t in p["tips"]) + "</ol>"
                 "<p class='m'>ペットの年齢・体質・アレルギーなどには個体差があります。不安がある場合は、獣医師に相談してください。</p>")
    if len(items) >= 3:
        rows = "".join(f"<tr><td>{n}位 {e(nm(it, 22))}</td><td>{yen(it.get('itemPrice'))}</td>"
                       f"<td>{num(it.get('reviewAverage')):.2f}点</td><td>{int(num(it.get('reviewCount'))):,}件</td></tr>"
                       for n, it in enumerate(items[:3], 1))
        o.append("<h2 id='compare'>上位3商品の比較</h2><div class='tw'><table><tr><th>商品</th><th>価格</th><th>評価</th><th>レビュー件数</th></tr>"
                 + rows + "</table></div><p class='m'>容量・入数・対象年齢は商品ごとに異なります。単価は商品ページでご確認ください。</p>")
    o.append(f"<h2 id='rank'>人気ランキング TOP{len(items)}</h2><p class='m'>レビュー件数が多い順です（{STAMP_T}取得）。</p>")
    for n, it in enumerate(items, 1):
        o.append(product_card(it, n, bd.get(n - 1, [])))
    if p.get("faq"):
        o.append("<h2 id='faq'>よくある質問</h2>" + "".join(
            f"<details><summary>{e(f['q'])}</summary><p>{e(f['a'])}</p></details>" for f in p["faq"]))
    same = [x for x in siblings if x["slug"] != p["slug"] and x.get("group") == p.get("group")]
    rest = [x for x in siblings if x["slug"] != p["slug"] and x not in same]
    rel = (same + rest)[:5]
    if rel:
        o.append("<h2>あわせてチェック</h2><div class='chips'>" + "".join(
            f"<a href='{x['slug']}.html'>{e(x['h1'])}</a>" for x in rel) + "</div>")
    o.append("<h2>ほかのカテゴリ</h2><div class='chips'>" + "".join(
        f"<a href='g-{c['slug']}.html'>{c['emoji']}{e(c['name'])}の一覧</a>" for c in CONF["categories"])
        + "<a href='index.html'>トップへ</a></div>")
    return "".join(o)


def groups_of(pages):
    order, d = [], {}
    for p in pages:
        g = p.get("group", "その他")
        if g not in d:
            d[g] = []
            order.append(g)
        d[g].append(p)
    return [(g, d[g]) for g in order]


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
                if not made and len(failed) >= 2 and "HTTP 40" in str(ex):
                    sys.exit(f"楽天APIに拒否されました。原因: {ex}")
                continue
            time.sleep(1.2)  # 1秒あたり1リクエスト程度に抑える
            if len(items) < 2:
                failed.append(p["kw"])
                continue
            made.setdefault(c["slug"], []).append((p, items))
            top = max(items, key=lambda i: num(i.get("reviewCount")))
            picks.append((c["slug"], num(top.get("reviewCount")), top, p, c))
    if not made:
        sys.exit("全ページの取得に失敗しました（キー/Referer/URL登録を確認）")

    # 各ランキングページ・カテゴリページ
    for c in CONF["categories"]:
        pages = made.get(c["slug"], [])
        sib = [p for p, _ in pages]
        for p, items in pages:
            write(f"{p['slug']}.html", layout(f"{p['h1']} 人気ランキング｜{SITE}", render(c, p, items, sib), p.get("lead", "")))
            urls.append(f"{SITE_URL}{p['slug']}.html")
        if pages:
            body = [f"<p class='m'><a href='index.html'>トップ</a> › {c['emoji']}{e(c['name'])}</p>",
                    f"<h1>{c['emoji']}{e(c['name'])}の人気ランキング</h1><p class='lead'>{e(c.get('desc', ''))}</p>",
                    "<div class='box'>各ランキングは、楽天市場のレビュー件数が多い順です。気になる項目を選んでください。</div>"]
            for g, ps in groups_of(sib):
                body.append(f"<h2>{e(g)}</h2>")
                for p in ps:
                    body.append(f"<a class='cc' href='{p['slug']}.html'><span class='tgt'>対象：{e(p.get('target', '全般'))}</span>"
                                f"<b>{e(p['h1'])} 人気ランキング</b><span class='m'>{e(p.get('lead', ''))}</span>"
                                f"<span class='go'>ランキングを見る →</span></a>")
            body.append("<h2>ほかのカテゴリ</h2><div class='chips'>" + "".join(
                f"<a href='g-{x['slug']}.html'>{x['emoji']}{e(x['name'])}の一覧</a>" for x in CONF["categories"] if x["slug"] != c["slug"])
                + "<a href='index.html'>トップへ</a></div>")
            write(f"g-{c['slug']}.html", layout(f"{c['name']}の人気ランキング｜{SITE}", "".join(body), c.get("desc", "")))
            urls.append(f"{SITE_URL}g-{c['slug']}.html")

    # トップページ
    big = "".join(f"<a href='g-{c['slug']}.html'><span>{c['emoji']}</span>{e(c['name'])}を探す"
                  f"<small>{len(made[c['slug']])}種類のランキング</small></a>" for c in CONF["categories"] if made.get(c["slug"]))
    tiles = []
    for c in CONF["categories"]:
        mine = sorted([x for x in picks if x[0] == c["slug"]], key=lambda x: -x[1])[:3]
        for _, cnt, it, p, _c in mine:
            tiles.append(f"<a class='tile' href='{p['slug']}.html'><img src='{e(img_of(it))}' alt='' loading='lazy'>"
                         f"<span class='tg'>{c['emoji']}{e(p['h1'])}</span><b>{e(nm(it, 40))}</b>"
                         f"<span class='pc'>{yen(it.get('itemPrice'))}</span>"
                         f"<span class='m'>レビュー {int(cnt):,}件</span></a>")
    sections = []
    for c in CONF["categories"]:
        if made.get(c["slug"]):
            sections.append(f"<h2>{c['emoji']}{e(c['name'])}</h2>")
            for g, ps in groups_of([p for p, _ in made[c["slug"]]]):
                chips = "".join(f"<a href='{p['slug']}.html'>{e(p['h1'])}</a>" for p in ps)
                sections.append(f"<h3>{e(g)}</h3><div class='chips'>{chips}</div>")
    write("index.html", layout(SITE, f"""<div class="hero"><h1>{e(CONF['hero_title']).replace(chr(10), '<br>')}</h1>
<p>{e(CONF['hero_sub'])}</p><div class="big">{big}</div></div>
<div class="box">📊 <b>ランキングの見方</b><br>楽天市場のレビュー件数が多い順に、毎日自動で更新しています。順位は人気の目安です。<a href="about.html">選定基準・広告について</a></div>
<h2>人気商品 TOP6</h2><p class='m'>犬用品・猫用品それぞれで、レビュー件数が特に多い商品です（{STAMP}更新）。</p>
<div class='grid'>{''.join(tiles)}</div>
<h2 style="margin-top:36px">目的から探す</h2>{''.join(sections)}""", CONF["hero_sub"]))

    about = "".join(f"<p>{e(t)}</p>" for t in CONF["about"])
    write("about.html", layout(f"運営方針・広告表示｜{SITE}", f"<h1>運営方針・広告表示について</h1>{about}"))
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{u}</loc><lastmod>{NOW.date()}</lastmod></url>" for u in urls) + "</urlset>")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    print(f"OK {sum(len(v) for v in made.values())} pages / failed: {failed}")


main()
