"""
Модуль для работы с полями AmoCRM через API.
Позволяет получать информацию о полях, их ID и значениях без доступа к интерфейсу.
"""
import os
import json
import logging
from . import api

# Настраиваем логирование на более подробный уровень
logger = logging.getLogger('amo.field_manager')
logger.setLevel(logging.DEBUG)

# Добавляем вывод логов в консоль для отладки
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Пути к файлам кэша для сохранения информации о полях
CACHE_DIR = 'amo/cache'
LEAD_FIELDS_CACHE = f'{CACHE_DIR}/lead_fields.json'
CONTACT_FIELDS_CACHE = f'{CACHE_DIR}/contact_fields.json'
COMPANY_FIELDS_CACHE = f'{CACHE_DIR}/company_fields.json'
PIPELINES_CACHE = f'{CACHE_DIR}/pipelines.json'
USERS_CACHE = f'{CACHE_DIR}/users.json'

# Создаем директорию для кэша, если она не существует
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_lead_fields(use_cache=True):
    """
    Получение списка всех полей для лидов
    
    Args:
        use_cache (bool): Использовать кэш или запрашивать заново
        
    Returns:
        dict: Словарь с информацией о полях
    """
    logger.debug("Запрос полей лидов (use_cache=%s)", use_cache)
    
    # Проверяем кэш
    if use_cache and os.path.exists(LEAD_FIELDS_CACHE):
        try:
            with open(LEAD_FIELDS_CACHE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug("Данные загружены из кэша: %s", LEAD_FIELDS_CACHE)
                return data
        except Exception as e:
            logger.error(f"Ошибка чтения кэша полей лидов: {e}")
    
    # Запрашиваем список полей через API
    logger.debug("Выполняется запрос к API: leads/custom_fields")
    result = api.get('leads/custom_fields')
    
    logger.debug("Получен ответ от API: %s", str(result)[:100] + '...' if result and len(str(result)) > 100 else str(result))
    
    if result:
        # Сохраняем в кэш
        try:
            with open(LEAD_FIELDS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                logger.debug("Данные сохранены в кэш: %s", LEAD_FIELDS_CACHE)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша полей лидов: {e}")
    else:
        logger.error("Не удалось получить данные о полях лидов через API")
    
    return result

def get_contact_fields(use_cache=True):
    """
    Получение списка всех полей для контактов
    
    Args:
        use_cache (bool): Использовать кэш или запрашивать заново
        
    Returns:
        dict: Словарь с информацией о полях
    """
    logger.debug("Запрос полей контактов (use_cache=%s)", use_cache)
    
    # Проверяем кэш
    if use_cache and os.path.exists(CONTACT_FIELDS_CACHE):
        try:
            with open(CONTACT_FIELDS_CACHE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug("Данные загружены из кэша: %s", CONTACT_FIELDS_CACHE)
                return data
        except Exception as e:
            logger.error(f"Ошибка чтения кэша полей контактов: {e}")
    
    # Запрашиваем список полей через API
    logger.debug("Выполняется запрос к API: contacts/custom_fields")
    result = api.get('contacts/custom_fields')
    
    logger.debug("Получен ответ от API: %s", str(result)[:100] + '...' if result and len(str(result)) > 100 else str(result))
    
    if result:
        # Сохраняем в кэш
        try:
            with open(CONTACT_FIELDS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                logger.debug("Данные сохранены в кэш: %s", CONTACT_FIELDS_CACHE)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша полей контактов: {e}")
    else:
        logger.error("Не удалось получить данные о полях контактов через API")
    
    return result

def get_company_fields(use_cache=True):
    """
    Получение списка всех полей для компаний
    
    Args:
        use_cache (bool): Использовать кэш или запрашивать заново
        
    Returns:
        dict: Словарь с информацией о полях
    """
    logger.debug("Запрос полей компаний (use_cache=%s)", use_cache)
    
    # Проверяем кэш
    if use_cache and os.path.exists(COMPANY_FIELDS_CACHE):
        try:
            with open(COMPANY_FIELDS_CACHE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug("Данные загружены из кэша: %s", COMPANY_FIELDS_CACHE)
                return data
        except Exception as e:
            logger.error(f"Ошибка чтения кэша полей компаний: {e}")
    
    # Запрашиваем список полей через API
    logger.debug("Выполняется запрос к API: companies/custom_fields")
    result = api.get('companies/custom_fields')
    
    logger.debug("Получен ответ от API: %s", str(result)[:100] + '...' if result and len(str(result)) > 100 else str(result))
    
    if result:
        # Сохраняем в кэш
        try:
            with open(COMPANY_FIELDS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                logger.debug("Данные сохранены в кэш: %s", COMPANY_FIELDS_CACHE)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша полей компаний: {e}")
    else:
        logger.error("Не удалось получить данные о полях компаний через API")
    
    return result

def get_pipelines(use_cache=True):
    """
    Получение списка воронок и их статусов
    
    Args:
        use_cache (bool): Использовать кэш или запрашивать заново
        
    Returns:
        dict: Словарь с информацией о воронках
    """
    logger.debug("Запрос воронок (use_cache=%s)", use_cache)
    
    # Проверяем кэш
    if use_cache and os.path.exists(PIPELINES_CACHE):
        try:
            with open(PIPELINES_CACHE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug("Данные загружены из кэша: %s", PIPELINES_CACHE)
                return data
        except Exception as e:
            logger.error(f"Ошибка чтения кэша воронок: {e}")
    
    # Запрашиваем список воронок через API
    logger.debug("Выполняется запрос к API: leads/pipelines")
    result = api.get('leads/pipelines')
    
    logger.debug("Получен ответ от API: %s", str(result)[:100] + '...' if result and len(str(result)) > 100 else str(result))
    
    if result:
        # Сохраняем в кэш
        try:
            with open(PIPELINES_CACHE, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                logger.debug("Данные сохранены в кэш: %s", PIPELINES_CACHE)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша воронок: {e}")
    else:
        logger.error("Не удалось получить данные о воронках через API")
    
    return result

def get_users(use_cache=True):
    """
    Получение списка пользователей
    
    Args:
        use_cache (bool): Использовать кэш или запрашивать заново
        
    Returns:
        dict: Словарь с информацией о пользователях
    """
    logger.debug("Запрос пользователей (use_cache=%s)", use_cache)
    
    # Проверяем кэш
    if use_cache and os.path.exists(USERS_CACHE):
        try:
            with open(USERS_CACHE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug("Данные загружены из кэша: %s", USERS_CACHE)
                return data
        except Exception as e:
            logger.error(f"Ошибка чтения кэша пользователей: {e}")
    
    # Запрашиваем список пользователей через API
    logger.debug("Выполняется запрос к API: users")
    result = api.get('users')
    
    logger.debug("Получен ответ от API: %s", str(result)[:100] + '...' if result and len(str(result)) > 100 else str(result))
    
    if result:
        # Сохраняем в кэш
        try:
            with open(USERS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                logger.debug("Данные сохранены в кэш: %s", USERS_CACHE)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша пользователей: {e}")
    else:
        logger.error("Не удалось получить данные о пользователях через API")
    
    return result

def find_field_id(entity_type, field_name):
    """
    Поиск ID поля по названию для указанного типа сущности
    
    Args:
        entity_type (str): Тип сущности ('leads', 'contacts', 'companies')
        field_name (str): Название поля (можно частичное)
        
    Returns:
        int: ID поля или None если поле не найдено
    """
    # Выбираем функцию получения полей в зависимости от типа сущности
    if entity_type == 'leads':
        fields_data = get_lead_fields()
    elif entity_type == 'contacts':
        fields_data = get_contact_fields()
    elif entity_type == 'companies':
        fields_data = get_company_fields()
    else:
        logger.error(f"Неизвестный тип сущности: {entity_type}")
        return None
    
    # Проверяем наличие данных
    if not fields_data or '_embedded' not in fields_data or 'custom_fields' not in fields_data['_embedded']:
        logger.error(f"Не удалось получить данные о полях для {entity_type}")
        return None
    
    # Ищем поле по названию
    field_name_lower = field_name.lower()
    for field in fields_data['_embedded']['custom_fields']:
        if field_name_lower in field.get('name', '').lower():
            return field['id']
    
    logger.warning(f"Поле '{field_name}' не найдено для {entity_type}")
    return None

def find_status_id(pipeline_id, status_name):
    """
    Поиск ID статуса в воронке по названию
    
    Args:
        pipeline_id (int): ID воронки
        status_name (str): Название статуса (можно частичное)
        
    Returns:
        int: ID статуса или None если статус не найден
    """
    pipelines_data = get_pipelines()
    
    # Проверяем наличие данных
    if not pipelines_data or '_embedded' not in pipelines_data or 'pipelines' not in pipelines_data['_embedded']:
        logger.error("Не удалось получить данные о воронках")
        return None
    
    # Находим нужную воронку
    pipeline = None
    for p in pipelines_data['_embedded']['pipelines']:
        if str(p['id']) == str(pipeline_id):
            pipeline = p
            break
    
    if not pipeline:
        logger.error(f"Воронка с ID={pipeline_id} не найдена")
        return None
    
    # Ищем статус по названию
    status_name_lower = status_name.lower()
    for status in pipeline.get('_embedded', {}).get('statuses', []):
        if status_name_lower in status.get('name', '').lower():
            return status['id']
    
    logger.warning(f"Статус '{status_name}' не найден в воронке {pipeline_id}")
    return None

def find_user_id(user_name):
    """
    Поиск ID пользователя по имени
    
    Args:
        user_name (str): Имя пользователя (можно частичное)
        
    Returns:
        int: ID пользователя или None если пользователь не найден
    """
    users_data = get_users()
    
    # Проверяем наличие данных
    if not users_data or '_embedded' not in users_data or 'users' not in users_data['_embedded']:
        logger.error("Не удалось получить данные о пользователях")
        return None
    
    # Ищем пользователя по имени
    user_name_lower = user_name.lower()
    for user in users_data['_embedded']['users']:
        full_name = f"{user.get('name', '')} {user.get('last_name', '')}"
        if user_name_lower in full_name.lower():
            return user['id']
    
    logger.warning(f"Пользователь '{user_name}' не найден")
    return None

def refresh_all_caches():
    """
    Принудительное обновление всех кэшей
    """
    logger.info("Начало обновления всех кэшей")
    
    lead_fields = get_lead_fields(use_cache=False)
    logger.debug("Обновлен кэш полей лидов: %s", "успешно" if lead_fields else "ошибка")
    
    contact_fields = get_contact_fields(use_cache=False)
    logger.debug("Обновлен кэш полей контактов: %s", "успешно" if contact_fields else "ошибка")
    
    company_fields = get_company_fields(use_cache=False)
    logger.debug("Обновлен кэш полей компаний: %s", "успешно" if company_fields else "ошибка")
    
    pipelines = get_pipelines(use_cache=False)
    logger.debug("Обновлен кэш воронок: %s", "успешно" if pipelines else "ошибка")
    
    users = get_users(use_cache=False)
    logger.debug("Обновлен кэш пользователей: %s", "успешно" if users else "ошибка")
    
    logger.info("Завершено обновление всех кэшей")
    
if __name__ == "__main__":
    # Тестовый код для проверки работы модуля
    logging.basicConfig(level=logging.INFO)
    
    print("Обновление кэшей...")
    refresh_all_caches()
    
    print("\nПоиск полей лидов:")
    phone_field_id = find_field_id('leads', 'телефон')
    print(f"ID поля 'телефон': {phone_field_id}")
    
    email_field_id = find_field_id('leads', 'email')
    print(f"ID поля 'email': {email_field_id}")
    
    print("\nПоиск статусов:")
    status_id = find_status_id(6375467, 'Новый')
    print(f"ID статуса 'Новый': {status_id}")
    
    print("\nПоиск пользователей:")
    user_id = find_user_id('Admin')
    print(f"ID пользователя 'Admin': {user_id}") 