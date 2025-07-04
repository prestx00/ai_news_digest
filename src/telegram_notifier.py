import telegram
from . import config

async def send_notification(summary: str, article_url: str):
    """Отправляет уведомление с анонсом и ссылкой в заданный чат."""
    if not summary or not article_url:
        print("Нет данных для отправки уведомления.")
        return

    bot = telegram.Bot(token=config.BOT_TOKEN)
    message_text = f"**Еженедельный AI-дайджест готов!**\n\n{summary}\n\n[Читать полный разбор]({article_url})"

    try:
        await bot.send_message(
            chat_id=config.CHAT_ID,
            text=message_text,
            parse_mode='Markdown'
        )
        print(f"Уведомление успешно отправлено в чат {config.CHAT_ID}")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")
