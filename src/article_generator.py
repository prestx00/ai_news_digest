import openai
from . import config

# Устанавливаем ключ API при импорте модуля
openai.api_key = config.OPENAI_API_KEY

def generate_article_and_summary(posts: list) -> tuple[str, str]:
    """Генерирует лонг-рид в HTML и краткое содержание на основе постов."""
    if not posts:
        return "", ""

    # Форматируем посты для подачи в модель
    formatted_posts = ""
    for post in posts:
        text = post[1]
        source_link = post[2]
        formatted_posts += f"<post>\n<content>{text}</content>\n<source>{source_link}</source>\n</post>\n\n"

    system_prompt = """
    Ты — экспертный AI-аналитик и редактор новостного IT-издания. Твоя задача — проанализировать подборку новостей в <post> тегах и превратить их в качественный, структурированный лонг-рид в формате HTML. Аудитория — IT-специалисты, менеджеры и энтузиасты.

    Требования к лонг-риду (HTML):
    1.  **Заголовок:** Используй тег <h1> для яркого и емкого заголовка всего дайджеста.
    2.  **Структура:** Сгруппируй новости по 3-5 ключевым темам. Каждая тема — это раздел, начинающийся с подзаголовка в теге <h2>.
    3.  **Содержание:** Внутри каждого раздела связно изложи новости в тегах <p>. Не просто копируй, а пересказывай и анализируй.
    4.  **Источники:** В конце каждого смыслового абзаца или утверждения, основанного на посте, ставь ссылку на источник. Ссылка должна выглядеть как маленький кликабельный значок или цифра, например: <a href="[source_link]">[1]</a>. Используй ссылки из тега <source>.
    5.  **Форматирование:** Используй <b> для выделения ключевых терминов и <i> для комментариев.

    Требования к краткому содержанию (summary):
    *   Это текст для анонса в Telegram. Он должен быть коротким (3-4 предложения).
    *   Перечисли основные темы, затронутые в дайджесте, чтобы заинтриговать читателя.

    Отформатируй свой ответ строго в виде двух частей, разделенных маркером '---SUMMARY---'.
    Сначала полный HTML-код лонг-рида, затем маркер, затем краткое содержание.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Вот подборка новостей за неделю:\n\n{formatted_posts}"}
            ],
            temperature=0.6,
            max_tokens=10000
        )
        content = response.choices[0].message.content
        if '---SUMMARY---' in content:
            article_html, summary = content.split('---SUMMARY---', 1)
            return article_html.strip(), summary.strip()
        else:
            return content.strip(), "Краткое содержание не было сгенерировано."

    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {e}")
        return {"article": "", "summary": ""} 