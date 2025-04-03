"""
Интерфейс командной строки для управления системой.

Предоставляет команды для добавления клиентов, проверки статуса и ручного запуска обработки.
"""
import argparse
import sys
import json
import os
import time
from datetime import datetime
from pathlib import Path

from src.setup import logger, SOURCE_SPREADSHEET_ID as SHEET_ID, SOURCE_SHEET_NAME as SHEET_NAME
from src.db import init_db, get_connection
from src.client_config import add_client, load_clients, add_client_to_config, get_all_clients, get_client_by_name, get_client_by_tag
from src.client_sheets import check_client_sheet_access, send_to_client_sheet
from src.webhook import test_webhook, send_to_webhook
from src.main import process_new_leads
from src.processor import process_sheet_data, check_for_new_rows
from src.service import get_google_sheets_service

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

def setup_cli():
    parser = argparse.ArgumentParser(description='Управление системой маршрутизации лидов')
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда init-db
    parser_init_db = subparsers.add_parser('init-db', help='Инициализировать базу данных')
    
    # Команда add-client
    parser_add_client = subparsers.add_parser('add-client', help='Добавить нового клиента')
    parser_add_client.add_argument('--name', required=True, help='Название клиента')
    parser_add_client.add_argument('--tag', required=True, help='Тег проекта для маршрутизации')
    parser_add_client.add_argument('--sheet-id', help='ID таблицы Google Sheets для выгрузки')
    parser_add_client.add_argument('--sheet-name', help='Название листа в таблице Google Sheets')
    parser_add_client.add_argument('--use-crm', action='store_true', help='Использовать интеграцию с CRM')
    parser_add_client.add_argument('--webhook-url', help='URL вебхука для отправки данных в CRM')
    
    # Команда process-data
    parser_process = subparsers.add_parser('process-data', help='Обработать данные из исходной таблицы')
    parser_process.add_argument('--force', action='store_true', help='Принудительно обработать все записи, игнорируя статус обработки')
    parser_process.add_argument('--verbose', action='store_true', help='Подробный вывод в процессе работы')
    
    # Команда list-clients
    parser_list = subparsers.add_parser('list-clients', help='Вывести список всех клиентов')
    parser_list.add_argument('--json', action='store_true', help='Вывести в формате JSON')
    
    # Команда run-daemon
    parser_daemon = subparsers.add_parser('run-daemon', help='Запустить процесс периодической проверки новых данных')
    parser_daemon.add_argument('--interval', type=int, default=600, help='Интервал проверки в секундах (по умолчанию 600)')
    
    # Команда delivery-status
    parser_status = subparsers.add_parser('delivery-status', help='Проверить статус доставки данных клиентам')
    parser_status.add_argument('--tag', help='Фильтр по тегу проекта')
    parser_status.add_argument('--since', help='Показать записи начиная с указанной даты (формат: YYYY-MM-DD)')
    parser_status.add_argument('--full', action='store_true', help='Показать подробную информацию по каждой записи')
    
    # Команда retry-delivery
    parser_retry = subparsers.add_parser('retry-delivery', help='Повторно отправить неотправленные данные')
    parser_retry.add_argument('--max-attempts', type=int, default=5, help='Максимальное количество попыток (по умолчанию 5)')
    parser_retry.add_argument('--tag', help='Фильтр по тегу проекта')
    parser_retry.add_argument('--target', choices=['sheet', 'crm', 'both'], default='both', 
                             help='Куда повторно отправить данные: sheet (таблицы), crm (CRM) или both (оба)')
    parser_retry.add_argument('--dry-run', action='store_true', help='Вывести список записей без фактической отправки')
    
    return parser

def handle_init_db(args):
    """Инициализирует базу данных."""
    init_db()
    print("База данных успешно инициализирована.")

def handle_add_client(args):
    """Добавляет нового клиента в конфигурацию."""
    client_config = {
        "name": args.name,
        "tag": args.tag,
        "use_sheet": bool(args.sheet_id and args.sheet_name),
        "sheet_id": args.sheet_id,
        "sheet_name": args.sheet_name,
        "use_crm": args.use_crm,
        "webhook_url": args.webhook_url
    }
    
    add_client_to_config(client_config)
    print(f"Клиент '{args.name}' с тегом '{args.tag}' успешно добавлен.")

def handle_process_data(args):
    """Обрабатывает данные из исходной таблицы."""
    if args.verbose:
        print("Получение сервиса Google Sheets...")
    
    service = get_google_sheets_service()
    if not service:
        print("Не удалось получить сервис Google Sheets.")
        return
    
    if args.verbose:
        print(f"Проверка наличия новых данных в таблице {SHEET_ID}...")
    
    new_rows = check_for_new_rows(service, SHEET_ID, SHEET_NAME, args.force)
    
    if not new_rows:
        print("Новые данные не обнаружены.")
        return
    
    print(f"Обнаружено {len(new_rows)} новых записей.")
    
    if args.verbose:
        print("Обработка данных...")
    
    success_count = process_sheet_data(service, new_rows)
    
    print(f"Обработано и маршрутизировано {success_count} из {len(new_rows)} записей.")

def handle_list_clients(args):
    """Выводит список всех клиентов."""
    clients = get_all_clients()
    
    if args.json:
        print(json.dumps(clients, indent=2, ensure_ascii=False))
        return
    
    if not clients:
        print("Клиенты не найдены.")
        return
    
    print("Список клиентов:")
    for client in clients:
        print(f"- {client['name']} (тег: {client['tag']})")
        if client.get('use_sheet'):
            print(f"  Таблица: {client.get('sheet_id')} / {client.get('sheet_name')}")
        if client.get('use_crm'):
            print(f"  Вебхук CRM: {client.get('webhook_url')}")
        print()

def handle_run_daemon(args):
    """Запускает процесс периодической проверки новых данных."""
    interval = args.interval
    
    print(f"Запуск процесса проверки новых данных с интервалом {interval} секунд.")
    print("Для остановки нажмите Ctrl+C.")
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Проверка новых данных...")
            
            service = get_google_sheets_service()
            if not service:
                print("Не удалось получить сервис Google Sheets. Повтор через 60 секунд...")
                time.sleep(60)
                continue
            
            new_rows = check_for_new_rows(service, SHEET_ID, SHEET_NAME)
            
            if not new_rows:
                print("Новые данные не обнаружены.")
            else:
                print(f"Обнаружено {len(new_rows)} новых записей.")
                success_count = process_sheet_data(service, new_rows)
                print(f"Обработано и маршрутизировано {success_count} из {len(new_rows)} записей.")
            
            print(f"Следующая проверка в {datetime.fromtimestamp(time.sleep() + interval).strftime('%H:%M:%S')}.")
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nПроцесс остановлен.")

def handle_delivery_status(args):
    """
    Проверяет статус доставки данных клиентам.
    
    Args:
        args: Аргументы командной строки
    """
    conn = get_connection()
    if not conn:
        print("Не удалось подключиться к базе данных.")
        return
    
    cursor = conn.cursor()
    
    # Строим запрос в зависимости от параметров
    query = """
    SELECT 
        id, created_at, phone, tag, original_tag,
        sheet_delivery_status, sheet_delivery_time,
        crm_delivery_status, crm_delivery_time,
        delivery_attempts
    FROM leads
    WHERE 1=1
    """
    
    params = []
    
    if args.tag:
        query += " AND tag = ?"
        params.append(args.tag)
    
    if args.since:
        try:
            # Преобразуем строку с датой в timestamp
            since_date = datetime.strptime(args.since, "%Y-%m-%d")
            query += " AND created_at >= ?"
            params.append(since_date.strftime("%Y-%m-%d"))
        except ValueError:
            print(f"Неверный формат даты: {args.since}. Используйте формат YYYY-MM-DD")
            return
    
    # Получаем данные
    cursor.execute(query, params)
    records = cursor.fetchall()
    
    if not records:
        print("Записи не найдены.")
        conn.close()
        return
    
    # Подсчитываем статистику
    total = len(records)
    sheet_delivered = sum(1 for r in records if r[5] == 'delivered')
    sheet_errors = sum(1 for r in records if r[5] and r[5].startswith('error'))
    sheet_pending = total - sheet_delivered - sheet_errors
    
    crm_delivered = sum(1 for r in records if r[7] == 'delivered')
    crm_errors = sum(1 for r in records if r[7] and r[7].startswith('error'))
    crm_pending = total - crm_delivered - crm_errors
    
    # Выводим общую статистику
    print(f"\nСтатистика доставки ({total} записей):")
    print(f"Таблицы: {sheet_delivered} доставлено, {sheet_errors} с ошибками, {sheet_pending} не отправлено")
    print(f"CRM: {crm_delivered} доставлено, {crm_errors} с ошибками, {crm_pending} не отправлено")
    
    # Если запрошен подробный вывод, показываем информацию по каждой записи
    if args.full:
        print("\nПодробная информация по записям:")
        for record in records:
            lead_id, created_at, phone, tag, original_tag, sheet_status, sheet_time, crm_status, crm_time, attempts = record
            
            print(f"\nИД: {lead_id}")
            print(f"Создан: {created_at}")
            print(f"Телефон: {phone}")
            print(f"Тег: {tag}")
            if original_tag:
                print(f"Исходный тег: {original_tag}")
            
            print(f"Статус отправки в таблицу: {sheet_status or 'не отправлено'}")
            if sheet_time:
                print(f"Время отправки в таблицу: {sheet_time}")
            
            print(f"Статус отправки в CRM: {crm_status or 'не отправлено'}")
            if crm_time:
                print(f"Время отправки в CRM: {crm_time}")
            
            print(f"Количество попыток: {attempts}")
    
    conn.close()
    
    print("\nИспользуйте команду retry-delivery для повторной отправки данных с ошибками.")

def handle_retry_delivery(args):
    """
    Повторно отправляет неотправленные данные.
    
    Args:
        args: Аргументы командной строки
    """
    conn = get_connection()
    if not conn:
        print("Не удалось подключиться к базе данных.")
        return
    
    cursor = conn.cursor()
    
    # Строим запрос в зависимости от параметров
    where_clauses = []
    params = []
    
    if args.target == 'sheet' or args.target == 'both':
        where_clauses.append("(sheet_delivery_status IS NULL OR sheet_delivery_status LIKE 'error:%')")
    
    if args.target == 'crm' or args.target == 'both':
        where_clauses.append("(crm_delivery_status IS NULL OR crm_delivery_status LIKE 'error:%')")
    
    if args.tag:
        where_clauses.append("tag = ?")
        params.append(args.tag)
    
    if args.max_attempts:
        where_clauses.append("delivery_attempts < ?")
        params.append(args.max_attempts)
    
    query = f"""
    SELECT 
        id, created_at, phone, tag, original_tag,
        sheet_delivery_status, crm_delivery_status
    FROM leads
    WHERE {" AND ".join(where_clauses)}
    """
    
    # Получаем данные
    cursor.execute(query, params)
    records = cursor.fetchall()
    
    if not records:
        print("Нет записей для повторной отправки.")
        conn.close()
        return
    
    print(f"Найдено {len(records)} записей для повторной отправки.")
    
    if args.dry_run:
        print("\nРежим симуляции. Данные не будут отправлены.")
        for record in records:
            lead_id, created_at, phone, tag, original_tag, sheet_status, crm_status = record
            print(f"\nИД: {lead_id}")
            print(f"Телефон: {phone}")
            print(f"Тег: {tag}")
            print(f"Статус отправки в таблицу: {sheet_status or 'не отправлено'}")
            print(f"Статус отправки в CRM: {crm_status or 'не отправлено'}")
        
        conn.close()
        return
    
    # Получаем сервис Google Sheets для отправки в таблицы
    service = None
    if args.target == 'sheet' or args.target == 'both':
        service = get_google_sheets_service()
        if not service and (args.target == 'sheet' or args.target == 'both'):
            print("Не удалось получить сервис Google Sheets. Отправка в таблицы будет пропущена.")
    
    # Обрабатываем каждую запись
    success_count = 0
    for record in records:
        lead_id, created_at, phone, tag, original_tag, sheet_status, crm_status = record
        
        # Получаем полные данные о лиде
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead_data_row = cursor.fetchone()
        
        if not lead_data_row:
            print(f"Не удалось получить данные для лида {lead_id}. Пропуск.")
            continue
        
        # Преобразуем строку из БД в словарь
        column_names = [description[0] for description in cursor.description]
        lead_data = {column_names[i]: lead_data_row[i] for i in range(len(column_names))}
        
        # Находим клиента по тегу
        client = get_client_by_tag(tag)
        
        if not client:
            print(f"Не найден клиент для тега {tag}. Пропуск лида {lead_id}.")
            continue
        
        # Отправка в таблицу
        sheet_success = False
        if (args.target == 'sheet' or args.target == 'both') and client.get('use_sheet') and service:
            if not sheet_status or sheet_status.startswith('error'):
                print(f"Отправка лида {lead_id} в таблицу клиента {client.get('name')}...")
                sheet_success = send_to_client_sheet(service, client, lead_data)
                if sheet_success:
                    print(f"Лид {lead_id} успешно отправлен в таблицу.")
                else:
                    print(f"Ошибка при отправке лида {lead_id} в таблицу.")
            else:
                sheet_success = True
        
        # Отправка в CRM
        crm_success = False
        if (args.target == 'crm' or args.target == 'both') and client.get('use_crm'):
            if not crm_status or crm_status.startswith('error'):
                print(f"Отправка лида {lead_id} в CRM клиента {client.get('name')}...")
                crm_success = send_to_webhook(client, lead_data)
                if crm_success:
                    print(f"Лид {lead_id} успешно отправлен в CRM.")
                else:
                    print(f"Ошибка при отправке лида {lead_id} в CRM.")
            else:
                crm_success = True
        
        if (args.target == 'sheet' and sheet_success) or \
           (args.target == 'crm' and crm_success) or \
           (args.target == 'both' and (sheet_success or crm_success)):
            success_count += 1
    
    print(f"\nУспешно обработано {success_count} из {len(records)} записей.")
    conn.close()

def process_cli_args(args):
    """Обрабатывает аргументы командной строки."""
    if args.command == 'init-db':
        handle_init_db(args)
    elif args.command == 'add-client':
        handle_add_client(args)
    elif args.command == 'process-data':
        handle_process_data(args)
    elif args.command == 'list-clients':
        handle_list_clients(args)
    elif args.command == 'run-daemon':
        handle_run_daemon(args)
    elif args.command == 'delivery-status':
        handle_delivery_status(args)
    elif args.command == 'retry-delivery':
        handle_retry_delivery(args)
    else:
        print("Не указана команда. Используйте --help для просмотра доступных команд.")

def run_cli():
    """Запускает интерфейс командной строки."""
    parser = setup_cli()
    args = parser.parse_args()
    process_cli_args(args)

if __name__ == "__main__":
    run_cli() 