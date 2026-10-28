"""dist/ を Cloudflare Pages に公開する（Wrangler を使う）。

使い方:
  python3 scripts/deploy_cloudflare.py --project my-lp              # 試し（打つコマンドを出すだけ）
  python3 scripts/deploy_cloudflare.py --project my-lp --create --go  # 初回：プロジェクトを作ってから公開
  python3 scripts/deploy_cloudflare.py --project my-lp --go           # 2回目から：公開

前もって必要なもの: Node.js（npx が動くこと）。
ログインは次のどちらか:
  1) 一度だけ `npx wrangler login` を人が打ってブラウザで許可する
  2) .env に CLOUDFLARE_API_TOKEN と CLOUDFLARE_ACCOUNT_ID を書く（自動で使われる）
"""
from __future__ import annotations

import os as _ng_os, sys as _ng_sys  # N-Hack 専用の門（下の3行を消すとこのキットは動きません）
_ng_sys.path.insert(0, _ng_os.path.dirname(_ng_os.path.abspath(__file__)))
import nhack_gate as _nhack_gate  # noqa: E402,F401


import argparse
import os
import pathlib
import re
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_env() -> None:
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="半角小文字・数字・ハイフン（公開URLの一部になる）")
    ap.add_argument("--dir", default=str(ROOT / "dist"))
    ap.add_argument("--create", action="store_true", help="初回だけ：プロジェクトを作る")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()
    load_env()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,57}", a.project):
        print("プロジェクト名は半角小文字・数字・ハイフンで")
        return 2
    d = pathlib.Path(a.dir)
    if not (d / "index.html").exists():
        print(f"{d}/index.html がありません。先に build_lp.py で作ってください")
        return 2
    cmds = []
    if a.create:
        cmds.append(["npx", "wrangler", "pages", "project", "create", a.project, "--production-branch", "main"])
    cmds.append(["npx", "wrangler", "pages", "deploy", str(d), "--project-name", a.project])
    print("打つコマンド:")
    for c in cmds:
        print("  " + " ".join(c))
    print("公開される先（目安）: https://" + a.project + ".pages.dev")
    print("ログイン: " + ("API トークン（.env）" if os.environ.get("CLOUDFLARE_API_TOKEN") else "wrangler login 済みであること"))
    if not a.go:
        print("\n[試し] 何もしていません。公開するときは --go を付けてください。")
        return 0
    if not shutil.which("npx"):
        print("止めました: npx がありません。Node.js を入れてください（https://nodejs.org/）")
        return 2
    for c in cmds:
        r = subprocess.run(c)
        if r.returncode != 0:
            print(f"失敗しました（終了コード {r.returncode}）: {' '.join(c)}")
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
