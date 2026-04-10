"""Клиент для работы с API валют"""

import requests
from config import CURRENCY_API_KEY


def convert_currency(amount, from_currency, to_currency):
    """
    Конвертация валюты

    Args:
        amount: Сумма для конвертации
        from_currency: Код валюты из которой конвертируем
        to_currency: Код валюты в которую конвертируем

    Returns:
        dict: Результат конвертации или ошибка
    """
    url = "https://api.exchangerate.host/convert"
    params = {
        "access_key": CURRENCY_API_KEY,
        "from": from_currency,
        "to": to_currency,
        "amount": amount
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('success', False):
            return {'error': data.get('error', {'info': 'Неизвестная ошибка API'})}

        return data
    except requests.exceptions.Timeout:
        return {'error': {'info': 'Таймаут соединения с API'}}
    except requests.exceptions.RequestException as e:
        return {'error': {'info': f'Ошибка соединения: {str(e)}'}}


def get_exchange_rate(source_currency, target_currencies):
    """
    Получение текущего курса валют

    Args:
        source_currency: Базовая валюта (например, USD)
        target_currencies: Список целевых валют

    Returns:
        dict: Курсы валют или ошибка
    """
    url = "https://api.exchangerate.host/live"
    params = {
        "access_key": CURRENCY_API_KEY,
        "source": source_currency,
        "currencies": ",".join(target_currencies)
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('success', False):
            return {'error': data.get('error', {'info': 'Неизвестная ошибка API'})}

        return data
    except requests.exceptions.Timeout:
        return {'error': {'info': 'Таймаут соединения с API'}}
    except requests.exceptions.RequestException as e:
        return {'error': {'info': f'Ошибка соединения: {str(e)}'}}
