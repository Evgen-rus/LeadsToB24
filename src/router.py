"""
Модуль маршрутизации данных.

Отвечает за определение клиента по тегу и маршрутизацию данных.
"""
from src.setup import logger
from src.client_config import get_client_by_tag_cached
from src.bitrix24 import send_to_bitrix24
from src.db import update_lead_client, mark_lead_as_sent

def route_lead(lead_data):
    """
    Маршрутизирует лид в Битрикс24.
    
    Args:
        lead_data (dict): Данные о лиде
    
    Returns:
        bool: True, если маршрутизация прошла успешно, иначе False
    """
    try:
        tag = lead_data.get('tag')
        if not tag:
            logger.warning(f"Лид {lead_data.get('id')} не имеет тега для маршрутизации.")
            return False
        
        # Определяем клиента по тегу
        client = get_client_by_tag_cached(tag)
        if not client:
            logger.warning(f"Не найден клиент для тега '{tag}'.")
            return False
        
        logger.info(f"Найден клиент '{client.get('name')}' для тега '{tag}'.")
        
        # Обновляем информацию о клиенте в записи лида
        update_lead_client(lead_data.get('id'), client.get('id'))
        
        # Отправляем лид в Битрикс24
        logger.info(f"Отправка лида {lead_data.get('id')} в Битрикс24 для клиента '{client.get('name')}'")
        bitrix_result = send_to_bitrix24(lead_data)
        
        if bitrix_result:
            # Если лид успешно отправлен, помечаем его как отправленный
            mark_lead_as_sent(lead_data.get('id'))
            logger.info(f"Лид {lead_data.get('id')} успешно отправлен в Битрикс24.")
            return True
        else:
            logger.error(f"Не удалось отправить лид {lead_data.get('id')} в Битрикс24.")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при маршрутизации лида {lead_data.get('id')}: {e}")
        return False 