"""dist/index.html を、公開用の別のリポジトリ（GitHub Pages）に入れて push する。

このキットのリポジトリそのものは公開しないでください。LP だけを置く公開用のリポジトリを別に作ります。
手順は playbooks/07-publish.md。

使い方:
  python3 scripts/publish_github_pages.py --repo-dir ../my-lp-site          # 試し（打つコマンドを出すだけ）
  python3 scripts/publish_github_pages.py --repo-dir ../my-lp-site --go     # 写して commit・push
"""
from __future__ import annotations

import os as _ng_os, sys as _ng_sys  # N-Hack 専用の門（下の3行を消すとこのキットは動きません）
_ng_sys.path.insert(0, _ng_os.path.dirname(_ng_os.path.abspath(__file__)))
import nhack_gate as _nhack_gate  # noqa: E402,F401


import argparse
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-dir", required=True, help="公開用リポジトリを clone した場所")
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    ap.add_argument("--message", default="LP を更新")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()
    repo = pathlib.Path(a.repo_dir).resolve()
    dist = pathlib.Path(a.dist)
    if repo == ROOT.resolve():
        print("止めました: このキット自体のリポジトリには入れません（公開用のリポジトリを別に作ってください）")
        return 2
    if not (dist / "index.html").exists():
        print(f"{dist}/index.html がありません。先に build_lp.py で作ってください")
        return 2
    files = [p for p in dist.iterdir() if p.is_file() and not p.name.startswith(".")]
    print(f"写すもの: {', '.join(p.name for p in files)} → {repo}")
    cmds = [["git", "-C", str(repo), "add", "-A"],
            ["git", "-C", str(repo), "commit", "-m", a.message],
            ["git", "-C", str(repo), "push"]]
    for c in cmds:
        print("  " + " ".join(c))
    if not a.go:
        print("\n[試し] 何もしていません。公開するときは --go を付けてください。")
        return 0
    if not (repo / ".git").exists():
        print(f"止めました: {repo} は git のリポジトリではありません")
        return 2
    for p in files:
        shutil.copy2(p, repo / p.name)
    for c in cmds:
        r = subprocess.run(c)
        if r.returncode != 0 and c[3] != "commit":
            print(f"失敗しました: {' '.join(c)}")
            return r.returncode
    print("push しました。数分後に https://<ユーザー名>.github.io/<リポジトリ名>/ で見られます")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
