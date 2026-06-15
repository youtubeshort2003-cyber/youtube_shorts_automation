"""バックテストの成績指標を計算する。"""
from __future__ import annotations


def summarize(equity_curve: list[float], realized_pnls: list[float],
              start_cash: float) -> dict:
    """資産推移と確定損益のリストから成績をまとめる。

    Parameters
    ----------
    equity_curve : list[float]
        各サイクル終了時の評価額（現金＋保有評価）。
    realized_pnls : list[float]
        売却で確定した損益のリスト（1約定=1要素）。
    """
    wins = [p for p in realized_pnls if p > 0]
    losses = [p for p in realized_pnls if p < 0]
    trades = len(realized_pnls)
    final = equity_curve[-1] if equity_curve else start_cash

    return {
        "trades": trades,
        "win_rate": round(len(wins) / trades, 3) if trades else None,
        "total_realized_pnl": round(sum(realized_pnls), 1),
        "avg_win": round(sum(wins) / len(wins), 1) if wins else 0.0,
        "avg_loss": round(sum(losses) / len(losses), 1) if losses else 0.0,
        "final_equity": round(final, 1),
        "return_pct": round((final / start_cash - 1) * 100, 2) if start_cash else None,
        "max_drawdown_pct": round(_max_drawdown(equity_curve) * 100, 2),
    }


def _max_drawdown(curve: list[float]) -> float:
    """資産推移の最大ドローダウン（0〜1）。"""
    peak = float("-inf")
    mdd = 0.0
    for v in curve:
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd
