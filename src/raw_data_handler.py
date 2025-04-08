"""
Модуль для сохранения и обработки сырых данных от webhook.

Отвечает за сохранение входящих данных в JSON-файлы и БД.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from src.setup import logger, get_db_path
from src.db import get_connection

def save_raw_data(data):
    """
    Сохраняет сырые данные в JSON-файл и БД.
    
    Args:
        data (dict): Входящие данные от webhook
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Создаем директорию для сырых данных если её нет
        raw_data_dir = Path("logs/raw_data")
        raw_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем имя файла на основе времени
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        json_path = raw_data_dir / f"{timestamp}.json"
        
        # Сохраняем в JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'raw_data': data
            }, f, ensure_ascii=False, indent=2)
        
        # Сохраняем в БД базовую информацию для анализа
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Получаем основные поля, если они есть
            vid = data.get('vid', '')
            phones = ','.join(data.get('phones', []))
            timestamp_data = data.get('time', '')
            page = data.get('page', '')
            
            # Сохраняем запись
            cursor.execute('''
            INSERT INTO raw_webhooks 
            (timestamp, json_file, vid, phones, source_timestamp, page, raw_json)
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
            ''', (
                str(json_path),
                str(vid),
                phones,
                str(timestamp_data),
                page,
                json.dumps(data, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
        
        logger.info(f"Сырые данные сохранены в {json_path}")
        return True, f"Данные сохранены в {json_path}"
        
    except Exception as e:
        error_msg = f"Ошибка при сохранении сырых данных: {e}"
        logger.error(error_msg)
        return False, error_msg

def analyze_saved_data(start_date=None, end_date=None):
    """
    Анализирует сохраненные данные за период.
    
    Args:
        start_date (datetime, optional): Начальная дата
        end_date (datetime, optional): Конечная дата
    
    Returns:
        list: Список обработанных записей
    """
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        # Базовый запрос
        query = 'SELECT * FROM raw_webhooks'
        params = []
        
        # Добавляем фильтры по датам если они указаны
        if start_date and end_date:
            query += ' WHERE timestamp BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"Ошибка при анализе сохраненных данных: {e}")
        return [] 