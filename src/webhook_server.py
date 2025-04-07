"""
Модуль веб-сервера для приема данных от поставщиков.

Реализует HTTP-сервер для приема данных через POST-запросы напрямую от поставщиков
и сохранения их в базу данных для последующей обработки и маршрутизации.
"""
import json
from flask import Flask, request, jsonify
from datetime import datetime
import logging
import re
import os
import sys
from pathlib import Path

# Настраиваем путь для импорта модулей из корневой директории проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.setup import logger, LOG_DIR
from src.db import init_db, insert_lead
from src.processor import clean_project_tag, validate_phone, parse_datetime
from src.router import route_lead

# Создаем приложение Flask
app = Flask(__name__)

# Настраиваем логгирование Flask
flask_log_path = Path(LOG_DIR) / 'webhook_server.log'
flask_handler = logging.FileHandler(flask_log_path)
flask_handler.setLevel(logging.INFO)
flask_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app.logger.addHandler(flask_handler)
app.logger.setLevel(logging.INFO)

def process_incoming_data(data):
    """
    Обрабатывает входящие данные от поставщика.
    
    Args:
        data (dict): Данные, полученные от поставщика
    
    Returns:
        dict: Результат обработки, содержащий статус и дополнительные данные
    """
    try:
        # Проверяем наличие необходимых полей
        required_fields = ['created_at', 'id', 'phone', 'project_tag']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {
                'success': False,
                'message': f'Отсутствуют обязательные поля: {", ".join(missing_fields)}'
            }
        
        # Валидируем и обрабатываем данные
        created_at = parse_datetime(data['created_at'])
        if not created_at:
            return {
                'success': False,
                'message': f'Некорректная дата создания: {data["created_at"]}'
            }
        
        cleaned_phone = validate_phone(data['phone'])
        if not cleaned_phone:
            return {
                'success': False,
                'message': f'Некорректный телефон: {data["phone"]}'
            }
        
        cleaned_tag = clean_project_tag(data['project_tag'])
        
        # Формируем данные для сохранения
        processed_data = {
            'created_at': created_at,
            'id': data['id'],
            'phone': cleaned_phone,
            'tag': cleaned_tag,
            'original_tag': data['project_tag']
        }
        
        # Пытаемся добавить запись в БД
        if not insert_lead(processed_data):
            # Проверка на ошибку дубликата выполняется внутри insert_lead
            return {
                'success': False,
                'message': f'Не удалось добавить запись в БД (возможно, дубликат)'
            }
        
        # Маршрутизируем запись соответствующему клиенту
        route_result = route_lead(processed_data)
        
        return {
            'success': True,
            'message': 'Данные успешно обработаны',
            'lead_id': data['id'],
            'routed': route_result
        }
    
    except Exception as e:
        logger.error(f"Ошибка при обработке входящих данных: {e}")
        return {
            'success': False,
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }

@app.route('/api/lead', methods=['POST'])
def receive_lead():
    """
    Эндпоинт для приема данных о лидах.
    
    Принимает данные в формате JSON, обрабатывает их и добавляет в БД.
    """
    try:
        # Проверяем, что получен JSON
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Ожидается JSON'
            }), 400
        
        # Получаем данные из запроса
        data = request.get_json()
        
        # Логируем полученные данные
        app.logger.info(f"Получены данные: {json.dumps(data, ensure_ascii=False)}")
        
        # Обрабатываем данные
        result = process_incoming_data(data)
        
        # Возвращаем результат
        if result['success']:
            return jsonify(result), 201
        else:
            app.logger.warning(f"Ошибка обработки: {result['message']}")
            return jsonify(result), 400
    
    except Exception as e:
        app.logger.error(f"Ошибка при обработке запроса: {e}")
        return jsonify({
            'success': False,
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Эндпоинт для проверки работоспособности сервера.
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }), 200

@app.route('/api/simulate', methods=['GET'])
def simulation_form():
    """
    Эндпоинт для отображения формы симуляции отправки данных.
    
    Используется для тестирования API без реальных запросов от поставщика.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Симулятор отправки лидов</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            label { display: block; margin-top: 10px; }
            input, textarea { width: 100%; padding: 8px; margin-top: 5px; }
            button { margin-top: 20px; padding: 10px 15px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #45a049; }
            pre { background-color: #f8f8f8; padding: 10px; border-radius: 5px; overflow-x: auto; }
            .response { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Симулятор отправки лидов</h1>
        <p>Используйте эту форму для тестирования приема данных от поставщика.</p>
        
        <form id="leadForm">
            <label for="created_at">Дата создания (формат: YYYY-MM-DD HH:MM:SS):</label>
            <input type="text" id="created_at" name="created_at" value="" placeholder="2025-04-03 15:37:53">
            
            <label for="id">ID:</label>
            <input type="text" id="id" name="id" value="" placeholder="1316458786">
            
            <label for="phone">Телефон:</label>
            <input type="text" id="phone" name="phone" value="" placeholder="79172700941">
            
            <label for="project_tag">Тег проекта:</label>
            <input type="text" id="project_tag" name="project_tag" value="" placeholder="B3_[ДМД13] Диалог Чанган Казань">
            
            <button type="submit">Отправить</button>
        </form>
        
        <div class="response">
            <h2>Ответ сервера:</h2>
            <pre id="response">Здесь будет отображен ответ сервера...</pre>
        </div>
        
        <script>
            document.getElementById('leadForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                var created_at = document.getElementById('created_at').value || getCurrentDateTime();
                document.getElementById('created_at').value = created_at;
                
                var formData = {
                    created_at: created_at,
                    id: document.getElementById('id').value || generateRandomId(),
                    phone: document.getElementById('phone').value || generateRandomPhone(),
                    project_tag: document.getElementById('project_tag').value
                };
                
                fetch('/api/lead', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('response').textContent = JSON.stringify(data, null, 2);
                })
                .catch((error) => {
                    document.getElementById('response').textContent = 'Ошибка: ' + error;
                });
            });
            
            function getCurrentDateTime() {
                var now = new Date();
                return now.getFullYear() + '-' + 
                       String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                       String(now.getDate()).padStart(2, '0') + ' ' + 
                       String(now.getHours()).padStart(2, '0') + ':' + 
                       String(now.getMinutes()).padStart(2, '0') + ':' + 
                       String(now.getSeconds()).padStart(2, '0');
            }
            
            function generateRandomId() {
                return Math.floor(Math.random() * 9000000000) + 1000000000;
            }
            
            function generateRandomPhone() {
                return '7' + (Math.floor(Math.random() * 900000000) + 100000000);
            }
        </script>
    </body>
    </html>
    """
    return html

def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    Запускает веб-сервер.
    
    Args:
        host (str): Хост для прослушивания
        port (int): Порт для прослушивания
        debug (bool): Режим отладки
    """
    # Инициализируем базу данных перед запуском
    if not init_db():
        logger.error("Ошибка инициализации базы данных. Сервер не будет запущен.")
        return False
    
    logger.info(f"Запуск веб-сервера на {host}:{port}")
    app.run(host=host, port=port, debug=debug)
    return True

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Сервер для приема данных от поставщиков')
    parser.add_argument('--host', default='0.0.0.0', help='Хост для прослушивания')
    parser.add_argument('--port', type=int, default=5000, help='Порт для прослушивания')
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug) 