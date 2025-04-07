#!/usr/bin/env python
"""
Скрипт для запуска веб-сервера, принимающего входящие данные.

Этот скрипт запускает Flask-сервер, который принимает POST-запросы от поставщиков
и направляет их в систему LeadsToB24 для обработки и маршрутизации.
"""
from src.webhook_server import run_server
from src.client_config import load_clients
from src.setup import logger

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Сервер для приема данных от поставщиков')
    parser.add_argument('--host', default='0.0.0.0', help='Хост для прослушивания')
    parser.add_argument('--port', type=int, default=5000, help='Порт для прослушивания')
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    
    args = parser.parse_args()
    
    logger.info("Запуск сервера для приема данных от поставщиков")
    
    # Загружаем информацию о клиентах
    if not load_clients():
        logger.error("Не удалось загрузить информацию о клиентах. Сервер не будет запущен.")
        exit(1)
    
    # Запускаем сервер
    run_server(host=args.host, port=args.port, debug=args.debug) 