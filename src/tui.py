import logging
import webbrowser
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Label, TextArea
from textual.binding import Binding
from textual.reactive import reactive
import asyncio

from src.youtube_auth import get_authenticated_service
from src.youtube_user import get_subscription_feed
from src.database import VideoDatabase
from src.gemini_api import get_youtube_transcript, summarize_text


logger = logging.getLogger('faria_logger')

class VideoPopup(ModalScreen):

    BINDINGS = [
        Binding("q", "close", "Close"),
    ]

    def __init__(self, video_id: str, title: str, summary: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_id = video_id
        self.title = title
        self.summary = summary

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.title),
            TextArea(self.summary, read_only=True)
        )


    def action_close(self) -> None:
        self.app.pop_screen()


class VideoApp(App):

    CSS = """
    DataTable {
        height: 1fr;
        border: solid green;
    }
    
    DataTable > .datatable--cursor {
        background: $accent-darken-2;
    }
    
    .highlight-row {
        background: $success;
        color: $text;
        text-style: bold;
        transition: background 500ms, color 500ms;
    }
    
    Vertical {
        align: center middle;
        padding: 2;
        border: solid green;
        background: black;
    }
    """

    BINDINGS = [
        Binding("s", "show_details", "Show Details"),
        Binding("d", "dislike", "Dislike"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("w", "watch", "Watch"),
    ]

    unwatched_videos = reactive([])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._db = VideoDatabase()

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type='row')
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("T", "S", "Channel", "Length", "Title")
        self.unwatched_videos = self._db.get_unwatched_videos()
        asyncio.create_task(self.task_get_videos())
        asyncio.create_task(self.task_fetch_summary())

    async def task_get_videos(self, row=None) -> None:
        table = self.query_one(DataTable)
        table.clear()
        self.unwatched_videos = self._db.get_unwatched_videos()
        for video in self.unwatched_videos:
            has_transcript = 'y' if video.get('transcription') else 'n'
            has_summary = 'y' if video.get('summary') else 'n'
            table.add_row(
                has_transcript,
                has_summary,
                video.get('channel', 'No channel'),
                video.get('duration', 'No duration'),
                video.get('title', 'No title')
            )
        if row is not None:
            new_row = min(row, len(table.rows) - 1)
            table.move_cursor(row=new_row)

    async def task_fetch_summary(self) -> None:
        while True:
            try:
                videos = self._db.get_unwatched_videos()
                videos = [video for video in videos if not video.get('summary')]
                for video in videos:
                    video_id = video.get('id')
                    if video.get('transcription') and video.get('summary'):
                        continue

                    if not video.get('transcription'):
                        transcript = get_youtube_transcript(video_id)
                        if transcript:
                            self._db.add_transcription(video_id, transcript)
                    else:
                        transcript = video.get('transcription')

                    summary = summarize_text(transcript)
                    if summary:
                        self._db.add_summary(video_id, summary)

                    table = self.query_one(DataTable)
                    row = table.cursor_row
                    await self.task_get_videos(row)
                    self.highlight_row(row)

                    await asyncio.sleep(120)

                await asyncio.sleep(30)

            except Exception as e:
                self.log.error(f"Error in background processing: {e}")
                await asyncio.sleep(30)

    async def task_update_feed(self) -> None:
        logger.info("Refreshing feed")
        youtube = get_authenticated_service()
        videos = get_subscription_feed(youtube)
        self._db.add_videos(videos)
        logger.info("Refreshed feed")
        asyncio.create_task(self.task_get_videos())

    def action_dislike(self):
        table = self.query_one(DataTable)
        row = table.cursor_row
        video = self.unwatched_videos[row]
        video_id = video.get('id')
        self._db.mark_as_disliked(video_id)
        asyncio.create_task(self.task_get_videos(row))

    def action_show_details(self) -> None:
        table = self.query_one(DataTable)
        row = table.cursor_row
        video = self.unwatched_videos[row]
        video_id = video.get('id')

        summary = video.get('summary')
        if not summary:
            transcript = get_youtube_transcript(video_id)
            summary = summarize_text(transcript)
            self._db.add_transcription(video_id, transcript)
            self._db.add_summary(video_id, summary)
        self.push_screen(VideoPopup(video_id=video_id, title=video.get('title'), summary=summary))

    def action_watch(self):
        table = self.query_one(DataTable)
        row = table.cursor_row
        video = self.unwatched_videos[row]
        video_id = video.get('id')
        url = f"https://www.youtube.com/watch?v={video_id}"
        webbrowser.open(url)
        self._db.mark_as_watched(video_id)
        asyncio.create_task(self.task_get_videos(row))

    def action_refresh(self):
        asyncio.create_task(self.task_update_feed())

    # TODO non funzionante
    async def highlight_row(self, row_index: int, duration: float = 2.0) -> None:
        table = self.query_one(DataTable)
        table.add_class("highlight-row", row_index)
        await asyncio.sleep(duration)
        if row_index < len(table.rows):
            table.remove_class("highlight-row", row_index)

