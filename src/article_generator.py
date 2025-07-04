from openai import AsyncOpenAI
import random
import asyncio
from . import config

# Создаем экземпляр асинхронного клиента OpenAI
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

async def generate_article_and_summary(posts: list) -> tuple[str, str]:
    """Генерирует лонг-рид в HTML и краткое содержание на основе постов."""
    if not posts:
        return "", ""

    # Форматируем посты для подачи в модель
    formatted_posts = ""
    for post in posts:
        text = post[1]
        source_link = post[2]
        has_media = "true" if post[3] else "false" # Получаем флаг has_media
        formatted_posts += f"<post>\n<content>{text}</content>\n<source>{source_link}</source>\n<has_media>{has_media}</has_media>\n</post>\n\n"

    system_prompt = """
    **Ты — экспертный AI-аналитик и редактор новостного IT-издания.** **Твоя задача — проанализировать подборку новостей и превратить их в качественный, структурированный лонг-рид в формате HTML для публикации на Telegra.ph.** **Аудитория — IT-специалисты, менеджеры и энтузиасты.**

    **Требования к лонг-риду (HTML для Telegra.ph):**
    **Разрешенные теги:**

    <h3>, <h4> — для подзаголовков **(НЕ используй <h1>, <h2>)**
    <p> — для абзацев
    <strong> или <b> — для выделения
    <em> или <i> — для курсива
    <a href="url"> — для ссылок
    <ul>, <ol>, <li> — для списков
    <blockquote> — для цитат
    <br> — для переносов строк
    <pre> — для кода

    **Структура контента:**

    **Заголовок: НЕ используй <h1> или <h2>** — начинай сразу с вводного абзаца в <p>, который содержит яркий заголовок дайджеста
    Разделы: Используй <h3> для основных тем, <h4> для подтем
    Содержание: Каждый раздел начинай с подзаголовка <h3>, затем излагай новости в <p>. Не копируй, а пересказывай и анализируй
    **Источники: В конце каждого абзаца ставь ссылку:** <a href="[source_link]">[1]</a>
    **Медиа: Если есть <has_media>true</has_media>, упоминай:** "(см. изображение в оригинальном посте)" или "(подробности на видео)". **Не пытайся описать само изображение, просто укажи на его наличие.**
    Форматирование: Используй <strong> для ключевых терминов и <em> для комментариев

    ***Важные ограничения:***

    **НЕ используй <html>, <head>, <body>, <h1>, <h2>**
    **НЕ используй <div>, <span>, <section>**
    **НЕ используй атрибуты стилей (style=)**
    **НЕ используй <img> теги**
    **Контент должен быть готов к прямой вставке в Telegra.ph**

    **Требования к краткому содержанию (summary):**

    **Короткий текст для анонса в Telegram (3-4 предложения)**
    Перечисли основные темы дайджеста

    **Формат ответа:**
    [HTML-код без тегов html/head/body]
    ---SUMMARY---
    [Краткое содержание для Telegram]
    Пример структуры:
    html<p><strong>🚀 IT-дайджест: Главные события недели</strong></p>

    <h3>🔥 Разработка и технологии</h3>
    <p>Текст новости с анализом... <a href="https://example.com">[1]</a></p>

    <h3>💼 Бизнес и стартапы</h3>
    <p>Другая новость... <a href="https://example2.com">[2]</a></p>
    """

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