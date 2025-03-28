import logging
import sqlite3
from typing import List, Dict, Optional, Any, Tuple


class VideoDatabase:
    def __init__(self, db_path: str = "db/faria.db"):
        self.db_path = db_path
        self._create_tables_if_not_exist()
        self.logger = logging.getLogger('faria_logger')

    def _create_tables_if_not_exist(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            duration TEXT,
            title TEXT NOT NULL,
            transcription TEXT,
            summary TEXT,
            watched INTEGER DEFAULT 0,
            disliked INTEGER DEFAULT 0,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = 'SELECT * FROM videos WHERE id = ?'
            cursor.execute(query, (video_id,))  # Note the comma to make a single-element tuple
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"Error getting video: {e}")
            return None

    def update_video(self, video_id: str, **kwargs) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            valid_fields = {'channel', 'title', 'transcription', 'summary', 'watched', 'disliked'}
            updates = {k: v for k, v in kwargs.items() if k in valid_fields}
            if not updates:
                return False

            for key in ['watched', 'disliked']:
                if key in updates and isinstance(updates[key], bool):
                    updates[key] = 1 if updates[key] else 0

            set_clause = ", ".join([f"{field} = ?" for field in updates])
            values = list(updates.values()) + [video_id]
            query = f"UPDATE videos SET {set_clause} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating video: {e}")
            return False

    def get_unwatched_videos(self) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = 'SELECT * FROM videos WHERE watched = 0 AND disliked = 0 ORDER BY published_at DESC LIMIT 200'
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting unwatched videos: {e}")
            return []

    def mark_as_watched(self, video_id: str) -> bool:
        return self.update_video(video_id, watched=True)

    def mark_as_disliked(self, video_id: str) -> bool:
        return self.update_video(video_id, disliked=True)

    def add_transcription(self, video_id: str, transcription: str) -> bool:
        return self.update_video(video_id, transcription=transcription)

    def add_summary(self, video_id: str, summary: str) -> bool:
        return self.update_video(video_id, summary=summary)

    def add_video(self, video_id: str, channel: str, duration: str, title: str, published_at) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = 'INSERT OR REPLACE INTO videos(id, channel, duration, title, published_at) VALUES (?, ?, ?, ?, ?)'
            parameters = (video_id, channel, duration, title, published_at)
            cursor.execute(query, parameters)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Error adding video: {e}")
            return False

    def add_videos(self, videos: List[Dict[str, Any]]) -> bool:
        if not videos:
            return True
        try:
            for video in videos:
                self.add_video(video['id'], video['channel'], video['duration'], video['title'], video['published_at'])
            return True
        except Exception as e:
            self.logger.error(f"Error adding videos batch: {e}")
            return False
