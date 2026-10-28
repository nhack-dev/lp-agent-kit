"""LP の中身（JSON）とデザインの型から、1ファイルの index.html を作る（手元だけで動く）。

使い方:
  python3 scripts/build_lp.py examples/lp-content.json                 # JSON の design を使う
  python3 scripts/build_lp.py examples/lp-content.json --design bold   # 型を指定（simple / bold / soft）
  python3 scripts/build_lp.py examples/lp-content.json --out dist/index.html

できるもの: CSS も JS もすべて中に入った HTML 1枚（外の読み込みは GA4 を使うときだけ）。
GA4 は .env の GA4_ID（例 G-XXXXXXXXXX）か JSON の tracking.ga4_id があるときだけ入れる。
"""
from __future__ import annotations

import os as _ng_os, sys as _ng_sys  # N-Hack 専用の門（下の3行を消すとこのキットは動きません）
_ng_sys.path.insert(0, _ng_os.path.dirname(_ng_os.path.abspath(__file__)))
import nhack_gate as _nhack_gate  # noqa: E402,F401


import argparse
import html
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DESIGNS = ("simple", "bold", "soft")


def load_env() -> None:
    p = ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def e(s) -> str:
    return html.escape(str(s or ""), quote=True)


def para(s: str) -> str:
    """改行2つで段落、1つで <br>。**太字** だけ使える。"""
    out = []
    for block in re.split(r"\n\s*\n", str(s or "").strip()):
        if not block.strip():
            continue
        t = e(block).replace("\n", "<br>")
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        out.append(f"<p>{t}</p>")
    return "\n".join(out)


def safe_url(u: str) -> str:
    u = str(u or "").strip()
    if u.startswith(("https://", "http://", "mailto:", "tel:", "#", "./", "/")) or not u:
        return e(u)
    return "#"


def cta_block(c: dict, where: str) -> str:
    btns = []
    if c.get("line_url"):
        btns.append(f'<a class="btn btn-line" href="{safe_url(c["line_url"])}" data-cta="line-{where}" '
                    f'rel="noopener">{e(c.get("line_text") or "LINEで受け取る")}</a>')
    if c.get("form_url"):
        btns.append(f'<a class="btn btn-main" href="{safe_url(c["form_url"])}" data-cta="form-{where}" '
                    f'rel="noopener">{e(c.get("form_text") or "申し込む")}</a>')
    if not btns:
        return ""
    micro = f'<p class="micro">{e(c.get("micro"))}</p>' if c.get("micro") else ""
    return f'<div class="cta">{"".join(btns)}{micro}</div>'


def section(cls: str, title: str, inner: str, label: str = "") -> str:
    lab = f'<p class="label">{e(label)}</p>' if label else ""
    h = f"<h2>{e(title)}</h2>" if title else ""
    return f'<section class="sec s-{cls}"><div class="wrap">{lab}{h}{inner}</div></section>'


def build(d: dict, design: str, ga4: str) -> str:
    meta = d.get("meta", {})
    hero = d.get("hero", {})
    cta = d.get("cta", {})
    parts: list[str] = []

    # ファーストビュー
    img = ""
    if hero.get("image"):
        img = (f'<img class="hero-img" src="{safe_url(hero["image"])}" alt="{e(hero.get("image_alt"))}" '
               f'width="{int(hero.get("image_w", 1200))}" height="{int(hero.get("image_h", 800))}">')
    parts.append(
        '<header class="hero"><div class="wrap">'
        + (f'<p class="eyebrow">{e(hero.get("eyebrow"))}</p>' if hero.get("eyebrow") else "")
        + f'<h1>{e(hero.get("headline"))}</h1>'
        + (f'<p class="sub">{e(hero.get("sub"))}</p>' if hero.get("sub") else "")
        + img + cta_block(cta, "top") + "</div></header>")

    # 本文のブロック（並びは JSON の sections の順）
    for s in d.get("sections", []):
        kind = s.get("type", "text")
        if kind == "list":
            items = "".join(f"<li>{e(x)}</li>" for x in s.get("items", []))
            inner = para(s.get("lead", "")) + f'<ul class="checks">{items}</ul>' + para(s.get("after", ""))
        elif kind == "points":
            cards = "".join(
                f'<div class="card"><p class="num">{i + 1:02d}</p><h3>{e(p.get("title"))}</h3>{para(p.get("body"))}</div>'
                for i, p in enumerate(s.get("items", [])))
            inner = para(s.get("lead", "")) + f'<div class="cards">{cards}</div>'
        elif kind == "offer":
            rows = "".join(f"<li>{e(x)}</li>" for x in s.get("items", []))
            price = f'<p class="price">{e(s.get("price"))}</p>' if s.get("price") else ""
            note = f'<p class="note">{e(s.get("price_note"))}</p>' if s.get("price_note") else ""
            inner = para(s.get("lead", "")) + f'<div class="offer"><ul>{rows}</ul>{price}{note}</div>'
        elif kind == "voices":
            vs = "".join(
                f'<figure class="voice"><blockquote>{para(v.get("text"))}</blockquote>'
                f'<figcaption>{e(v.get("who"))}</figcaption></figure>' for v in s.get("items", []))
            note = f'<p class="note">{e(s.get("note"))}</p>' if s.get("note") else ""
            inner = f'<div class="voices">{vs}</div>{note}'
        elif kind == "faq":
            qs = "".join(f'<details><summary>{e(q.get("q"))}</summary>{para(q.get("a"))}</details>'
                         for q in s.get("items", []))
            inner = f'<div class="faq">{qs}</div>'
        elif kind == "cta":
            inner = para(s.get("lead", "")) + cta_block(cta, s.get("id", "mid"))
        elif kind == "form_embed":
            src = safe_url(s.get("src"))
            inner = para(s.get("lead", "")) + (
                f'<div class="embed"><iframe src="{src}" title="{e(s.get("title") or "フォーム")}" '
                f'loading="lazy" height="{int(s.get("height", 900))}"></iframe></div>')
        else:
            inner = para(s.get("body", ""))
        parts.append(section(kind, s.get("title", ""), inner, s.get("label", "")))

    # 最後のひと押し
    parts.append(section("final", cta.get("final_title", ""), para(cta.get("final_lead", "")) + cta_block(cta, "bottom")))

    # フッター（特商法・プライバシー）
    f = d.get("footer", {})
    links = []
    for key, label in (("tokushoho_url", "特定商取引法に基づく表記"), ("privacy_url", "プライバシーポリシー"),
                       ("contact_url", "お問い合わせ")):
        if f.get(key):
            links.append(f'<a href="{safe_url(f[key])}">{label}</a>')
    footer = ('<footer class="foot"><div class="wrap">'
              + (f'<nav>{" ／ ".join(links)}</nav>' if links else "")
              + (f'<p>{e(f.get("ad_note"))}</p>' if f.get("ad_note") else "")
              + f'<p>&copy; {e(f.get("owner") or meta.get("site_name") or "")}</p></div></footer>')

    sticky = ""
    if cta.get("sticky") and (cta.get("line_url") or cta.get("form_url")):
        u = cta.get("line_url") or cta.get("form_url")
        t = cta.get("line_text") if cta.get("line_url") else cta.get("form_text")
        sticky = (f'<div class="sticky"><a class="btn {"btn-line" if cta.get("line_url") else "btn-main"}" '
                  f'href="{safe_url(u)}" data-cta="sticky">{e(t or "受け取る")}</a></div>')

    ga = ""
    if ga4:
        if not re.fullmatch(r"G-[A-Z0-9]{4,}", ga4):
            raise SystemExit(f"GA4 の ID の形が違います: {ga4}（G- で始まる）")
        ga = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga4}"></script>\n'
              "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
              f"gtag('js',new Date());gtag('config','{ga4}');</script>")

    css = (ROOT / "templates" / "designs" / "base.css").read_text(encoding="utf-8") + "\n" + \
        (ROOT / "templates" / "designs" / f"{design}.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s*\n\s*", "\n", css).strip()

    # ボタンが押されたら GA4 に送る（GA4 が無ければ何もしない）
    js = ("<script>document.addEventListener('click',function(ev){var a=ev.target.closest('[data-cta]');"
          "if(a&&window.gtag){gtag('event','cta_click',{cta_id:a.getAttribute('data-cta'),link_url:a.href});}});</script>")

    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    og_img = f'<meta property="og:image" content="{safe_url(meta.get("og_image"))}">' if meta.get("og_image") else ""
    canonical = f'<link rel="canonical" href="{safe_url(meta.get("url"))}">' if meta.get("url") else ""
    return f"""<!doctype html>
<html lang="ja">
<head>
{ga}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(meta.get("title") or hero.get("headline"))}</title>
<meta name="description" content="{e(meta.get("description"))}">
<meta property="og:title" content="{e(meta.get("title") or hero.get("headline"))}">
<meta property="og:description" content="{e(meta.get("description"))}">
<meta property="og:type" content="website">
{og_img}
{canonical}
{robots}
<style>
{css}
</style>
</head>
<body class="d-{design}">
{"".join(parts)}
{footer}
{sticky}
{js}
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--design", choices=DESIGNS)
    ap.add_argument("--out", default=str(ROOT / "dist" / "index.html"))
    a = ap.parse_args()
    load_env()
    d = json.loads(pathlib.Path(a.content).read_text(encoding="utf-8"))
    design = a.design or d.get("design", "simple")
    if design not in DESIGNS:
        print(f"デザインは {', '.join(DESIGNS)} のどれかです: {design}")
        return 2
    ga4 = (d.get("tracking") or {}).get("ga4_id") or os.environ.get("GA4_ID", "")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    page = build(d, design, ga4.strip())
    out.write_text(page, encoding="utf-8")
    print(f"できました: {out}（{len(page.encode('utf-8')) / 1024:.1f} KB・デザイン {design}・GA4 {'あり' if ga4 else 'なし'}）")
    print("次: python3 scripts/check_lp.py " + str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
