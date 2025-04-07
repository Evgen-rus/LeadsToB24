#!/usr/bin/env python
"""
Скрипт для обновления тега клиента в базе данных.
"""
import sqlite3
import sys

# Подключение к базе данных
conn = sqlite3.connect('database/leads.db')
cursor = conn.cursor()

# Выводим список клиентов до обновления
print("Список клиентов до обновления:")
cursor.execute('SELECT id, name, tag FROM clients')
clients = cursor.fetchall()
for client in clients:
    print(f"ID: {client[0]}, Имя: {client[1]}, Тег: {client[2]}")

# Обновляем тег клиента с именем, содержащим "анган"
cursor.execute('UPDATE clients SET tag = ? WHERE name LIKE ?', 
               ("[ДМД13] Диалог Чанган Казань", "%анган%"))
conn.commit()

# Выводим список клиентов после обновления
print("\nСписок клиентов после обновления:")
cursor.execute('SELECT id, name, tag FROM clients')
clients = cursor.fetchall()
for client in clients:
    print(f"ID: {client[0]}, Имя: {client[1]}, Тег: {client[2]}")

# Закрываем соединение
conn.close()

print("\nТег клиента успешно обновлен.") 