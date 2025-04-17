"""
Пример скрипта для отправки лидов в AmoCRM.
Может использоваться для тестирования или периодической отправки лидов из файла.
"""
import csv
import json
import logging
import os
import requests
from dotenv import load_dotenv
from . import lead
from . import field_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/sender.log'
)
logger = logging.getLogger('amo.sender')

# Загружаем переменные окружения
load_dotenv()

def send_lead_from_dict(lead_data):
    """
    Отправка лида в AmoCRM из словаря с данными
    
    Args:
        lead_data (dict): Данные лида
            {
                'name': 'Имя клиента',
                'phone': '+79001234567',
                'email': 'example@mail.com',
                'source': 'Источник лида',
                'comment': 'Комментарий'
                # Другие поля...
            }
    
    Returns:
        dict: Результат создания лида
    """
    # Подготавливаем данные для AmoCRM
    amo_lead = {
        'name': lead_data.get('name', 'Новый лид'),
        'custom_fields_values': []
    }
    
    # Добавляем телефон
    if 'phone' in lead_data and lead_data['phone']:
        # Получаем ID поля телефона через field_manager
        phone_field_id = field_manager.find_field_id('leads', 'телефон')
        if phone_field_id:
            amo_lead['custom_fields_values'].append({
                'field_id': phone_field_id,
                'values': [{'value': lead_data['phone']}]
            })
    
    # Добавляем email
    if 'email' in lead_data and lead_data['email']:
        # Получаем ID поля email через field_manager
        email_field_id = field_manager.find_field_id('leads', 'email')
        if email_field_id:
            amo_lead['custom_fields_values'].append({
                'field_id': email_field_id,
                'values': [{'value': lead_data['email']}]
            })
    
    # Добавляем источник
    if 'source' in lead_data and lead_data['source']:
        # Получаем ID поля источника через field_manager
        source_field_id = field_manager.find_field_id('leads', 'источник')
        if source_field_id:
            amo_lead['custom_fields_values'].append({
                'field_id': source_field_id,
                'values': [{'value': lead_data['source']}]
            })
    
    # Добавляем комментарий
    if 'comment' in lead_data and lead_data['comment']:
        # Получаем ID поля комментария через field_manager
        comment_field_id = field_manager.find_field_id('leads', 'комментарий')
        if comment_field_id:
            amo_lead['custom_fields_values'].append({
                'field_id': comment_field_id,
                'values': [{'value': lead_data['comment']}]
            })
    
    # Устанавливаем статус
    if 'status' in lead_data and lead_data['status']:
        # Получаем первую воронку (или можно указать конкретную)
        pipelines = field_manager.get_pipelines()
        if pipelines and '_embedded' in pipelines and 'pipelines' in pipelines['_embedded']:
            pipeline_id = pipelines['_embedded']['pipelines'][0]['id']
            status_id = field_manager.find_status_id(pipeline_id, lead_data['status'])
            if status_id:
                amo_lead['status_id'] = status_id
    
    # Устанавливаем ответственного
    if 'responsible' in lead_data and lead_data['responsible']:
        user_id = field_manager.find_user_id(lead_data['responsible'])
        if user_id:
            amo_lead['responsible_user_id'] = user_id
    
    # Отправляем лид в AmoCRM
    result = lead.create_lead(amo_lead)
    
    if result:
        logger.info(f"Лид успешно отправлен в AmoCRM: {lead_data.get('name')}")
    else:
        logger.error(f"Ошибка отправки лида в AmoCRM: {lead_data.get('name')}")
    
    return result

def send_lead_to_webhook(lead_data, webhook_url):
    """
    Отправка лида на вебхук
    
    Args:
        lead_data (dict): Данные лида
        webhook_url (str): URL вебхука
        
    Returns:
        dict: Ответ от сервера вебхука
    """
    try:
        response = requests.post(
            webhook_url,
            json=lead_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Лид успешно отправлен на вебхук: {lead_data.get('name')}")
            return response.json()
        else:
            logger.error(f"Ошибка отправки лида на вебхук: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Исключение при отправке лида на вебхук: {e}")
        return None

def send_leads_from_csv(csv_file, webhook_url=None, has_header=True):
    """
    Отправка лидов из CSV файла
    
    Args:
        csv_file (str): Путь к CSV файлу
        webhook_url (str, optional): URL вебхука, если нужно отправлять через вебхук
        has_header (bool): Есть ли заголовок в CSV файле
        
    Returns:
        int: Количество успешно отправленных лидов
    """
    if not os.path.exists(csv_file):
        logger.error(f"Файл не найден: {csv_file}")
        return 0
    
    success_count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # Пропускаем заголовок, если он есть
            if has_header:
                next(reader)
            
            for row in reader:
                try:
                    # Предполагаем структуру CSV: name,phone,email,source,comment
                    lead_data = {
                        'name': row[0],
                        'phone': row[1],
                        'email': row[2] if len(row) > 2 else '',
                        'source': row[3] if len(row) > 3 else '',
                        'comment': row[4] if len(row) > 4 else '',
                        'status': row[5] if len(row) > 5 else 'Новый',
                        'responsible': row[6] if len(row) > 6 else None
                    }
                    
                    # Отправляем лид либо напрямую в AmoCRM, либо через вебхук
                    if webhook_url:
                        result = send_lead_to_webhook(lead_data, webhook_url)
                    else:
                        result = send_lead_from_dict(lead_data)
                    
                    if result:
                        success_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки строки CSV: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"Ошибка чтения CSV файла: {e}")
    
    logger.info(f"Всего отправлено лидов: {success_count}")
    return success_count

# Пример использования
if __name__ == "__main__":
    # Обновляем кэш полей
    field_manager.refresh_all_caches()
    
    # Пример данных лида
    test_lead = {
        'name': 'Тестовый клиент',
        'phone': '+79001234567',
        'email': 'test@example.com',
        'source': 'Тестовый источник',
        'comment': 'Тестовый комментарий',
        'status': 'Новый',
        'responsible': 'Admin'
    }
    
    # Прямая отправка в AmoCRM
    print("Отправка лида напрямую в AmoCRM...")
    result1 = send_lead_from_dict(test_lead)
    print(f"Результат: {result1}")
    
    # Отправка через вебхук
    webhook_url = 'http://leadrecordwh.ru/webhook'
    print(f"Отправка лида на вебхук {webhook_url}...")
    result2 = send_lead_to_webhook(test_lead, webhook_url)
    print(f"Результат: {result2}")
    
    # Отправка из CSV файла
    csv_file = 'data/leads.csv'
    print(f"Отправка лидов из CSV файла {csv_file}...")
    count = send_leads_from_csv(csv_file)
    print(f"Отправлено лидов: {count}") 