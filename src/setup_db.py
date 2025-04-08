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

def add_test_client(name, tag):
    """
    Добавляет тестового клиента в базу данных.
    
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
        
        # Добавляем тестового клиента
        cursor.execute('''
        INSERT INTO clients (id, name, tag)
        VALUES (?, ?, ?)
        ''', (
            f"test_{name.lower().replace(' ', '_')}",
            name,
            tag
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
            name="СуперМет_СП",
            tag="[LR115] СуперМет_СП"
        )
        
        add_test_client(
            name="Диалог Чанган Казань",
            tag="[ДМД13] Диалог Чанган Казань"
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