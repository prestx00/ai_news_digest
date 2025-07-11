from openai import AsyncOpenAI
import random
import asyncio
from . import config

# Клиент будет инициализирован внутри функции, когда понадобится

async def generate_article_and_summary(posts: list) -> tuple[str, str]:
    """Генерирует лонг-рид в HTML и краткое содержание на основе постов."""
    # Инициализируем клиент здесь, когда конфигурация уже загружена
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    if not posts:
        return "", ""

    # Форматируем посты для подачи в модель
    formatted_posts = ""
    for post in posts:
        text = post[1]
        source_link = post[2]
        has_media = "true" if post[3] else "false" # Получаем флаг has_media
        formatted_posts += f"<post>\n<content>{text}</content>\n<source>{source_link}</source>\n<has_media>{has_media}</has_media>\n</post>\n\n"

    system_prompt = config.ARTICLE_PROMPT

    try:
        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Вот подборка новостей за неделю:\n\n{formatted_posts}"}
            ],
            temperature=0.6,
            max_tokens=10000
        )
        await asyncio.sleep(random.uniform(1, 3))
        content = response.choices[0].message.content
        if '---SUMMARY---' in content:
            article_html, summary = content.split('---SUMMARY---', 1)
            return article_html.strip(), summary.strip()
        else:
            return content.strip(), "Краткое содержание не было сгенерировано."

    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {e}")
        return {"article": "", "summary": ""} 