#!/usr/bin/env python3
"""はてなブログ AtomPub API で記事を下書き投稿するスクリプト.

使い方:
    HATENA_ID=... HATENA_API_KEY=... HATENA_ENDPOINT=... \
        python3 scripts/post_to_hatena.py articles/2026-06-14-elecom-dryer-holder.md

認証情報は環境変数から読む（リポジトリにキーを残さないため）:
    HATENA_ID        はてなID（例: katte-yokatta）
    HATENA_API_KEY   AtomPub の APIキー
    HATENA_ENDPOINT  AtomPub ルートエンドポイント
                     例: https://blog.hatena.ne.jp/katte-yokatta/katte-yokatta.hatenablog.com/atom

デフォルトは「下書き(draft)」として投稿する。--publish を付けると即公開。
"""
import argparse
import base64
import datetime
import hashlib
import os
import random
import sys
import urllib.request
import urllib.error
from xml.sax.saxutils import escape


def parse_markdown(path):
    """YAMLフロントマター付きMarkdownを (title, categories, body) に分解する。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()

    title = None
    categories = []
    body = text

    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            front = text[3:end]
            body = text[end + 4:].lstrip("\n")
            for line in front.splitlines():
                if ":" not in line:
                    continue
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # 行内コメント(# ...)を除去
                if "  #" in val:
                    val = val.split("  #")[0].strip().strip('"')
                if key == "title":
                    title = val
                elif key == "categories":
                    categories = [c.strip() for c in val.split(",") if c.strip()]

    if not title:
        title = os.path.splitext(os.path.basename(path))[0]
    return title, categories, body


def make_wsse(username, api_key):
    """X-WSSE 認証ヘッダを生成する。"""
    nonce = bytes(random.randint(0, 255) for _ in range(20))
    created = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = hashlib.sha1(nonce + created.encode() + api_key.encode()).digest()
    return (
        'UsernameToken Username="{u}", PasswordDigest="{p}", '
        'Nonce="{n}", Created="{c}"'.format(
            u=username,
            p=base64.b64encode(digest).decode(),
            n=base64.b64encode(nonce).decode(),
            c=created,
        )
    )


def build_entry(title, body, categories, draft=True):
    cats = "".join(
        '  <category term="{}" />\n'.format(escape(c)) for c in categories
    )
    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<entry xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:app="http://www.w3.org/2007/app">\n'
        "  <title>{title}</title>\n"
        "  <updated>{updated}</updated>\n"
        '  <content type="text/x-markdown">{body}</content>\n'
        "{cats}"
        "  <app:control>\n"
        "    <app:draft>{draft}</app:draft>\n"
        "  </app:control>\n"
        "</entry>\n"
    ).format(
        title=escape(title),
        updated=updated,
        body=escape(body),
        cats=cats,
        draft="yes" if draft else "no",
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown", help="投稿するMarkdownファイル")
    ap.add_argument("--publish", action="store_true", help="即公開（デフォルトは下書き）")
    args = ap.parse_args()

    hatena_id = os.environ.get("HATENA_ID")
    api_key = os.environ.get("HATENA_API_KEY")
    endpoint = os.environ.get("HATENA_ENDPOINT")
    if not all([hatena_id, api_key, endpoint]):
        sys.exit("環境変数 HATENA_ID / HATENA_API_KEY / HATENA_ENDPOINT を設定してください。")

    title, categories, body = parse_markdown(args.markdown)
    entry = build_entry(title, body, categories, draft=not args.publish)

    url = endpoint.rstrip("/") + "/entry"
    req = urllib.request.Request(
        url,
        data=entry.encode("utf-8"),
        headers={
            "X-WSSE": make_wsse(hatena_id, api_key),
            "Content-Type": "application/atom+xml; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print("投稿成功:", resp.status)
            location = resp.headers.get("Location")
            if location:
                print("記事URL(編集):", location)
            print("→ はてなブログの管理画面「記事の管理」で下書きを確認してください。")
    except urllib.error.HTTPError as e:
        print("HTTPエラー:", e.code, e.reason)
        print(e.read().decode("utf-8", "replace")[:500])
        sys.exit(1)
    except urllib.error.URLError as e:
        print("接続エラー:", e.reason)
        print("（この実行環境からはてなへ接続できない可能性があります。手元のPCで実行してください）")
        sys.exit(2)


if __name__ == "__main__":
    main()
