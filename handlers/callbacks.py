"""Обработчики callback-запросов (inline кнопки)"""

import re

from database import (
    get_active_trip,
    get_expenses_history,
    get_user_trips,
    switch_active_trip,
    update_exchange_rate,
)
from keyboards import back_button, main_menu, trip_list_buttons
from utils.currency_utils import format_currency_display


def register_callbacks(bot):
    """Регистрация обработчиков callback"""

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        if call.data == "new_trip":
            from handlers.commands import process_departure_country

            msg = bot.reply_to(call.message, "Введите страну отправления:")
            bot.register_next_step_handler(msg, process_departure_country)
        elif call.data == "my_trips":
            show_my_trips(call, bot)
        elif call.data == "balance":
            show_balance(call, bot)
        elif call.data == "history":
            show_history(call, bot)
        elif call.data == "set_rate":
            set_rate_cmd(call, bot)
        elif call.data.startswith("switch_to_"):
            trip_id = int(call.data.split("_")[2])
            switch_to_trip(call, trip_id, bot)
        elif call.data.startswith("activate_trip_"):
            trip_id = int(call.data.split("_")[2])
            switch_to_trip(call, trip_id, bot)
        elif call.data == "exchange_rate_confirm":
            handle_exchange_rate_confirm(call, bot)
        elif call.data == "exchange_rate_manual":
            handle_exchange_rate_manual(call, bot)
        elif call.data == "expense_skip_desc":
            handle_expense_skip(call, bot)
        elif call.data == "expense_cancel_input":
            handle_expense_cancel(call, bot)
        elif call.data == "back_to_menu":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Выберите действие:",
                reply_markup=main_menu(),
            )


def show_my_trips(call, bot):
    """Показ списка путешествий"""
    trips = get_user_trips(call.from_user.id)

    if not trips:
        bot.reply_to(call.message, "❌ У вас нет созданных путешествий.")
        return

    trips_text = "🧳 Ваши путешествия:\n\n"

    for i, trip in enumerate(trips, 1):
        is_active = trip[9] == 1
        status = "🟢 АКТИВНО" if is_active else "⚪ Неактивно"

        dep_curr_name = format_currency_display(trip[4], trip)
        dest_curr_name = format_currency_display(trip[5], trip)

        trips_text += f"{i}. {trip[2]} → {trip[3]} ({dep_curr_name} → {dest_curr_name})\n"
        trips_text += f"   {status}\n"
        trips_text += f"   Баланс: {trip[7]:,.2f} {dep_curr_name} = {trip[8]:,.2f} {dest_curr_name}\n\n"

    markup = trip_list_buttons(trips)
    bot.reply_to(call.message, trips_text, reply_markup=markup)


def show_balance(call, bot):
    """Показ баланса активного путешествия"""
    trip = get_active_trip(call.from_user.id)

    if not trip:
        bot.reply_to(call.message, "❌ У вас нет активного путешествия. Создайте его с помощью /newtrip")
        return

    dep_curr_name = format_currency_display(trip[4], trip)
    dest_curr_name = format_currency_display(trip[5], trip)

    bot.reply_to(call.message, f"💰 Баланс:\n{trip[7]:,.2f} {dep_curr_name} = {trip[8]:,.2f} {dest_curr_name}")


def show_history(call, bot):
    """Показ истории расходов"""
    trip = get_active_trip(call.from_user.id)

    if not trip:
        bot.reply_to(call.message, "❌ У вас нет активного путешествия.")
        return

    expenses = get_expenses_history(trip[0])

    if not expenses:
        bot.reply_to(call.message, "📋 История расходов пуста.")
        return

    dep_curr_name = format_currency_display(trip[4], trip)
    dest_curr_name = format_currency_display(trip[5], trip)

    history_text = "📋 История расходов:\n\n"
    for expense in expenses[:10]:
        desc = expense[4] or "Без описания"
        history_text += (
            f"• {expense[2]:,.2f} {dest_curr_name} = "
            f"{expense[3]:,.2f} {dep_curr_name} - {desc}\n"
        )

    bot.reply_to(call.message, history_text)


def set_rate_cmd(call, bot):
    """Команда изменения курса обмена"""
    trip = get_active_trip(call.from_user.id)

    if not trip:
        bot.reply_to(call.message, "❌ У вас нет активного путешествия.")
        return

    dep_curr_name = format_currency_display(trip[4], trip)
    dest_curr_name = format_currency_display(trip[5], trip)

    markup = back_button()
    msg = bot.reply_to(
        call.message,
        f"💱 Введите курс валюты страны пребывания:\n\n1 {dest_curr_name} = ? {dep_curr_name}",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, update_exchange_rate_handler, bot)


def update_exchange_rate_handler(message, bot):
    """Обработчик обновления курса обмена"""
    try:
        rate_text = message.text.strip().replace(',', '.')
        direct_rate = float(re.sub(r'[^\d.-]', '', rate_text))

        active_trip = get_active_trip(message.from_user.id)
        if not active_trip:
            bot.reply_to(message, "❌ У вас нет активного путешествия.")
            return

        dep_curr_name = format_currency_display(active_trip[4], active_trip)
        dest_curr_name = format_currency_display(active_trip[5], active_trip)

        inverse_rate = 1 / direct_rate
        new_destination_balance = update_exchange_rate(active_trip[0], inverse_rate, active_trip[7])

        dep_balance_formatted = f"{active_trip[7]:,.2f}"
        dest_balance_formatted = f"{new_destination_balance:,.2f}"
        direct_rate_formatted = f"{direct_rate:.2f}"
        inverse_rate_formatted = f"{inverse_rate:.4f}"

        bot.reply_to(
            message,
            f"✅ Курс обмена обновлён:\n"
            f"1 {dest_curr_name} = {direct_rate_formatted} {dep_curr_name}\n"
            f"(1 {dep_curr_name} = {inverse_rate_formatted} {dest_curr_name})\n\n"
            f"Новый баланс:\n"
            f"{dep_balance_formatted} {dep_curr_name} = {dest_balance_formatted} {dest_curr_name}",
        )
    except ValueError:
        bot.reply_to(message, "❌ Пожалуйста, введите корректное число для курса обмена.")
    except ZeroDivisionError:
        bot.reply_to(message, "❌ Курс не может быть равен нулю. Введите число больше 0.")


def switch_to_trip(call, trip_id, bot):
    """Переключение активного путешествия"""
    success, trip = switch_active_trip(call.from_user.id, trip_id)

    if not success:
        bot.reply_to(call.message, "❌ Путешествие не найдено.")
        return

    # Обновляем сообщение со списком путешествий
    show_my_trips(call, bot)


def handle_exchange_rate_confirm(call, bot):
    """Подтверждение курса из API"""
    user_data = getattr(bot, 'temp_data', {}).get(f"exchange_{call.from_user.id}")
    if user_data:
        user_data['final_rate'] = user_data['exchange_rate']
        bot.temp_data = getattr(bot, 'temp_data', {})
        bot.temp_data.pop(f"exchange_{call.from_user.id}", None)

        from handlers.messages import process_initial_amount_prompt
        process_initial_amount_prompt(call.message, user_data, bot)
    else:
        bot.answer_callback_query(call.id, "Ошибка: данные не найдены")


def handle_exchange_rate_manual(call, bot):
    """Ручной ввод курса обмена"""
    user_data = getattr(bot, 'temp_data', {}).get(f"exchange_{call.from_user.id}")
    if user_data:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=call.message.text + "\n\n✏️ Введите ваш курс обмена:"
        )
        bot.register_next_step_handler(call.message, process_manual_exchange_rate, user_data, bot)
    else:
        bot.answer_callback_query(call.id, "Ошибка: данные не найдены")


def handle_expense_skip(call, bot):
    """Пропуск описания расхода"""
    user_expense_data = getattr(bot, 'temp_data', {}).get(call.from_user.id)
    if user_expense_data:
        from handlers.messages import process_expense_description
        process_expense_description(call.message, user_expense_data, True, bot)
    else:
        bot.answer_callback_query(call.id, "Ошибка: данные не найдены")


def handle_expense_cancel(call, bot):
    """Отмена ввода расхода"""
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=call.message.text.split('\n')[0] + "\n\n❌ Ввод расхода отменён.",
    )
    bot.temp_data = getattr(bot, 'temp_data', {})
    bot.temp_data.pop(call.from_user.id, None)
    bot.clear_step_handler(call.message)


def process_manual_exchange_rate(message, user_data, bot):
    """Обработка ручного ввода курса обмена"""
    try:
        user_data['final_rate'] = float(message.text.strip())
        bot.temp_data = getattr(bot, 'temp_data', {})
        bot.temp_data.pop(f"exchange_{message.from_user.id}", None)

        from handlers.messages import process_initial_amount_prompt
        process_initial_amount_prompt(message, user_data, bot)
    except ValueError:
        markup = back_button()
        bot.reply_to(message, "❌ Пожалуйста, введите корректное число для курса обмена.", reply_markup=markup)
