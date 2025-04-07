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
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('leads_to_b24')

# Создание логгера
logger = setup_logging() 