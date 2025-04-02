"""
Интерфейс командной строки для управления системой.

Предоставляет команды для добавления клиентов, проверки статуса и ручного запуска обработки.
"""
import argparse
import sys

from src.setup import logger
from src.db import init_db
from src.client_config import add_client, load_clients
from src.client_sheets import check_client_sheet_access
from src.webhook import test_webhook
from src.main import process_new_leads

def add_client_command(args):
    """
    Добавляет нового клиента в систему.
    
    Args:
        args: Аргументы командной строки
    """
    logger.info(f"Добавление нового клиента: {args.name} с тегом '{args.tag}'")
    
    # Проверяем доступность таблицы, если указаны spreadsheet_id и sheet_name
    if args.spreadsheet_id and args.sheet_name:
        logger.info("Проверка доступа к таблице клиента...")
        if not check_client_sheet_access(args.spreadsheet_id, args.sheet_name):
            logger.error("Таблица недоступна или не найден указанный лист.")
            sys.exit(1)
    
    # Проверяем вебхук, если указан
    if args.use_crm and args.webhook_url:
        logger.info("Тестирование вебхука...")
        if not test_webhook(args.webhook_url):
            logger.error("Вебхук недоступен.")
            sys.exit(1)
    
    # Добавляем клиента
    client_id = add_client(
        name=args.name,
        tag=args.tag,
        spreadsheet_id=args.spreadsheet_id,
        sheet_name=args.sheet_name,
        use_crm=args.use_crm,
        webhook_url=args.webhook_url
    )
    
    if client_id:
        logger.info(f"Клиент успешно добавлен.")
    else:
        logger.error("Не удалось добавить клиента.")
        sys.exit(1)

def check_status_command(args):
    """
    Проверяет статус системы.
    
    Args:
        args: Аргументы командной строки
    """
    logger.info("Проверка статуса системы...")
    
    # Инициализируем БД (также проверяет доступность)
    if not init_db():
        logger.error("Ошибка доступа к базе данных.")
        sys.exit(1)
    
    # Загружаем информацию о клиентах
    if not load_clients():
        logger.error("Ошибка загрузки данных о клиентах.")
        sys.exit(1)
    
    # Проверяем доступность таблиц клиентов
    # Эта функция будет реализована в отдельном модуле (опционально)
    
    logger.info("Система работает нормально.")

def process_command(args):
    """
    Запускает обработку новых записей.
    
    Args:
        args: Аргументы командной строки
    """
    logger.info("Запуск ручной обработки данных...")
    
    # Вызываем функцию обработки новых записей
    result = process_new_leads()
    
    if result:
        logger.info("Обработка данных завершена успешно.")
    else:
        logger.error("Ошибка при обработке данных.")
        sys.exit(1)

def main():
    """
    Основная функция для обработки аргументов командной строки.
    """
    parser = argparse.ArgumentParser(description='Интерфейс управления системой LeadsToB24')
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда добавления клиента
    add_parser = subparsers.add_parser('add-client', help='Добавить нового клиента')
    add_parser.add_argument('--name', required=True, help='Имя клиента')
    add_parser.add_argument('--tag', required=True, help='Тег для маршрутизации')
    add_parser.add_argument('--spreadsheet-id', help='ID Google таблицы клиента')
    add_parser.add_argument('--sheet-name', help='Имя листа в таблице клиента')
    add_parser.add_argument('--use-crm', action='store_true', help='Использовать CRM')
    add_parser.add_argument('--webhook-url', help='URL вебхука для CRM')
    
    # Команда проверки статуса
    status_parser = subparsers.add_parser('status', help='Проверить статус системы')
    
    # Команда ручного запуска обработки
    process_parser = subparsers.add_parser('process', help='Запустить обработку данных')
    
    args = parser.parse_args()
    
    if args.command == 'add-client':
        add_client_command(args)
    elif args.command == 'status':
        check_status_command(args)
    elif args.command == 'process':
        process_command(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 