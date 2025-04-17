"""
Модуль авторизации в AmoCRM.
Используется для получения и обновления токенов.
"""
import os
import json
import time
import logging
import requests
from dotenv import load_dotenv

# Настраиваем логирование на более подробный уровень
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/amo.log'
)
logger = logging.getLogger('amo.auth')
logger.setLevel(logging.DEBUG)

# Добавляем вывод логов в консоль для отладки
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Загружаем переменные окружения
load_dotenv()

# Параметры из .env
AMO_CLIENT_ID = os.getenv('AMO_CLIENT_ID')
AMO_CLIENT_SECRET = os.getenv('AMO_CLIENT_SECRET')
AMO_TOKEN = os.getenv('AMO_TOKEN')
AMO_BASE_DOMAIN = os.getenv('AMO_BASE_DOMAIN')
AMO_API_DOMAIN = os.getenv('AMO_API_DOMAIN')
AMO_ACCOUNT_ID = os.getenv('AMO_ACCOUNT_ID')
# Проверяем, является ли токен долгосрочным
AMO_LONG_TERM_TOKEN = True if AMO_TOKEN and len(AMO_TOKEN) > 40 else False

# Проверяем наличие всех необходимых параметров
logger.debug("Проверка параметров авторизации:")
logger.debug(f"AMO_CLIENT_ID: {'Задан' if AMO_CLIENT_ID else 'Не задан'}")
logger.debug(f"AMO_CLIENT_SECRET: {'Задан' if AMO_CLIENT_SECRET else 'Не задан'}")
logger.debug(f"AMO_TOKEN: {'Задан' if AMO_TOKEN else 'Не задан'} (первые 20 символов: {AMO_TOKEN[:20] if AMO_TOKEN else 'нет'}...)")
logger.debug(f"AMO_BASE_DOMAIN: {AMO_BASE_DOMAIN}")
logger.debug(f"AMO_API_DOMAIN: {AMO_API_DOMAIN}")
logger.debug(f"AMO_ACCOUNT_ID: {AMO_ACCOUNT_ID}")
logger.debug(f"Тип токена: {'Долгосрочный' if AMO_LONG_TERM_TOKEN else 'Обычный'}")

# Файл для хранения токенов
TOKEN_FILE = 'amo/tokens.json'

def get_token():
    """
    Получение текущего токена доступа.
    
    Если используется долгосрочный токен, всегда возвращается токен из .env
    Если используется обычный токен, то проверяется его актуальность и при необходимости токен обновляется
    
    Returns:
        str: Токен доступа к API
    """
    logger.debug("Запрос токена доступа")
    
    # Если используется долгосрочный токен из .env, всегда возвращаем его
    if AMO_LONG_TERM_TOKEN and AMO_TOKEN:
        logger.info("Используется долгосрочный токен из .env")
        return AMO_TOKEN
    
    # Если указан обычный токен в .env, используем его
    if AMO_TOKEN:
        logger.info("Используется токен из .env")
        return AMO_TOKEN
    
    # Иначе пробуем использовать сохраненный токен
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                
            # Если токен действителен, возвращаем его
            if tokens.get('expires_at', 0) > time.time():
                logger.info("Используется сохраненный токен")
                return tokens.get('access_token')
                
            # Если токен истек, обновляем его
            logger.info("Токен истек, обновляем")
            refresh_token = tokens.get('refresh_token')
            if refresh_token:
                return refresh_access_token(refresh_token)
        except Exception as e:
            logger.error(f"Ошибка при чтении токенов: {e}")
    else:
        logger.debug(f"Файл токенов не найден: {TOKEN_FILE}")
    
    # Если нет файла с токенами или возникла ошибка, возвращаем токен из .env
    logger.warning("Используется токен из .env (нет сохраненных токенов)")
    return AMO_TOKEN

def refresh_access_token(refresh_token):
    """
    Обновление токена доступа по refresh_token
    
    Args:
        refresh_token (str): Токен для обновления
    
    Returns:
        str: Новый токен доступа
    """
    # Если используется долгосрочный токен, не пытаемся его обновить
    if AMO_LONG_TERM_TOKEN:
        logger.info("Используется долгосрочный токен, обновление не требуется")
        return AMO_TOKEN
        
    logger.debug(f"Попытка обновления токена с refresh_token: {refresh_token[:10]}...")
    
    try:
        refresh_data = {
            'client_id': AMO_CLIENT_ID,
            'client_secret': AMO_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'redirect_uri': 'https://leadrecordwh.ru/'
        }
        
        logger.debug(f"Отправка запроса обновления токена на https://{AMO_BASE_DOMAIN}/oauth2/access_token")
        
        response = requests.post(
            f'https://{AMO_BASE_DOMAIN}/oauth2/access_token', 
            json=refresh_data
        )
        
        logger.debug(f"Статус ответа: {response.status_code}")
        
        tokens = response.json()
        logger.debug(f"Ответ: {tokens}")
        
        if 'access_token' in tokens and 'refresh_token' in tokens:
            # Сохраняем время истечения токена
            tokens['expires_at'] = time.time() + tokens.get('expires_in', 86400)
            
            # Сохраняем токены в файл
            with open(TOKEN_FILE, 'w') as f:
                json.dump(tokens, f)
                
            logger.info("Токен успешно обновлен")
            return tokens['access_token']
        else:
            logger.error(f"Ошибка обновления токена: {tokens}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сетевого запроса при обновлении токена: {e}")
    except ValueError as e:
        logger.error(f"Ошибка парсинга JSON при обновлении токена: {e}")
        logger.debug(f"Текст ответа: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Исключение при обновлении токена: {e}")
    
    # В случае ошибки возвращаем токен из .env
    logger.warning("Возвращается токен из .env из-за ошибки обновления")
    return AMO_TOKEN 