"""
Модуль для обработки входящих вебхуков и отправки лидов в AmoCRM.
"""
import json
import logging
from flask import Flask, request, jsonify
from . import lead
from . import field_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/webhook.log'
)
logger = logging.getLogger('amo.webhook')

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Простая страница для проверки работы вебхука"""
    return "AmoCRM Webhook сервер работает!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Обработчик входящих вебхуков.
    Принимает данные о лиде и отправляет их в AmoCRM.
    
    Ожидаемый формат JSON:
    {
        "name": "Имя клиента",
        "phone": "+79001234567",
        "email": "example@mail.com",
        "source": "Источник лида",
        "comment": "Комментарий к лиду",
        "status": "Название статуса",
        "responsible": "Имя ответственного",
        "custom_fields": {
            "field_id_1": "значение_1",
            "field_id_2": "значение_2"
        }
    }
    
    Returns:
        json: Результат обработки запроса
    """
    try:
        # Получаем данные из запроса
        data = request.json
        logger.info(f"Получен вебхук: {json.dumps(data, ensure_ascii=False)}")
        
        if not data:
            logger.warning("Получен пустой запрос")
            return jsonify({"status": "error", "message": "Отсутствуют данные"}), 400
        
        # Формируем данные для AmoCRM
        lead_data = {
            'name': data.get('name', 'Новый лид'),
            'custom_fields_values': []
        }
        
        # Добавляем телефон
        if 'phone' in data and data['phone']:
            phone_field_id = field_manager.find_field_id('leads', 'телефон')
            if phone_field_id:
                lead_data['custom_fields_values'].append({
                    'field_id': phone_field_id,
                    'values': [{'value': data['phone']}]
                })
        
        # Добавляем email
        if 'email' in data and data['email']:
            email_field_id = field_manager.find_field_id('leads', 'email')
            if email_field_id:
                lead_data['custom_fields_values'].append({
                    'field_id': email_field_id,
                    'values': [{'value': data['email']}]
                })
        
        # Добавляем источник
        if 'source' in data and data['source']:
            source_field_id = field_manager.find_field_id('leads', 'источник')
            if source_field_id:
                lead_data['custom_fields_values'].append({
                    'field_id': source_field_id,
                    'values': [{'value': data['source']}]
                })
        
        # Добавляем комментарий
        if 'comment' in data and data['comment']:
            comment_field_id = field_manager.find_field_id('leads', 'комментарий')
            if comment_field_id:
                lead_data['custom_fields_values'].append({
                    'field_id': comment_field_id,
                    'values': [{'value': data['comment']}]
                })
        
        # Устанавливаем статус
        if 'status' in data and data['status']:
            # Получаем первую воронку (или можно указать конкретную)
            pipelines = field_manager.get_pipelines()
            if pipelines and '_embedded' in pipelines and 'pipelines' in pipelines['_embedded']:
                pipeline_id = pipelines['_embedded']['pipelines'][0]['id']
                status_id = field_manager.find_status_id(pipeline_id, data['status'])
                if status_id:
                    lead_data['status_id'] = status_id
        
        # Устанавливаем ответственного
        if 'responsible' in data and data['responsible']:
            user_id = field_manager.find_user_id(data['responsible'])
            if user_id:
                lead_data['responsible_user_id'] = user_id
        
        # Добавляем пользовательские поля
        if 'custom_fields' in data and isinstance(data['custom_fields'], dict):
            for field_id, value in data['custom_fields'].items():
                lead_data['custom_fields_values'].append({
                    'field_id': int(field_id),
                    'values': [{'value': value}]
                })
        
        # Отправляем лид в AmoCRM
        result = lead.create_lead(lead_data)
        
        if result:
            logger.info(f"Лид успешно отправлен в AmoCRM: {result}")
            return jsonify({
                "status": "success", 
                "message": "Лид успешно создан",
                "lead_id": result.get('_embedded', {}).get('leads', [{}])[0].get('id')
            }), 200
        else:
            logger.error("Ошибка создания лида в AmoCRM")
            return jsonify({"status": "error", "message": "Ошибка создания лида"}), 500
            
    except Exception as e:
        logger.exception(f"Ошибка обработки вебхука: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run_webhook_server(host='0.0.0.0', port=5000):
    """
    Запуск сервера для обработки вебхуков
    
    Args:
        host (str): Хост для запуска сервера
        port (int): Порт для запуска сервера
    """
    # Обновляем кэш полей при запуске
    try:
        field_manager.refresh_all_caches()
        logger.info("Кэш полей AmoCRM обновлен")
    except Exception as e:
        logger.error(f"Ошибка обновления кэша полей: {e}")
    
    app.run(host=host, port=port)

if __name__ == '__main__':
    run_webhook_server() 