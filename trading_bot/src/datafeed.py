"""市場データの供給インターフェースと、検証用のモック実装。

実運用では MockDataFeed を、証券会社のリアルタイムデータを返す
実装（kabuステーションAPI / 楽天RSS など）に差し替える。
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod

from .indicators import Bar


class DataFeed(ABC):
    """市場データ供給の抽象クラス。"""

    @abstractmethod
    def get_bars(self, symbol: str, count: int) -> list[Bar]:
        """直近 count 本の分足を古い順で返す。"""

    @abstractmethod
    def get_order_book(self, symbol: str) -> dict:
        """板情報を返す。{'bids': [(価格, 数量)...], 'asks': [...]}"""


class MockDataFeed(DataFeed):
    """ランダムウォークで価格を生成する検証用フィード。

    APIキーや証券口座が無くてもループ全体を動かせるようにするためのもの。
    """

    def __init__(self, start_price: float = 1000.0, seed: int | None = None):
        self._rng = random.Random(seed)
        self._price = start_price
        self._bars: list[Bar] = []
        self._warmup(60)

    def _step(self) -> Bar:
        # ±0.4% 程度の変動でランダムウォーク
        drift = self._rng.uniform(-0.004, 0.004)
        open_ = self._price
        close = max(1.0, open_ * (1 + drift))
        high = max(open_, close) * (1 + abs(self._rng.uniform(0, 0.002)))
        low = min(open_, close) * (1 - abs(self._rng.uniform(0, 0.002)))
        volume = self._rng.uniform(1000, 5000)
        self._price = close
        bar = Bar(open=open_, high=high, low=low, close=close, volume=volume)
        self._bars.append(bar)
        return bar

    def _warmup(self, n: int) -> None:
        for _ in range(n):
            self._step()

    def advance(self) -> None:
        """1本ぶん時間を進める（ループのたびに呼ぶ）。"""
        self._step()

    def get_bars(self, symbol: str, count: int) -> list[Bar]:
        return self._bars[-count:]

    def get_order_book(self, symbol: str) -> dict:
        price = self._price
        tick = max(0.1, round(price * 0.001, 1))
        bids = [(round(price - tick * i, 1), int(self._rng.uniform(100, 2000)))
                for i in range(1, 6)]
        asks = [(round(price + tick * i, 1), int(self._rng.uniform(100, 2000)))
                for i in range(1, 6)]
        return {"bids": bids, "asks": asks}
