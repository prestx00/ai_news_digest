import asyncio
import argparse
import pytz # Добавляем импорт pytz
import os # Добавляем импорт os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src import (
    config, # Импортируем модуль config
    database,
    telegram_parser,
    article_generator,
    telegraph_publisher,
    telegram_notifier
)

async def weekly_digest_job():
    """Основная задача, выполняющая весь цикл создания дайджеста с пакетной обработкой."""
    print("\n--- НАЧАЛО НОВОГО ЦИКЛА СОЗДАНИЯ ДАЙДЖЕСТА ---")

    # 1. Парсинг каналов
    print("\n[Шаг 1/5] Запуск парсинга новых постов...")
    await telegram_parser.parse_channels()
    print("[Шаг 1/5] Парсинг завершен.")

    # 2. Пакетная обработка постов и сборка общего саммари
    print("\n[Шаг 2/5] Начало пакетной обработки постов для создания саммари...")
    all_posts_ids = []
    all_summaries_text = ""
    batch_size = 50  # Размер одной пачки. Можно подобрать экспериментально.
    offset = 0
    batch_num = 1

    while True:
        print(f"  - Обработка пачки #{batch_num}, смещение: {offset}...")
        posts_batch = database.get_unprocessed_posts(limit=batch_size, offset=offset)

        if not posts_batch:
            print("  - Все посты обработаны, пачек больше нет.")
            break

        print(f"  - В пачке #{batch_num} найдено {len(posts_batch)} постов.")
        batch_ids = [p[0] for p in posts_batch]
        all_posts_ids.extend(batch_ids)

        # Генерируем КРАТКОЕ саммари для текущей пачки постов
        print(f"  - Отправка пачки #{batch_num} в OpenAI для генерации краткого саммари...")
        _, batch_summary = await article_generator.generate_article_and_summary(
            posts_batch,
            prompt_template=config.SUMMARY_PROMPT
        )

        if batch_summary:
            all_summaries_text += batch_summary + "\n\n"
            print(f"  - Саммари для пачки #{batch_num} успешно сгенерировано.")
        else:
            print(f"  - !!! Не удалось сгенерировать саммари для пачки #{batch_num}.")

        offset += batch_size
        batch_num += 1
        print("  - Пауза 10 секунд перед следующей пачкой...")
        await asyncio.sleep(10)

    if not all_summaries_text:
        print("\n[ЗАВЕРШЕНИЕ] Не удалось сгенерировать ни одного саммари. Пропускаем этот цикл.")
        return
    
    print("[Шаг 2/5] Пакетная обработка завершена. Общий текст саммари собран.")

    # 3. Генерация финального лонгрида из общего саммари
    print("\n[Шаг 3/5] Генерация финального лонгрида и саммари из общего текста...")
    final_input_for_generator = [(0, all_summaries_text, "", False)]
    
    article_html, summary = await article_generator.generate_article_and_summary(
        final_input_for_generator,
        prompt_template=config.ARTICLE_PROMPT
    )

    if not article_html or not summary:
        print("\n[ОШИБКА] Не удалось сгенестрировать финальную статью или саммари. Посты не будут отмечены как обработанные.")
        return

    print("[Шаг 3/5] Финальный лонгрид и саммари успешно сгенерированы.")

    try:
        title = article_html.split('<h1>')[1].split('</h1>')[0]
    except IndexError:
        title = "Еженедельный AI-дайджест"

    # 4. Публикация в Telegra.ph
    print(f"\n[Шаг 4/5] Публикация статьи в Telegra.ph с заголовком: '{title}'...")
    article_url = await telegraph_publisher.publish_to_telegraph(title, article_html)

    if not article_url:
        print("\n[ОШИБКА] Не удалось опубликовать статью в Telegra.ph.")
        return
    
    print(f"[Шаг 4/5] Статья успешно опубликована: {article_url}")

    # 5. Отправка уведомления в Telegram
    print("\n[Шаг 5/5] Отправка уведомления в Telegram...")
    await telegram_notifier.send_notification(summary, article_url)
    print("[Шаг 5/5] Уведомление успешно отправлено.")

    # 6. Отметка ВСЕХ обработанных постов как завершенных
    database.mark_posts_as_processed(all_posts_ids)
    print(f"\n[УСПЕХ] Дайджест успешно создан и отправлен! Всего обработано {len(all_posts_ids)} постов.")
    print("--- ЦИКЛ СОЗДАНИЯ ДАЙДЖЕСТА ЗАВЕРШЕН ---")

async def main_async(config_file: str, init_session: bool):
    # Загружаем конфигурацию
    config.load_config(config_file)

    # Устанавливаем имя сессии на основе имени файла конфигурации
    file_base_name = os.path.basename(config_file)
    if file_base_name.startswith('.env.'):
        session_name = file_base_name[len('.env.'):]
    else:
        session_name = os.path.splitext(file_base_name)[0]
    config.SESSION_NAME = session_name

    # Инициализация базы данных при первом запуске
    database.init_db()

    # Если указан флаг --init-session, просто запускаем парсер и выходим
    if init_session:
        print("Запуск в режиме инициализации сессии...")
        await telegram_parser.parse_channels()
        print("Инициализация сессии завершена.")
        return

    # database.reset_processed_posts()
    # Настройка планировщика
    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Moscow'))
    # Запуск задачи каждую неделю, в пятницу в 20:40
    scheduler.add_job(
        weekly_digest_job, 
        'cron', 
        day_of_week=config.SCHEDULE_DAY_OF_WEEK, 
        hour=config.SCHEDULE_HOUR, 
        minute=config.SCHEDULE_MINUTE
    )

    print(f"Планировщик для {config_file} запущен. Следующий запуск в {config.SCHEDULE_DAY_OF_WEEK} в {config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d}.")
    print("Нажмите Ctrl+C для выхода.")

    scheduler.start()

    # Поддерживаем работу скрипта, чтобы цикл событий не завершался
    try:
        # Создаем Future, который никогда не будет завершен, чтобы держать loop активным
        await asyncio.Future()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск бота для создания дайджестов.")
    parser.add_argument(
        "--config", 
        default=".env.ai", 
        help="Путь к файлу конфигурации (например, .env.ai или .env.hr)"
    )
    parser.add_argument(
        "--init-session",
        action="store_true", # Этот флаг не требует значения, он просто есть или его нет
        help="Запустить парсер один раз для создания сессии Telegram и выйти."
    )
    args = parser.parse_args()

    asyncio.run(main_async(args.config, args.init_session))