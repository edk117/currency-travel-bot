# Currency Travel Bot

Кошелёк-конвертер валют для путешественников 🏖

## 📁 Структура проекта

```
currency_travel_bot/
├── bot.py                    # Главный файл запуска
├── config.py                 # Конфигурация и константы
├── database.py               # Работа с базой данных
├── api_client.py             # Клиент для API валют
├── handlers/                 # Обработчики сообщений
│   ├── __init__.py
│   ├── commands.py           # Команды (/start, /balance, etc.)
│   ├── callbacks.py          # Callback кнопки
│   └── messages.py           # Текстовые сообщения
├── keyboards/                # Клавиатуры
│   ├── __init__.py
│   └── inline.py             # Inline кнопки
├── utils/                    # Утилиты
│   ├── __init__.py
│   └── helpers.py            # Вспомогательные функции
├── .env                      # Переменные окружения
├── .env.example              # Пример .env
├── requirements.txt          # Зависимости
└── travel_wallet.db          # База данных
```

## 🚀 Запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте `.env` файл:
```
TELEGRAM_BOT_TOKEN=your_bot_token
CURRENCY_API_KEY=your_api_key
```

3. Запустите бота:
```bash
python3 bot.py
```

## 📋 Команды

- `/start` - Приветствие и главное меню
- `/newtrip` - Создать новое путешествие
- `/balance` - Показать баланс активного путешествия
- `/history` - История расходов
- `/setrate` - Изменить курс обмена
- `/switch` - Переключиться между путешествиями

## 💡 Возможности

- ✅ Создание путешествия с указанием стран и валют
- ✅ Автоматическое получение курса валют через API
- ✅ Учёт расходов с конвертацией
- ✅ Описание расходов
- ✅ Переключение между активными путешествиями
- ✅ История последних 10 расходов

## 🔧 Модули

### `config.py`
Конфигурация, токены, словарь стран и валют.

### `database.py`
Все функции для работы с SQLite:
- `init_db()` - инициализация БД
- `get_active_trip()` - получение активного путешествия
- `create_trip()` - создание путешествия
- `add_expense()` - добавление расхода
- и другие

### `api_client.py`
Клиент для работы с exchangerate.host API:
- `convert_currency()` - конвертация валют
- `get_exchange_rate()` - получение курса

### `handlers/`
- `commands.py` - обработка команд (/start, /newtrip, etc.)
- `callbacks.py` - обработка inline кнопок
- `messages.py` - обработка текстовых сообщений

### `keyboards/`
- `inline.py` - функции для создания inline клавиатур

### `utils/`
- `helpers.py` - вспомогательные функции
