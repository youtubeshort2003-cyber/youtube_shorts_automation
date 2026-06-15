"""分足デイトレ 自動売買プロトタイプのエントリポイント。

既定はペーパートレード（実発注なし）＋モックデータで、
APIキーや証券口座が無くても動作確認できる。

使い方:
    python main.py --symbol 7203 --cash 100000 --cycles 100

ANTHROPIC_API_KEY を設定すると判断が Claude になり、
未設定なら簡易ルールにフォールバックする（どちらでもループは回る）。
"""
import argparse

from src.broker import PaperBroker
from src.datafeed import MockDataFeed
from src.engine import Engine
from src.logbook import LogBook
from src.risk import RiskLimits


def parse_args():
    p = argparse.ArgumentParser(description="分足デイトレ自動売買プロトタイプ（ペーパー）")
    p.add_argument("--symbol", default="TEST", help="銘柄コード")
    p.add_argument("--cash", type=int, default=100000, help="初期資金（円）")
    p.add_argument("--cycles", type=int, default=100, help="検証サイクル数")
    p.add_argument("--seed", type=int, default=42, help="モック乱数シード")
    p.add_argument("--log", default="paper_trades.jsonl", help="ログ出力先")
    p.add_argument("--max-order", type=int, default=100000, help="1注文の上限（円）")
    p.add_argument("--daily-loss", type=int, default=5000, help="1日の損失上限（円）")
    return p.parse_args()


def main():
    args = parse_args()
    feed = MockDataFeed(start_price=1000.0, seed=args.seed)
    broker = PaperBroker(cash=args.cash)
    limits = RiskLimits(
        max_order_yen=args.max_order,
        max_position_yen=args.cash,
        daily_loss_limit_yen=args.daily_loss,
    )
    engine = Engine(feed, broker, args.symbol, limits, LogBook(args.log))

    print(f"=== ペーパートレード開始 symbol={args.symbol} cash={args.cash} ===")
    engine.run(args.cycles)

    acc = broker.account()
    equity = acc.cash + acc.position_qty * feed.get_bars(args.symbol, 1)[-1].close
    print("=== 終了 ===")
    print(f"現金: {acc.cash:.0f} / 保有: {acc.position_qty}株 "
          f"/ 評価額合計: {equity:.0f} / 確定損益: {engine.state.realized_pnl:.0f}")
    print(f"ログ: {args.log}")


if __name__ == "__main__":
    main()
