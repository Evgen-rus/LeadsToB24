"""
Модуль с ID полей AmoCRM для удобной и понятной работы с API.
"""

# ID полей для лидов
LEAD_FIELDS = {
    # Основные поля (примеры, нужно заменить на реальные ID полей)
    'PHONE': 838789,     # Телефон
    'EMAIL': 838791,     # Email
    'SOURCE': 838793,    # Источник
    'COMMENT': 838795,   # Комментарий
    
    # Дополнительные поля
    'COMPANY': 838797,   # Компания
    'POSITION': 838799,  # Должность
    'ADDRESS': 838801,   # Адрес
    'BUDGET': 838803,    # Бюджет
}

# ID статусов воронки
LEAD_STATUSES = {
    'NEW': 43578325,         # Новый лид
    'IN_PROGRESS': 43578328, # В работе
    'MEETING': 43578331,     # Встреча назначена
    'CLOSED_WON': 142,       # Успешно реализовано
    'CLOSED_LOST': 143,      # Закрыто и не реализовано
}

# ID ответственных пользователей
USERS = {
    'DEFAULT': 0,        # ID пользователя по умолчанию (замените на реальный)
    'MANAGER1': 12345,   # Менеджер 1 (замените на реальный)
    'MANAGER2': 67890,   # Менеджер 2 (замените на реальный)
}

# ID воронок
PIPELINES = {
    'MAIN': 6375467,    # Основная воронка (замените на реальный ID)
}

def get_lead_field(field_name):
    """
    Получение ID поля лида по имени
    
    Args:
        field_name (str): Имя поля
        
    Returns:
        int: ID поля или None если поле не найдено
    """
    return LEAD_FIELDS.get(field_name.upper())

def get_lead_status(status_name):
    """
    Получение ID статуса по имени
    
    Args:
        status_name (str): Имя статуса
        
    Returns:
        int: ID статуса или None если статус не найден
    """
    return LEAD_STATUSES.get(status_name.upper())

def get_user_id(user_name):
    """
    Получение ID пользователя по имени
    
    Args:
        user_name (str): Имя пользователя
        
    Returns:
        int: ID пользователя или ID пользователя по умолчанию
    """
    return USERS.get(user_name.upper(), USERS['DEFAULT']) 