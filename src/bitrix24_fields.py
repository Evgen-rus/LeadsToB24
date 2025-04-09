"""
Модуль для получения и анализа полей Битрикс24.

Позволяет получить список доступных полей и их параметров через API Битрикс24.
Документация: https://apidocs.bitrix24.ru/api-reference/crm/leads/
"""
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

class Bitrix24API:
    """Класс для работы с API Битрикс24"""
    
    def __init__(self, webhook_url: str):
        """
        Инициализация клиента API
        
        Args:
            webhook_url (str): URL вебхука Битрикс24
        """
        self.webhook_url = webhook_url.rstrip('/')
        
    def _make_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """
        Выполняет запрос к API Битрикс24
        
        Args:
            method (str): Метод API (например, 'crm.lead.fields')
            params (Dict, optional): Параметры запроса
            
        Returns:
            Dict: Ответ от API
            
        Raises:
            requests.exceptions.RequestException: При ошибке запроса
        """
        url = f"{self.webhook_url}/{method}"
        try:
            response = requests.post(url, json=params) if params else requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении запроса {method}: {e}")
            print(f"URL запроса: {url}")
            if hasattr(response, 'text'):
                print(f"Ответ сервера: {response.text[:500]}...")
            raise

    def get_lead_fields(self) -> Dict[str, Any]:
        """
        Получает список полей лида
        
        Returns:
            Dict[str, Any]: Словарь с описанием полей лида
        """
        try:
            result = self._make_request('crm.lead.fields')
            fields = result.get('result', {})
            
            print("\nДоступные поля лида в Bitrix24:")
            print("-" * 50)
            
            for field_name, field_info in fields.items():
                print(f"\nПоле: {field_name}")
                print(f"Тип: {field_info.get('type', 'Не указан')}")
                print(f"Название: {field_info.get('title', 'Не указано')}")
                
                if field_info.get('isRequired'):
                    print("Обязательное: Да")
                if field_info.get('isReadOnly'):
                    print("Только для чтения: Да")
                if field_info.get('isMultiple'):
                    print("Множественное: Да")
                    
                if 'items' in field_info:
                    print("Возможные значения:")
                    for item in field_info['items']:
                        print(f"  - {item.get('ID')}: {item.get('VALUE')}")
                        
            return fields
            
        except Exception as e:
            print(f"Ошибка при получении полей лида: {e}")
            return {}

    def get_field_info(self, field_name: str) -> None:
        """
        Выводит детальную информацию о конкретном поле
        
        Args:
            field_name (str): Имя поля
        """
        try:
            fields = self.get_lead_fields()
            if field_name in fields:
                print(f"\nДетальная информация о поле {field_name}:")
                print(json.dumps(fields[field_name], indent=2, ensure_ascii=False))
            else:
                print(f"Поле {field_name} не найдено")
        except Exception as e:
            print(f"Ошибка при получении информации о поле: {e}")

def main():
    """Основная функция для тестирования API"""
    # Webhook URL
    #webhook_url = "https://b24-2l18k6.bitrix24.ru/rest/1/g2io5xchou3u0t17/"  # б24 для теста
    webhook_url = "https://supermet.bitrix24.ru/rest/3900/bq745g4ngowz4z43/"  # битрикс супермет
    
    try:
        # Создаем экземпляр API клиента
        bitrix24 = Bitrix24API(webhook_url)
        
        # Получаем все поля лида
        print("Получение полей лида...")
        fields = bitrix24.get_lead_fields()
        
        if fields:
            print("\nСписок всех полей:")
            print("-" * 30)
            for field_id, field_info in fields.items():
                print(f"ID: {field_id}")
                print(f"Название: {field_info.get('title', 'Не указано')}")
                print(f"Тип: {field_info.get('type', 'Не указан')}")
                print("-" * 30)
                
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()