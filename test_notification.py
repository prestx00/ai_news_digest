#!/usr/bin/env python3
"""
Скрипт для тестирования отправки уведомлений в Telegram.
Использование: python test_notification.py --config .env.ai
"""

import asyncio
import argparse
import os
import sys
from src import config
from src.telegram_notifier import send_test_notification

async def main():
    """Главная функция для тестирования уведомлений."""
    parser = argparse.ArgumentParser(description="Тестирование уведомлений Telegram бота.")
    parser.add_argument(
        "--config", 
        default=".env.ai", 
        help="Путь к файлу конфигурации (например, .env.ai или .env.hr)"
    )
    args = parser.parse_args()

    try:
        # Загружаем конфигурацию
        config.load_config(args.config)
        print(f"Конфигурация загружена из {args.config}")
        print(f"CHAT_ID: {config.CHAT_ID}")
        print(f"MESSAGE_THREAD_ID: {config.MESSAGE_THREAD_ID}")
        
        # Отправляем тестовое уведомление
        print("\nОтправляем тестовое уведомление...")
        await send_test_notification()
        print("Тест завершен!")
        
    except FileNotFoundError:
        print(f"Ошибка: Файл конфигурации '{args.config}' не найден.")
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка в конфигурации '{args.config}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при отправке тестового уведомления: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
