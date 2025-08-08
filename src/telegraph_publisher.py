import random
import asyncio
from telegraph import Telegraph
from . import config

async def publish_to_telegraph(title: str, html_content: str) -> str:
    """Публикует статью в Telegra.ph и возвращает ссылку.

    Использует access_token из конфига, если он задан. Иначе создаёт аккаунт один раз.
    """
    # Инициализируем клиент с токеном, если он задан, иначе создаём аккаунт и переинициализируем
    if config.TELEGRAPH_ACCESS_TOKEN:
        telegraph = Telegraph(access_token=config.TELEGRAPH_ACCESS_TOKEN)
    else:
        telegraph = Telegraph()
        account = telegraph.create_account(short_name=config.TELEGRAPH_AUTHOR_NAME or 'AI Digest')
        token = account.get('access_token')
        # Рекомендуется сохранить token в .env вручную после первого получения
        telegraph = Telegraph(access_token=token)
    try:
        response = telegraph.create_page(
            title=title,
            html_content=html_content,
            author_name=config.TELEGRAPH_AUTHOR_NAME or 'AI Digest',
            author_url=config.TELEGRAPH_AUTHOR_URL or None
        )
        # Задержка после публикации
        await asyncio.sleep(random.uniform(1, 3))
        return response['url']
    except Exception as e:
        print(f"Ошибка при публикации в Telegra.ph: {e}")
        return ""
