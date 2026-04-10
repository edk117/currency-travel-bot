"""Модуль для работы с базой данных"""

import sqlite3
from config import DATABASE_NAME


def get_connection():
    """Получение соединения с базой данных"""
    return sqlite3.connect(DATABASE_NAME)


def init_db():
    """Инициализация базы данных - создание таблиц"""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY,"
        "telegram_id INTEGER UNIQUE,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ")"
    )

    # Таблица путешествий
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS trips ("
        "id INTEGER PRIMARY KEY,"
        "user_id INTEGER,"
        "departure_country TEXT,"
        "destination_country TEXT,"
        "departure_currency TEXT,"
        "destination_currency TEXT,"
        "exchange_rate REAL,"
        "departure_balance REAL DEFAULT 0,"
        "destination_balance REAL DEFAULT 0,"
        "is_active BOOLEAN DEFAULT 0,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "FOREIGN KEY (user_id) REFERENCES users (id)"
        ")"
    )

    # Таблица расходов
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS expenses ("
        "id INTEGER PRIMARY KEY,"
        "trip_id INTEGER,"
        "amount_destination REAL,"
        "amount_departure REAL,"
        "description TEXT,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "FOREIGN KEY (trip_id) REFERENCES trips (id)"
        ")"
    )

    conn.commit()
    conn.close()


def get_active_trip(telegram_id):
    """Получение активного путешествия пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT t.* FROM trips t "
        "JOIN users u ON t.user_id = u.id "
        "WHERE u.telegram_id = ? AND t.is_active = 1",
        (telegram_id,),
    )
    trip = cursor.fetchone()
    conn.close()
    return trip


def get_user_trips(telegram_id):
    """Получение всех путешествий пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT t.* FROM trips t "
        "JOIN users u ON t.user_id = u.id "
        "WHERE u.telegram_id = ?",
        (telegram_id,),
    )
    trips = cursor.fetchall()
    conn.close()
    return trips


def create_trip(telegram_id, departure_country, destination_country,
                departure_currency, destination_currency, exchange_rate,
                initial_amount, convert_currency_func):
    """
    Создание нового путешествия
    
    Args:
        telegram_id: ID пользователя в Telegram
        departure_country: Страна отправления
        destination_country: Страна назначения
        departure_currency: Валюта отправления
        destination_currency: Валюта назначения
        exchange_rate: Курс обмена
        initial_amount: Начальная сумма
        convert_currency_func: Функция для конвертации валюты
    
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем внутренний id пользователя по telegram_id
    cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False, "Пользователь не найден"

    user_id = user[0]

    # Деактивируем все предыдущие путешествия пользователя
    cursor.execute('UPDATE trips SET is_active = 0 WHERE user_id = ?', (user_id,))
    conn.commit()

    # Сначала конвертируем начальную сумму в валюту назначения
    converted_amount_data = convert_currency_func(initial_amount, departure_currency, destination_currency)
    if 'error' in converted_amount_data:
        conn.close()
        return False, "Ошибка при конвертации валюты"

    converted_amount = converted_amount_data['result']

    # Создаем путешествие
    cursor.execute(
        "INSERT INTO trips (user_id, departure_country, destination_country, "
        "departure_currency, destination_currency, "
        "exchange_rate, departure_balance, destination_balance, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
        (user_id, departure_country, destination_country,
         departure_currency, destination_currency,
         exchange_rate, initial_amount, converted_amount),
    )

    conn.commit()
    conn.close()
    return True, "Путешествие успешно создано"


def update_trip_balance(trip_id, amount_dest_change, amount_dep_change):
    """Обновление баланса путешествия"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trips "
        "SET destination_balance = destination_balance + ?, "
        "departure_balance = departure_balance + ? "
        "WHERE id = ?",
        (amount_dest_change, amount_dep_change, trip_id),
    )

    conn.commit()
    conn.close()


def add_expense(trip_id, amount_destination, amount_departure, description=""):
    """Добавление расхода"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO expenses (trip_id, amount_destination, amount_departure, description) "
        "VALUES (?, ?, ?, ?)",
        (trip_id, amount_destination, amount_departure, description),
    )

    conn.commit()
    conn.close()


def get_expenses_history(trip_id):
    """Получение истории расходов"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM expenses "
        "WHERE trip_id = ? "
        "ORDER BY created_at DESC",
        (trip_id,),
    )
    expenses = cursor.fetchall()
    conn.close()
    return expenses


def switch_active_trip(telegram_id, trip_id):
    """
    Переключение активного путешествия

    Args:
        telegram_id: ID пользователя в Telegram
        trip_id: ID путешествия для активации

    Returns:
        tuple: (success: bool, trip: dict or None)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False, None

    user_id = user[0]

    cursor.execute("SELECT * FROM trips WHERE id = ? AND user_id = ?", (trip_id, user_id))
    trip = cursor.fetchone()
    if not trip:
        conn.close()
        return False, None

    cursor.execute("UPDATE trips SET is_active = 0 WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE trips SET is_active = 1 WHERE id = ? AND user_id = ?", (trip_id, user_id))

    conn.commit()
    conn.close()
    return True, trip


def update_exchange_rate(trip_id, new_rate, departure_balance):
    """
    Обновление курса обмена и пересчёт баланса

    Args:
        trip_id: ID путешествия
        new_rate: Новый курс обмена
        departure_balance: Баланс в валюте отправления

    Returns:
        float: Новый баланс в валюте назначения
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE trips SET exchange_rate = ? WHERE id = ?", (new_rate, trip_id))

    new_destination_balance = departure_balance * new_rate
    cursor.execute(
        "UPDATE trips SET destination_balance = ? WHERE id = ?",
        (new_destination_balance, trip_id),
    )

    conn.commit()
    conn.close()
    return new_destination_balance
