"""
海外バズ動画の「発見」専用モジュール（ダウンロードはしない）。

Reddit公式APIの読み取り専用アクセスで、動物・自然・人間ハプニング系
subredditの急上昇/人気投稿を監視し、動画候補のメタデータ（タイトル・
スコア・投稿元リンク）を一覧化する。実際の動画ダウンロードは行わず、
候補選定後にユーザーが手動でDLする運用を前提とする。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import praw
from config.config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    DISCOVERY_SUBREDDITS, DISCOVERY_LIMIT_PER_SUB, DISCOVERY_MIN_SCORE,
    DISCOVERY_SEEN_FILE,
)

VIDEO_DOMAINS = ("v.redd.it", "gfycat.com", "redgifs.com", "streamable.com")


def _reddit() -> praw.Reddit:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise RuntimeError(
            "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET が未設定です。"
            "https://www.reddit.com/prefs/apps で script アプリを作成し .env に設定してください。"
        )
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def _is_video_post(post) -> bool:
    if getattr(post, "is_video", False):
        return True
    domain = getattr(post, "domain", "") or ""
    return any(d in domain for d in VIDEO_DOMAINS)


def _video_url(post) -> str | None:
    if getattr(post, "is_video", False):
        media = getattr(post, "media", None) or {}
        reddit_video = media.get("reddit_video", {})
        return reddit_video.get("fallback_url")
    return post.url  # gfycat/streamable等は投稿URL自体が動画ページ


def _to_candidate(post) -> dict:
    return {
        "id": post.id,
        "subreddit": str(post.subreddit),
        "title": post.title,
        "score": post.score,
        "num_comments": post.num_comments,
        "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
        "permalink": f"https://www.reddit.com{post.permalink}",
        "video_url": _video_url(post),
        "thumbnail": post.thumbnail if str(post.thumbnail).startswith("http") else None,
        "author": str(post.author) if post.author else "[deleted]",
        "nsfw": bool(post.over_18),
    }


def _load_seen() -> set[str]:
    if DISCOVERY_SEEN_FILE.exists():
        return set(json.loads(DISCOVERY_SEEN_FILE.read_text(encoding="utf-8")))
    return set()


def _save_seen(seen: set[str]) -> None:
    DISCOVERY_SEEN_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")


def discover(
    subreddits: list[str] | None = None,
    keywords: list[str] | None = None,
    min_score: int = DISCOVERY_MIN_SCORE,
    limit_per_sub: int = DISCOVERY_LIMIT_PER_SUB,
    mark_seen: bool = True,
) -> list[dict]:
    """
    候補を収集して返す。既にseen済みのpost idは除外する。
    mark_seen=Trueなら今回返した分をseenに追記する（次回以降は出てこない）。
    """
    reddit = _reddit()
    seen = _load_seen()
    candidates: dict[str, dict] = {}

    for sub in (subreddits or DISCOVERY_SUBREDDITS):
        for post in reddit.subreddit(sub).hot(limit=limit_per_sub):
            if post.id in seen or post.stickied or post.over_18:
                continue
            if not _is_video_post(post) or post.score < min_score:
                continue
            candidates[post.id] = _to_candidate(post)

    for kw in (keywords or []):
        for post in reddit.subreddit("all").search(kw, sort="top", time_filter="week", limit=limit_per_sub):
            if post.id in seen or post.stickied or post.over_18:
                continue
            if not _is_video_post(post) or post.score < min_score:
                continue
            candidates[post.id] = _to_candidate(post)

    results = sorted(candidates.values(), key=lambda c: c["score"], reverse=True)

    if mark_seen:
        seen |= {c["id"] for c in results}
        _save_seen(seen)

    return results
