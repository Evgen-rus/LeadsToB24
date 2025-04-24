"""
Модуль конфигурации проекта LeadsToB24.

Загружает настройки из .env файла и предоставляет их другим модулям.
"""
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Загрузка переменных окружения из .env файла
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / 'database'
LOGS_DIR = BASE_DIR / 'logs'

# Создаем необходимые директории
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Путь к файлу БД
DB_PATH = os.getenv('DB_PATH', 'database/leads.db')
if not DB_PATH.startswith('/'):
    DB_PATH = str(BASE_DIR / DB_PATH)

def get_db_path():
    """
    Возвращает путь к файлу базы данных.
    
    Returns:
        str: Абсолютный путь к файлу БД
    """
    return DB_PATH

# Настройки для логирования
LOG_FILE = str(LOGS_DIR / 'leads_to_b24.log')
LOG_LEVEL = logging.INFO

def setup_logging():
    """
    Настройка системы логирования.
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Создаем логгер
    logger = logging.getLogger('leads_to_b24')
    logger.setLevel(LOG_LEVEL)
    
    # Форматтер для логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Файловый handler - записывает все логи
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Консольный handler - только важные сообщения
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    
    # Фильтр для консоли - пропускаем только сообщения о создании лидов
    class LeadCreationFilter(logging.Filter):
        def filter(self, record):
            return "Был создан лид в Битрикс24" in record.getMessage()
    
    console_handler.addFilter(LeadCreationFilter())
    logger.addHandler(console_handler)
    
    return logger

# Создание логгера
logger = setup_logging() 