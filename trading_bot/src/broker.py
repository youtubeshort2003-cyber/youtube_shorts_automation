"""発注の抽象化と、検証用の PaperBroker（仮想約定）。

実運用では Broker を継承して、kabuステーションAPI や
楽天マーケットスピードII RSS など実際の発注処理を実装する。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Account:
    cash: float
    position_qty: int = 0
    avg_price: float = 0.0

    def as_dict(self) -> dict:
        return {
            "cash": round(self.cash, 1),
            "position_qty": self.position_qty,
            "avg_price": round(self.avg_price, 2),
        }


@dataclass
class Fill:
    side: str
    qty: int
    price: float
    realized_pnl: float = 0.0


class Broker(ABC):
    """発注の抽象クラス。"""

    @abstractmethod
    def buy(self, symbol: str, qty: int, price: float) -> Fill: ...

    @abstractmethod
    def sell(self, symbol: str, qty: int, price: float) -> Fill: ...

    @abstractmethod
    def account(self) -> Account: ...


class PaperBroker(Broker):
    """実発注せず、約定をその場でシミュレートする。

    最初はこれで安全に検証する。手数料・スリッページは簡略化。
    """

    def __init__(self, cash: float, fee_rate: float = 0.0):
        self._acc = Account(cash=cash)
        self._fee_rate = fee_rate
        self.fills: list[Fill] = []

    def buy(self, symbol: str, qty: int, price: float) -> Fill:
        cost = qty * price
        fee = cost * self._fee_rate
        if cost + fee > self._acc.cash:
            raise ValueError("資金不足で買付できない")
        # 平均取得単価を更新
        total_qty = self._acc.position_qty + qty
        self._acc.avg_price = (
            (self._acc.avg_price * self._acc.position_qty) + cost
        ) / total_qty
        self._acc.position_qty = total_qty
        self._acc.cash -= cost + fee
        fill = Fill(side="buy", qty=qty, price=price)
        self.fills.append(fill)
        return fill

    def sell(self, symbol: str, qty: int, price: float) -> Fill:
        if qty > self._acc.position_qty:
            raise ValueError("保有を超える売却はできない")
        proceeds = qty * price
        fee = proceeds * self._fee_rate
        realized = (price - self._acc.avg_price) * qty - fee
        self._acc.position_qty -= qty
        self._acc.cash += proceeds - fee
        if self._acc.position_qty == 0:
            self._acc.avg_price = 0.0
        fill = Fill(side="sell", qty=qty, price=price, realized_pnl=realized)
        self.fills.append(fill)
        return fill

    def account(self) -> Account:
        return self._acc
