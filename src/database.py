import sqlite3
from . import config

def init_db():
    """Инициализирует базу данных и создает таблицу для постов."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            date INTEGER NOT NULL,
            source_link TEXT,
            has_media BOOLEAN DEFAULT 0,
            is_processed BOOLEAN DEFAULT 0,
            UNIQUE(channel, message_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_post(channel: str, message_id: int, text: str, date: int, source_link: str, has_media: bool = False):
    """Добавляет новый пост в базу данных, избегая дубликатов."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO posts (channel, message_id, text, date, source_link, has_media) VALUES (?, ?, ?, ?, ?, ?)",
                       (channel, message_id, text, date, source_link, has_media))
        conn.commit()
    except sqlite3.IntegrityError:
        # Пост уже существует
        pass
    finally:
        conn.close()

def get_unprocessed_posts():
    """Возвращает все необработанные посты (id, текст, ссылку, наличие медиа) из базы данных."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    # Выбираем id, текст, ссылку на источник и наличие медиа
    cursor.execute("SELECT id, text, source_link, has_media FROM posts WHERE is_processed = 0")
    posts = cursor.fetchall()
    conn.close()
    return posts

def mark_posts_as_processed(post_ids: list):
    """Отмечает посты как обработанные."""
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    cursor.executemany("UPDATE posts SET is_processed = 1 WHERE id = ?", [(pid,) for pid in post_ids])
    conn.commit()
    conn.close()

# def reset_processed_posts():
#     """Сбрасывает флаг is_processed для всех постов на 0 (необработанные)."""
#     conn = sqlite3.connect(config.DB_NAME)
#     cursor = conn.cursor()
#     cursor.execute("UPDATE posts SET is_processed = 0")
#     conn.commit()
#     conn.close()
#     print("Все посты помечены как необработанные (is_processed = 0).")
