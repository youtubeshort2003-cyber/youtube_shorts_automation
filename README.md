# YouTube Shorts Automation

YouTube Shorts動画を自動生成・投稿するツールです。

## 機能

- テキストから動画を自動生成
- BGM・字幕の自動追加
- YouTube への自動アップロード

## セットアップ

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 使い方

```bash
python main.py --topic "今日のニュース" --duration 30
```

## 設定

`.env` ファイルを作成して以下を設定してください：

```
YOUTUBE_API_KEY=your_api_key_here
```
