import os


class VideoGenerator:
    OUTPUT_DIR = "output"

    def __init__(self, topic: str, duration: int = 30):
        self.topic = topic
        self.duration = duration

    def generate(self) -> str:
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(self.OUTPUT_DIR, f"{self.topic}.mp4")
        # TODO: 動画生成ロジックを実装する
        return output_path
