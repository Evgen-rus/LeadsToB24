"""
Модуль для управления конфигурацией клиентов.

Отвечает за загрузку настроек клиентов из БД и их кэширование.
"""
import uuid
from src.setup import logger
from src.db import get_connection, get_client_by_tag

# Кэш клиентов для ускорения поиска
_clients_cache = {}
_tags_mapping = {}

def load_clients():
    """
    Загружает информацию о всех клиентах из БД и обновляет кэш.
    
    Returns:
        bool: True, если загрузка прошла успешно, иначе False.
    """
    global _clients_cache, _tags_mapping
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients')
        clients = cursor.fetchall()
        
        # Очищаем кэш
        _clients_cache = {}
        _tags_mapping = {}
        
        # Заполняем кэш
        for client in clients:
            client_dict = dict(client)
            client_id = client_dict['id']
            tag = client_dict['tag']
            
            _clients_cache[client_id] = client_dict
            _tags_mapping[tag] = client_id
        
        conn.close()
        
        logger.info(f"Загружено {len(_clients_cache)} клиентов.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке клиентов: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def get_client_by_tag_cached(tag):
    """
    Получает информацию о клиенте по тегу из кэша или из БД.
    
    Args:
        tag (str): Тег для поиска клиента
    
    Returns:
        dict: Данные о клиенте или None, если клиент не найден
    """
    # Если кэш пуст, загружаем клиентов
    if not _clients_cache:
        load_clients()
    
    # Пытаемся найти клиента в кэше
    client_id = _tags_mapping.get(tag)
    if client_id:
        return _clients_cache.get(client_id)
    
    # Если клиент не найден в кэше, ищем в БД
    client = get_client_by_tag(tag)
    if client:
        # Обновляем кэш
        client_id = client['id']
        _clients_cache[client_id] = client
        _tags_mapping[tag] = client_id
        return client
    
    return None

def add_client(name, tag):
    """
    Добавляет нового клиента в БД.
    
    Args:
        name (str): Имя клиента
        tag (str): Тег для маршрутизации
    
    Returns:
        str: ID добавленного клиента или None в случае ошибки
    """
    try:
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Проверяем, существует ли клиент с таким тегом
        cursor.execute('SELECT id FROM clients WHERE tag = ?', (tag,))
        existing_client = cursor.fetchone()
        
        if existing_client:
            logger.warning(f"Клиент с тегом '{tag}' уже существует.")
            conn.close()
            return None
        
        # Генерируем уникальный ID для клиента
        client_id = str(uuid.uuid4())
        
        # Добавляем нового клиента
        cursor.execute('''
        INSERT INTO clients (id, name, tag)
        VALUES (?, ?, ?)
        ''', (
            client_id,
            name,
            tag
        ))
        
        conn.commit()
        conn.close()
        
        # Обновляем кэш
        load_clients()
        
        logger.info(f"Добавлен новый клиент: {name} с тегом '{tag}'.")
        return client_id
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении клиента: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def update_client(client_id, **kwargs):
    """
    Обновляет информацию о клиенте.
    
    Args:
        client_id (str): ID клиента
        **kwargs: Параметры для обновления
    
    Returns:
        bool: True, если обновление успешно, иначе False
    """
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Проверяем существование клиента
        cursor.execute('SELECT id FROM clients WHERE id = ?', (client_id,))
        if not cursor.fetchone():
            logger.warning(f"Клиент с ID {client_id} не найден.")
            conn.close()
            return False
        
        # Формируем SQL-запрос для обновления
        set_clauses = []
        params = []
        
        for key, value in kwargs.items():
            if key in ['name', 'tag']:
                set_clauses.append(f"{key} = ?")
                params.append(value)
        
        if not set_clauses:
            logger.warning("Нет параметров для обновления.")
            conn.close()
            return False
        
        # Добавляем ID клиента в параметры
        params.append(client_id)
        
        # Выполняем запрос на обновление
        query = f"UPDATE clients SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        # Обновляем кэш
        load_clients()
        
        logger.info(f"Клиент {client_id} успешно обновлен.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении клиента {client_id}: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def get_all_clients():
    """
    Возвращает список всех клиентов.
    
    Returns:
        list: Список словарей с данными о клиентах
    """
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients')
        clients = cursor.fetchall()
        
        conn.close()
        
        return [dict(client) for client in clients]
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка клиентов: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return []

def add_client_to_config(client_config):
    """
    Добавляет нового клиента в конфигурацию.
    
    Args:
        client_config (dict): Словарь с настройками клиента
    
    Returns:
        bool: True, если клиент успешно добавлен, иначе False
    """
    try:
        name = client_config.get('name')
        tag = client_config.get('tag')
        
        if not name or not tag:
            logger.error("Не указаны обязательные параметры name и tag")
            return False
        
        spreadsheet_id = client_config.get('sheet_id')
        sheet_name = client_config.get('sheet_name')
        use_crm = client_config.get('use_crm', False)
        webhook_url = client_config.get('webhook_url')
        
        client_id = add_client(
            name=name,
            tag=tag,
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            use_crm=use_crm,
            webhook_url=webhook_url
        )
        
        return client_id is not None
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении клиента в конфигурацию: {e}")
        return False

def get_client_by_name(name):
    """
    Находит клиента по имени.
    
    Args:
        name (str): Имя клиента
    
    Returns:
        dict: Данные о клиенте или None, если клиент не найден
    """
    try:
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE name = ?', (name,))
        client = cursor.fetchone()
        
        conn.close()
        
        if client:
            return dict(client)
        else:
            logger.warning(f"Клиент с именем '{name}' не найден.")
            return None
    
    except Exception as e:
        logger.error(f"Ошибка при поиске клиента по имени '{name}': {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None 