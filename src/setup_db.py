"""
Скрипт для первоначальной настройки базы данных.

Инициализирует БД и добавляет тестовые данные.
"""
import sys

from src.setup import logger
from src.db import init_db, get_connection

def setup_database():
    """
    Инициализирует базу данных и создает необходимые таблицы.
    
    Returns:
        bool: True, если настройка прошла успешно, иначе False
    """
    try:
        # Инициализируем БД
        if not init_db():
            logger.error("Не удалось инициализировать базу данных.")
            return False
        
        logger.info("База данных успешно настроена.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при настройке базы данных: {e}")
        return False

def add_test_client(name, tag, spreadsheet_id=None, sheet_name=None, use_crm=False, webhook_url=None):
    """
    Добавляет тестового клиента в базу данных.
    
    Args:
        name (str): Имя клиента
        tag (str): Тег для маршрутизации
        spreadsheet_id (str, optional): ID Google таблицы клиента
        sheet_name (str, optional): Имя листа в таблице клиента
        use_crm (bool, optional): Флаг использования CRM
        webhook_url (str, optional): URL вебхука для CRM
    
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
        
        # Добавляем тестового клиента
        cursor.execute('''
        INSERT INTO clients (id, name, tag, spreadsheet_id, sheet_name, use_crm, webhook_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"test_{name.lower().replace(' ', '_')}",
            name,
            tag,
            spreadsheet_id,
            sheet_name,
            1 if use_crm else 0,
            webhook_url
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Добавлен тестовый клиент: {name} с тегом '{tag}'.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении тестового клиента: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def add_test_data():
    """
    Добавляет тестовые данные в базу данных.
    
    Returns:
        bool: True, если данные добавлены успешно, иначе False
    """
    try:
        # Добавляем тестовых клиентов
        add_test_client(
            name="Неометрия Ростов",
            tag="[П8] Неометрия Ростов",
            spreadsheet_id="your_spreadsheet_id_here",
            sheet_name="Лиды"
        )
        
        add_test_client(
            name="МОЛОТОВ-1 проектирование",
            tag="[П179] МОЛОТОВ-1 проектирование",
            spreadsheet_id="your_spreadsheet_id_here",
            sheet_name="Лиды",
            use_crm=True,
            webhook_url="https://example.com/webhook"
        )
        
        logger.info("Тестовые данные успешно добавлены.")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении тестовых данных: {e}")
        return False

def main():
    """
    Основная функция для запуска настройки БД.
    """
    logger.info("Запуск настройки базы данных...")
    
    if setup_database():
        # Если передан аргумент --with-test-data, добавляем тестовые данные
        if len(sys.argv) > 1 and sys.argv[1] == '--with-test-data':
            logger.info("Добавление тестовых данных...")
            add_test_data()
        
        logger.info("Настройка базы данных завершена успешно.")
    else:
        logger.error("Настройка базы данных завершилась с ошибкой.")
        sys.exit(1)

if __name__ == '__main__':
    main() 