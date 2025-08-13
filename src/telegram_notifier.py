import telegram
import random
import asyncio
import re  # Импортируем модуль для работы с регулярными выражениями
from . import config

async def send_notification(summary: str, article_url: str):
    """Отправляет уведомление с анонсом и ссылкой в заданный чат."""
    if not summary or not article_url:
        print("Нет данных для отправки уведомления.")
        return

    # Очищаем саммари от всех HTML-тегов, чтобы избежать ошибок парсинга
    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()


    safe_summary = clean_summary

    bot = telegram.Bot(token=config.BOT_TOKEN)
    # Используем очищенный текст в сообщении
    message_text = f"**Мяу! Еженедельный {config.DIGEST_NAME} дайджест готов!**\n\n{safe_summary}\n\n[Читать полный разбор]({article_url})"

    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            message_thread_id=config.MESSAGE_THREAD_ID,
            text=message_text,
            parse_mode='Markdown'
        )
        print(f"Уведомление успешно отправлено в чат {config.CHAT_ID}")
        # Задержка после отправки уведомления
        await asyncio.sleep(random.uniform(1, 3))
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")


async def send_test_notification():
    """Отправляет тестовое уведомление."""
    bot = telegram.Bot(token=config.BOT_TOKEN)
    message_text = "Это тестовое уведомление от вашего AI News Digest бота."
    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            message_thread_id=config.MESSAGE_THREAD_ID,
            text=message_text,
            parse_mode='Markdown'
        )
        print(f"Тестовое уведомление успешно отправлено в чат {config.CHAT_ID}")
    except Exception as e:
        print(f"Ошибка при отправке тестового уведомления: {e}")
        
async def send_error_notification(error_message: str):
    """Отправляет уведомление об ошибке."""
    bot = telegram.Bot(token=config.BOT_TOKEN)
    message_text = f"**Произошла ошибка в работе AI News Digest:**\n\n`{error_message}`"
    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            message_thread_id=config.MESSAGE_THREAD_ID,
            text=message_text,
            parse_mode='Markdown'
        )
        print(f"Уведомление об ошибке успешно отправлено в чат {config.CHAT_ID}")
    except Exception as e:
        print(f"Ошибка при отправке уведомления об ошибке: {e}")