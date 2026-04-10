"""Обработчики команд бота"""

from telebot import types

from api_client import convert_currency
from database import get_user_trips, get_connection
from handlers.callbacks import (
    show_balance,
    show_history,
    set_rate_cmd,
)
from keyboards import main_menu, switch_trip_buttons, exchange_rate_buttons
from utils.currency_utils import get_currency_info

# Ссылка на бота (устанавливается в bot.py)
bot = None


def register_commands(bot_instance):
    """Регистрация обработчиков команд"""
    global bot
    bot = bot_instance

    @bot_instance.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id

        # Добавляем пользователя в базу данных, если его там нет
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (user_id,))
        conn.commit()
        conn.close()

        bot_instance.reply_to(
            message,
            "👋 Привет! Я ваш миникошелёк для путешествий. Выберите действие:",
            reply_markup=main_menu(),
        )

    @bot_instance.message_handler(commands=['newtrip'])
    def new_trip_cmd(message):
        msg = bot_instance.reply_to(message, "Введите страну отправления:")
        bot_instance.register_next_step_handler(msg, process_departure_country)

    @bot_instance.message_handler(commands=['balance'])
    def show_balance_handler(message):
        call_wrapper = types.SimpleNamespace(message=message, from_user=message.from_user)
        show_balance(call_wrapper, bot_instance)

    @bot_instance.message_handler(commands=['history'])
    def show_history_handler(message):
        call_wrapper = types.SimpleNamespace(message=message, from_user=message.from_user)
        show_history(call_wrapper, bot_instance)

    @bot_instance.message_handler(commands=['setrate'])
    def set_rate_cmd_handler(message):
        call_wrapper = types.SimpleNamespace(message=message, from_user=message.from_user)
        set_rate_cmd(call_wrapper, bot_instance)

    @bot_instance.message_handler(commands=['switch'])
    def switch_trip_handler(message):
        trips = get_user_trips(message.from_user.id)

        if not trips:
            bot_instance.reply_to(
                message,
                "❌ У вас нет созданных путешествий.",
            )
            return

        markup = switch_trip_buttons(trips)
        bot_instance.reply_to(
            message,
            "Выберите путешествие для переключения:",
            reply_markup=markup,
        )


def process_departure_country(message):
    """Обработка ввода страны отправления"""
    country_input = message.text.strip().lower()
    result = get_currency_info(country_input)

    if not result:
        bot.reply_to(
            message,
            f"❌ Не удалось определить валюту для страны '{country_input}'. Попробуйте снова.",
        )
        return

    user_data = {
        'departure_country': result[0],
        'departure_currency': result[1][0],
        'departure_currency_name': result[1][1],
    }

    msg = bot.reply_to(message, "Введите страну назначения:")
    bot.register_next_step_handler(msg, process_destination_country, user_data)


def process_destination_country(message, user_data):
    """Обработка ввода страны назначения"""
    dest_input = message.text.strip().lower()

    dep_result = get_currency_info(user_data['departure_country'])
    dest_result = get_currency_info(dest_input)

    if not dep_result:
        dep_country = user_data['departure_country']
        bot.reply_to(
            message,
            f"❌ Не удалось определить валюту для страны "
            f"'{dep_country}'. Попробуйте снова.",
        )
        return

    if not dest_result:
        bot.reply_to(
            message,
            f"❌ Не удалось определить валюту для страны назначения '{dest_input}'. Попробуйте снова.",
        )
        return

    user_data['departure_country'] = dep_result[0]
    user_data['departure_currency'] = dep_result[1][0]
    user_data['departure_currency_name'] = dep_result[1][1]
    user_data['destination_country'] = dest_result[0]
    user_data['destination_currency'] = dest_result[1][0]
    user_data['destination_currency_name'] = dest_result[1][1]

    # Получаем курс обмена
    rate_data = convert_currency(1, user_data['departure_currency'], user_data['destination_currency'])

    if 'error' in rate_data:
        from keyboards import back_button
        error_info = rate_data['error']['info']
        bot.reply_to(
            message,
            f"❌ Ошибка при получении курса: {error_info}",
            reply_markup=back_button(),
        )
        return

    rate = rate_data['result']
    user_data['exchange_rate'] = rate

    dest_country = user_data['destination_country'].title()
    dest_curr = user_data['destination_currency']
    dest_curr_name = user_data['destination_currency_name']
    dep_curr = user_data['departure_currency']

    response_text = f"страна назначения: {dest_country}\n"
    response_text += f"валюта: {dest_curr} ({dest_curr_name})\n"
    response_text += f"текщий курс по данным API: 1 {dep_curr} = {rate} {dest_curr}"

    # Сохраняем данные для callback
    bot.temp_data = getattr(bot, 'temp_data', {})
    bot.temp_data[f"exchange_{message.from_user.id}"] = user_data

    bot.reply_to(message, f"{response_text}\n\nПодходит ли вам этот курс?", reply_markup=exchange_rate_buttons())
