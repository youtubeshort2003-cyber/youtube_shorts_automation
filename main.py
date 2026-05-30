import argparse
from video_generator import VideoGenerator
from uploader import YouTubeUploader


def parse_args():
    parser = argparse.ArgumentParser(description="YouTube Shorts自動生成ツール")
    parser.add_argument("--topic", required=True, help="動画のトピック")
    parser.add_argument("--duration", type=int, default=30, help="動画の長さ（秒）")
    parser.add_argument("--upload", action="store_true", help="生成後にYouTubeへアップロード")
    return parser.parse_args()


def main():
    args = parse_args()

    if not 1 <= args.duration <= 60:
        print("エラー: --duration は1〜60秒の範囲で指定してください（YouTube Shortsの制限）")
        return

    print(f"トピック: {args.topic}")
    print(f"動画の長さ: {args.duration}秒")

    generator = VideoGenerator(topic=args.topic, duration=args.duration)
    output_path = generator.generate()
    print(f"動画を生成しました: {output_path}")

    if args.upload:
        uploader = YouTubeUploader()
        video_id = uploader.upload(output_path, title=args.topic)
        print(f"アップロード完了: https://youtube.com/shorts/{video_id}")


if __name__ == "__main__":
    main()
