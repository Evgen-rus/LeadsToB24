"""
Модуль обработки данных.

Отвечает за очистку и подготовку данных перед записью в БД.
"""
import re
from datetime import datetime
from src.setup import logger

def clean_project_tag(tag):
    """
    Очищает тег проекта от префикса и хвоста.
    
    Args:
        tag (str): Исходное значение тега, например "B1_[П8] Неометрия Ростов_new"
    
    Returns:
        str: Очищенный тег, например "[П8] Неометрия Ростов"
    """
    try:
        # Удаляем пробелы в начале и конце строки
        clean_tag = tag.strip()
        
        # Удаляем префикс вида "B1_" или "В2_", но только если это именно префикс
        clean_tag = re.sub(r'^([BВ]\d+_)', '', clean_tag)
        
        # Удаляем хвост после второго подчёркивания (если есть)
        parts = clean_tag.split('_', 2)
        if len(parts) >= 3:
            clean_tag = '_'.join(parts[:2])
        
        # Ещё раз удаляем пробелы в начале и конце строки для гарантии
        clean_tag = clean_tag.strip()
        
        # Логируем преобразование тега для отладки
        logger.debug(f"Исходный тег: '{tag}', очищенный тег: '{clean_tag}'")
        
        return clean_tag
    except Exception as e:
        logger.error(f"Ошибка при очистке тега '{tag}': {e}")
        return tag

def validate_phone(phone):
    """
    Проверяет и форматирует номер телефона.
    
    Args:
        phone (str): Номер телефона, например "79991234567"
    
    Returns:
        str: Отформатированный номер телефона или пустая строка, если формат неверный
    """
    try:
        # Удаляем все нецифровые символы
        digits_only = re.sub(r'\D', '', str(phone))
        
        # Проверяем, что номер соответствует формату "79XXXXXXXXX"
        if re.match(r'^7\d{10}$', digits_only):
            return digits_only
        else:
            logger.warning(f"Некорректный формат телефона: {phone}")
            return ""
    except Exception as e:
        logger.error(f"Ошибка при валидации телефона '{phone}': {e}")
        return ""

def parse_datetime(date_str):
    """
    Преобразует строку даты в объект datetime.
    
    Args:
        date_str (str): Строка даты в формате "YYYY-MM-DD HH:MM:SS"
    
    Returns:
        datetime: Объект datetime или None в случае ошибки
    """
    try:
        if not date_str:  # Если дата не указана
            return datetime.now()  # Возвращаем текущее время
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Ошибка при парсинге даты '{date_str}': {e}")
        return datetime.now()  # В случае ошибки возвращаем текущее время

def process_row(data):
    """
    Обрабатывает данные, полученные через webhook.
    
    Args:
        data (dict): Словарь с данными лида
    
    Returns:
        dict: Словарь с обработанными данными или None, если данные некорректны
    """
    try:
        # Валидируем и обрабатываем данные
        created_at = parse_datetime(data.get('created_at', ''))
        cleaned_phone = validate_phone(data.get('phone', ''))
        if not cleaned_phone:
            logger.warning(f"Некорректный телефон: {data.get('phone')}")
            return None
        
        cleaned_tag = clean_project_tag(data.get('project_tag', ''))
        
        # Формируем результат
        return {
            'created_at': created_at,
            'id': data.get('id', str(int(datetime.now().timestamp()))),
            'phone': cleaned_phone,
            'tag': cleaned_tag,
            'original_tag': data.get('project_tag', '')
        }
    
    except Exception as e:
        logger.error(f"Ошибка при обработке данных {data}: {e}")
        return None 