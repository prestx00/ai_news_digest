from openai import AsyncOpenAI
import random
import asyncio
from . import config

# Клиент будет инициализирован внутри функции, когда понадобится

async def generate_article_and_summary(posts: list, prompt_template: str = None) -> tuple[str, str]:
    """Генерирует лонг-рид в HTML и краткое содержание на основе постов."""
    print(f"Начинаем генерацию. Количество постов: {len(posts)}")
    # Если специальный промпт не передан, используем основной промпт для статьи
    if prompt_template is None:
        prompt_template = config.ARTICLE_PROMPT

    # Инициализируем клиент здесь, когда конфигурация уже загружена
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    if not posts:
        print("Нет постов для обработки")
        return "", ""

    # Форматируем посты для подачи в модель
    formatted_posts = ""
    # Особый случай: если нам передали уже готовый поток <post> (после первого этапа),
    # не оборачиваем повторно
    if len(posts) == 1 and isinstance(posts[0][1], str) and "<post>" in posts[0][1]:
        formatted_posts = posts[0][1]
    else:
        for post in posts:
            text = post[1]
            source_link = post[2]
            has_media = "true" if post[3] else "false"  # Получаем флаг has_media
            # Строго следуем ожидаемому XML-формату в промптах
            formatted_posts += (
                f"<post>\n<content>{text}</content>\n<source>{source_link}</source>\n"
                f"<has_media>{has_media}</has_media>\n</post>\n\n"
            )
        formatted_posts += f"<post>\n<content>{text}</content>\n<source>{source_link}</source>\n<has_media>{has_media}</has_media>\n</post>\n\n"

    system_prompt = prompt_template

    try:
        response = await client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Вот подборка новостей за неделю:\n\n{formatted_posts}"}
            ],
            temperature=0.6,
            max_tokens=20000
        )
        await asyncio.sleep(random.uniform(1, 3))
        content = response.choices[0].message.content
        print(f"Получен ответ от OpenAI, длина: {len(content)} символов")

        article_html = ""
        summary = ""

        # Новая, более чистая логика обработки
        if prompt_template == config.SUMMARY_PROMPT:
            print("Обработка ответа от SUMMARY_PROMPT.")
            summary = content.strip()
            # article_html остается пустым, так как мы генерировали только саммари
        else:
            print("Обработка ответа от ARTICLE_PROMPT.")
            if '---SUMMARY---' in content:
                print("Статья успешно сгенерирована с кратким содержанием.")
                article_html, summary = content.split('---SUMMARY---', 1)
                article_html = article_html.strip()
                summary = summary.strip()
            else:
                print("Статья сгенерирована, но краткое содержание не найдено.")
                article_html = content.strip()
                # summary остается пустым
        
        return article_html, summary

    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Детали ошибки: {str(e)}")
        return "", ""