from telethon.sync import TelegramClient
from telethon.tl.types import Channel
from . import config, database
import asyncio

async def parse_channels():
    """Парсит заданные каналы и сохраняет новые посты в базу данных."""
    # Используем имя сессии, чтобы Telethon сохранил авторизацию в файл
    async with TelegramClient('telegram_session', config.API_ID, config.API_HASH) as client:
        print("Парсер запущен...")
        for channel_name in config.TELEGRAM_CHANNELS:
            if not channel_name:
                continue
            try:
                entity = await client.get_entity(channel_name)
                if isinstance(entity, Channel):
                    print(f"Парсинг канала: {entity.title}")
                    async for message in client.iter_messages(entity, limit=50):
                        # Формируем прямую ссылку на пост
                        source_link = f"https://t.me/{entity.username}/{message.id}"
                        # Проверяем наличие медиа (фото, видео, документ)
                        has_media = bool(message.photo or message.video or message.document)

                        # Сохраняем пост, даже если нет текста, но есть медиа
                        if message.text or has_media:
                            database.add_post(
                                channel=channel_name,
                                message_id=message.id,
                                text=message.text if message.text else "", # Сохраняем пустую строку, если текста нет
                                date=int(message.date.timestamp()),
                                source_link=source_link,
                                has_media=has_media
                            )
            except Exception as e:
                print(f"Ошибка при парсинге канала {channel_name}: {e}")
        print("Парсинг завершен.")

if __name__ == '__main__':
    # Этот блок нужен для первоначальной авторизации
    print("Запуск скрипта для авторизации Telethon...")
    print("Пожалуйста, введите ваш номер телефона и код, который придет в Telegram.")
    asyncio.run(parse_channels())
