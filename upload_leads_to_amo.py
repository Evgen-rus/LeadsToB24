"""
Скрипт для загрузки лидов из Excel-файла в AmoCRM.
Основные функции:
1. Выбор Excel файла через диалоговое окно
2. Чтение телефонов из файла
3. Отправка лидов в AmoCRM
"""

# Импорт необходимых библиотек
import time  # Для создания задержек между запросами
import sys   # Для работы с путями и системными функциями
import os    # Для работы с файловой системой
from typing import Dict, Any, List, Tuple  # Для типизации данных
import pandas as pd  # Для работы с Excel файлами
from tkinter import Tk, filedialog  # Для создания диалогового окна выбора файла
import logging

# Импортируем функции для работы с AmoCRM
from create_lead import create_lead_with_phone

# Настраиваем логирование
if not os.path.exists('logs'):
    os.makedirs('logs')
    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/upload_leads.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('upload_leads')

def read_leads_from_excel(file_path: str) -> List[str]:
    """
    Читает телефоны лидов из Excel-файла.
    
    Args:
        file_path (str): Путь к Excel-файлу с телефонами
        
    Returns:
        List[str]: Список телефонов для создания лидов
    """
    phones = []
    try:
        # Читаем Excel-файл в pandas DataFrame
        df = pd.read_excel(file_path)
        
        # Проверяем наличие обязательной колонки 'Телефон'
        required_columns = ['Телефон']
        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"В файле отсутствует колонка '{column}'")
        
        # Проходим по каждой строке Excel файла
        for index, row in df.iterrows():
            # Получаем телефон и убираем лишние пробелы
            phone = str(row['Телефон']).strip()
            
            # Пропускаем пустые строки и строки с nan (Not a Number)
            if phone and phone.lower() != 'nan':
                # Убираем .0 из номера, если телефон был распознан как число
                phone = phone.replace('.0', '')
                
                phones.append(phone)
                    
        logger.info(f"Прочитано {len(phones)} телефонов из файла")
        return phones
        
    except Exception as e:
        logger.error(f"Ошибка при чтении Excel-файла: {e}")
        return []

def upload_leads_to_amo(phones: List[str]) -> None:
    """
    Загружает лиды в AmoCRM.
    
    Args:
        phones (List[str]): Список телефонов для создания лидов
    """
    total = len(phones)  # Общее количество лидов
    success = 0  # Счетчик успешно созданных лидов
    
    # Проходим по каждому телефону
    for index, phone in enumerate(phones, 1):
        try:
            # Отправляем лид в AmoCRM
            lead_id, contact_id = create_lead_with_phone(phone)
            
            if lead_id:
                success += 1
                print(f"Успешно создан лид {index}/{total}: {phone} (ID лида: {lead_id}, ID контакта: {contact_id})")
            elif contact_id:
                print(f"Создан только контакт {index}/{total}: {phone} (ID контакта: {contact_id})")
            else:
                print(f"Не удалось создать лид {index}/{total}: {phone}")
            
            # Пауза 1 секунда между запросами, чтобы не перегрузить API AmoCRM
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Ошибка при создании лида с телефоном {phone}: {e}")
            print(f"Ошибка при создании лида с телефоном {phone}: {e}")
    
    # Выводим итоговую статистику
    print(f"\nЗагрузка завершена. Успешно: {success}/{total}")

def select_excel_file() -> str:
    """
    Открывает диалоговое окно для выбора Excel файла.
    
    Returns:
        str: Путь к выбранному файлу или пустая строка, если файл не выбран
    """
    # Создаем корневое окно Tkinter
    root = Tk()
    root.withdraw()  # Скрываем основное окно
    root.attributes('-topmost', True)  # Окно выбора файла будет поверх других окон
    
    # Открываем диалог выбора файла
    file_path = filedialog.askopenfilename(
        title="Выберите Excel файл с телефонами",
        filetypes=[("Excel files", "*.xlsx *.xls")],  # Только Excel файлы
        initialdir=os.path.dirname(os.path.abspath(__file__))  # Начальная директория
    )
    
    root.destroy()  # Закрываем окно Tkinter
    return file_path

def main():
    """
    Основная функция для запуска загрузки лидов.
    Последовательность действий:
    1. Выбор Excel файла через диалоговое окно
    2. Проверка существования файла
    3. Чтение телефонов из файла
    4. Показ примера первых трех телефонов
    5. Подтверждение загрузки
    6. Загрузка лидов в AmoCRM
    """
    # Открываем диалог выбора файла
    file_path = select_excel_file()
    
    # Проверяем, был ли выбран файл
    if not file_path:
        print("Файл не выбран. Загрузка отменена.")
        return
    
    # Проверяем существование файла
    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        return
    
    # Читаем телефоны из файла
    phones = read_leads_from_excel(file_path)
    
    if phones:
        # Показываем информацию о найденных телефонах
        print(f"Найдено {len(phones)} телефонов.")
        print("\nПример первых 3 телефонов:")
        for i, phone in enumerate(phones[:3]):
            print(f"{i+1}. {phone}")
        print("-" * 50)
            
        # Запрашиваем подтверждение на загрузку
        print("\nНачать загрузку лидов в AmoCRM? (y/n)")
        if input().lower() == 'y':
            upload_leads_to_amo(phones)
        else:
            print("Загрузка отменена")
    else:
        print("Не найдено телефонов для загрузки")

# Точка входа в программу
if __name__ == "__main__":
    main() 