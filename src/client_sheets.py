"""
Модуль для работы с таблицами клиентов.

Отвечает за отправку данных в Google таблицы клиентов.
"""
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.setup import CREDENTIALS_PATH, SCOPES, logger

def send_to_client_sheet(client_config, lead_data):
    """
    Отправляет данные лида в Google таблицу клиента.
    
    Args:
        client_config (dict): Конфигурация клиента
        lead_data (dict): Данные о лиде
    
    Returns:
        bool: True, если отправка прошла успешно, иначе False
    """
    try:
        # Проверяем наличие необходимых настроек клиента
        if not client_config.get('spreadsheet_id') or not client_config.get('sheet_name'):
            logger.warning(f"Для клиента {client_config.get('name')} не настроена Google таблица.")
            return False
        
        # Получаем сервис для работы с Google Sheets
        service = get_sheets_service()
        if not service:
            return False
        
        # Подготавливаем данные для добавления в таблицу
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [
            now,  # Дата отправки
            lead_data.get('created_at').strftime("%Y-%m-%d %H:%M:%S"),  # Дата создания лида
            lead_data.get('id'),  # ID лида
            lead_data.get('phone'),  # Телефон
            lead_data.get('tag')  # Тег проекта
        ]
        
        # Определяем диапазон для добавления данных
        sheet_range = f"{client_config['sheet_name']}!A:E"
        
        # Получаем текущее количество строк в таблице
        result = service.spreadsheets().values().get(
            spreadsheetId=client_config['spreadsheet_id'],
            range=sheet_range
        ).execute()
        
        rows = result.get('values', [])
        next_row = len(rows) + 1  # Индекс новой строки
        
        # Формируем запрос на добавление строки
        body = {
            'values': [row_data]
        }
        
        # Обновляем диапазон с учетом номера строки
        update_range = f"{client_config['sheet_name']}!A{next_row}:E{next_row}"
        
        # Отправляем данные в таблицу
        result = service.spreadsheets().values().update(
            spreadsheetId=client_config['spreadsheet_id'],
            range=update_range,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Данные лида {lead_data.get('id')} успешно отправлены в таблицу клиента {client_config.get('name')}.")
        return True
    
    except HttpError as error:
        logger.error(f"Ошибка Google API при отправке данных в таблицу клиента: {error}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке данных в таблицу клиента: {e}")
        return False

def get_sheets_service():
    """
    Создаёт и возвращает сервис для работы с Google Sheets API.
    
    Returns:
        Объект сервиса Google Sheets API или None в случае ошибки.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Ошибка аутентификации в Google Sheets: {e}")
        return None

def check_client_sheet_access(spreadsheet_id, sheet_name):
    """
    Проверяет доступность таблицы клиента и наличие указанного листа.
    
    Args:
        spreadsheet_id (str): ID таблицы
        sheet_name (str): Имя листа
    
    Returns:
        bool: True, если таблица и лист доступны, иначе False
    """
    try:
        service = get_sheets_service()
        if not service:
            return False
        
        # Получаем информацию о таблице
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        # Проверяем наличие указанного листа
        sheets = spreadsheet.get('sheets', [])
        sheet_exists = False
        
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name:
                sheet_exists = True
                break
        
        if not sheet_exists:
            logger.warning(f"Лист '{sheet_name}' не найден в таблице {spreadsheet_id}.")
            return False
        
        # Проверяем права доступа, пытаясь прочитать данные
        service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1:A1"
        ).execute()
        
        logger.info(f"Таблица {spreadsheet_id}, лист '{sheet_name}' доступны.")
        return True
    
    except HttpError as error:
        logger.error(f"Ошибка доступа к таблице {spreadsheet_id}: {error}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке доступа к таблице: {e}")
        return False 