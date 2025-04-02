"""
Модуль для работы с Google Sheets.

Отвечает за чтение данных из исходной таблицы и обновление статусов обработки.
"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.setup import (
    CREDENTIALS_PATH, SCOPES, SOURCE_SPREADSHEET_ID, 
    SOURCE_SHEET_NAME, COLUMN_INDICES, logger
)

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

def get_new_rows():
    """
    Получает строки из исходной таблицы, которые еще не были обработаны.
    
    Returns:
        list: Список строк с данными или пустой список в случае ошибки.
    """
    try:
        service = get_sheets_service()
        if not service:
            return []
        
        # Формируем запрос для получения всего листа
        sheet_range = f"{SOURCE_SHEET_NAME}!A2:I"
        result = service.spreadsheets().values().get(
            spreadsheetId=SOURCE_SPREADSHEET_ID,
            range=sheet_range
        ).execute()
        
        rows = result.get('values', [])
        if not rows:
            logger.info("В таблице не найдено данных.")
            return []
        
        # Фильтруем строки, у которых нет отметки в колонке "Already sent"
        new_rows = []
        for row in rows:
            # Проверяем, что строка имеет достаточную длину
            if len(row) <= COLUMN_INDICES['already_sent']:
                # Добавляем пустые элементы, если строка короче ожидаемой
                row.extend([''] * (COLUMN_INDICES['already_sent'] + 1 - len(row)))
                
            # Проверяем наличие отметки в колонке "Already sent"
            if row[COLUMN_INDICES['already_sent']] != '✅':
                new_rows.append(row)
        
        logger.info(f"Найдено {len(new_rows)} необработанных строк.")
        return new_rows
    
    except HttpError as error:
        logger.error(f"Ошибка при получении данных из Google Sheets: {error}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении данных: {e}")
        return []

def mark_row_as_processed(row_index):
    """
    Помечает строку в исходной таблице как обработанную.
    
    Args:
        row_index (int): Индекс строки в таблице (начиная с 0 для данных, 
                          реальный индекс в таблице будет row_index + 2)
    
    Returns:
        bool: True, если обновление прошло успешно, иначе False.
    """
    try:
        service = get_sheets_service()
        if not service:
            return False
        
        # Формируем запрос на обновление ячейки
        range_name = f"{SOURCE_SHEET_NAME}!I{row_index + 2}"
        body = {
            'values': [['✅']]
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=SOURCE_SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Строка {row_index + 2} помечена как обработанная.")
        return True
    
    except HttpError as error:
        logger.error(f"Ошибка при обновлении статуса строки {row_index + 2}: {error}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обновлении статуса: {e}")
        return False 