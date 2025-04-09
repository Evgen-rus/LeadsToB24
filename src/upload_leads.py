"""
Скрипт для загрузки лидов из Excel-файла в Битрикс24.
"""
import time
import sys
import os
from typing import Dict, Any
import pandas as pd

# Добавляем родительскую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bitrix24 import send_to_bitrix24
from src.setup import logger

def read_leads_from_excel(file_path: str) -> list[Dict[str, Any]]:
    """
    Читает данные лидов из Excel-файла.
    
    Args:
        file_path (str): Путь к Excel-файлу с лидами
        
    Returns:
        list[Dict[str, Any]]: Список словарей с данными лидов
    """
    leads = []
    try:
        # Читаем Excel-файл
        df = pd.read_excel(file_path)
        
        # Проверяем наличие необходимых колонок
        required_columns = ['Телефон']
        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"В файле отсутствует колонка '{column}'")
        
        # Проходим по каждой строке
        for index, row in df.iterrows():
            # Получаем телефон и убираем лишние символы
            phone = str(row['Телефон']).strip()
            
            # Пропускаем пустые строки и строки с nan
            if phone and phone.lower() != 'nan':
                # Убираем точку из номера, если это float
                phone = phone.replace('.0', '')
                
                # Формируем данные лида
                lead_data = {
                    'phone': phone,
                    'SOURCE_ID': '106',
                    'STATUS_ID': 'UC_LF7L5W',
                    'ASSIGNED_BY_ID': '20140'
                }
                
                leads.append(lead_data)
                    
        logger.info(f"Прочитано {len(leads)} лидов из файла")
        return leads
        
    except Exception as e:
        print(f"Ошибка при чтении Excel-файла: {e}")
        return []

def upload_leads_to_bitrix(leads: list[Dict[str, Any]], config: Dict[str, str]) -> None:
    """
    Загружает лиды в Битрикс24.
    
    Args:
        leads (list[Dict[str, Any]]): Список лидов для загрузки
        config (Dict[str, str]): Конфигурация для подключения к Битрикс24
    """
    total = len(leads)
    success = 0
    
    for index, lead in enumerate(leads, 1):
        try:
            # Отправляем лид в Битрикс24
            if send_to_bitrix24(lead, config):
                success += 1
                print(f"Успешно создан лид {index}/{total}: {lead['phone']}")
            else:
                print(f"Не удалось создать лид {index}/{total}: {lead['phone']}")
            
            # Делаем паузу между запросами, чтобы не перегрузить API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Ошибка при создании лида {lead['phone']}: {e}")
    
    print(f"\nЗагрузка завершена. Успешно: {success}/{total}")

def main():
    """
    Основная функция для запуска загрузки лидов.
    """
    # Excel-файл с лидами
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "09.04.2025.xlsx")
    
    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        return
    
    # Конфигурация для подключения к Битрикс24
    config = {
        'webhook_url': 'https://supermet.bitrix24.ru/rest/3900/bq745g4ngowz4z43/crm.lead.add.json' #битрикс супермет
    }
    
    # Читаем лиды из файла
    leads = read_leads_from_excel(file_path)
    
    if leads:
        print(f"Найдено {len(leads)} лидов.")
        print("\nПример первых 3 лидов:")
        for lead in leads[:3]:
            print(f"- Телефон: {lead['phone']}")
            print("-" * 50)
            
        print("\nНачать загрузку? (y/n)")
        if input().lower() == 'y':
            upload_leads_to_bitrix(leads, config)
        else:
            print("Загрузка отменена")
    else:
        print("Не найдено лидов для загрузки")

if __name__ == "__main__":
    main() 