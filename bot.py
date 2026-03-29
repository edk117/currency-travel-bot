"""
Currency Travel Bot - Кошелёк-конвертер валют для путешественников
"""

import telebot
from config import BOT_TOKEN
from database import init_db
from handlers import register_commands, register_callbacks, register_messages
from keyboards import main_menu

# Создаём бота
bot = telebot.TeleBot(BOT_TOKEN)

# Сохраняем ссылку на бота для использования в модулях
import handlers.commands as commands_module
commands_module.bot = bot
commands_module.process_departure_country.bot = bot
commands_module.process_destination_country.bot = bot


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
    from telebot import apihelper
    apihelper.RETRY_ON_ERROR = True
    apihelper.MAX_RETRIES = 5
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=30)
    except Exception as e:
        print(f"Ошибка бота: {e}")
        print("Перезапустите бота")


if __name__ == '__main__':
    main()
