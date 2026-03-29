"""Модуль для создания inline клавиатур"""

import telebot


def main_menu():
    """Главное меню бота"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✈️ Создать новое путешествие", callback_data="new_trip"),
        telebot.types.InlineKeyboardButton("🧳 Мои путешествия", callback_data="my_trips"),
        telebot.types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        telebot.types.InlineKeyboardButton("📜 История расходов", callback_data="history"),
        telebot.types.InlineKeyboardButton("🔄 Изменить курс", callback_data="set_rate")
    )
    return markup


def back_button():
    """Клавиатура с кнопкой 'Назад'"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    return markup


def exchange_rate_buttons():
    """Кнопки подтверждения курса обмена"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("✅ Да, подходит", callback_data="exchange_rate_confirm"),
        telebot.types.InlineKeyboardButton("✏️ Нет, ввести вручную", callback_data="exchange_rate_manual")
    )
    return markup


def expense_description_buttons():
    """Кнопки для ввода описания расхода"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("⏭ Пропустить", callback_data="expense_skip_desc"),
        telebot.types.InlineKeyboardButton("❌ Отмена", callback_data="expense_cancel_input")
    )
    return markup


def trip_list_buttons(trips):
    """
    Кнопки для списка путешествий
    
    Args:
        trips: Список путешествий из БД
    
    Returns:
        InlineKeyboardMarkup: Клавиатура со списком путешествий
    """
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    for trip in trips:
        is_active = trip[9] == 1
        status_icon = "✅" if is_active else "⬜"
        btn_text = f"{status_icon} {trip[2]} → {trip[3]}"
        callback_data = f"activate_trip_{trip[0]}"
        markup.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    return markup


def switch_trip_buttons(trips):
    """
    Кнопки для переключения между путешествиями
    
    Args:
        trips: Список путешествий из БД
    
    Returns:
        InlineKeyboardMarkup: Клавиатура со списком путешествий
    """
    markup = telebot.types.InlineKeyboardMarkup()
    
    for trip in trips:
        dep_curr_code = trip[4]
        dest_curr_code = trip[5]
        
        # Ищем названия валют в словаре
        dep_curr_name = dep_curr_code
        dest_curr_name = dest_curr_code
        from config import COUNTRY_CURRENCIES
        for country, (code, name) in COUNTRY_CURRENCIES.items():
            if code == dep_curr_code:
                dep_curr_name = f"{code} ({name})"
                break
        for country, (code, name) in COUNTRY_CURRENCIES.items():
            if code == dest_curr_code:
                dest_curr_name = f"{code} ({name})"
                break
        
        btn_text = f"{trip[2]} → {trip[3]} ({dep_curr_name} → {dest_curr_name})"
        callback_data = f"switch_to_{trip[0]}"
        markup.add(telebot.types.InlineKeyboardButton(btn_text, callback_data=callback_data))
    
    markup.add(telebot.types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    return markup
