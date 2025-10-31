import os
import sys
import argparse

from .voice_downloader import VoiceDownloader


def main():
    parser = argparse.ArgumentParser(description="Bestdori 角色语音下载（调试控制台）")
    parser.add_argument("--names", type=str, default="tomorin", help="角色昵称或别名，逗号分隔（示例：tomorin,anon}")
    parser.add_argument("--mode", type=str, default="card", help="语音模式占位（默认 card）")
    parser.add_argument("--save", type=str, default=None, help="保存根目录（默认项目 downloads/voices）")
    parser.add_argument("--start", type=int, default=1, help="起始索引（默认 1）")
    parser.add_argument("--end", type=int, default=200, help="结束索引（默认 200）")
    parser.add_argument("--miss", type=int, default=15, help="连续未命中上限（默认 15）")

    args = parser.parse_args()

    names = [s.strip() for s in (args.names or "").split(",") if s.strip()]

    downloader = VoiceDownloader(save_root_dir=args.save)

    def on_status(text: str):
        print(text)

    def on_progress(val: float):
        # 简易显示：每完成 5% 输出一次
        sys.stdout.write(f"\r进度: {val:.1f}%")
        sys.stdout.flush()

    print("开始语音下载...")
    stats = downloader.download_by_characters(
        nicknames=names,
        mode=args.mode,
        to_wav=False,
        start_index=args.start,
        end_index=args.end,
        max_consecutive_miss=args.miss,
        status_callback=on_status,
        progress_callback=on_progress
    )

    print("\n完成。统计：")
    print(stats)


if __name__ == "__main__":
    main()


