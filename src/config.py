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
DB_NAME = None
SCHEDULE_DAY_OF_WEEK = None
SCHEDULE_HOUR = None
SCHEDULE_MINUTE = None
TELEGRAM_PARSE_LIMIT = None # Новая переменная

def load_config(config_path: str):
    """Загружает конфигурацию из указанного .env файла."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    load_dotenv(dotenv_path=config_path)

    # Используем global, чтобы изменить переменные на уровне модуля
    global API_ID, API_HASH, BOT_TOKEN, CHAT_ID, OPENAI_API_KEY, TELEGRAM_CHANNELS, ARTICLE_PROMPT, DB_NAME, SCHEDULE_DAY_OF_WEEK, SCHEDULE_HOUR, SCHEDULE_MINUTE, TELEGRAM_PARSE_LIMIT

    # Telegram User API
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")

    # Telegram Bot API
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")

    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Каналы для парсинга
    TELEGRAM_CHANNELS = os.getenv("TELEGRAM_CHANNELS", "").split(',')

    # Промпт для генерации статьи
    ARTICLE_PROMPT = os.getenv("ARTICLE_PROMPT")

    # Имя файла базы данных
    DB_NAME = os.getenv("DB_NAME", "news.db")

    # Настройки расписания
    SCHEDULE_DAY_OF_WEEK = os.getenv("SCHEDULE_DAY_OF_WEEK", "mon")
    SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", 9))
    SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", 0))

    # Лимит парсинга Telegram
    TELEGRAM_PARSE_LIMIT = int(os.getenv("TELEGRAM_PARSE_LIMIT", 30)) # По умолчанию 30

    # Проверка наличия обязательных переменных
    required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "CHAT_ID", "OPENAI_API_KEY", "TELEGRAM_CHANNELS", "ARTICLE_PROMPT", "DB_NAME", "TELEGRAM_PARSE_LIMIT"]
    missing_vars = [var for var in required_vars if not globals().get(var)]

    if missing_vars:
        raise ValueError(f"В файле {config_path} отсутствуют переменные: {', '.join(missing_vars)}")

    print(f"Конфигурация успешно загружена из {config_path}")

