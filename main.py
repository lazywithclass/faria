from src.gemini_api import summarize_text, get_youtube_transcript
from src.logger import setup_logger
from src.tui import VideoApp
from src.youtube_auth import get_authenticated_service
from src.youtube_user import get_subscription_feed


def get_videos():
    youtube = get_authenticated_service()
    videos = get_subscription_feed(youtube)
    print(videos)

def get_summary():
    transcript = get_youtube_transcript("Pb6RYlRtEEA")
    summary = summarize_text(transcript)
    print(summary)

def run_tui():
    app = VideoApp()
    app.run()

if __name__ == "__main__":
    logger = setup_logger()
    run_tui()
