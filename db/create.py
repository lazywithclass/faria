import sqlite3


def truncate_videos_table():
    conn = sqlite3.connect('./db/faria.db')
    try:
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
    except Exception as e:
        print(f"Error truncating videos table: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    truncate_videos_table()
