import random
import asyncio
from telegraph import Telegraph

async def publish_to_telegraph(title: str, html_content: str) -> str:
    """Публикует статью в Telegra.ph и возвращает ссылку."""
    telegraph = Telegraph()
    telegraph.create_account(short_name='AI Digest')
    try:
        response = telegraph.create_page(
            title=title,
            html_content=html_content
        )
        # Задержка после публикации
        await asyncio.sleep(random.uniform(1, 3))
        return response['url']
    except Exception as e:
        print(f"Ошибка при публикации в Telegra.ph: {e}")
        return ""
