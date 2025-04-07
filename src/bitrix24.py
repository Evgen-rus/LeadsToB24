"""
Модуль для работы с API Битрикс24.

Отвечает за формирование и отправку запросов в Битрикс24 через REST API.
"""
import json
import requests
from datetime import datetime

from src.setup import logger
from src.db import get_connection

def send_to_bitrix24(lead_data, config=None):
    """
    Отправляет данные лида в Битрикс24 через REST API.
    
    Сначала создает контакт, затем на основе контакта создает сделку.
    
    Args:
        lead_data (dict): Данные о лиде
        config (dict, optional): Дополнительные настройки для Битрикс24
    
    Returns:
        bool: True, если отправка прошла успешно, иначе False
    """
    try:
        # Если конфиг не передан, используем значения по умолчанию
        if config is None:
            config = {
                'contact_webhook': 'https://b24-2l18k6.bitrix24.ru/rest/1/szllvyugkf2n9sst/crm.lead.contact.add.json',
                'deal_webhook': 'https://b24-2l18k6.bitrix24.ru/rest/1/szllvyugkf2n9sst/crm.deal.add.json'
            }
        
        # Шаг 1: Создаем контакт
        contact_payload = {
            'fields': {
                'NAME': 'Контакт',  # Если имя не известно, используем значение по умолчанию
                'PHONE': [{'VALUE': lead_data.get('phone'), 'VALUE_TYPE': 'WORK'}],
                'SOURCE_ID': 'WEB',
                'SOURCE_DESCRIPTION': lead_data.get('tag'),
                'COMMENTS': f"Создано автоматически от LeadsToB24. ID: {lead_data.get('id')}, Тег: {lead_data.get('tag')}"
            },
            'params': {
                'REGISTER_SONET_EVENT': 'Y'
            }
        }
        
        logger.info(f"Отправка запроса на создание контакта для лида {lead_data.get('id')} в Битрикс24")
        
        contact_response = requests.post(
            config['contact_webhook'],
            json=contact_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if contact_response.status_code >= 200 and contact_response.status_code < 300:
            try:
                contact_result = contact_response.json()
                contact_id = contact_result.get('result')
                
                if not contact_id:
                    raise ValueError("Не удалось получить ID контакта из ответа Битрикс24")
                
                logger.info(f"Контакт успешно создан в Битрикс24, ID: {contact_id}")
                
                # Шаг 2: Создаем сделку на основе контакта
                created_at_str = lead_data.get('created_at').strftime("%Y-%m-%d %H:%M:%S") if lead_data.get('created_at') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                deal_payload = {
                    'fields': {
                        'TITLE': f"Заявка {lead_data.get('tag')} от {created_at_str}",
                        'STAGE_ID': 'NEW',  # Начальная стадия воронки (новая сделка)
                        'CONTACT_ID': contact_id,
                        'SOURCE_ID': 'WEB',
                        'SOURCE_DESCRIPTION': lead_data.get('tag'),
                        'COMMENTS': f"Создано автоматически от LeadsToB24. ID: {lead_data.get('id')}, Тег: {lead_data.get('tag')}",
                        'ASSIGNED_BY_ID': 1,  # ID ответственного пользователя (обычно администратор)
                        'CATEGORY_ID': 0,  # ID направления сделки
                        'OPENED': 'Y',
                        'ADDITIONAL_INFO': json.dumps({
                            'lead_id': lead_data.get('id'),
                            'original_tag': lead_data.get('original_tag'),
                            'created_at': created_at_str,
                            'source': 'LeadsToB24'
                        }, ensure_ascii=False)
                    },
                    'params': {
                        'REGISTER_SONET_EVENT': 'Y'
                    }
                }
                
                logger.info(f"Отправка запроса на создание сделки для контакта {contact_id} в Битрикс24")
                
                deal_response = requests.post(
                    config['deal_webhook'],
                    json=deal_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if deal_response.status_code >= 200 and deal_response.status_code < 300:
                    try:
                        deal_result = deal_response.json()
                        deal_id = deal_result.get('result')
                        
                        if not deal_id:
                            raise ValueError("Не удалось получить ID сделки из ответа Битрикс24")
                        
                        logger.info(f"Сделка успешно создана в Битрикс24, ID: {deal_id}")
                        
                        # Обновляем статус доставки в БД
                        conn = get_connection()
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                            UPDATE leads
                            SET crm_delivery_status = ?, crm_delivery_time = CURRENT_TIMESTAMP
                            WHERE id = ?
                            ''', (f'delivered: Contact {contact_id}, Deal {deal_id}', lead_data.get('id')))
                            conn.commit()
                            conn.close()
                        
                        return True
                    except json.JSONDecodeError as e:
                        error_message = f"Ошибка парсинга JSON ответа при создании сделки: {e}, ответ: {deal_response.text}"
                        logger.error(error_message)
                        raise
                else:
                    error_message = f"Ошибка при создании сделки. Код ответа: {deal_response.status_code}, ответ: {deal_response.text}"
                    logger.error(error_message)
                    
                    # Обновляем статус доставки
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                        UPDATE leads
                        SET crm_delivery_status = ?, delivery_attempts = delivery_attempts + 1
                        WHERE id = ?
                        ''', (f'error: HTTP {deal_response.status_code} - {deal_response.text[:100]}', lead_data.get('id')))
                        conn.commit()
                        conn.close()
                    
                    return False
            except json.JSONDecodeError as e:
                error_message = f"Ошибка парсинга JSON ответа при создании контакта: {e}, ответ: {contact_response.text}"
                logger.error(error_message)
                raise
            except Exception as e:
                error_message = f"Ошибка при обработке ответа создания контакта: {e}"
                logger.error(error_message)
                raise
        else:
            error_message = f"Ошибка при создании контакта. Код ответа: {contact_response.status_code}, ответ: {contact_response.text}"
            logger.error(error_message)
            
            # Обновляем статус доставки
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE leads
                SET crm_delivery_status = ?, delivery_attempts = delivery_attempts + 1
                WHERE id = ?
                ''', (f'error: HTTP {contact_response.status_code} - {contact_response.text[:100]}', lead_data.get('id')))
                conn.commit()
                conn.close()
            
            return False
                
    except requests.RequestException as e:
        error_message = f"Ошибка сети при отправке данных в Битрикс24: {e}"
        logger.error(error_message)
        
        # Обновляем статус доставки
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE leads
            SET crm_delivery_status = ?, delivery_attempts = delivery_attempts + 1
            WHERE id = ?
            ''', (f'error: Network - {str(e)[:100]}', lead_data.get('id')))
            conn.commit()
            conn.close()
        
        return False
    except json.JSONDecodeError as e:
        error_message = f"Ошибка формирования JSON для Битрикс24: {e}"
        logger.error(error_message)
        
        # Обновляем статус доставки
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE leads
            SET crm_delivery_status = ?, delivery_attempts = delivery_attempts + 1
            WHERE id = ?
            ''', (f'error: JSON - {str(e)[:100]}', lead_data.get('id')))
            conn.commit()
            conn.close()
        
        return False
    except Exception as e:
        error_message = f"Неожиданная ошибка при отправке данных в Битрикс24: {e}"
        logger.error(error_message)
        
        # Обновляем статус доставки
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE leads
            SET crm_delivery_status = ?, delivery_attempts = delivery_attempts + 1
            WHERE id = ?
            ''', (f'error: {str(e)[:100]}', lead_data.get('id')))
            conn.commit()
            conn.close()
        
        return False 