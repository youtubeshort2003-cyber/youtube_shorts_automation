"""売買判断エンジン。

Claude API に現状スナップショットを渡し、必ず決まったJSON形式
（action / qty / reason / confidence）で判断を返させる。
ANTHROPIC_API_KEY が無い場合は、ループを止めないための
簡易ルールベース判断にフォールバックする。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """あなたは日本株の分足デイトレードの判断アシスタントです。
渡されたスナップショット（指標・直近の足・板情報・口座状況）だけを根拠に、
次の1手を判断してください。推測で材料を増やさないこと。

ルール:
- action は "buy" / "sell" / "hold" のいずれか。
- すでにポジションを持っていない時に売る判断はしない（空売り非対応）。
- qty は株数。買えるのは現金の範囲内のみ。確信が薄ければ "hold"。
- reason は日本語で簡潔に（根拠の指標・板の偏りに言及）。
- confidence は 0.0〜1.0。

必ず submit_decision ツールを使って構造化して回答すること。"""

DECISION_TOOL = {
    "name": "submit_decision",
    "description": "売買判断を構造化して提出する",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["buy", "sell", "hold"]},
            "qty": {"type": "integer", "minimum": 0},
            "reason": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["action", "qty", "reason", "confidence"],
    },
}


@dataclass
class Decision:
    action: str
    qty: int
    reason: str
    confidence: float

    @classmethod
    def hold(cls, reason: str) -> "Decision":
        return cls(action="hold", qty=0, reason=reason, confidence=0.0)


def decide(snapshot: dict) -> Decision:
    """スナップショットから売買判断を返す。"""
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return _decide_with_claude(snapshot)
        except Exception as e:  # APIエラー時もループは止めない
            return Decision.hold(f"API判断失敗のため様子見: {e}")
    return _decide_with_rules(snapshot)


def _decide_with_claude(snapshot: dict) -> Decision:
    import anthropic

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        tools=[DECISION_TOOL],
        tool_choice={"type": "tool", "name": "submit_decision"},
        messages=[{
            "role": "user",
            "content": "次のスナップショットから判断してください:\n"
                       + json.dumps(snapshot, ensure_ascii=False),
        }],
    )
    for block in msg.content:
        if block.type == "tool_use" and block.name == "submit_decision":
            d = block.input
            return Decision(
                action=d["action"],
                qty=int(d["qty"]),
                reason=d["reason"],
                confidence=float(d["confidence"]),
            )
    return Decision.hold("ツール出力が得られなかったため様子見")


def _decide_with_rules(snapshot: dict) -> Decision:
    """鍵が無い時のフォールバック。SMAゴールデン/デッドクロスの簡易版。

    あくまでループ確認用であり、収益性を意図したものではない。
    """
    ind = snapshot["indicators"]
    acc = snapshot["account"]
    s5, s25 = ind.get("sma_5"), ind.get("sma_25")
    price = ind.get("last_price")
    if s5 is None or s25 is None or price is None:
        return Decision.hold("指標の算出に必要なデータが不足")

    has_position = acc.get("position_qty", 0) > 0
    if not has_position and s5 > s25:
        # 1株単位で買える最大数を提案（最終的な単位丸めはリスクガードが行う）
        affordable = int(acc.get("cash", 0) // price)
        if affordable <= 0:
            return Decision.hold("資金不足で買えない")
        return Decision(action="buy", qty=affordable,
                        reason=f"SMA5({s5})>SMA25({s25})の上抜けで押し目買い",
                        confidence=0.55)
    if has_position and s5 < s25:
        return Decision(action="sell", qty=acc["position_qty"],
                        reason=f"SMA5({s5})<SMA25({s25})の下抜けで手仕舞い",
                        confidence=0.55)
    return Decision.hold("クロスのシグナルなし")
