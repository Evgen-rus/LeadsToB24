# LeadsToB24

Система для автоматизации создания лидов в AmoCRM с привязкой контактов.

## Назначение

Программа позволяет создавать лиды в AmoCRM с привязкой контактов по номеру телефона. Система автоматически создает контакт с телефоном и привязывает его к лиду.

## Общая схема работы

1. Система получает номер телефона
2. Создает контакт с указанным телефоном
3. Создает лид в указанной воронке и этапе
4. Привязывает контакт к лиду
5. Устанавливает ответственного и теги

## Требования

- Python 3.8 или выше
- Pip для установки зависимостей
- Доступ к AmoCRM API

## Зависимости

- `requests`
- `python-dotenv`
- `logging`

## Установка

1. Клонировать репозиторий:

```bash
git clone https://github.com/yourusername/LeadsToB24.git
cd LeadsToB24
```

2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Настроить доступ к AmoCRM:

```bash
cp .env.example .env
```

4. Редактировать `.env` файл, указав необходимые параметры:

```bash
AMO_DOMAIN=your_domain.amocrm.ru
AMO_ACCESS_TOKEN=your_access_token
```

## Структура проекта

```
LeadsToB24/
├── amo/                    # Модуль для работы с AmoCRM
│   ├── __init__.py
│   ├── api.py             # Базовые функции для работы с API
│   ├── auth.py            # Аутентификация в AmoCRM
│   ├── field_manager.py   # Управление полями AmoCRM
│   ├── fields.py          # Константы полей
│   ├── lead.py            # Функции для работы с лидами
│   └── webhook_handler.py # Обработчик вебхуков
├── create_lead.py         # Основной скрипт создания лидов
├── amo_get_fields.py      # Утилита для получения ID полей
├── logs/                  # Директория для логов
├── .env                   # Переменные окружения
└── README.md              # Документация проекта
```

## Конфигурация

### ID для создания лидов

```python
# Воронка и этапы
PIPELINE_ID = 2194891      # ID воронки "Частный Дизайн"
STATUS_ID = 68384126       # ID этапа "DMP - LeadRecord"

# Ответственные
RESPONSIBLE_USER_ID = 9480922  # ID ответственного "Михаил Васнецов"

# Поля и теги
PHONE_FIELD_ID = 318033    # ID поля телефона для контакта
TAG_NAME = "LeadRecord"    # Тег для лида
SOURCE_NAME = "LeadRecord" # Источник лида
```

## Использование

### Создание лида

```python
from create_lead import create_lead_with_phone

# Создание лида с телефоном
phone = "+79991234567"
lead_id, contact_id = create_lead_with_phone(phone)

if lead_id:
    print(f"Создан лид {lead_id} с контактом {contact_id}")
```

### Получение ID полей

Для получения актуальных ID полей, воронок и пользователей:

```bash
python amo_get_fields.py
```

Доступные команды:
- `refresh` - Обновить все кэши
- `leads` - Показать поля лидов
- `contacts` - Показать поля контактов
- `pipelines` - Показать воронки и статусы
- `users` - Показать пользователей
- `field [entity_type] [field_name]` - Найти ID поля по имени
- `status [pipeline_id] [status_name]` - Найти ID статуса по имени
- `user [user_name]` - Найти ID пользователя по имени

## Логирование

Система ведет подробное логирование в файл `logs/amo.log`. Для каждого созданного лида записывается:
- ID лида и контакта
- Название лида
- Воронка и этап
- Ответственный
- Теги и источник

## Обработка ошибок

Система обрабатывает следующие ошибки:
- Ошибки аутентификации в AmoCRM
- Ошибки создания контакта
- Ошибки создания лида
- Ошибки привязки контакта к лиду

Все ошибки логируются в файл `logs/amo.log` с подробным описанием.

## Рекомендации по безопасности

1. Храните токены доступа в `.env` файле
2. Не публикуйте `.env` файл в репозитории
3. Используйте HTTPS для всех запросов к API
4. Регулярно обновляйте токены доступа
5. Ограничивайте права доступа к API

## Техническая поддержка

По вопросам работы с системой обращайтесь к администратору проекта.
