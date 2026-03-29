"""Обработчики текстовых сообщений"""

import re
from config import COUNTRY_CURRENCIES
from database import get_active_trip, update_trip_balance, add_expense, create_trip
from keyboards import expense_description_buttons, back_button, main_menu
from api_client import convert_currency


def register_messages(bot):
    """Регистрация обработчиков сообщений"""
    
    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        # Проверяем, является ли сообщение числом
        if is_number(message.text):
            active_trip = get_active_trip(message.from_user.id)

            if not active_trip:
                bot.reply_to(message, "❌ У вас нет активного путешествия. Создайте его с помощью /newtrip")
                return

            # Определяем названия валют для отображения
            dep_curr_code = active_trip[4]
            dest_curr_code = active_trip[5]

            dep_curr_name = dep_curr_code
            dest_curr_name = dest_curr_code
            for country, (code, name) in COUNTRY_CURRENCIES.items():
                if code == dep_curr_code:
                    dep_curr_name = f"{code} ({name})"
                    break
            for country, (code, name) in COUNTRY_CURRENCIES.items():
                if code == dest_curr_code:
                    dest_curr_name = f"{code} ({name})"
                    break

            try:
                amount = float(re.sub(r'[^\d.-]', '', message.text))

                # Конвертируем сумму из валюты назначения в валюту отправления
                # exchange_rate хранится как "1 RUB = ? GEL" (обратный курс)
                # Для конвертации: amount_GEL / exchange_rate = amount_RUB
                exchange_rate = active_trip[6]
                converted_amount = amount / exchange_rate

                response_text = f"{amount} {dest_curr_name} = {converted_amount:.2f} {dep_curr_name}"

                # Создаём клавиатуру с кнопками
                markup = expense_description_buttons()

                msg = bot.reply_to(message, f"{response_text}\n\n📝 Введите описание расхода:\n• Нажмите '⏭ Пропустить' — оставить без описания\n• Нажмите '❌ Отмена' — отмена ввода", reply_markup=markup)
                
                # Сохраняем данные для следующего шага
                user_expense_data = {
                    'amount_dest': amount,
                    'amount_dep': converted_amount,
                    'trip_id': active_trip[0],
                    'dest_curr': dest_curr_name,
                    'dep_curr': dep_curr_name
                }
                bot.temp_data = getattr(bot, 'temp_data', {})
                bot.temp_data[message.from_user.id] = user_expense_data

                bot.register_next_step_handler(msg, lambda m: process_expense_description(m, user_expense_data, False, bot))

            except ValueError:
                bot.reply_to(message, "❌ Пожалуйста, введите корректное число.")
        else:
            bot.reply_to(message, "Выберите действие:", reply_markup=main_menu())


def is_number(text):
    """Проверка, является ли сообщение числом"""
    try:
        float(re.sub(r'[^\d.-]', '', text))
        return True
    except ValueError:
        return False


def process_manual_exchange_rate(message, user_data, bot):
    """Обработка ручного ввода курса обмена"""
    try:
        user_data['final_rate'] = float(message.text.strip())
        bot.temp_data = getattr(bot, 'temp_data', {})
        bot.temp_data.pop(f"exchange_{message.from_user.id}", None)
        process_initial_amount_prompt(message, user_data, bot)
    except ValueError:
        markup = back_button()
        bot.reply_to(message, "❌ Пожалуйста, введите корректное число для курса обмена.", reply_markup=markup)


def process_initial_amount_prompt(message, user_data, bot):
    """Запрос начальной суммы"""
    markup = back_button()
    msg = bot.reply_to(message, f"💰 Введите начальную сумму в валюте {user_data['departure_currency']} ({user_data['departure_currency_name']}):", reply_markup=markup)
    bot.register_next_step_handler(msg, process_initial_amount, user_data, bot)


def process_initial_amount(message, user_data, bot):
    """Обработка начальной суммы и создание путешествия"""
    try:
        initial_amount = float(re.sub(r'[^\d.-]', '', message.text))

        success, msg_text = create_trip(
            message.from_user.id,
            user_data['departure_country'].title(),
            user_data['destination_country'].title(),
            user_data['departure_currency'],
            user_data['destination_currency'],
            user_data['final_rate'],
            initial_amount,
            convert_currency
        )

        if success:
            bot.reply_to(message, f"✅ Путешествие '{user_data['destination_country'].title()}' создано!\n\n"
                                f"Страна отправления: {user_data['departure_country'].title()} ({user_data['departure_currency']} - {user_data['departure_currency_name']})\n"
                                f"Страна назначения: {user_data['destination_country'].title()} ({user_data['destination_currency']} - {user_data['destination_currency_name']})\n"
                                f"Курс обмена: 1 {user_data['departure_currency']} = {user_data['final_rate']} {user_data['destination_currency']}\n"
                                f"Начальный баланс: {initial_amount} {user_data['departure_currency']} = "
                                f"{initial_amount * user_data['final_rate']} {user_data['destination_currency']}\n\n"
                                f"📝 Теперь просто вводите сумму в {user_data['destination_currency']} (валюта страны пребывания) для учёта расходов.")
        else:
            bot.reply_to(message, f"❌ {msg_text}")

    except ValueError:
        bot.reply_to(message, "❌ Пожалуйста, введите корректное число для начальной суммы.")


def process_expense_description(message, user_expense_data, skip, bot):
    """Обработка описания расхода"""
    # Проверяем, не был ли отменён ввод для этого пользователя
    bot.expense_cancelled = getattr(bot, 'expense_cancelled', set())
    if message.from_user.id in bot.expense_cancelled:
        bot.expense_cancelled.discard(message.from_user.id)
        return
    
    if skip:
        description = ""
    else:
        description = message.text.strip()
        if description.lower() in ['пропустить', 'skip', '']:
            description = ""
    
    trip_id = user_expense_data['trip_id']
    amount_dest = user_expense_data['amount_dest']
    amount_dep = user_expense_data['amount_dep']
    
    # Добавляем расход с описанием
    add_expense(trip_id, amount_dest, amount_dep, description)
    
    # Обновляем баланс (вычитаем расход)
    update_trip_balance(trip_id, -amount_dest, -amount_dep)
    
    # Создаём клавиатуру с кнопкой "Назад"
    markup = back_button()
    
    desc_text = f"Описание: {description}" if description else "Описание: без описания"
    bot.reply_to(message, f"✅ Расход учтён!\n\n"
                         f"{amount_dest:,.2f} {user_expense_data['dest_curr']} = {amount_dep:,.2f} {user_expense_data['dep_curr']}\n"
                         f"{desc_text}", reply_markup=markup)

    # Очищаем временные данные
    bot.temp_data = getattr(bot, 'temp_data', {})
    bot.temp_data.pop(message.from_user.id, None)
    bot.expense_cancelled.discard(message.from_user.id)
