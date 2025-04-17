"""
Модуль для работы с лидами в AmoCRM.
Позволяет создавать и обновлять лиды.
"""
import logging
from . import api

# Настраиваем логирование
logger = logging.getLogger('amo.lead')

def get_leads(limit=50, page=1, with_params=None):
    """
    Получение списка лидов из AmoCRM
    
    Args:
        limit (int): Количество лидов на страницу
        page (int): Номер страницы
        with_params (list): Дополнительные параметры запроса
    
    Returns:
        dict: Результат запроса с лидами
    """
    params = {
        'limit': limit,
        'page': page
    }
    
    if with_params:
        params['with'] = ','.join(with_params)
    
    return api.get('leads', params=params)

def get_lead(lead_id, with_params=None):
    """
    Получение информации о конкретном лиде
    
    Args:
        lead_id (int): ID лида
        with_params (list): Дополнительные параметры запроса
    
    Returns:
        dict: Данные лида
    """
    params = {}
    if with_params:
        params['with'] = ','.join(with_params)
    
    return api.get(f'leads/{lead_id}', params=params)

def create_lead(lead_data):
    """
    Создание нового лида в AmoCRM
    
    Args:
        lead_data (dict): Данные для создания лида
            {
                'name': 'Имя лида',
                'price': 10000,
                'status_id': 123,
                'responsible_user_id': 456,
                'custom_fields_values': [
                    {
                        'field_id': 789,
                        'values': [{'value': 'Значение поля'}]
                    }
                ]
            }
    
    Returns:
        dict: Результат создания лида
    """
    # Проверка обязательных полей
    if 'name' not in lead_data:
        lead_data['name'] = 'Новый лид'
    
    # Отправка запроса
    result = api.post('leads', [lead_data])
    
    if result:
        logger.info(f"Лид создан: {lead_data.get('name')}")
        return result
    else:
        logger.error(f"Ошибка создания лида: {lead_data}")
        return None

def create_lead_with_contacts(lead_data, contacts=None, company=None):
    """
    Создание лида с привязкой контактов и компании
    
    Args:
        lead_data (dict): Данные лида
        contacts (list): Список контактов для привязки
        company (dict): Компания для привязки
    
    Returns:
        dict: Результат создания лида
    """
    # Создаем лид
    result = create_lead(lead_data)
    
    if not result or '_embedded' not in result or 'leads' not in result['_embedded']:
        return result
    
    # Получаем ID созданного лида
    lead_id = result['_embedded']['leads'][0]['id']
    
    # Привязываем контакты, если указаны
    if contacts and lead_id:
        for contact in contacts:
            link_contact_to_lead(lead_id, contact)
    
    # Привязываем компанию, если указана
    if company and lead_id:
        link_company_to_lead(lead_id, company)
    
    return result

def update_lead(lead_id, data):
    """
    Обновление данных лида
    
    Args:
        lead_id (int): ID лида
        data (dict): Данные для обновления
    
    Returns:
        dict: Результат обновления
    """
    return api.patch(f'leads/{lead_id}', data)

def link_contact_to_lead(lead_id, contact_id):
    """
    Привязка контакта к лиду
    
    Args:
        lead_id (int): ID лида
        contact_id (int): ID контакта
    
    Returns:
        dict: Результат привязки
    """
    data = {
        'to_entity_id': contact_id,
        'to_entity_type': 'contacts'
    }
    return api.post(f'leads/{lead_id}/link', data)

def link_company_to_lead(lead_id, company_id):
    """
    Привязка компании к лиду
    
    Args:
        lead_id (int): ID лида
        company_id (int): ID компании
    
    Returns:
        dict: Результат привязки
    """
    data = {
        'to_entity_id': company_id,
        'to_entity_type': 'companies'
    }
    return api.post(f'leads/{lead_id}/link', data) 