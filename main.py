from src.gemini_api import extended_summarize_text, get_youtube_transcript
from src.logger import setup_logger
from src.tui import VideoApp
from src.youtube_auth import get_authenticated_service
from src.youtube_user import get_subscription_feed
import argparse


def get_videos():
    youtube = get_authenticated_service()
    videos = get_subscription_feed(youtube)
    print(videos)

def get_summary(video_id):
    transcript = get_youtube_transcript(video_id)
    summary = extended_summarize_text(transcript)
    print(summary)

def run_tui():
    app = VideoApp()
    app.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Faria")
    
    parser.add_argument("--tui", action="store_true", help="Run the TUI application")
    parser.add_argument("--summarize", help="Summarize the video")
    args = parser.parse_args()

    setup_logger()
    if args.tui:
        run_tui()
    elif args.summarize:
        get_summary(args.summarize)
    else:
        parser.print_help()
