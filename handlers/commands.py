"""Обработчики команд бота"""

from telebot import types
from database import get_user_trips, get_active_trip, get_connection
from keyboards import main_menu, switch_trip_buttons, exchange_rate_buttons
from config import COUNTRY_CURRENCIES
from api_client import convert_currency

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

        bot_instance.reply_to(message, "👋 Привет! Я ваш миникошелёк для путешествий. Выберите действие:", reply_markup=main_menu())

    @bot_instance.message_handler(commands=['newtrip'])
    def new_trip_cmd(message):
        msg = bot_instance.reply_to(message, "Введите страну отправления:")
        bot_instance.register_next_step_handler(msg, process_departure_country)

    @bot_instance.message_handler(commands=['balance'])
    def show_balance_handler(message):
        from handlers.callbacks import show_balance
        call_wrapper = types.SimpleNamespace(message=message, from_user=message.from_user)
        show_balance(call_wrapper, bot_instance)

    @bot_instance.message_handler(commands=['history'])
    def show_history_handler(message):
        from handlers.callbacks import show_history
        call_wrapper = types.SimpleNamespace(message=message, from_user=message.from_user)
        show_history(call_wrapper, bot_instance)

    @bot_instance.message_handler(commands=['setrate'])
    def set_rate_cmd_handler(message):
        from handlers.callbacks import set_rate_cmd
        call_wrapper = types.SimpleNamespace(message=message, from_user=message.from_user)
        set_rate_cmd(call_wrapper, bot_instance)

    @bot_instance.message_handler(commands=['switch'])
    def switch_trip_handler(message):
        trips = get_user_trips(message.from_user.id)

        if not trips:
            bot_instance.reply_to(message, "❌ У вас нет созданных путешествий.")
            return

        markup = switch_trip_buttons(trips)
        bot_instance.reply_to(message, "Выберите путешествие для переключения:", reply_markup=markup)


def process_departure_country(message):
    """Обработка ввода страны отправления"""
    user_data = {'departure_country': message.text.strip().lower()}

    # Проверяем, существует ли валюта для введенной страны
    departure_currency_info = COUNTRY_CURRENCIES.get(user_data['departure_country'])

    # Если не нашли точное совпадение, пробуем найти частичное совпадение
    if not departure_currency_info:
        for country, currency_info in COUNTRY_CURRENCIES.items():
            if user_data['departure_country'] in country or country in user_data['departure_country']:
                departure_currency_info = currency_info
                user_data['departure_country'] = country
                break

    if not departure_currency_info:
        bot.reply_to(message, f"❌ Не удалось определить валюту для страны '{user_data['departure_country']}'. Попробуйте снова.")
        return

    msg = bot.reply_to(message, "Введите страну назначения:")
    bot.register_next_step_handler(msg, process_destination_country, user_data)


def process_departure_country_wrapper(message, bot_instance):
    """Обёртка для использования в callback"""
    global bot
    bot = bot_instance
    process_departure_country(message)


def process_destination_country(message, user_data):
    """Обработка ввода страны назначения"""
    user_data['destination_country'] = message.text.strip().lower()

    # Определяем валюты по названиям стран
    departure_currency_info = COUNTRY_CURRENCIES.get(user_data['departure_country'])
    destination_currency_info = COUNTRY_CURRENCIES.get(user_data['destination_country'])

    # Если не нашли точное совпадение, пробуем найти частичное совпадение
    if not departure_currency_info:
        for country, currency_info in COUNTRY_CURRENCIES.items():
            if user_data['departure_country'] in country or country in user_data['departure_country']:
                departure_currency_info = currency_info
                user_data['departure_country'] = country
                break

    if not destination_currency_info:
        for country, currency_info in COUNTRY_CURRENCIES.items():
            if user_data['destination_country'] in country or country in user_data['destination_country']:
                destination_currency_info = currency_info
                user_data['destination_country'] = country
                break

    if not departure_currency_info:
        bot.reply_to(message, f"❌ Не удалось определить валюту для страны отправления '{user_data['departure_country']}'. Попробуйте снова.")
        return

    if not destination_currency_info:
        bot.reply_to(message, f"❌ Не удалось определить валюту для страны назначения '{user_data['destination_country']}'. Попробуйте снова.")
        return

    user_data['departure_currency'] = departure_currency_info[0]
    user_data['departure_currency_name'] = departure_currency_info[1]
    user_data['destination_currency'] = destination_currency_info[0]
    user_data['destination_currency_name'] = destination_currency_info[1]

    # Получаем курс обмена
    rate_data = convert_currency(1, user_data['departure_currency'], user_data['destination_currency'])

    if 'error' in rate_data:
        from keyboards import back_button
        bot.reply_to(message, f"❌ Ошибка при получении курса: {rate_data['error']['info']}", reply_markup=back_button())
        return

    rate = rate_data['result']
    user_data['exchange_rate'] = rate

    # Отправляем информацию о валюте назначения и курсе
    response_text = f"страна назначения: {user_data['destination_country'].title()}\n"
    response_text += f"валюта: {user_data['destination_currency']} ({user_data['destination_currency_name']})\n"
    response_text += f"текщий курс по данным API: 1 {user_data['departure_currency']} = {rate} {user_data['destination_currency']}"

    # Сохраняем данные для callback
    bot.temp_data = getattr(bot, 'temp_data', {})
    bot.temp_data[f"exchange_{message.from_user.id}"] = user_data

    bot.reply_to(message, f"{response_text}\n\nПодходит ли вам этот курс?", reply_markup=exchange_rate_buttons())
