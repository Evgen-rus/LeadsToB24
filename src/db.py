"""
Модуль для работы с базой данных.

Отвечает за инициализацию БД и базовые операции с данными.
"""
import sqlite3
from datetime import datetime
from src.setup import logger, get_db_path

def init_db():
    """
    Инициализирует базу данных и создает необходимые таблицы.
    
    Returns:
        bool: True, если инициализация прошла успешно, иначе False
    """
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Создаем таблицу клиентов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tag TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Создаем таблицу лидов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            phone TEXT,
            tag TEXT,
            client_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            delivery_attempts INTEGER DEFAULT 0,
            crm_delivery_status TEXT,
            crm_delivery_time TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("База данных успешно инициализирована.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def get_connection():
    """
    Создает и возвращает соединение с базой данных.
    
    Returns:
        sqlite3.Connection: Объект соединения с БД или None в случае ошибки
    """
    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        return conn
    
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        return None

def get_client_by_tag(tag):
    """
    Получает информацию о клиенте по тегу.
    
    Args:
        tag (str): Тег для поиска клиента
    
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
        return None
    
    except Exception as e:
        logger.error(f"Ошибка при получении клиента по тегу: {e}")
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
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении клиента для лида: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def mark_lead_as_sent(lead_id):
    """
    Помечает лид как отправленный.
    
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
        SET sent_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (lead_id,))
        
        conn.commit()
        conn.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса отправки лида: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

def insert_lead(lead_data):
    """
    Добавляет новый лид в базу данных.
    
    Args:
        lead_data (dict): Данные о лиде, включая:
            - id: Уникальный идентификатор лида
            - phone: Номер телефона
            - tag: Тег проекта
            - created_at: Дата создания (datetime или строка в формате YYYY-MM-DD HH:MM:SS)
    
    Returns:
        bool: True, если лид успешно добавлен, иначе False
    """
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Проверяем, существует ли лид с таким ID
        cursor.execute('SELECT id FROM leads WHERE id = ?', (lead_data['id'],))
        if cursor.fetchone():
            logger.warning(f"Лид с ID {lead_data['id']} уже существует в базе.")
            conn.close()
            return False
        
        # Преобразуем created_at в строку, если это datetime объект
        created_at = lead_data['created_at']
        if isinstance(created_at, datetime):
            created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        # Добавляем новый лид
        cursor.execute('''
        INSERT INTO leads (id, phone, tag, created_at)
        VALUES (?, ?, ?, ?)
        ''', (
            lead_data['id'],
            lead_data['phone'],
            lead_data['tag'],
            created_at
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Лид {lead_data['id']} успешно добавлен в базу.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении лида: {e}")
        if 'conn' in locals() and conn:
            conn.close()