"""判断と約定を JSONL で記録する。

「もし発注していたら」を含めて全ステップを残し、後で検証できるようにする。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone


class LogBook:
    def __init__(self, path: str):
        self._path = path

    def write(self, record: dict) -> None:
        record = {"ts": datetime.now(timezone.utc).isoformat(), **record}
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
