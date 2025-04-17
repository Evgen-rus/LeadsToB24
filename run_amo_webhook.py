"""
Скрипт для запуска вебхук-сервера AmoCRM.
Обрабатывает входящие запросы и отправляет лиды в AmoCRM.
"""
import os
import logging
from dotenv import load_dotenv
from amo.webhook_handler import run_webhook_server

# Настраиваем логирование
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/webhook_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('amo_webhook')

# Загружаем переменные окружения
load_dotenv()

if __name__ == "__main__":
    # Получаем настройки из .env или используем значения по умолчанию
    host = os.getenv('WEBHOOK_HOST', '0.0.0.0')
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    
    logger.info(f"Запуск сервера AmoCRM вебхуков на {host}:{port}")
    
    try:
        run_webhook_server(host=host, port=port)
    except Exception as e:
        logger.exception(f"Ошибка запуска сервера: {e}") 