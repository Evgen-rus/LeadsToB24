"""
Модуль для работы с полями AmoCRM через API.
Позволяет получать информацию о полях, их ID и значениях без доступа к интерфейсу.
"""
import logging
from . import api

# Настраиваем логирование
logger = logging.getLogger('amo.field_manager')
logger.setLevel(logging.DEBUG)

# Добавляем вывод логов в консоль
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    # Упрощенный формат: [время] тип_лога: сообщение
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', 
                                datefmt='%H:%M:%S')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def get_lead_fields():
    """
    Получение списка всех полей для лидов
    
    Returns:
        dict: Словарь с информацией о полях
    """
    logger.debug("Запрос полей лидов")
    return api.get('leads/custom_fields')

def get_contact_fields():
    """
    Получение списка всех полей для контактов
    
    Returns:
        dict: Словарь с информацией о полях
    """
    logger.debug("Запрос полей контактов")
    return api.get('contacts/custom_fields')

def get_company_fields():
    """
    Получение списка всех полей для компаний
    
    Returns:
        dict: Словарь с информацией о полях
    """
    logger.debug("Запрос полей компаний")
    return api.get('companies/custom_fields')

def get_pipelines():
    """
    Получение списка воронок и их статусов
    
    Returns:
        dict: Словарь с информацией о воронках
    """
    logger.debug("Запрос воронок")
    return api.get('leads/pipelines')

def get_users():
    """
    Получение списка всех пользователей
    
    Returns:
        dict: Словарь с информацией о пользователях
    """
    logger.debug("Запрос пользователей")
    return api.get('users')
