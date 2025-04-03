"""
Модуль для отправки данных через вебхуки.

Отвечает за формирование и отправку запросов в CRM клиентов.
"""
import json
import requests
from datetime import datetime

from src.setup import logger
from src.db import get_connection

def send_to_webhook(client_config, lead_data):
    """
    Отправляет данные лида через вебхук в CRM клиента.
    
    Args:
        client_config (dict): Конфигурация клиента
        lead_data (dict): Данные о лиде
    
    Returns:
        bool: True, если отправка прошла успешно, иначе False
    """
    try:
        # Проверяем наличие настроек вебхука
        if not client_config.get('use_crm') or not client_config.get('webhook_url'):
            logger.warning(f"Для клиента {client_config.get('name')} не настроена интеграция с CRM.")
            
            # Обновляем статус доставки
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE leads
                SET crm_delivery_status = ?, delivery_attempts = delivery_attempts + 1
                WHERE id = ?
                ''', ('error: no CRM configured', lead_data.get('id')))
                conn.commit()
                conn.close()
                
            return False
        
        # Формируем данные для отправки
        payload = {
            'lead_id': lead_data.get('id'),
            'created_at': lead_data.get('created_at').strftime("%Y-%m-%d %H:%M:%S") if lead_data.get('created_at') else None,
            'phone': lead_data.get('phone'),
            'tag': lead_data.get('tag'),
            'source': 'LeadsToB24',
            'timestamp': datetime.now().timestamp()
        }
        
        # Добавляем дополнительные данные, если они есть
        if lead_data.get('original_tag'):
            payload['original_tag'] = lead_data.get('original_tag')
        
        # Отправляем данные через вебхук
        response = requests.post(
            client_config['webhook_url'],
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10  # Устанавливаем таймаут для запроса
        )
        
        # Проверяем ответ
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Данные лида {lead_data.get('id')} успешно отправлены в CRM клиента {client_config.get('name')}.")
            
            # Обновляем статус доставки
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE leads
                SET crm_delivery_status = ?, crm_delivery_time = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', ('delivered', lead_data.get('id')))
                conn.commit()
                conn.close()
                
            return True
        else:
            error_message = f"Ошибка при отправке данных в CRM. Код ответа: {response.status_code}, ответ: {response.text}"
            logger.error(error_message)
            
            # Обновляем статус доставки
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE leads
                SET crm_delivery_status = ?, delivery_attempts = delivery_attempts + 1
                WHERE id = ?
                ''', (f'error: HTTP {response.status_code} - {response.text[:100]}', lead_data.get('id')))
                conn.commit()
                conn.close()
                
            return False
    
    except requests.RequestException as e:
        error_message = f"Ошибка сети при отправке данных в CRM: {e}"
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
        error_message = f"Ошибка формирования JSON для вебхука: {e}"
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
        error_message = f"Неожиданная ошибка при отправке данных через вебхук: {e}"
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

def test_webhook(webhook_url):
    """
    Тестирует доступность вебхука.
    
    Args:
        webhook_url (str): URL вебхука для тестирования
    
    Returns:
        bool: True, если вебхук доступен, иначе False
    """
    try:
        # Формируем тестовые данные
        payload = {
            'test': True,
            'timestamp': datetime.now().timestamp()
        }
        
        # Отправляем тестовый запрос
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5  # Короткий таймаут для тестового запроса
        )
        
        # Проверяем ответ
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Вебхук {webhook_url} успешно протестирован.")
            return True
        else:
            logger.error(f"Ошибка при тестировании вебхука. Код ответа: {response.status_code}, ответ: {response.text}")
            return False
    
    except requests.RequestException as e:
        logger.error(f"Ошибка сети при тестировании вебхука: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при тестировании вебхука: {e}")
        return False 