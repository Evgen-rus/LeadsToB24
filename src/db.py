"""
Модуль для работы с базой данных SQLite.

Отвечает за инициализацию БД, создание таблиц и выполнение операций с данными.
"""
import sqlite3
from pathlib import Path

from src.setup import DB_PATH, logger

def init_db():
    """
    Инициализирует базу данных и создает необходимые таблицы, если они отсутствуют.
    
    Returns:
        bool: True, если инициализация прошла успешно, иначе False.
    """
    try:
        # Убедимся, что директория для базы данных существует
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Создаем таблицу leads, если она не существует
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP NOT NULL,
            phone TEXT NOT NULL,
            tag TEXT NOT NULL,
            original_tag TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_sent_to_client BOOLEAN DEFAULT 0,
            client_id TEXT,
            sheet_delivery_status TEXT DEFAULT NULL,
            sheet_delivery_time TIMESTAMP DEFAULT NULL,
            crm_delivery_status TEXT DEFAULT NULL,
            crm_delivery_time TIMESTAMP DEFAULT NULL,
            delivery_attempts INTEGER DEFAULT 0
        )
        ''')
        
        # Создаем таблицу clients для хранения информации о клиентах
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tag TEXT NOT NULL,
            spreadsheet_id TEXT,
            sheet_name TEXT,
            use_crm BOOLEAN DEFAULT 0,
            webhook_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("База данных успешно инициализирована.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        return False

def get_connection():
    """
    Создает и возвращает соединение с базой данных.
    
    Returns:
        Connection: Объект соединения с базой данных SQLite или None в случае ошибки.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Для доступа к результатам по имени колонки
        return conn
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        return None

def insert_lead(lead_data):
    """
    Добавляет новую запись в таблицу leads.
    
    Args:
        lead_data (dict): Словарь с данными о лиде
            {
                'id': str,
                'created_at': datetime,
                'phone': str,
                'tag': str,
                'original_tag': str
            }
    
    Returns:
        bool: True, если запись успешно добавлена, иначе False.
    """
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Проверяем, существует ли запись с таким id
        cursor.execute('SELECT id FROM leads WHERE id = ?', (lead_data['id'],))
        if cursor.fetchone():
            logger.info(f"Запись с id {lead_data['id']} уже существует в базе данных.")
            conn.close()
            return False
        
        # Добавляем новую запись
        cursor.execute('''
        INSERT INTO leads (id, created_at, phone, tag, original_tag)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            lead_data['id'],
            lead_data['created_at'],
            lead_data['phone'],
            lead_data['tag'],
            lead_data['original_tag']
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Запись с id {lead_data['id']} успешно добавлена в базу данных.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении записи в базу данных: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def lead_exists(lead_id):
    """
    Проверяет, существует ли запись с указанным ID в базе данных.
    
    Args:
        lead_id (str): ID лида для проверки
    
    Returns:
        bool: True, если запись существует, иначе False
    """
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM leads WHERE id = ?', (lead_id,))
        result = cursor.fetchone() is not None
        
        conn.close()
        return result
    
    except Exception as e:
        logger.error(f"Ошибка при проверке существования записи {lead_id}: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def get_client_by_tag(tag):
    """
    Находит клиента по тегу.
    
    Args:
        tag (str): Очищенный тег для поиска клиента
    
    Returns:
        dict: Данные о клиенте или None, если клиент не найден
    """
    try:
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM clients WHERE tag = ?', (tag,))
        client = cursor.fetchone()
        
        conn.close()
        
        if client:
            return dict(client)
        else:
            logger.warning(f"Клиент с тегом '{tag}' не найден.")
            return None
    
    except Exception as e:
        logger.error(f"Ошибка при поиске клиента по тегу '{tag}': {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def update_lead_client(lead_id, client_id):
    """
    Обновляет информацию о клиенте для лида.
    
    Args:
        lead_id (str): ID лида
        client_id (str): ID клиента
    
    Returns:
        bool: True, если обновление успешно, иначе False
    """
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE leads
        SET client_id = ?
        WHERE id = ?
        ''', (client_id, lead_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Для лида {lead_id} установлен клиент {client_id}.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении информации о клиенте для лида {lead_id}: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def mark_lead_as_sent(lead_id):
    """
    Помечает лид как отправленный клиенту.
    
    Args:
        lead_id (str): ID лида
    
    Returns:
        bool: True, если обновление успешно, иначе False
    """
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE leads
        SET is_sent_to_client = 1
        WHERE id = ?
        ''', (lead_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Лид {lead_id} помечен как отправленный клиенту.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса отправки для лида {lead_id}: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False