"""Утилиты для работы с валютами"""

from config import COUNTRY_CURRENCIES


def get_currency_info(country_name):
    """
    Получение информации о валюте по названию страны.

    Args:
        country_name: Название страны (в нижнем регистре).

    Returns:
        tuple: (country, (currency_code, currency_name)) или None, если не найдено.
    """
    # Точное совпадение
    if country_name in COUNTRY_CURRENCIES:
        return country_name, COUNTRY_CURRENCIES[country_name]

    # Частичное совпадение
    for country, currency_info in COUNTRY_CURRENCIES.items():
        if country_name in country or country in country_name:
            return country, currency_info

    return None


def format_currency_display(currency_code, trip_data):
    """
    Форматирование отображения валюты для вывода пользователю.

    Args:
        currency_code: Код валюты (например, USD, EUR).
        trip_data: Данные о путешестве (список из БД).

    Returns:
        str: Форматированная строка с кодом и названием валюты.
    """
    for country, (code, name) in COUNTRY_CURRENCIES.items():
        if code == currency_code:
            return f"{code} ({name})"
    return currency_code
