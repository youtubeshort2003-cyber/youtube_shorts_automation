"""リスクガード。AIの判断は必ずここを通してから発注する。

暴走発注を防ぐための最後の砦。AIが何を返しても、
ここで上限・損失・整合性のチェックに通らなければ発注しない。
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from .decision import Decision


@dataclass
class RiskLimits:
    max_order_yen: int = 50000        # 1注文の最大金額
    max_position_yen: int = 100000    # 保有ポジションの最大金額
    daily_loss_limit_yen: int = 5000  # 1日の最大損失（超えたら全停止）
    min_confidence: float = 0.5       # これ未満の確信度は見送り
    kill_switch_file: str = "KILL"    # このファイルが存在したら全停止
    lot_size: int = 100               # 売買単位（日本株=100、米国株=1）


@dataclass
class RiskState:
    realized_pnl: float = 0.0  # その日の確定損益
    halted: bool = False


def apply(decision: Decision, snapshot: dict, limits: RiskLimits,
          state: RiskState) -> tuple[Decision, str]:
    """判断を検査し、安全な判断に丸めて返す。

    Returns
    -------
    (調整後Decision, 説明文)
    """
    # キルスイッチ（ファイル1個で全停止）
    if os.path.exists(limits.kill_switch_file):
        state.halted = True
        return Decision.hold("キルスイッチ作動のため全停止"), "killed"

    # 1日の損失上限
    if state.realized_pnl <= -limits.daily_loss_limit_yen:
        state.halted = True
        return Decision.hold("1日の損失上限に到達したため停止"), "daily_loss"

    if decision.action == "hold":
        return decision, "hold"

    # 確信度フィルタ
    if decision.confidence < limits.min_confidence:
        return Decision.hold(
            f"確信度{decision.confidence}が下限{limits.min_confidence}未満"), "low_conf"

    price = snapshot["indicators"]["last_price"]
    acc = snapshot["account"]

    if decision.action == "sell":
        # 保有株数を超える売りは許可しない
        qty = min(decision.qty, acc.get("position_qty", 0))
        if qty <= 0:
            return Decision.hold("保有なしのため売却不可"), "no_position"
        return Decision(action="sell", qty=qty, reason=decision.reason,
                        confidence=decision.confidence), "ok"

    # buy: 注文額・ポジション額・現金で制限
    if price is None or price <= 0:
        return Decision.hold("価格不明のため発注不可"), "no_price"

    qty = decision.qty
    # 1注文上限
    qty = min(qty, int(limits.max_order_yen // price))
    # ポジション上限（現在の保有額を考慮）
    current_pos_yen = acc.get("position_qty", 0) * acc.get("avg_price", 0)
    room_yen = max(0, limits.max_position_yen - current_pos_yen)
    qty = min(qty, int(room_yen // price))
    # 現金の範囲
    qty = min(qty, int(acc.get("cash", 0) // price))
    # 売買単位に丸める（日本株=100株、米国株=1株）
    qty = (qty // limits.lot_size) * limits.lot_size

    if qty <= 0:
        return Decision.hold("上限・資金により買付数量が0に制限された"), "capped_zero"

    return Decision(action="buy", qty=qty, reason=decision.reason,
                    confidence=decision.confidence), "ok"
