"""
Модуль обработки данных из таблицы.

Отвечает за очистку и подготовку данных перед записью в БД.
"""
import re
from datetime import datetime
from src.setup import COLUMN_INDICES, logger

def clean_project_tag(tag):
    """
    Очищает тег проекта от префикса и хвоста.
    
    Args:
        tag (str): Исходное значение тега, например "B1_[П8] Неометрия Ростов_new"
    
    Returns:
        str: Очищенный тег, например "[П8] Неометрия Ростов"
    """
    try:
        # Удаляем префикс вида "B1_" или "В2_"
        clean_tag = re.sub(r'^[BВ]\d+_', '', tag)
        
        # Удаляем хвост после второго подчёркивания (если есть)
        parts = clean_tag.split('_', 2)
        if len(parts) >= 3:
            clean_tag = '_'.join(parts[:2])
        
        # Удаляем пробелы в начале и конце строки и убеждаемся, что тег не содержит лишних пробелов
        clean_tag = clean_tag.strip()
        
        # Логируем преобразование тега для отладки
        logger.debug(f"Исходный тег: '{tag}', очищенный тег: '{clean_tag}'")
        
        return clean_tag
    except Exception as e:
        logger.error(f"Ошибка при очистке тега '{tag}': {e}")
        return tag

def validate_phone(phone):
    """
    Проверяет и форматирует номер телефона.
    
    Args:
        phone (str): Номер телефона, например "79991234567"
    
    Returns:
        str: Отформатированный номер телефона или пустая строка, если формат неверный
    """
    try:
        # Удаляем все нецифровые символы
        digits_only = re.sub(r'\D', '', str(phone))
        
        # Проверяем, что номер соответствует формату "79XXXXXXXXX"
        if re.match(r'^7\d{10}$', digits_only):
            return digits_only
        else:
            logger.warning(f"Некорректный формат телефона: {phone}")
            return ""
    except Exception as e:
        logger.error(f"Ошибка при валидации телефона '{phone}': {e}")
        return ""

def parse_datetime(date_str):
    """
    Преобразует строку даты в объект datetime.
    
    Args:
        date_str (str): Строка даты в формате "YYYY-MM-DD HH:MM:SS"
    
    Returns:
        datetime: Объект datetime или None в случае ошибки
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Ошибка при парсинге даты '{date_str}': {e}")
        return None

def process_row(row):
    """
    Обрабатывает строку данных из таблицы.
    
    Args:
        row (list): Список значений ячеек строки
    
    Returns:
        dict: Словарь с обработанными данными или None, если данные некорректны
    """
    try:
        # Проверяем, что строка имеет достаточную длину
        if len(row) <= max(COLUMN_INDICES.values()):
            logger.warning(f"Недостаточно данных в строке: {row}")
            return None
        
        # Получаем значения из соответствующих колонок
        created_at_str = row[COLUMN_INDICES['created_at']]
        row_id = row[COLUMN_INDICES['id']]
        phone = row[COLUMN_INDICES['phone']]
        project_tag = row[COLUMN_INDICES['project_tag']]
        
        # Валидируем и обрабатываем данные
        created_at = parse_datetime(created_at_str)
        if not created_at:
            logger.warning(f"Некорректная дата создания: {created_at_str}")
            return None
        
        cleaned_phone = validate_phone(phone)
        if not cleaned_phone:
            logger.warning(f"Некорректный телефон: {phone}")
            return None
        
        cleaned_tag = clean_project_tag(project_tag)
        
        # Формируем результат
        return {
            'created_at': created_at,
            'id': row_id,
            'phone': cleaned_phone,
            'tag': cleaned_tag,
            'original_tag': project_tag
        }
    
    except Exception as e:
        logger.error(f"Ошибка при обработке строки {row}: {e}")
        return None

def check_for_new_rows(service, sheet_id, sheet_name, force_process=False):
    """
    Проверяет наличие новых строк в таблице.
    
    Args:
        service: Сервис Google Sheets API
        sheet_id (str): ID таблицы Google Sheets
        sheet_name (str): Название листа
        force_process (bool): Игнорировать статус обработки
    
    Returns:
        list: Список необработанных строк или пустой список
    """
    try:
        # Формируем запрос для получения всего листа
        sheet_range = f"{sheet_name}!A2:I"
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
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
            if force_process or row[COLUMN_INDICES['already_sent']] != '✅':
                new_rows.append(row)
        
        logger.info(f"Найдено {len(new_rows)} необработанных строк.")
        return new_rows
    
    except Exception as e:
        logger.error(f"Ошибка при проверке новых строк: {e}")
        return []

def process_sheet_data(service, rows):
    """
    Обрабатывает данные из Google Sheet и маршрутизирует лиды.
    
    Args:
        service: Сервис Google Sheets API
        rows (list): Список строк с данными
    
    Returns:
        int: Количество успешно обработанных строк
    """
    from src.db import insert_lead, lead_exists
    from src.router import route_lead
    from src.setup import SOURCE_SPREADSHEET_ID as SHEET_ID, SOURCE_SHEET_NAME as SHEET_NAME
    
    success_count = 0
    
    for i, row in enumerate(rows):
        try:
            # Обрабатываем данные строки
            processed_data = process_row(row)
            if not processed_data:
                logger.warning(f"Не удалось обработать строку {i+1}.")
                continue
            
            # Проверяем, существует ли запись в БД
            if lead_exists(processed_data['id']):
                logger.warning(f"Запись {processed_data['id']} уже существует в БД.")
                
                # Помечаем строку как обработанную
                update_range = f"{SHEET_NAME}!I{i + 2}"
                body = {
                    'values': [['✅']]
                }
                service.spreadsheets().values().update(
                    spreadsheetId=SHEET_ID,
                    range=update_range,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                continue
            
            # Добавляем запись в БД
            if not insert_lead(processed_data):
                logger.warning(f"Не удалось добавить запись в БД: {processed_data['id']}.")
                continue
            
            # Маршрутизируем запись соответствующему клиенту
            if not route_lead(processed_data):
                logger.warning(f"Не удалось маршрутизировать запись: {processed_data['id']}.")
                continue
            
            # Помечаем строку как обработанную
            update_range = f"{SHEET_NAME}!I{i + 2}"
            body = {
                'values': [['✅']]
            }
            service.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=update_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Запись {processed_data['id']} успешно обработана.")
            success_count += 1
            
        except Exception as e:
            logger.error(f"Ошибка при обработке строки {i+1}: {e}")
            continue
    
    return success_count 