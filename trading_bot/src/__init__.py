"""分足デイトレ用 自動売買プロトタイプ（ペーパートレード既定）。

証券会社・データソースに依存しない骨組み。
- DataFeed: 市場データの供給（MockDataFeed を同梱）
- indicators: OHLCV から指標を計算
- snapshot: Claude に渡すスナップショットJSONを生成
- decision: Claude API で売買判断（鍵が無ければルールベースにフォールバック）
- risk: AI出力を必ず通す安全装置
- broker: 発注の抽象化（PaperBroker を同梱）
- engine: メインループ
"""
