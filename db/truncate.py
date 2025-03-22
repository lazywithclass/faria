import sqlite3


def truncate_videos_table():
    conn = sqlite3.connect('./db/faria.db')
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM videos')
        conn.commit()
    except Exception as e:
        print(f"Error truncating videos table: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    truncate_videos_table()
