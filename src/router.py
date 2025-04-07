"""
Модуль маршрутизации данных.

Отвечает за определение клиента по тегу и маршрутизацию данных.
"""
from src.setup import logger
from src.client_config import get_client_by_tag_cached
from src.client_sheets import send_to_client_sheet
from src.webhook import send_to_webhook
from src.bitrix24 import send_to_bitrix24
from src.db import update_lead_client, mark_lead_as_sent

def route_lead(lead_data):
    """
    Маршрутизирует лид соответствующему клиенту.
    
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
        
        # Флаг успешной отправки хотя бы одним способом
        sent_successfully = False
        
        # Проверяем, содержит ли тег "[ДМД13]" для отправки в Битрикс24
        if "[ДМД13]" in tag:
            logger.info(f"Отправка лида {lead_data.get('id')} в Битрикс24 для клиента '{client.get('name')}'")
            bitrix_result = send_to_bitrix24(lead_data)
            if bitrix_result:
                sent_successfully = True
                logger.info(f"Лид {lead_data.get('id')} успешно отправлен в Битрикс24.")
            else:
                logger.error(f"Не удалось отправить лид {lead_data.get('id')} в Битрикс24.")
        else:
            # Если у клиента настроена таблица, отправляем данные в неё
            if client.get('spreadsheet_id') and client.get('sheet_name'):
                sheet_result = send_to_client_sheet(client, lead_data)
                if sheet_result:
                    sent_successfully = True
                    logger.info(f"Лид {lead_data.get('id')} успешно отправлен в таблицу клиента.")
                else:
                    logger.error(f"Не удалось отправить лид {lead_data.get('id')} в таблицу клиента.")
            
            # Если у клиента настроен вебхук для CRM, отправляем данные через него
            if client.get('use_crm') and client.get('webhook_url'):
                webhook_result = send_to_webhook(client, lead_data)
                if webhook_result:
                    sent_successfully = True
                    logger.info(f"Лид {lead_data.get('id')} успешно отправлен в CRM клиента.")
                else:
                    logger.error(f"Не удалось отправить лид {lead_data.get('id')} в CRM клиента.")
        
        # Если лид был успешно отправлен хотя бы одним способом, помечаем его как отправленный
        if sent_successfully:
            mark_lead_as_sent(lead_data.get('id'))
            return True
        else:
            logger.warning(f"Лид {lead_data.get('id')} не был отправлен ни одним из доступных способов.")
            return False
    
    except Exception as e:
        logger.error(f"Ошибка при маршрутизации лида {lead_data.get('id')}: {e}")
        return False 