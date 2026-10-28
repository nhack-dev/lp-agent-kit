"""LP の URL に「どこから来たか」の印（UTM）を付けたリンクを作る（手元だけ）。

GA4 は UTM 付きの URL から来た訪問を、参照元・メディア・キャンペーンごとに分けて数えます。

使い方:
  python3 scripts/utm_link.py https://example.github.io/lp/ --campaign spring
  → X・Instagram・LINE・メール・YouTube 用のリンクを一度に出す
  python3 scripts/utm_link.py https://example.github.io/lp/ --campaign spring --source x --medium social --content post1
"""
from __future__ import annotations

import os as _ng_os, sys as _ng_sys  # N-Hack 専用の門（下の3行を消すとこのキットは動きません）
_ng_sys.path.insert(0, _ng_os.path.dirname(_ng_os.path.abspath(__file__)))
import nhack_gate as _nhack_gate  # noqa: E402,F401


import argparse
import urllib.parse

PRESETS = [("x", "social"), ("instagram", "social"), ("threads", "social"), ("line", "message"),
           ("email", "email"), ("youtube", "video")]


def build(url: str, source: str, medium: str, campaign: str, content: str = "") -> str:
    u = urllib.parse.urlsplit(url)
    q = dict(urllib.parse.parse_qsl(u.query))
    q.update({"utm_source": source, "utm_medium": medium, "utm_campaign": campaign})
    if content:
        q["utm_content"] = content
    return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, urllib.parse.urlencode(q), u.fragment))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--campaign", required=True, help="半角英数字とハイフン（例 2026-11-trial）")
    ap.add_argument("--source")
    ap.add_argument("--medium")
    ap.add_argument("--content", default="")
    a = ap.parse_args()
    if a.source:
        print(build(a.url, a.source, a.medium or "referral", a.campaign, a.content))
        return 0
    for s, m in PRESETS:
        print(f"{s:10s} {build(a.url, s, m, a.campaign, a.content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
