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
BRAND = CONF.get("brand", SITE)
BRAND_SUB = CONF.get("brand_sub", "")
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


def tidy(n, limit=36):
    """キーワード羅列の商品名を、コンパクト表示用に読みやすく整える"""
    toks = clean_name(n).split()
    dig = [bool(re.search(r"\d", t)) for t in toks]
    out, seen = [], set()
    for i, t in enumerate(toks):
        if t in seen:
            continue
        seen.add(t)
        if i < 4 or dig[i] or (i + 1 < len(toks) and dig[i + 1]):
            out.append(t)
    s = " ".join(out)
    return short(s if len(s) >= 6 else clean_name(n), limit)


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


def rich(text):
    """[[強調]] を蛍光ペン風に、改行を<br>に変換"""
    return e(text).replace("[[", "<em>").replace("]]", "</em>").replace(chr(10), "<br>")


CSS = """:root{--rf:'M PLUS Rounded 1c','Hiragino Maru Gothic ProN','Hiragino Sans',sans-serif;
--bg:#f4faf0;--fg:#243024;--mut:#667564;--card:#fff;--line:#dcebd2;--g:#2a8a45;--g2:#1d6e35;--g3:#eaf6e3;--hd:#2a8a45;
--ac:#e8590c;--cta-fg:#fff;--pr:#d9480f;--mark:#fff0a6;--t1:#e6f5dc;--t2:#fff0dc;--t3:#e3f0fb;--sh:0 1px 4px rgba(40,70,40,.10)}
@media(prefers-color-scheme:dark){:root{--bg:#131a13;--fg:#eef5ea;--mut:#a9b8a5;--card:#1d261d;--line:#2f3f2f;--g:#4cae67;--g2:#8fd9a2;--g3:#233323;--hd:#1f5e30;--ac:#ff8f4d;--cta-fg:#2b1500;--pr:#ff9b66;--mark:#5a4d12;--t1:#26402a;--t2:#4a3520;--t3:#223a50;--sh:none}}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html{scroll-behavior:smooth;scroll-padding-top:64px}
h1,h2,h3,.lead,.hero2>p,.box{text-wrap:balance}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.8 -apple-system,'Hiragino Sans','Noto Sans JP',sans-serif}
a{color:var(--g2)}main{max-width:720px;margin:0 auto;padding:0 16px 24px}
h1,h2,h3{font-family:var(--rf)}
header.top{background:var(--hd);position:sticky;top:0;z-index:5;box-shadow:0 2px 6px rgba(0,0,0,.15)}
header.top div{max-width:720px;margin:0 auto;padding:6px 12px;display:flex;justify-content:space-between;align-items:center;gap:4px}
header.top a.logo{font-family:var(--rf);font-weight:800;color:#fff;text-decoration:none;font-size:17px;white-space:nowrap}
header.top nav{display:flex}header.top nav a{display:inline-block;padding:9px 8px;text-decoration:none;font-size:13px;font-weight:700;color:#fff;white-space:nowrap}
.banner{position:relative;margin:0 -16px;padding:14px 8px 28px;overflow:hidden;
background:radial-gradient(circle at 15% 25%,#b8f08f 0,transparent 38%),radial-gradient(circle at 85% 75%,#6fd35c 0,transparent 42%),linear-gradient(135deg,#8ee06a,#38a84a)}
.banner:after{content:'';position:absolute;left:0;right:0;bottom:-1px;height:16px;background:radial-gradient(circle at 12px -5px,transparent 13px,var(--bg) 14px) repeat-x;background-size:24px 16px}
.row{display:flex;justify-content:center;gap:2%}
.fr{flex:0 0 22%;aspect-ratio:1;background:#fff;padding:3px 3px 8px;box-shadow:0 3px 8px rgba(0,0,0,.28);outline:1px solid rgba(0,0,0,.06);transform:rotate(var(--r,0deg))}
.fr img{width:100%;height:100%;object-fit:contain;display:block}
.strip{position:relative;background:#fff;margin:22px 4px 14px;padding:22px 10px 12px;display:flex;align-items:center;justify-content:center;gap:10px;
border-radius:46px 60px 50px 64px/34px 40px 36px 42px;transform:rotate(-1.2deg);box-shadow:0 3px 10px rgba(0,0,0,.2);color:#2a8a45}
.bowl{font-size:34px}.bt{text-align:center;line-height:1.25}
.bt b{display:block;font-family:var(--rf);font-size:clamp(28px,9vw,44px);font-weight:800}
.bt span{display:block;font-family:var(--rf);font-weight:800;font-size:clamp(14px,4.4vw,22px)}
.crown{position:absolute;top:-14px;right:21%;font-size:24px;line-height:1;transform:rotate(12deg)}
.paw{font-size:30px;animation:wag 2.4s ease-in-out infinite;transform-origin:50% 80%}
@keyframes wag{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(10deg)}}
@media(prefers-reduced-motion:reduce){.paw{animation:none}html{scroll-behavior:auto}}
.pr{font-size:12px;color:var(--mut);background:var(--g3);border-radius:8px;padding:6px 10px;margin:12px 0}
.hero2{position:relative;background:linear-gradient(160deg,var(--g3),var(--card));border:1px solid var(--line);border-radius:20px;padding:24px 14px 16px;margin:22px 0 14px;text-align:center}
.ribbon{position:absolute;top:-11px;left:14px;background:var(--ac);color:var(--cta-fg);font-size:12px;font-weight:800;padding:2px 14px;border-radius:999px}
.hero2 h1{margin:0 0 8px;font-size:clamp(20px,5.6vw,30px);line-height:1.5}
.hero2 h1 em{font-style:normal;background:linear-gradient(transparent 60%,var(--mark) 60%);padding:0 2px}
.hero2>p{margin:0;color:var(--mut);font-size:14px}
.trust{list-style:none;padding:0;margin:12px 0 16px;display:flex;flex-wrap:wrap;gap:5px;justify-content:center}
.trust li{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700;color:var(--g2);white-space:nowrap}
.cats{display:grid;gap:12px;grid-template-columns:1fr;text-align:left}@media(min-width:600px){.cats{grid-template-columns:1fr 1fr}}
a.cat{display:block;background:var(--card);border:2px solid var(--g);border-radius:18px;padding:12px;text-decoration:none;color:var(--fg);box-shadow:0 4px 0 var(--g);transition:transform .08s,box-shadow .08s}
a.cat:active{transform:translateY(3px);box-shadow:0 1px 0 var(--g)}
.cat-h{display:flex;align-items:center;gap:8px}.cat-h .em{font-size:32px;line-height:1}.cat-h b{font-size:20px;font-family:var(--rf)}.cat-h small{margin-left:auto;font-size:12px;color:var(--mut)}
.pv{display:flex;gap:10px;align-items:center;margin-top:8px;background:var(--g3);border-radius:12px;padding:8px}
.pv img{width:64px;height:64px;object-fit:contain;background:#fff;border-radius:8px;flex:none}
.pvt{font-size:12px;line-height:1.5;min-width:0}.pvt i{font-style:normal;font-weight:800;color:var(--g2);display:block}
.pvt span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.pvt u{text-decoration:none;color:var(--mut)}
.gob{display:block;box-shadow:0 3px 0 rgba(0,0,0,.18);text-align:center;background:var(--ac);color:var(--cta-fg);font-weight:800;border-radius:999px;padding:11px;margin-top:10px;font-size:15px}
.icons{display:grid;grid-template-columns:repeat(4,1fr);gap:10px 4px}
.ic{display:block;text-align:center;text-decoration:none;color:var(--fg);font-size:12px;line-height:1.35;font-weight:700}
.ic span{display:flex;width:54px;height:54px;margin:0 auto 4px;border-radius:50%;background:var(--t1);border:2px solid var(--card);align-items:center;justify-content:center;font-size:26px;box-shadow:0 2px 0 var(--line),var(--sh)}
.ic.t2 span{background:var(--t2)}.ic.t3 span{background:var(--t3)}.ic:active span{transform:translateY(2px)}
.steps{list-style:none;padding:0;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.steps li{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 4px 10px;text-align:center;font-size:12.5px;line-height:1.5;font-weight:700;position:relative;box-shadow:var(--sh)}
.steps li:not(:last-child):after{content:'›';position:absolute;right:-11px;top:34%;color:var(--g);font-weight:800;font-size:20px}
.steps b{display:block;width:26px;height:26px;line-height:26px;margin:0 auto 4px;border-radius:50%;background:var(--g);color:#fff;font-size:14px}
h1{font-size:23px;line-height:1.45}h2{font-size:20px;margin:32px 0 12px;padding-left:10px;border-left:6px solid var(--g)}h3{font-size:16px;margin:20px 0 6px}
.m{font-size:13px;color:var(--mut)}.lead{font-size:16px}
.box{background:var(--g3);border-radius:12px;padding:10px 14px;margin:12px 0;font-size:14px;line-height:1.7}
.toc{margin:10px 0}.toc a,.chips a{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:8px 14px;margin:4px 4px 0 0;font-size:14px;text-decoration:none;min-height:40px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px;box-shadow:var(--sh);text-decoration:none;color:var(--fg);display:block}
.tile img{width:100%;aspect-ratio:1;object-fit:contain;background:#fff;border-radius:10px}
.tile .tg{font-size:11px;color:var(--g2);font-weight:800;margin-top:6px;display:block}
.tile b{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-size:13px;line-height:1.5}
.tile .pc{color:var(--pr);font-weight:800;font-size:15px;display:block}.tile .m{display:block}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px;margin:14px 0;display:flex;gap:12px;box-shadow:var(--sh)}
.card img{width:104px;height:104px;object-fit:contain;border-radius:10px;background:#fff;flex:none}
.card .body{flex:1;min-width:0}.card.best{border:2px solid var(--g);flex-direction:column;align-items:center;text-align:center}.card.best img{width:200px;height:200px}
.card.best .body{width:100%}
.medal{display:inline-block;min-width:48px;text-align:center;border-radius:999px;padding:0 10px;color:#fff;font-weight:800;font-size:14px;margin-bottom:2px}
.m1{background:linear-gradient(135deg,#f5b400,#e08a00)}.m2{background:linear-gradient(135deg,#a7b0b8,#7d8790)}.m3{background:linear-gradient(135deg,#c98a55,#a2602f)}.m4{background:var(--g)}
.price{font-weight:800;font-size:19px;line-height:1.5;color:var(--pr)}.st{color:#f59f00;letter-spacing:1px}
.nm{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;line-height:1.55;margin:2px 0}
.rv{font-size:13px;color:var(--mut);line-height:1.6}.rv b{color:var(--fg)}
.bd{display:inline-block;font-size:11px;font-weight:700;background:var(--g);color:#fff;border-radius:6px;padding:1px 8px;margin:0 4px 4px 0}
.btn{display:block;text-align:center;background:var(--ac);color:var(--cta-fg)!important;font-weight:800;padding:13px 16px;border-radius:12px;text-decoration:none;margin-top:10px;min-height:48px;box-shadow:0 3px 0 rgba(0,0,0,.18);transition:transform .08s,box-shadow .08s}
.btn:active,.gob:active{transform:translateY(2px);box-shadow:0 1px 0 rgba(0,0,0,.18)}
.prt{font-size:10px;font-weight:700;border:1px solid currentColor;border-radius:4px;padding:0 4px;margin-left:6px;vertical-align:middle}
.tips{list-style:none;counter-reset:t;padding:0}.tips li{counter-increment:t;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px 10px 48px;margin:8px 0;position:relative}
.tips li:before{content:counter(t);position:absolute;left:12px;top:10px;width:26px;height:26px;border-radius:50%;background:var(--g);color:#fff;text-align:center;font-weight:800;line-height:26px}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.5}th,td{border:1px solid var(--line);padding:6px;text-align:left;vertical-align:top}th{background:var(--g3)}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:8px 0}summary{font-weight:700;cursor:pointer;min-height:32px}
.cc{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:10px 0;text-decoration:none;color:var(--fg)}
.cc b{display:block;font-size:17px}.cc .go{color:var(--g2);font-weight:700;font-size:14px;display:block;margin-top:4px}
.tgt{display:inline-block;font-size:11px;font-weight:700;color:var(--g2);border:1px solid var(--g);border-radius:999px;padding:0 8px;margin-bottom:4px}
.up{text-align:center;margin:24px 0 0}.up a{display:inline-block;padding:10px 20px;border:1px solid var(--line);border-radius:999px;text-decoration:none;background:var(--card)}
footer{font-size:12px;color:var(--mut);margin:36px 0 12px;border-top:1px solid var(--line);padding-top:14px}"""


def layout(title, body, desc="", banner=""):
    gv = CONF.get("google_verification", "")
    meta_gv = f'<meta name="google-site-verification" content="{e(gv)}">' if gv else ""
    nav = "".join(f'<a href="g-{c["slug"]}.html">{c["emoji"]}{e(c["name"])}</a>' for c in CONF["categories"])
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website">
<meta name="theme-color" content="#2a8a45">{meta_gv}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@500;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body id="top">
<header class="top"><div><a class="logo" href="index.html">🐾 {e(BRAND)}</a><nav>{nav}<a href="about.html">運営方針</a></nav></div></header>
<main>{banner}<p class="pr">【PR】本ページは広告（楽天アフィリエイト）を含みます。</p>{body}
<p class="up"><a href="#top">↑ ページ上部へ</a></p>
<footer>価格・在庫・レビュー件数は{STAMP_T}（日本時間）に自動取得した情報です。購入前に、楽天市場の各商品ページで最新の情報をご確認ください。<br>
<a href="about.html">選定基準・広告について（運営方針）</a></footer></main></body></html>"""


def medal(n):
    return f'<span class="medal m{n if n <= 3 else 4}">{"👑" if n == 1 else ""}{n}位</span>'


def product_card(it, n, bd, best=False):
    img = img_of(it)
    im = f'<img src="{e(img)}" alt="{e(nm(it, 40))}" loading="lazy">' if img else ""
    bs = "".join(f'<span class="bd">{e(x)}</span>' for x in bd if not (best and x == "レビュー件数 No.1"))
    label = '<span class="medal m1">👑 レビュー件数 No.1</span>' if best else medal(n)
    avg, cnt = num(it.get("reviewAverage")), int(num(it.get("reviewCount")))
    rv = (f'<span class="st">{stars(avg)}</span> 評価：<b>{avg:.2f}点</b>' if avg > 0 else "評価：なし") + \
         f' ／ レビュー件数：<b>{cnt:,}件</b>'
    return f"""<div class="card{' best' if best else ''}">{im}<div class="body">
<div>{label}</div>{bs}<div class="nm">{e(nm(it))}</div>
<div class="price">{yen(it.get('itemPrice'))}</div>
<div class="rv">{rv}<br>{e(it.get('shopName', ''))}</div>
<a class="btn" href="{e(link_of(it))}" rel="nofollow sponsored noopener" target="_blank">楽天市場で価格・在庫を見る<span class="prt">PR</span></a></div></div>"""


def render(cat, p, items, siblings):
    bd = badges(items)
    top_i = max(range(len(items)), key=lambda i: num(items[i].get("reviewCount")))
    prices = [int(num(i.get("itemPrice"))) for i in items]
    o = [f"<p class='m'><a href='index.html'>トップ</a> › <a href='g-{cat['slug']}.html'>{cat['emoji']}{e(cat['name'])}</a></p>",
         f"<h1>{p.get('icon', '')} {e(p['h1'])} 人気ランキング</h1>",
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
        rows = "".join(f"<tr><td>{n}位 {e(tidy(it.get('itemName', ''), 22))}</td><td>{yen(it.get('itemPrice'))}</td>"
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


def banner_html(imgs):
    def fr(u, i):
        return f'<div class="fr" style="--r:{(-4, 3, -2, 5)[i % 4]}deg"><img src="{e(u)}" alt="" loading="eager"></div>'
    top = "".join(fr(u, i) for i, u in enumerate(imgs[:4]))
    bot = "".join(fr(u, i + 2) for i, u in enumerate(imgs[4:8]))
    return (f'<section class="banner"><div class="row">{top}</div><div class="strip"><span class="bowl">🥣</span>'
            f'<div class="bt"><b>{e(BRAND)}</b><span>{e(BRAND_SUB)}</span></div><span class="crown">👑</span><span class="paw">🐾</span></div>'
            f'<div class="row">{bot}</div></section>')


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
                                f"<b>{p.get('icon', '')} {e(p['h1'])} 人気ランキング</b><span class='m'>{e(p.get('lead', ''))}</span>"
                                f"<span class='go'>ランキングを見る →</span></a>")
            body.append("<h2>ほかのカテゴリ</h2><div class='chips'>" + "".join(
                f"<a href='g-{x['slug']}.html'>{x['emoji']}{e(x['name'])}の一覧</a>" for x in CONF["categories"] if x["slug"] != c["slug"])
                + "<a href='index.html'>トップへ</a></div>")
            write(f"g-{c['slug']}.html", layout(f"{c['name']}の人気ランキング｜{SITE}", "".join(body), c.get("desc", "")))
            urls.append(f"{SITE_URL}g-{c['slug']}.html")

    # トップページ: バナー用の商品写真（犬・猫を交互に最大8枚）
    lists = []
    for c in CONF["categories"]:
        l = [x for x in picks if x[0] == c["slug"]]
        lists.append(l[0::2] + l[1::2])
    imgs, i = [], 0
    while len(imgs) < 8 and any(i < len(l) for l in lists):
        for l in lists:
            if i < len(l) and len(imgs) < 8:
                u = img_of(l[i][2])
                if u and u not in imgs:
                    imgs.append(u)
        i += 1

    cards = []
    for c in CONF["categories"]:
        mine = [x for x in picks if x[0] == c["slug"]]
        if not mine:
            continue
        _, cnt, it, p, _c = max(mine, key=lambda x: x[1])
        cards.append(f"""<a class="cat" href="g-{c['slug']}.html"><span class="cat-h"><span class="em">{c['emoji']}</span><b>{e(c['name'])}</b>
<small>{len(made[c['slug']])}種類のランキング</small></span><span class="pv"><img src="{e(img_of(it))}" alt="" loading="lazy">
<span class="pvt"><i>👑 いまレビュー件数が最多</i><span>{e(tidy(it.get('itemName', ''), 40))}</span><u>レビュー {int(cnt):,}件</u></span></span>
<span class="gob">{e(c['name'])}ランキングを見る →</span></a>""")

    icons = []
    for c in CONF["categories"]:
        if made.get(c["slug"]):
            cells = "".join(f"<a class='ic {'t2' if 'おやつ' in p.get('group', '') else ('t3' if 'トイレ' in p.get('group', '') else 't1')}' href='{p['slug']}.html'><span>{p.get('icon', '🐾')}</span>{e(p.get('label', p['h1']))}</a>"
                            for p, _ in made[c["slug"]])
            icons.append(f"<h3>{c['emoji']}{e(c['name'])}</h3><div class='icons'>{cells}</div>")

    tiles = []
    for c in CONF["categories"]:
        mine = sorted([x for x in picks if x[0] == c["slug"]], key=lambda x: -x[1])[:3]
        for k, (_, cnt, it, p, _c) in enumerate(mine):
            tiles.append(f"<a class='tile' href='{p['slug']}.html'><img src='{e(img_of(it))}' alt='' loading='lazy'>"
                         f"<span class='tg'>{'👑' if k == 0 else ''}{c['emoji']}{e(p['h1'])}</span><b>{e(tidy(it.get('itemName', ''), 40))}</b>"
                         f"<span class='pc'>{yen(it.get('itemPrice'))}</span>"
                         f"<span class='m'>レビュー {int(cnt):,}件</span></a>")

    write("index.html", layout(SITE, f"""<div class="hero2"><span class="ribbon">毎日更新</span>
<h1>{rich(CONF['hero_title'])}</h1><p>{e(CONF['hero_sub'])}</p>
<ul class="trust"><li>✔ レビュー数で比較</li><li>✔ 選び方つき</li><li>✔ 運営方針を公開</li></ul>
<div class="cats">{''.join(cards)}</div></div>
<h2>人気カテゴリから探す</h2>{''.join(icons)}
<h2>かんたん3ステップ</h2>
<ol class="steps"><li><b>1</b>犬か猫を<br>選ぶ</li><li><b>2</b>選び方と<br>順位を見る</li><li><b>3</b>楽天で価格を<br>確認する</li></ol>
<div class="box">📊 <b>ランキングの見方</b><br>楽天市場のレビュー件数が多い順に、毎日自動で更新しています。順位は人気の目安です。<a href="about.html">選定基準・広告について</a></div>
<h2>人気商品 TOP6</h2><p class='m'>犬用品・猫用品それぞれで、レビュー件数が特に多い商品です（{STAMP}更新）。</p>
<div class='grid'>{''.join(tiles)}</div>""", CONF["hero_sub"], banner=banner_html(imgs)))

    about = "".join(f"<p>{e(t)}</p>" for t in CONF["about"])
    write("about.html", layout(f"運営方針・広告表示｜{SITE}", f"<h1>運営方針・広告表示について</h1>{about}"))
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          + "".join(f"<url><loc>{u}</loc><lastmod>{NOW.date()}</lastmod></url>" for u in urls) + "</urlset>")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    print(f"OK {sum(len(v) for v in made.values())} pages / failed: {failed}")


main()
