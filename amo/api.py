"""
Модуль для работы с API AmoCRM.
Содержит базовые функции для отправки запросов.
Использует долгосрочный токен, не требующий обновления.
"""
import os
import json
import time
import logging
import requests
from requests.exceptions import RequestException
from . import auth

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/amo.log'
)
logger = logging.getLogger('amo.api')
logger.setLevel(logging.DEBUG)

# Добавляем вывод логов в консоль для отладки
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Создаем директорию для логов, если ее нет
if not os.path.exists('logs'):
    os.makedirs('logs')

def get_headers():
    """
    Формирует заголовки для запросов к API
    
    Returns:
        dict: Заголовки с токеном авторизации
    """
    token = auth.get_amo_token()
    logger.debug(f"Получен токен для запроса (первые 5 символов): {token[:5] if token else 'нет'}...")
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'amoCRM-oAuth-client/1.0'
    }

def get_url(path):
    """
    Формирует URL для запроса к API
    
    Args:
        path (str): Путь API
        
    Returns:
        str: Полный URL
    """
    base_domain = auth.get_amo_domain()
    api_domain = auth.get_amo_api_domain()
    return f'https://{api_domain}.{base_domain}/api/v4/{path}'

def retry_request(func, max_retries=3, delay=1):
    """
    Декоратор для повторных попыток выполнения запроса
    
    Args:
        func: Функция для выполнения
        max_retries (int): Максимальное количество попыток
        delay (int): Задержка между попытками в секундах
        
    Returns:
        Результат выполнения функции или None в случае всех неудачных попыток
    """
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except (RequestException, TimeoutError) as e:
                retries += 1
                if retries == max_retries:
                    logger.error(f"Исчерпаны все попытки ({max_retries}). Последняя ошибка: {e}")
                    return None
                logger.warning(f"Попытка {retries}/{max_retries} не удалась: {e}. Повторная попытка через {delay} сек.")
                time.sleep(delay)
        return None
    return wrapper

@retry_request
def make_request(method, url, params=None, data=None, timeout=30):
    """
    Выполняет запрос к API AmoCRM
    
    Args:
        method (str): HTTP метод (GET, POST, PATCH, DELETE)
        url (str): URL запроса
        params (dict, optional): Параметры запроса
        data (dict, optional): Данные для отправки в теле запроса
        timeout (int, optional): Таймаут запроса в секундах
    
    Returns:
        dict: Ответ от API в формате JSON или None в случае ошибки
    """
    headers = get_headers()
    
    # Логируем детали запроса
    logger.debug(f"API запрос: {method} {url}")
    logger.debug(f"Заголовки: {headers}")
    logger.debug(f"Параметры: {params}")
    if data:
        # Ограничиваем вывод данных, чтобы не перегружать логи
        if isinstance(data, dict):
            log_data = {k: (v[:100] + '...' if isinstance(v, str) and len(v) > 100 else v) 
                        for k, v in data.items()}
        elif isinstance(data, list):
            log_data = f"Список из {len(data)} элементов"
        else:
            log_data = str(data)[:200] + '...' if len(str(data)) > 200 else data
        logger.debug(f"Данные: {log_data}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=timeout, verify=True)
        elif method == 'POST':
            response = requests.post(url, headers=headers, params=params, json=data, timeout=timeout, verify=True)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, params=params, json=data, timeout=timeout, verify=True)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=timeout, verify=True)
        else:
            logger.error(f"Неизвестный метод запроса: {method}")
            return None
        
        # Логируем ответ
        logger.debug(f"Статус ответа: {response.status_code}")
        logger.debug(f"Заголовки ответа: {dict(response.headers)}")
        
        # Обработка rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            logger.warning(f"Достигнут лимит запросов. Ожидание {retry_after} секунд")
            time.sleep(retry_after)
            # Рекурсивно повторяем запрос
            return make_request(method, url, params, data, timeout)
            
        # Проверяем статус ответа
        if response.status_code in (200, 201, 204):
            try:
                # Для ответов без контента
                if response.status_code == 204 or not response.text:
                    logger.info(f"Успешный запрос без данных: {method} {url}")
                    return {}
                
                # Парсим JSON
                result = response.json()
                logger.debug(f"Тело ответа: {result}")
                
                # Проверяем, содержит ли ответ данные
                if not result:
                    logger.warning(f"Пустой ответ от API: {method} {url}")
                    return {}
                
                # Логируем краткую информацию о результате
                if isinstance(result, dict):
                    if '_embedded' in result and isinstance(result['_embedded'], dict):
                        for key, value in result['_embedded'].items():
                            if isinstance(value, list):
                                logger.debug(f"Получено {len(value)} элементов в {key}")
                            else:
                                logger.debug(f"Получены данные в {key}")
                    else:
                        logger.debug(f"Получен ответ с ключами: {list(result.keys())}")
                elif isinstance(result, list):
                    logger.debug(f"Получен список из {len(result)} элементов")
                
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования JSON: {e}")
                logger.debug(f"Текст ответа: {response.text[:200]}...")
                return None
        else:
            # Логируем ошибки
            logger.error(f"Ошибка {response.status_code}: {method} {url}")
            try:
                error_data = response.json()
                logger.error(f"Детали ошибки: {error_data}")
            except Exception:
                logger.error(f"Текст ошибки: {response.text[:200]}...")
            
            # Проверяем, истек ли токен
            if response.status_code == 401:
                logger.warning("Ошибка авторизации (401). Проверьте правильность токена и домена.")
            
            return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Таймаут запроса: {e}")
        return None
    except RequestException as e:
        logger.error(f"Ошибка сетевого запроса: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при выполнении запроса: {e}")
        return None

# Обертки для разных типов запросов
def get(path, params=None):
    """GET запрос к API"""
    url = get_url(path)
    return make_request('GET', url, params)

def post(path, data, params=None):
    """POST запрос к API"""
    url = get_url(path)
    return make_request('POST', url, params, data)

def patch(path, data, params=None):
    """PATCH запрос к API"""
    url = get_url(path)
    return make_request('PATCH', url, params, data)

def delete(path, params=None):
    """DELETE запрос к API"""
    url = get_url(path)
    return make_request('DELETE', url, params)
