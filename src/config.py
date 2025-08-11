import os
from dotenv import load_dotenv

# Объявляем переменные на уровне модуля, чтобы IDE их видела
API_ID = None
API_HASH = None
BOT_TOKEN = None
CHAT_ID = None
OPENAI_API_KEY = None
TELEGRAM_CHANNELS = []
ARTICLE_PROMPT = ""
SUMMARY_PROMPT = "" # Промпт для коротких саммари
DB_NAME = None
SCHEDULE_DAY_OF_WEEK = None
SCHEDULE_HOUR = None
SCHEDULE_MINUTE = None
TELEGRAM_PARSE_LIMIT = None # Новая переменная
OFFICIAL_CHANNELS = []  # Имена телеграм-каналов (username) официальных источников
ENABLE_TOC = True
NAVIGATION_TITLE = "🧭 Навигация"
NAVIGATION_STYLE = "list"  # "list" для ul/li или "paragraph" для p
ENABLE_SECTION_REORDER = True  # Переупорядочивание секций в правильном порядке
ENABLE_SECTION_SPLIT = False
OFFICIAL_SECTION_TITLE = "Официальные источники"
OTHER_SECTION_TITLE = "Другие источники"
STRIP_ORIGINAL_SECTIONS = False
STRIP_H3_TITLES = []
TELEGRAPH_ACCESS_TOKEN = None
TELEGRAPH_AUTHOR_NAME = None
TELEGRAPH_AUTHOR_URL = None
DIGEST_NAME = "AI"  # Имя тематики для заголовка (например: AI, HR, Ozon, Wildberries)

def load_config(config_path: str):
    """Загружает конфигурацию из указанного .env файла."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    load_dotenv(dotenv_path=config_path)

    # Используем global, чтобы изменить переменные на уровне модуля
    global API_ID, API_HASH, BOT_TOKEN, CHAT_ID, OPENAI_API_KEY, TELEGRAM_CHANNELS, ARTICLE_PROMPT, SUMMARY_PROMPT, DB_NAME, SCHEDULE_DAY_OF_WEEK, SCHEDULE_HOUR, SCHEDULE_MINUTE, TELEGRAM_PARSE_LIMIT, OFFICIAL_CHANNELS, ENABLE_TOC, NAVIGATION_TITLE, NAVIGATION_STYLE, ENABLE_SECTION_REORDER, ENABLE_SECTION_SPLIT, OFFICIAL_SECTION_TITLE, OTHER_SECTION_TITLE, STRIP_ORIGINAL_SECTIONS, STRIP_H3_TITLES, TELEGRAPH_ACCESS_TOKEN, TELEGRAPH_AUTHOR_NAME, TELEGRAPH_AUTHOR_URL, DIGEST_NAME

    # Telegram User API
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")

    # Telegram Bot API
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Каналы для парсинга
    TELEGRAM_CHANNELS = [c.strip() for c in os.getenv("TELEGRAM_CHANNELS", "").split(',') if c.strip()]

    # Промпты
    ARTICLE_PROMPT = os.getenv("ARTICLE_PROMPT")
    SUMMARY_PROMPT = os.getenv("SUMMARY_PROMPT")

    # Имя файла базы данных
    DB_NAME = os.getenv("DB_NAME", "news.db")

    # Настройки расписания
    SCHEDULE_DAY_OF_WEEK = os.getenv("SCHEDULE_DAY_OF_WEEK", "mon")
    SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", 9))
    SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", 0))

    # Лимит парсинга Telegram
    TELEGRAM_PARSE_LIMIT = int(os.getenv("TELEGRAM_PARSE_LIMIT", 30)) # По умолчанию 30

    # Список официальных каналов (через запятую), например: "ozon,ozonnews,wildberries_official"
    OFFICIAL_CHANNELS = [c.strip() for c in os.getenv("OFFICIAL_CHANNELS", "").split(',') if c.strip()]

    # Постобработка: навигация и секции
    ENABLE_TOC = os.getenv("ENABLE_TOC", "true").strip().lower() in ("1", "true", "yes")
    NAVIGATION_TITLE = os.getenv("NAVIGATION_TITLE", "🧭 Навигация").strip()
    NAVIGATION_STYLE = os.getenv("NAVIGATION_STYLE", "list").strip().lower()  # "list" или "paragraph"
    ENABLE_SECTION_REORDER = os.getenv("ENABLE_SECTION_REORDER", "true").strip().lower() in ("1", "true", "yes")
    ENABLE_SECTION_SPLIT = os.getenv("ENABLE_SECTION_SPLIT", "false").strip().lower() in ("1", "true", "yes")
    OFFICIAL_SECTION_TITLE = os.getenv("OFFICIAL_SECTION_TITLE", "Официальные источники").strip()
    OTHER_SECTION_TITLE = os.getenv("OTHER_SECTION_TITLE", "Другие источники").strip()
    STRIP_ORIGINAL_SECTIONS = os.getenv("STRIP_ORIGINAL_SECTIONS", "false").strip().lower() in ("1", "true", "yes")
    STRIP_H3_TITLES = [s.strip() for s in os.getenv("STRIP_H3_TITLES", "").split(',') if s.strip()]

    # Telegraph
    TELEGRAPH_ACCESS_TOKEN = os.getenv("TELEGRAPH_ACCESS_TOKEN")
    TELEGRAPH_AUTHOR_NAME = os.getenv("TELEGRAPH_AUTHOR_NAME", "AI Digest")
    TELEGRAPH_AUTHOR_URL = os.getenv("TELEGRAPH_AUTHOR_URL", "")

    # Имя тематики для заголовка статьи
    DIGEST_NAME = os.getenv("DIGEST_NAME", "AI")

    # Проверка наличия обязательных переменных
    required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "CHAT_ID", "OPENAI_API_KEY", "TELEGRAM_CHANNELS", "ARTICLE_PROMPT", "SUMMARY_PROMPT", "DB_NAME", "TELEGRAM_PARSE_LIMIT"]
    missing_vars = [var for var in required_vars if not globals().get(var)]

    if missing_vars:
        raise ValueError(f"В файле {config_path} отсутствуют переменные: {', '.join(missing_vars)}")

    print(f"Конфигурация успешно загружена из {config_path}")

