"""
Currency Travel Bot - Кошелёк-конвертер валют для путешественников
"""

import telebot
from telebot import apihelper

from config import BOT_TOKEN
from database import init_db
from handlers import register_commands, register_callbacks, register_messages
from handlers import commands as commands_module


# Создаём бота
bot = telebot.TeleBot(BOT_TOKEN)

# Сохраняем ссылку на бота для использования в модулях
commands_module.bot = bot


def main():
    """Основная функция запуска бота"""
    # Инициализация базы данных
    init_db()

    # Регистрация обработчиков
    register_commands(bot)
    register_callbacks(bot)
    register_messages(bot)

    # Запуск бота
    print("Бот запущен...")

    # Настройка повторных попыток подключения
    apihelper.RETRY_ON_ERROR = True
    apihelper.MAX_RETRIES = 5

    try:
        bot.polling(none_stop=True, interval=1, timeout=30, skip_pending=True)
    except Exception as e:
        print(f"Ошибка бота: {e}")
        print("Перезапустите бота")


if __name__ == '__main__':
    main()
