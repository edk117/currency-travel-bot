"""Вспомогательные утилиты"""

import re


def is_number(text):
    """
    Проверка, является ли сообщение числом
    
    Args:
        text: Текст для проверки
    
    Returns:
        bool: True если число, False иначе
    """
    try:
        float(re.sub(r'[^\d.-]', '', text))
        return True
    except ValueError:
        return False


def format_currency(amount, currency_code, currency_name=None):
    """
    Форматирование суммы с валютой
    
    Args:
        amount: Сумма
        currency_code: Код валюты (RUB, USD, etc.)
        currency_name: Название валюты (опционально)
    
    Returns:
        str: Отформатированная строка
    """
    if currency_name:
        return f"{amount:.2f} {currency_code} ({currency_name})"
    return f"{amount:.2f} {currency_code}"


def get_currency_name(currency_code):
    """
    Получение названия валюты по коду
    
    Args:
        currency_code: Код валюты (RUB, USD, etc.)
    
    Returns:
        str: Название валюты
    """
    from config import COUNTRY_CURRENCIES
    
    for country, (code, name) in COUNTRY_CURRENCIES.items():
        if code == currency_code:
            return name
    return None
