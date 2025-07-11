

import asyncio
import sys
from telethon.sync import TelegramClient
from src import config

def main():
    """Главная функция для запуска проверки сессии."""
    if len(sys.argv) < 2:
        print("Ошибка: Укажите путь к файлу конфигурации в качестве аргумента.")
        print("Пример: python3 check_session.py .env.ai")
        sys.exit(1)

    config_path = sys.argv[1]

    try:
        config.load_config(config_path)
    except FileNotFoundError:
        print(f"Ошибка: Файл конфигурации '{config_path}' не найден.")
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка в конфигурации '{config_path}': {e}")
        sys.exit(1)

    asyncio.run(check_session())

async def check_session():
    """
    Проверяет валидность файла telegram_session.session,
    пытаясь подключиться к Telegram и получить информацию о себе.
    """
    session_name = 'telegram_session'
    print(f"Пытаюсь подключиться, используя сессию '{session_name}.session'...")

    try:
        async with TelegramClient(session_name, config.API_ID, config.API_HASH) as client:
            print("Файл сессии найден и успешно прочитан.")
            me = await client.get_me()

            if me:
                print("\nПроверка прошла успешно!\n")
                print("Файл сессии действителен и принадлежит пользователю:")
                print(f"  ID: {me.id}")
                print(f"  Имя: {me.first_name}")
                if me.last_name:
                    print(f"  Фамилия: {me.last_name}")
                if me.username:
                    print(f"  Юзернейм: @{me.username}")
            else:
                print("Не удалось получить информацию о пользователе. Сессия может быть повреждена.")

    except Exception as e:
        print(f"\nПроизошла ошибка при попытке подключения: {e}")
        print("Это может означать, что файл сессии недействителен или поврежден.")
        print("Вам нужно будет пройти аутентификацию заново, запустив основной скрипт.")

if __name__ == "__main__":
    main()

