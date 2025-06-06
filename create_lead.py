"""
Скрипт для создания лида в AmoCRM с номером телефона
"""
import logging
from amo import api

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/amo.log'
)
logger = logging.getLogger('create_lead')

# Добавляем вывод в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(message)s')  # Упрощенный формат для консоли
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Константы
PHONE_FIELD_ID = 318033  # ID поля телефона для контакта
PIPELINE_ID = 2194891  # ID воронки "Частный Дизайн"
STATUS_ID = 68384126  # ID этапа "DMP - LEADRECORD"
RESPONSIBLE_USER_ID = 9480922  # ID ответственного "Михаил Васнецов"
TAG_NAME = "LeadRecord"
SOURCE_NAME = "LeadRecord"

def create_contact_with_phone(phone, name=None):
    """
    Создание контакта с номером телефона
    
    Args:
        phone (str): Номер телефона
        name (str, optional): Имя контакта
        
    Returns:
        int: ID созданного контакта или None в случае ошибки
    """
    if not name:
        name = f"Контакт {phone}"
        
    # Формируем данные контакта
    contact_data = {
        "name": name,
        "custom_fields_values": [
            {
                "field_id": PHONE_FIELD_ID,
                "values": [
                    {
                        "value": phone,
                        "enum_code": "WORK"  # Рабочий телефон
                    }
                ]
            }
        ]
    }
    
    logger.info(f"Подготовлены данные для создания контакта: {name}")
    
    # Создаем контакт
    result = api.post('contacts', [contact_data])
    
    if not result or '_embedded' not in result or 'contacts' not in result['_embedded']:
        logger.error(f"Ошибка при создании контакта с телефоном {phone}")
        return None
        
    contact_id = result['_embedded']['contacts'][0]['id']
    logger.info(f"Создан контакт с ID {contact_id} и телефоном {phone}")
    return contact_id

def create_lead_with_contact(name, contact_id):
    """
    Создание лида и привязка к нему контакта
    
    Args:
        name (str): Название лида
        contact_id (int): ID контакта для привязки
        
    Returns:
        int: ID созданного лида или None в случае ошибки
    """
    # Формируем данные лида
    lead_data = {
        "name": name,
        "pipeline_id": PIPELINE_ID,
        "status_id": STATUS_ID,
        "responsible_user_id": RESPONSIBLE_USER_ID,
        "tags": [TAG_NAME],
        "source": SOURCE_NAME
    }
    
    logger.info(f"Создание лида: {name}")
    
    # Создаем лид
    result = api.post('leads', [lead_data])
    
    if not result or '_embedded' not in result or 'leads' not in result['_embedded']:
        logger.error(f"Ошибка при создании лида {name}")
        return None
        
    lead_id = result['_embedded']['leads'][0]['id']
    
    # Выводим краткую информацию о созданном лиде
    logger.info(f"✅ Создан лид: {name}")
    logger.info(f"   ID лида: {lead_id}")
    logger.info(f"   ID контакта: {contact_id}")
    logger.info(f"   Воронка: Частный Дизайн")
    logger.info(f"   Этап: DMP - LEADRECORD")
    logger.info(f"   Ответственный: Михаил Васнецов")
    logger.info(f"   Тег: {TAG_NAME}")
    logger.info(f"   Источник: {SOURCE_NAME}")
    logger.info("----------------------------------------")
    
    # Связываем лид с контактом
    link_data = [{
        "to_entity_id": contact_id,
        "to_entity_type": "contacts"
    }]
    
    link_result = api.post(f"leads/{lead_id}/link", link_data)
    
    if link_result:
        logger.info(f"Лид {lead_id} связан с контактом {contact_id}")
    else:
        logger.error(f"Ошибка при связывании лида {lead_id} с контактом {contact_id}")
        
    return lead_id

def create_lead_with_phone(phone):
    """
    Создание лида с номером телефона через создание контакта
    
    Args:
        phone (str): Номер телефона
        
    Returns:
        tuple: (lead_id, contact_id) или (None, None) в случае ошибки
    """
    # Создаем контакт с телефоном
    contact_id = create_contact_with_phone(phone)
    
    if not contact_id:
        return None, None
        
    # Создаем лид и связываем с контактом
    lead_name = f"LR_{phone}"  # Изменено название лида
    lead_id = create_lead_with_contact(lead_name, contact_id)
    
    if not lead_id:
        return None, contact_id
        
    return lead_id, contact_id

if __name__ == "__main__":
    # Пример использования
    phone_number = input("Введите номер телефона: ")
    lead_id, contact_id = create_lead_with_phone(phone_number)
    
    if lead_id:
        print(f"Успешно создан лид (ID: {lead_id}) с контактом (ID: {contact_id})!")
    elif contact_id:
        print(f"Создан только контакт (ID: {contact_id}), но не удалось создать лид.")
    else:
        print(f"Ошибка при создании лида и контакта. Подробности в логах.") 