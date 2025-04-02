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
CREDENTIALS_DIR = BASE_DIR / 'credentials'
DATABASE_DIR = BASE_DIR / 'database'
LOGS_DIR = BASE_DIR / 'logs'

# Настройки Google Sheets
SOURCE_SPREADSHEET_ID = os.getenv('SOURCE_SPREADSHEET_ID')
SOURCE_SHEET_NAME = os.getenv('SOURCE_SHEET_NAME')

# Путь к файлу БД
DB_PATH = os.getenv('DB_PATH')
if not DB_PATH.startswith('/'):
    DB_PATH = str(BASE_DIR / DB_PATH)

# Интервал проверки в минутах
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 10))

# Путь к файлу учетных данных сервисного аккаунта Google
CREDENTIALS_PATH = str(CREDENTIALS_DIR / 'sheets-credentials.json')

# Константы для работы с API Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Настройки колонок в исходной таблице
COLUMN_INDICES = {
    'created_at': 0,  # A
    'id': 1,          # B
    'phone': 2,       # C
    'project_tag': 4, # E
    'already_sent': 8 # I
}

# Настройки для логирования
LOG_FILE = str(LOGS_DIR / 'leads_to_b24.log')
LOG_LEVEL = logging.INFO

def setup_logging():
    """Настройка системы логирования."""
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