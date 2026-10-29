"""
海外バズ動画の発見CLI（ダウンロードはしない・候補提示のみ）。

使い方:
  python src\\discovery_main.py                       # 既定subreddit群を走査
  python src\\discovery_main.py --keyword "otter" --keyword "seal"
  python src\\discovery_main.py --min-score 1000 --top 10
  python src\\discovery_main.py --peek                # seenに記録せず確認だけ

出力: output/discovery/<timestamp>.json に全候補を保存し、上位をコンソール表示。
候補のURL(permalink)を開いて気に入ったものだけ、これまで通り手動でDLしてください。
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config.config import DISCOVERY_DIR, DISCOVERY_MIN_SCORE, DISCOVERY_LIMIT_PER_SUB
from src.modules.reddit_discovery import discover


def main():
    ap = argparse.ArgumentParser(description="海外バズ動画の発見(DLはしない)")
    ap.add_argument("--keyword", action="append", default=[], help="r/all横断キーワード検索(複数指定可)")
    ap.add_argument("--subreddit", action="append", default=None, help="監視subredditを上書き(複数指定可)")
    ap.add_argument("--min-score", type=int, default=DISCOVERY_MIN_SCORE)
    ap.add_argument("--limit-per-sub", type=int, default=DISCOVERY_LIMIT_PER_SUB)
    ap.add_argument("--top", type=int, default=20, help="コンソール表示件数")
    ap.add_argument("--peek", action="store_true", help="seenに記録しない(確認のみ)")
    a = ap.parse_args()

    results = discover(
        subreddits=a.subreddit,
        keywords=a.keyword,
        min_score=a.min_score,
        limit_per_sub=a.limit_per_sub,
        mark_seen=not a.peek,
    )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = DISCOVERY_DIR / f"{stamp}.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[discovery] {len(results)}件の新規候補 -> {out_path}")
    for i, c in enumerate(results[: a.top], 1):
        print(f"\n#{i} [{c['subreddit']}] score={c['score']} comments={c['num_comments']}")
        print(f"  {c['title']}")
        print(f"  {c['permalink']}")

    if not results:
        print("(新規候補なし。--peek で既出も含め再確認、--min-score を下げる等試してください)")


if __name__ == "__main__":
    main()
