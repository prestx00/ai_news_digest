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
DB_NAME = None # Теперь имя БД будет загружаться из конфига

def load_config(config_path: str):
    """Загружает конфигурацию из указанного .env файла."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

    load_dotenv(dotenv_path=config_path)

    # Используем global, чтобы изменить переменные на уровне модуля
    global API_ID, API_HASH, BOT_TOKEN, CHAT_ID, OPENAI_API_KEY, TELEGRAM_CHANNELS, ARTICLE_PROMPT, DB_NAME

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
    DB_NAME = os.getenv("DB_NAME", "news.db") # По умолчанию news.db, если не указано

    # Проверка наличия обязательных переменных
    required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "CHAT_ID", "OPENAI_API_KEY", "TELEGRAM_CHANNELS", "ARTICLE_PROMPT", "DB_NAME"]
    missing_vars = [var for var in required_vars if not globals().get(var)]

    if missing_vars:
        raise ValueError(f"В файле {config_path} отсутствуют переменные: {', '.join(missing_vars)}")

    print(f"Конфигурация успешно загружена из {config_path}")

