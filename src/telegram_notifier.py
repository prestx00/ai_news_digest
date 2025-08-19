import telegram
import random
import asyncio
import re
from . import config

async def _send_to_all_recipients(message_text: str, parse_mode: str = 'Markdown'):
    """Внутренняя функция для отправки сообщения всем получателям из конфига."""
    bot = telegram.Bot(token=config.BOT_TOKEN)
    
    if not config.TELEGRAM_RECIPIENTS:
        print("Список получателей (TELEGRAM_RECIPIENTS) пуст. Уведомление не отправлено.")
        return

    for recipient in config.TELEGRAM_RECIPIENTS:
        chat_id = recipient.get('chat_id')
        message_thread_id = recipient.get('message_thread_id')

        if not chat_id:
            print(f"Пропуск получателя из-за отсутствия chat_id: {recipient}")
            continue

        try:
            await bot.send_message(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                text=message_text,
                parse_mode=parse_mode
            )
            print(f"Уведомление успешно отправлено в чат {chat_id}" + (f" (топик {message_thread_id})" if message_thread_id else ""))
            await asyncio.sleep(random.uniform(1, 3)) # Задержка между отправками
        except Exception as e:
            print(f"Ошибка при отправке уведомления в чат {chat_id}: {e}")


async def send_notification(summary: str, article_url: str):
    """Отправляет уведомление с анонсом и ссылкой всем получателям."""
    if not summary or not article_url:
        print("Нет данных для отправки уведомления.")
        return

    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
    safe_summary = clean_summary
    message_text = f"**Мяу! Еженедельный {config.DIGEST_NAME} дайджест готов!**\n\n{safe_summary}\n\n[Читать полный разбор]({article_url})"
    
    await _send_to_all_recipients(message_text)


async def send_test_notification():
    """Отправляет тестовое уведомление всем получателям."""
    message_text = "Это тестовое уведомление от вашего AI News Digest бота."
    await _send_to_all_recipients(message_text)

        
async def send_error_notification(error_message: str):
    """Отправляет уведомление об ошибке всем получателям."""
    message_text = f"**Произошла ошибка в работе AI News Digest:**\n\n`{error_message}`"
    await _send_to_all_recipients(message_text, parse_mode='Markdown')


async def main():
    # Пример использования
    # Загрузка конфигурации
    config.load_config('.env')
    # await send_notification("Это краткое содержание статьи...", "https://telegra.ph/example-12-34")
    await send_test_notification()

if __name__ == "__main__":
    asyncio.run(main())
