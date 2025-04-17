"""
Скрипт для получения и вывода информации о полях из AmoCRM.
Позволяет узнать ID полей, статусов и пользователей для использования при отправке лидов.
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv
from amo.field_manager import (
    refresh_all_caches, 
    get_lead_fields,
    get_contact_fields, 
    get_company_fields,
    get_pipelines,
    get_users,
    find_field_id,
    find_status_id,
    find_user_id
)

# Настраиваем логирование
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/amo_fields.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('amo_get_fields')

# Загружаем переменные окружения
load_dotenv()

def print_json(data):
    """Печать JSON в удобном формате"""
    print(json.dumps(data, ensure_ascii=False, indent=2))

def print_fields(entity_type):
    """
    Вывод всех полей сущности
    
    Args:
        entity_type (str): Тип сущности ('leads', 'contacts', 'companies')
    """
    print(f"\n=== Поля для {entity_type} ===")
    
    if entity_type == 'leads':
        fields_data = get_lead_fields()
    elif entity_type == 'contacts':
        fields_data = get_contact_fields()
    elif entity_type == 'companies':
        fields_data = get_company_fields()
    else:
        print(f"Неизвестный тип сущности: {entity_type}")
        return
    
    if not fields_data or '_embedded' not in fields_data or 'custom_fields' not in fields_data['_embedded']:
        print(f"Не удалось получить данные о полях для {entity_type}")
        return
    
    # Выводим все поля в формате 'ID: Название'
    for field in fields_data['_embedded']['custom_fields']:
        print(f"{field['id']}: {field.get('name', '???')}")

def print_pipelines():
    """Вывод всех воронок и их статусов"""
    print("\n=== Воронки и статусы ===")
    
    pipelines_data = get_pipelines()
    
    if not pipelines_data or '_embedded' not in pipelines_data or 'pipelines' not in pipelines_data['_embedded']:
        print("Не удалось получить данные о воронках")
        return
    
    # Выводим все воронки и их статусы
    for pipeline in pipelines_data['_embedded']['pipelines']:
        print(f"\nВоронка: {pipeline['id']} - {pipeline.get('name', '???')}")
        
        if '_embedded' in pipeline and 'statuses' in pipeline['_embedded']:
            print("  Статусы:")
            for status in pipeline['_embedded']['statuses']:
                print(f"    {status['id']}: {status.get('name', '???')}")
        else:
            print("  Статусы не найдены")

def print_users():
    """Вывод всех пользователей"""
    print("\n=== Пользователи ===")
    
    users_data = get_users()
    
    if not users_data or '_embedded' not in users_data or 'users' not in users_data['_embedded']:
        print("Не удалось получить данные о пользователях")
        return
    
    # Выводим всех пользователей
    for user in users_data['_embedded']['users']:
        full_name = f"{user.get('name', '')} {user.get('last_name', '')}"
        print(f"{user['id']}: {full_name} ({user.get('email', '')})")

def find_field(args):
    """
    Поиск поля по имени
    
    Args:
        args (list): Аргументы командной строки в формате [entity_type, field_name]
    """
    if len(args) < 2:
        print("Не указаны тип сущности и название поля")
        print("Использование: python amo_get_fields.py field leads телефон")
        return
    
    entity_type = args[0]
    field_name = args[1]
    
    field_id = find_field_id(entity_type, field_name)
    if field_id:
        print(f"Найдено поле: {field_id} ({field_name})")
    else:
        print(f"Поле '{field_name}' не найдено")

def find_status(args):
    """
    Поиск статуса по имени
    
    Args:
        args (list): Аргументы командной строки в формате [pipeline_id, status_name]
    """
    if len(args) < 2:
        print("Не указаны ID воронки и название статуса")
        print("Использование: python amo_get_fields.py status 6375467 Новый")
        return
    
    pipeline_id = args[0]
    status_name = args[1]
    
    status_id = find_status_id(pipeline_id, status_name)
    if status_id:
        print(f"Найден статус: {status_id} ({status_name})")
    else:
        print(f"Статус '{status_name}' не найден в воронке {pipeline_id}")

def find_user(args):
    """
    Поиск пользователя по имени
    
    Args:
        args (list): Аргументы командной строки - имя пользователя
    """
    if len(args) < 1:
        print("Не указано имя пользователя")
        print("Использование: python amo_get_fields.py user Admin")
        return
    
    user_name = args[0]
    
    user_id = find_user_id(user_name)
    if user_id:
        print(f"Найден пользователь: {user_id} ({user_name})")
    else:
        print(f"Пользователь '{user_name}' не найден")

def main():
    """Основная функция скрипта"""
    if len(sys.argv) < 2:
        print("""
Использование:
  python amo_get_fields.py refresh       - Обновить все кэши
  python amo_get_fields.py leads         - Показать поля лидов
  python amo_get_fields.py contacts      - Показать поля контактов
  python amo_get_fields.py companies     - Показать поля компаний
  python amo_get_fields.py pipelines     - Показать воронки и статусы
  python amo_get_fields.py users         - Показать пользователей
  python amo_get_fields.py field [entity_type] [field_name] - Найти ID поля по имени
  python amo_get_fields.py status [pipeline_id] [status_name] - Найти ID статуса по имени
  python amo_get_fields.py user [user_name] - Найти ID пользователя по имени
        """)
        return 0
    
    command = sys.argv[1]
    
    if command == 'refresh':
        print("Обновление всех кэшей...")
        refresh_all_caches()
        print("Кэши обновлены")
    
    elif command == 'leads':
        print_fields('leads')
    
    elif command == 'contacts':
        print_fields('contacts')
    
    elif command == 'companies':
        print_fields('companies')
    
    elif command == 'pipelines':
        print_pipelines()
    
    elif command == 'users':
        print_users()
    
    elif command == 'field':
        find_field(sys.argv[2:])
    
    elif command == 'status':
        find_status(sys.argv[2:])
    
    elif command == 'user':
        find_user(sys.argv[2:])
    
    else:
        print(f"Неизвестная команда: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())