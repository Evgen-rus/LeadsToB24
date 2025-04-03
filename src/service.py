"""
Модуль для работы с сервисами Google API.

Содержит функции для получения экземпляров сервисов Google API.
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.setup import CREDENTIALS_PATH, SCOPES, logger

def get_google_sheets_service():
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
        logger.debug("Сервис Google Sheets API успешно получен.")
        return service
    except HttpError as error:
        logger.error(f"API Error при получении сервиса Google Sheets: {error}")
        return None
    except Exception as e:
        logger.error(f"Ошибка аутентификации в Google Sheets: {e}")
        return None 