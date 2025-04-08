"""
Модуль для получения и анализа полей Битрикс24.

Позволяет получить список доступных полей и их параметров через API Битрикс24.
"""
import requests
import json

def get_crm_fields(webhook_url):
    """
    Получает список полей лида из Bitrix24
    """
    # Убираем /crm.lead.add.json из URL если есть
    base_url = webhook_url.split('/crm.')[0]
    
    # URL для получения полей лида
    url = f"{base_url}/crm.lead.fields.json"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на наличие ошибок

        fields = response.json().get('result', {})
        
        # Выводим поля в более читаемом виде
        print("\nДоступные поля лида в Bitrix24:")
        print("-" * 50)
        for field_name, field_info in fields.items():
            print(f"\nПоле: {field_name}")
            print(f"Тип: {field_info.get('type', 'Не указан')}")
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

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None

def print_field_details(webhook_url, field_name):
    """
    Выводит детальную информацию о конкретном поле
    """
    fields = get_crm_fields(webhook_url)
    if fields and field_name in fields:
        print(f"\nДетальная информация о поле {field_name}:")
        print(json.dumps(fields[field_name], indent=2, ensure_ascii=False))
    else:
        print(f"Поле {field_name} не найдено")

# Замените на ваш URL вебхука
webhook_url = "https://b24-2l18k6.bitrix24.ru/rest/1/g2io5xchou3u0t17/"

fields = get_crm_fields(webhook_url)
if fields:
    for field_id, field_info in fields.items():
        print(f"ID поля: {field_id}, Название: {field_info.get('title')}, Тип: {field_info.get('type')}")