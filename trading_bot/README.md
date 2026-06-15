# 自動売買プロトタイプ（分足デイトレ / ペーパートレード）

「ニュース・チャート・板情報から AI が売買判断する」自動売買の**骨組み**です。
証券会社に依存しない設計で、まずは**ペーパートレード（実発注なし）＋モックデータ**で
安全に動作確認できます。

> ⚠️ これは検証用の雛形であり、収益を保証するものではありません。
> 実弾投入の前に必ず少額・ペーパーで十分に検証してください。

## 設計の考え方

- **「見張る」のはプログラム、「判断する」のは AI**。
  常駐ループが一定間隔でスナップショットを作り、Claude が売買判断（JSON）を返す。
- **板やチャートは数値に落として渡す**（画像のままより判断が安定する）。
- **AI の出力は必ずリスクガードを通してから発注**（暴走発注の防止）。

## 構成

```
データ取得(DataFeed) → スナップショット生成 → 判断(Claude/decide) →
リスクガード(risk) → 発注(Broker) → 記録(LogBook)
```

| モジュール | 役割 | 差し替えポイント |
|---|---|---|
| `datafeed.py` | 市場データ供給 | `MockDataFeed` → 証券会社のリアルタイムデータ |
| `indicators.py` | SMA/RSI/VWAP 等の計算 | そのまま流用可 |
| `snapshot.py` | AI に渡す現状JSON生成 | ニュース等の材料を追記可 |
| `decision.py` | Claude で売買判断 | プロンプト/モデル調整 |
| `risk.py` | 安全装置（上限・損切・キルスイッチ） | 上限値の調整 |
| `broker.py` | 発注 | `PaperBroker` → kabu API / 楽天RSS |
| `engine.py` | メインループ | 実行間隔・トリガー条件 |

## 使い方

```bash
cd trading_bot
python main.py --symbol 7203 --cash 100000 --cycles 100
```

`ANTHROPIC_API_KEY` を設定すると判断が **Claude** に、未設定なら
**簡易ルール（SMAクロス）** にフォールバックします（どちらでもループは回る）。

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python main.py --symbol 7203 --cash 100000 --cycles 50
```

## 実データでバックテスト（口座不要・推奨の検証方法）

モック（ランダムウォーク）は配線確認用で、戦略の良し悪しは測れません。
実際の値動きで検証するには CSV を流すバックテストを使います。

```bash
# 1) データを用意（yfinance 利用例。日本株は「コード.T」）
pip install yfinance
python fetch_data.py --symbol 7203.T --interval 5m --period 5d --out data/7203.csv

# 2) バックテスト実行（成績レポートが出る）
python backtest.py --csv data/7203.csv --cash 100000
```

出力される成績指標: 取引回数 / 勝率 / 確定損益 / 平均勝ち・負け /
最終評価額 / リターン% / 最大ドローダウン%。
CSV を自前で用意する場合のヘッダは `date,open,high,low,close,volume`。

## 安全装置（risk.py）

- `max_order_yen`：1注文の最大金額
- `max_position_yen`：保有ポジションの最大金額
- `daily_loss_limit_yen`：1日の損失上限（超過で全停止）
- `min_confidence`：確信度の下限（未満は見送り）
- **キルスイッチ**：`KILL` という名前のファイルを作ると全停止

## 実運用へ進む際の差し替え（後工程）

1. `DataFeed` を証券会社のリアルタイムデータ実装に差し替え。
2. `Broker` を実発注（kabuステーションAPI / 楽天RSS 等）に差し替え。
3. `snapshot.py` にニュース/センチメント等の材料を追加。
4. まずペーパー → 単元未満株で少額 → 段階的に拡大。
