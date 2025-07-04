import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram User API
# API_ID = os.getenv("API_ID")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")


# Telegram Bot API
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Каналы для парсинга
TELEGRAM_CHANNELS = os.getenv("TELEGRAM_CHANNELS", "").split(',')

# Настройки базы данных
DB_NAME = "news.db"
