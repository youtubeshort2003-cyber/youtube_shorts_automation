"""実データ(CSV)に対するバックテスト。

ランダムウォークではなく実際の値動きで、AI/ルールの判断が
どう動くか・成績がどうなるかを口座なしで検証する。

CSV 形式（ヘッダ必須・列名は大小文字どちらでも可）:
    date,open,high,low,close,volume

使い方:
    python backtest.py --csv data/7203.csv --cash 100000

データの用意（口座不要・例: yfinance を使う場合）:
    pip install yfinance
    python fetch_data.py --symbol 7203.T --interval 5m --period 5d --out data/7203.csv
"""
import argparse

from src.broker import PaperBroker
from src.datafeed import CsvReplayFeed
from src.decision import decide
from src.logbook import LogBook
from src.metrics import summarize
from src.risk import RiskLimits, RiskState, apply
from src.snapshot import build_snapshot


def parse_args():
    p = argparse.ArgumentParser(description="CSV実データのバックテスト（ペーパー）")
    p.add_argument("--csv", required=True, help="OHLCV の CSV ファイル")
    p.add_argument("--symbol", default="TEST", help="銘柄コード（ログ用）")
    p.add_argument("--cash", type=int, default=100000, help="初期資金（円）")
    p.add_argument("--log", default="backtest.jsonl", help="ログ出力先")
    p.add_argument("--max-order", type=int, default=100000, help="1注文の上限（円）")
    p.add_argument("--daily-loss", type=int, default=5000, help="損失上限（円）")
    p.add_argument("--quiet", action="store_true", help="各サイクルの出力を抑制")
    return p.parse_args()


def main():
    args = parse_args()
    feed = CsvReplayFeed(args.csv)
    broker = PaperBroker(cash=args.cash)
    limits = RiskLimits(
        max_order_yen=args.max_order,
        max_position_yen=args.cash,
        daily_loss_limit_yen=args.daily_loss,
    )
    state = RiskState()
    log = LogBook(args.log)

    equity_curve: list[float] = []
    realized: list[float] = []

    print(f"=== バックテスト開始 {args.csv} bars={len(feed)} cash={args.cash} ===")
    while True:
        acc = broker.account()
        snap = build_snapshot(feed, args.symbol, acc.as_dict())
        price = snap["indicators"]["last_price"]
        raw = decide(snap)
        decision, status = apply(raw, snap, limits, state)

        if decision.action == "buy":
            try:
                broker.buy(args.symbol, decision.qty, price)
            except ValueError as e:
                status = f"rejected: {e}"
        elif decision.action == "sell":
            try:
                fill = broker.sell(args.symbol, decision.qty, price)
                state.realized_pnl += fill.realized_pnl
                realized.append(fill.realized_pnl)
            except ValueError as e:
                status = f"rejected: {e}"

        acc = broker.account()
        equity = acc.cash + acc.position_qty * price
        equity_curve.append(equity)
        log.write({
            "symbol": args.symbol, "price": price,
            "ai_action": raw.action, "final_action": decision.action,
            "qty": decision.qty, "status": status, "equity": round(equity, 1),
        })
        if not args.quiet and decision.action != "hold":
            print(f"price={price:>8} {decision.action:<4} qty={decision.qty:>4} "
                  f"equity={equity:>10.0f} ({status})")

        if state.halted or not feed.advance():
            break

    print("=== 成績 ===")
    for k, v in summarize(equity_curve, realized, args.cash).items():
        print(f"  {k}: {v}")
    print(f"ログ: {args.log}")


if __name__ == "__main__":
    main()
