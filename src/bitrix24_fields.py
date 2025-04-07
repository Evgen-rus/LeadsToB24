"""
Модуль для получения и анализа полей Битрикс24.

Позволяет получить список доступных полей и их параметров через API Битрикс24.
"""
import requests

def get_crm_fields(webhook_url):
    # URL для получения полей лида
    url = f"{webhook_url}/crm.lead.fields.json"

    try:
        response = requests.get(url)
        response.raise_for_status() # Проверка на наличие ошибок

        fields = response.json().get('result', {})
        return fields

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None

# Замените на ваш URL вебхука
webhook_url = "https://b24-2l18k6.bitrix24.ru/rest/1/g2io5xchou3u0t17/"

fields = get_crm_fields(webhook_url)
if fields:
    for field_id, field_info in fields.items():
        print(f"ID поля: {field_id}, Название: {field_info.get('title')}, Тип: {field_info.get('type')}")