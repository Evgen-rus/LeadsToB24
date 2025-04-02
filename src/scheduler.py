"""
Модуль планировщика задач.

Отвечает за планирование и выполнение периодических задач.
"""
import time
import schedule
import threading

from src.setup import CHECK_INTERVAL, logger

def run_scheduler(job_function):
    """
    Запускает планировщик с заданной функцией.
    
    Args:
        job_function (callable): Функция, которая будет выполняться по расписанию
    """
    # Настраиваем расписание
    schedule.every(CHECK_INTERVAL).minutes.do(job_function)
    
    logger.info(f"Планировщик настроен на запуск каждые {CHECK_INTERVAL} минут.")
    
    # Запускаем задачу сразу при старте
    logger.info("Выполняем первоначальную проверку...")
    job_function()
    
    # Бесконечный цикл для выполнения запланированных задач
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
            time.sleep(60)  # Пауза перед повторной попыткой в случае ошибки

def run_scheduler_background(job_function):
    """
    Запускает планировщик в отдельном потоке.
    
    Args:
        job_function (callable): Функция, которая будет выполняться по расписанию
    
    Returns:
        Thread: Объект потока с планировщиком
    """
    scheduler_thread = threading.Thread(target=run_scheduler, args=(job_function,))
    scheduler_thread.daemon = True  # Поток будет автоматически завершен при выходе из программы
    scheduler_thread.start()
    
    logger.info("Планировщик запущен в фоновом режиме.")
    return scheduler_thread 