"""
Основной модуль для обработки данных из Google Sheets.

Координирует работу всех остальных модулей.
"""
import time
import sys
from datetime import datetime

from src.setup import logger, init_db
from src.sheets import get_new_rows, mark_row_as_processed
from src.processor import process_row
from src.db import insert_lead
from src.router import route_lead
from src.client_config import load_clients
from src.scheduler import run_scheduler

def process_new_leads():
    """
    Обрабатывает новые записи из исходной таблицы.
    
    Returns:
        bool: True, если обработка прошла успешно, иначе False
    """
    try:
        logger.info("Начало обработки новых записей...")
        
        # Инициализируем БД
        if not init_db():
            logger.error("Не удалось инициализировать базу данных.")
            return False
        
        # Загружаем информацию о клиентах
        if not load_clients():
            logger.error("Не удалось загрузить информацию о клиентах.")
            return False
        
        # Получаем новые строки из таблицы
        rows = get_new_rows()
        if not rows:
            logger.info("Новых записей не найдено.")
            return True
        
        logger.info(f"Найдено {len(rows)} новых записей.")
        
        # Обрабатываем каждую строку
        for i, row in enumerate(rows):
            try:
                # Обрабатываем данные строки
                processed_data = process_row(row)
                if not processed_data:
                    logger.warning(f"Не удалось обработать строку {i+1}.")
                    continue
                
                # Добавляем запись в БД
                if not insert_lead(processed_data):
                    logger.warning(f"Не удалось добавить запись в БД: {processed_data['id']}.")
                    continue
                
                # Маршрутизируем запись соответствующему клиенту
                if not route_lead(processed_data):
                    logger.warning(f"Не удалось маршрутизировать запись: {processed_data['id']}.")
                    continue
                
                # Помечаем строку как обработанную
                if not mark_row_as_processed(i):
                    logger.warning(f"Не удалось пометить строку {i+1} как обработанную.")
                    continue
                
                logger.info(f"Запись {processed_data['id']} успешно обработана.")
                
                # Небольшая пауза между обработкой строк для снижения нагрузки на API
                time.sleep(0.2)
            
            except Exception as e:
                logger.error(f"Ошибка при обработке строки {i+1}: {e}")
                continue
        
        logger.info("Обработка новых записей завершена.")
        return True
    
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке данных: {e}")
        return False

def main():
    """
    Основная функция программы.
    """
    logger.info("Запуск системы LeadsToB24...")
    
    try:
        # Запускаем планировщик с функцией обработки новых записей
        run_scheduler(process_new_leads)
    
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 