import asyncio
import argparse
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
    """Основная задача, выполняющая весь цикл создания дайджеста."""
    print("Запуск еженедельной задачи по созданию дайджеста...")

    # 1. Парсинг каналов
    await telegram_parser.parse_channels()

    # 2. Получение необработанных постов
    posts = database.get_unprocessed_posts()
    if not posts:
        print("Нет новых постов для обработки. Задача завершена.")
        return

    post_ids = [p[0] for p in posts]

    # 3. Генерация статьи и саммари
    print("Генерация статьи с помощью OpenAI...")
    article_html, summary = await article_generator.generate_article_and_summary(posts)

    if not article_html or not summary:
        print("Не удалось сгенерировать статью. Задача прервана.")
        return

    # Извлекаем заголовок из HTML (ищем первый тег h1)
    try:
        title = article_html.split('<h1>')[1].split('</h1>')[0]
    except IndexError:
        title = "Еженедельный AI-дайджест"

    # 4. Публикация в Telegra.ph
    print("Публикация статьи в Telegra.ph...")
    article_url = await telegraph_publisher.publish_to_telegraph(title, article_html)

    if not article_url:
        print("Не удалось опубликовать статью. Задача прервана.")
        return

    # 5. Отправка уведомления в Telegram
    await telegram_notifier.send_notification(summary, article_url)

    # 6. Отметка постов как обработанных
    database.mark_posts_as_processed(post_ids)
    print("Дайджест успешно создан и отправлен!")

async def main_async(config_file: str):
    # Загружаем конфигурацию
    config.load_config(config_file)

    # Инициализация базы данных при первом запуске
    database.init_db()
    # database.reset_processed_posts()
    # Настройка планировщика
    scheduler = AsyncIOScheduler()
    # Запуск задачи каждую неделю, в пятницу в 20:40
    scheduler.add_job(weekly_digest_job, 'cron', day_of_week='fri', hour=22, minute=36)

    print(f"Планировщик для {config_file} запущен. Следующий запуск в пятницу в 22:36.")
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
    args = parser.parse_args()

    asyncio.run(main_async(args.config))
