"""バックテスト用の OHLCV データを yfinance で取得して CSV 保存する。

証券口座は不要。インターネット接続のある環境で実行する。

    pip install yfinance
    python fetch_data.py --symbol 7203.T --interval 5m --period 5d --out data/7203.csv

注意:
- 日本株は「銘柄コード.T」（例: トヨタ=7203.T）。
- 分足(1m/5m等)は取得できる期間が短い点に注意（yfinanceの制限）。
"""
import argparse
import csv
import os


def parse_args():
    p = argparse.ArgumentParser(description="yfinance で OHLCV を取得し CSV 保存")
    p.add_argument("--symbol", required=True, help="例: 7203.T")
    p.add_argument("--interval", default="5m", help="1m/5m/15m/1h/1d など")
    p.add_argument("--period", default="5d", help="例: 5d, 1mo, 6mo")
    p.add_argument("--out", required=True, help="出力CSVパス")
    return p.parse_args()


def main():
    args = parse_args()
    try:
        import yfinance as yf
    except ImportError:
        raise SystemExit("yfinance が必要です: pip install yfinance")

    df = yf.download(args.symbol, interval=args.interval,
                     period=args.period, progress=False, auto_adjust=False)
    if df.empty:
        raise SystemExit("データが取得できませんでした（銘柄/期間/間隔を確認）")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        for ts, row in df.iterrows():
            w.writerow([
                ts.isoformat(),
                _v(row, "Open"), _v(row, "High"), _v(row, "Low"),
                _v(row, "Close"), _v(row, "Volume"),
            ])
    print(f"保存しました: {args.out}（{len(df)}本）")


def _v(row, col):
    # MultiIndex 列にも単一列にも対応
    val = row[col]
    return float(val.iloc[0]) if hasattr(val, "iloc") else float(val)


if __name__ == "__main__":
    main()
