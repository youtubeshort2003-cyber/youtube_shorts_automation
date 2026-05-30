import os
from dotenv import load_dotenv

load_dotenv()


class YouTubeUploader:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY が .env に設定されていません")

    def upload(self, video_path: str, title: str) -> str:
        # TODO: YouTube Data API を使ったアップロードを実装する
        raise NotImplementedError("アップロード機能は未実装です")
