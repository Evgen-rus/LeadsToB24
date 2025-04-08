"""
Модуль для работы с API Битрикс24.

Отвечает за формирование и отправку запросов в Битрикс24 через REST API.
"""
import requests
from datetime import datetime
from src.setup import logger
from src.db import get_connection

def create_contact(phone, webhook_base_url):
    """
    Создает контакт в Битрикс24.
    
    Args:
        phone (str): Номер телефона
        webhook_base_url (str): Базовый URL вебхука
    
    Returns:
        int: ID созданного контакта или None в случае ошибки
    """
    try:
        # Формируем данные для создания контакта
        contact_payload = {
            'fields': {
                'NAME': phone,  # Используем телефон как имя
                'PHONE': [{'VALUE': phone, 'VALUE_TYPE': 'WORK'}],  # Телефон
                'OPENED': 'Y'  # Доступен для всех
            }
        }
        
        # Отправляем запрос на создание контакта
        response = requests.post(
            f"{webhook_base_url}/crm.contact.add.json",
            json=contact_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code >= 200 and response.status_code < 300:
            result = response.json()
            contact_id = result.get('result')
            if contact_id:
                logger.info(f"Контакт успешно создан, ID: {contact_id}")
                return contact_id
        
        logger.error(f"Ошибка при создании контакта: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при создании контакта: {e}")
        return None

def send_to_bitrix24(lead_data, config=None):
    """
    Отправляет данные лида в Битрикс24 через REST API.
    
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
                'webhook_url': 'https://b24-2l18k6.bitrix24.ru/rest/1/g2io5xchou3u0t17/crm.lead.add.json'
            }
        
        # Получаем телефон из данных
        phone = lead_data.get('phone', '')
        istochnic = "САНКТ-ПЕТЕРБУРГ. LeadRecord. Сэндвич-Панели"
        
        # Создаем контакт
        webhook_base_url = config['webhook_url'].split('/crm.')[0]
        contact_id = create_contact(phone, webhook_base_url)
        
        # Формируем данные для создания лида
        lead_payload = {
            'fields': {
                'TITLE': f"LR_конк_{phone}",  # Название лида в нужном формате
                'PHONE': [{'VALUE': phone, 'VALUE_TYPE': 'WORK'}] if phone else [],  # Телефон
                'SOURCE_ID': istochnic,  # Источник
                'ASSIGNED_BY_ID': 1,  # ID Вероники Родителевой
                'STATUS_ID': 'NEW',  # Статус "Новый"
                'COMMENTS': "",  # Комментарий
                'NAME': phone,  # Используем телефон как имя
                'COMPANY_TITLE': phone,  # Название компании
                'OPENED': 'Y',  # Доступен для всех
                'SOURCE_DESCRIPTION': istochnic,  # Описание источника
                'CONTACT_ID': contact_id if contact_id else None  # ID созданного контакта
            }
        }
        
        logger.info(f"Отправка запроса на создание лида {lead_data.get('id')} в Битрикс24")
        logger.info(f"Данные лида: {lead_payload}")
        
        # Отправляем запрос в Битрикс24
        response = requests.post(
            config['webhook_url'],
            json=lead_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        # Логируем ответ от сервера для отладки
        logger.info(f"Ответ сервера: {response.status_code} - {response.text}")
        
        if response.status_code >= 200 and response.status_code < 300:
            result = response.json()
            lead_id = result.get('result')
            
            if not lead_id:
                raise ValueError("Не удалось получить ID лида из ответа Битрикс24")
            
            logger.info(f"Лид успешно создан в Битрикс24, ID: {lead_id}")
            
            # Обновляем статус доставки в БД
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE leads
                SET crm_delivery_status = ?, crm_delivery_time = CURRENT_TIMESTAMP
                WHERE id = ?
                ''', (f'delivered: Lead {lead_id}', lead_data.get('id')))
                conn.commit()
                conn.close()
            
            return True
        else:
            error_message = f"Ошибка при создании лида. Код ответа: {response.status_code}, ответ: {response.text}"
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
                
    except Exception as e:
        error_message = f"Ошибка при отправке данных в Битрикс24: {e}"
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