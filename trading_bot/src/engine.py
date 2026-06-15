"""メインループ。

「見張る」のはこのループ、「判断する」のは decision（Claude）。
1サイクル = データ取得 → スナップショット生成 → 判断 → リスクガード → 発注 → 記録。
"""
from __future__ import annotations

from . import snapshot as snap_mod
from .broker import Broker
from .datafeed import DataFeed, MockDataFeed
from .decision import decide
from .logbook import LogBook
from .risk import RiskLimits, RiskState, apply


class Engine:
    def __init__(self, feed: DataFeed, broker: Broker, symbol: str,
                 limits: RiskLimits, logbook: LogBook):
        self.feed = feed
        self.broker = broker
        self.symbol = symbol
        self.limits = limits
        self.state = RiskState()
        self.log = logbook

    def step(self) -> dict:
        """1サイクル実行して結果の要約を返す。"""
        acc = self.broker.account()
        snapshot = snap_mod.build_snapshot(self.feed, self.symbol, acc.as_dict())
        raw = decide(snapshot)
        decision, status = apply(raw, snapshot, self.limits, self.state)

        result = {
            "symbol": self.symbol,
            "price": snapshot["indicators"]["last_price"],
            "ai_action": raw.action,
            "ai_confidence": raw.confidence,
            "final_action": decision.action,
            "qty": decision.qty,
            "status": status,
            "reason": decision.reason,
        }

        if decision.action in ("buy", "sell"):
            price = snapshot["indicators"]["last_price"]
            try:
                if decision.action == "buy":
                    fill = self.broker.buy(self.symbol, decision.qty, price)
                else:
                    fill = self.broker.sell(self.symbol, decision.qty, price)
                    self.state.realized_pnl += fill.realized_pnl
                    result["realized_pnl"] = round(fill.realized_pnl, 1)
            except ValueError as e:
                result["status"] = f"order_rejected: {e}"
                result["final_action"] = "hold"

        result["cash"] = round(self.broker.account().cash, 1)
        result["position_qty"] = self.broker.account().position_qty
        result["day_pnl"] = round(self.state.realized_pnl, 1)
        self.log.write(result)
        return result

    def run(self, cycles: int) -> None:
        """指定サイクル数だけ回す（検証用）。"""
        for i in range(cycles):
            if self.state.halted:
                break
            if isinstance(self.feed, MockDataFeed):
                self.feed.advance()  # モック時は時間を1本進める
            res = self.step()
            print(f"[{i+1:3d}] price={res['price']:>8} "
                  f"ai={res['ai_action']:<4} -> {res['final_action']:<4} "
                  f"qty={res['qty']:>4} cash={res['cash']:>9} "
                  f"pos={res['position_qty']:>4} pnl={res['day_pnl']:>8} "
                  f"({res['status']})")
