from openai import AsyncOpenAI
import asyncio
import random
import html
from . import config

def _xml(text: str) -> str:
    # Экранируем спецсимволы, чтобы не порвать XML
    return html.escape(text or "", quote=True)


async def generate_article_and_summary(posts: list, prompt_template: str = None) -> tuple[str, str]:
    """Генерирует лонг-рид в HTML и краткое содержание на основе постов."""
    print(f"Начинаем генерацию. Количество постов: {len(posts)}")

    if prompt_template is None:
        prompt_template = config.ARTICLE_PROMPT

    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

    if not posts:
        print("Нет постов для обработки")
        return "", ""

    # Форматируем посты для подачи в модель (XML), экранируем содержимое
    if len(posts) == 1 and isinstance(posts[0][1], str) and "<post>" in posts[0][1]:
        formatted_posts = posts[0][1]
    else:
        chunks = []
        for post in posts:
            # ожидаем структуру: (id, text, source_link, has_media_bool, ...)
            text = post[1]
            source_link = post[2]
            has_media = "true" if post[3] else "false"
            chunks.append(
                "<post>\n"
                f"<content>{_xml(text)}</content>\n"
                f"<source>{_xml(source_link)}</source>\n"
                f"<has_media>{has_media}</has_media>\n"
                "</post>\n"
            )
        formatted_posts = "\n".join(chunks)

    system_prompt = prompt_template

    # --- Параметры модели GPT-5 (reasoning) ---
    base_params = {
        "model": "gpt-5",
        "seed": 42,
        "response_format": {"type": "text"},  # можно переключить на {"type": "json"} при необходимости
    }

    if prompt_template == config.SUMMARY_PROMPT:
        request_params = {
            **base_params,
            "max_completion_tokens": 16000,
            "reasoning": {"effort": "low"},
            # ВАЖНО: НЕ передаем temperature/top_p/penalties для gpt-5
        }
        fallback_temperature = 0.25  # только для chat.completions
    else:
        request_params = {
            **base_params,
            "max_completion_tokens": 20000,
            "reasoning": {"effort": "medium"},
        }
        fallback_temperature = 0.55

    # Собираем вход под Responses API.
    # В responses лучше отправить единый input-текст, чтобы не нарваться на несовместимость "messages" в SDK.
    input_text = (
        "### System Instructions\n"
        f"{system_prompt}\n\n"
        "### User Content\n"
        "Вот подборка новостей за неделю:\n\n"
        f"{formatted_posts}"
    )

    try:
        attempt = 0
        last_error = None
        response = None

        while attempt < 2 and response is None:
            try:
                # Путь 1: Responses API — корректный путь для gpt-5
                # НЕ передаём temperature/top_p/penalties (они либо игнорируются, либо дают 400)
                response = await client.responses.create(
                    model=request_params["model"],
                    input=input_text,
                    max_completion_tokens=request_params.get("max_completion_tokens"),
                    reasoning=request_params.get("reasoning"),
                    seed=request_params.get("seed"),
                    response_format=request_params.get("response_format"),
                )
            except Exception as e_inner:
                last_error = e_inner
                attempt += 1
                print(f"[Attempt {attempt}] Responses API error: {e_inner}")
                await asyncio.sleep(1.0 * attempt)

        # Если не вышло — fallback на chat.completions с совместимыми параметрами и моделью
        if response is None:
            print("Переходим на fallback: chat.completions + gpt-4o")

            # Конвертация max_completion_tokens -> max_tokens c разумной отсечкой
            # (чтобы не прыгать за лимиты fallback-модели)
            mct = request_params.get("max_completion_tokens", 16000)
            fallback_max_tokens = min(mct, 20000)

            response = await client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Вот подборка новостей за неделю:\n\n{formatted_posts}"},
                ],
                max_tokens=fallback_max_tokens,
                temperature=fallback_temperature,
                top_p=1,
                frequency_penalty=0.1 if prompt_template != config.SUMMARY_PROMPT else 0.0,
                presence_penalty=0.0,
            )

        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Унифицированное извлечение текста
        content = None

        # 1) Responses API (новые модели): у многих SDK есть .output_text
        content = getattr(response, "output_text", None)

        # 2) Доп. попытка — некоторые SDK возвращают "output" массив
        if not content and hasattr(response, "output"):
            try:
                # Пытаемся собрать текст из структурированного вывода
                parts = []
                for block in getattr(response, "output", []):
                    for item in block.get("content", []):
                        if isinstance(item, dict) and "text" in item:
                            parts.append(item["text"])
                if parts:
                    content = "\n".join(parts)
            except Exception:
                pass

        # 3) Chat Completions
        if not content:
            try:
                content = response.choices[0].message.content
            except Exception:
                pass

        if not content:
            raise RuntimeError("Не удалось извлечь текст ответа из OpenAI API")

        print(f"Получен ответ от OpenAI, длина: {len(content)} символов")

        article_html = ""
        summary = ""

        if prompt_template == config.SUMMARY_PROMPT:
            print("Обработка ответа от SUMMARY_PROMPT.")
            summary = content.strip()
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

        return article_html, summary

    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Детали ошибки: {str(e)}")
        return "", ""
