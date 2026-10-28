"""できた LP を公開前に機械で確かめる（手元だけで動く・どこにも送らない）。

使い方:
  python3 scripts/check_lp.py dist/index.html
  python3 scripts/check_lp.py dist/index.html --strict   # 要直しがあれば終了コード1

見るもの: 重さ・スマホ表示の設定・タイトルと説明文・画像の alt・申し込みボタンの数と行き先・
特商法とプライバシーポリシーへのリンク・書きかけの印・根拠が要る言い方・医薬品のような言い方・
外から読み込むもの・http のリンク・公開前の noindex。
"""
from __future__ import annotations

import os as _ng_os, sys as _ng_sys  # N-Hack 専用の門（下の3行を消すとこのキットは動きません）
_ng_sys.path.insert(0, _ng_os.path.dirname(_ng_os.path.abspath(__file__)))
import nhack_gate as _nhack_gate  # noqa: E402,F401


import argparse
import html.parser
import pathlib
import re

KONKYO = ["No.1", "ナンバーワン", "日本一", "世界一", "業界初", "日本初", "世界初", "最安", "最高品質", "最強", "100%"]
YOWAI = ["絶対", "必ず", "確実に", "誰でも", "今だけ", "本日限り", "限定", "残りわずか", "通常価格", "稼げる", "儲かる"]
YAKKI = ["治る", "治す", "完治", "予防", "痩せる", "やせる", "脂肪燃焼", "若返", "シミが消", "育毛", "発毛",
         "免疫力", "デトックス", "副作用なし", "医師も推奨"]
TODO = re.compile(r"〇〇|○○|TODO|XXX|\[要確認\]|example\.com")


class P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict]] = []
        self.text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, d):
        if not self._skip:
            self.text.append(d)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    raw = pathlib.Path(a.file).read_text(encoding="utf-8")
    p = P()
    p.feed(raw)
    text = "".join(p.text)
    fix: list[str] = []
    note: list[str] = []

    kb = len(raw.encode("utf-8")) / 1024
    (fix if kb > 300 else note if kb > 100 else []).append(f"HTML の重さ {kb:.0f} KB（目安 100KB 以下）")
    metas = [t[1] for t in p.tags if t[0] == "meta"]
    if not any(m.get("name") == "viewport" for m in metas):
        fix.append("スマホ表示の設定（meta viewport）が無い")
    if not re.search(r"<title>[^<]+</title>", raw):
        fix.append("タイトルが無い")
    if not any(m.get("name") == "description" and m.get("content") for m in metas):
        fix.append("説明文（meta description）が無い")
    if any(m.get("name") == "robots" and "noindex" in (m.get("content") or "") for m in metas):
        note.append("noindex が入っています（検索に出ません）。公開するときは meta.noindex を false に")

    for t, at in p.tags:
        if t == "img" and not at.get("alt"):
            fix.append(f"画像に alt（説明）が無い: {at.get('src', '')[:60]}")
        if t == "img" and not (at.get("width") and at.get("height")):
            note.append(f"画像に width/height が無い（読み込み中に画面がずれる）: {at.get('src', '')[:60]}")

    links = [at for t, at in p.tags if t == "a"]
    ctas = [at for at in links if at.get("data-cta")]
    if len(ctas) < 2:
        fix.append(f"申し込みボタンが {len(ctas)} 個（上と下に最低2つ）")
    for at in ctas:
        h = at.get("href", "")
        if not h or h == "#":
            fix.append(f"ボタン {at.get('data-cta')} の行き先が空")
    for at in links:
        h = at.get("href", "")
        if h.startswith("http://"):
            note.append(f"http のリンク（https にできないか）: {h[:60]}")
    hrefs = " ".join(at.get("href", "") for at in links)
    body_text = text
    if not re.search(r"プライバシー", body_text):
        fix.append("プライバシーポリシーへのリンクが無い（フォーム・計測を使うなら必須）")
    has_price = bool(re.search(r"[0-9０-９,]+\s*円", body_text))
    if has_price and "特定商取引法" not in body_text:
        fix.append("値段があるのに「特定商取引法に基づく表記」へのリンクが無い")
    if "#tokushoho" in hrefs or "#privacy" in hrefs:
        note.append("特商法・プライバシーのリンクが見本（#tokushoho / #privacy）のまま。本物のページへ")

    for m in sorted(set(TODO.findall(raw))):
        fix.append(f"書きかけ・見本の印「{m}」が残っている")
    for w in KONKYO:
        if w in body_text:
            fix.append(f"根拠が要る言い方「{w}」（根拠を横に書くか言い換える）")
    for w in YAKKI:
        if w in body_text:
            fix.append(f"医薬品のような言い方「{w}」（医薬品でなければ言い換える）")
    for w in YOWAI:
        if w in body_text:
            note.append(f"「{w}」… 期限・人数・効果の保証は本当か")

    ext = [at.get("src") for t, at in p.tags if t == "script" and at.get("src")]
    ext += [at.get("href") for t, at in p.tags if t == "link" and at.get("rel") == "stylesheet"]
    if ext:
        note.append("外から読み込むもの: " + ", ".join(e[:50] for e in ext))
        if any("googletagmanager" in e for e in ext) and "Google アナリティクス" not in body_text:
            note.append("GA4 を使っています。プライバシーポリシーに Google アナリティクスの利用を書く（GA の規約）")

    print(f"重さ {kb:.1f} KB ／ ボタン {len(ctas)} ／ リンク {len(links)} ／ 外部読み込み {len(ext)}")
    print(f"\n要直し {len(fix)} 件")
    for x in fix:
        print("  - " + x)
    print(f"\n見てほしい {len(note)} 件")
    for x in note:
        print("  - " + x)
    print("\n※ 機械で拾えるのは入口だけです。最後は playbooks/09-law.md と人の目で。")
    return 1 if (a.strict and fix) else 0


if __name__ == "__main__":
    raise SystemExit(main())
