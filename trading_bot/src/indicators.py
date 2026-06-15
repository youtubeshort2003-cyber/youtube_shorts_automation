"""OHLCV から売買判断用の指標を計算する。

外部ライブラリに依存せず標準ライブラリだけで実装している。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Bar:
    """1本のローソク足（始値・高値・安値・終値・出来高）。"""

    open: float
    high: float
    low: float
    close: float
    volume: float


def sma(values: list[float], period: int) -> float | None:
    """単純移動平均。データが足りなければ None。"""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(closes: list[float], period: int = 14) -> float | None:
    """RSI（相対力指数）。0〜100。データが足りなければ None。"""
    if len(closes) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(-period, 0):
        diff = closes[i] - closes[i - 1]
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def vwap(bars: list[Bar]) -> float | None:
    """出来高加重平均価格。出来高ゼロなら None。"""
    total_pv = 0.0
    total_v = 0.0
    for b in bars:
        typical = (b.high + b.low + b.close) / 3.0
        total_pv += typical * b.volume
        total_v += b.volume
    if total_v == 0:
        return None
    return total_pv / total_v


def compute(bars: list[Bar]) -> dict:
    """直近のバー列から指標一式をまとめて返す。"""
    closes = [b.close for b in bars]
    return {
        "last_price": round(closes[-1], 2) if closes else None,
        "sma_5": _round(sma(closes, 5)),
        "sma_25": _round(sma(closes, 25)),
        "rsi_14": _round(rsi(closes, 14)),
        "vwap": _round(vwap(bars)),
        "bars_available": len(bars),
    }


def _round(x: float | None, digits: int = 2) -> float | None:
    return round(x, digits) if x is not None else None
