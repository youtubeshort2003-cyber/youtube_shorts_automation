"""Claude に渡す「現状スナップショット」JSONを組み立てる。

板やチャートは画像のままではなく数値に落として渡すのが基本。
（画像より数値の方が判断が安定する）
"""
from __future__ import annotations

from . import indicators
from .datafeed import DataFeed


def build_snapshot(feed: DataFeed, symbol: str, account: dict,
                   bar_count: int = 30) -> dict:
    """売買判断に必要な情報を1つの辞書にまとめる。

    Parameters
    ----------
    account : dict
        現在の残高・保有ポジションなど。例:
        {"cash": 100000, "position_qty": 0, "avg_price": 0.0}
    """
    bars = feed.get_bars(symbol, bar_count)
    book = feed.get_order_book(symbol)
    ind = indicators.compute(bars)

    # 直近数本だけ生データも添える（AIが直近の動きを見られるように）
    recent = [
        {"o": round(b.open, 2), "h": round(b.high, 2),
         "l": round(b.low, 2), "c": round(b.close, 2), "v": int(b.volume)}
        for b in bars[-5:]
    ]

    return {
        "symbol": symbol,
        "indicators": ind,
        "recent_bars": recent,
        "order_book": {
            "bids": book["bids"],
            "asks": book["asks"],
        },
        "account": account,
    }
