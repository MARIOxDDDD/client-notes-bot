import telebot
from telebot import types
import sqlite3
import pandas as pd
import os

# 🔐 Ваш токен
TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
bot = telebot.TeleBot(TOKEN)

# 📦 База данных
conn = sqlite3.connect('clients.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    description TEXT
)
''')
conn.commit()

# 📍 Хранение состояний
user_state = {}
temp_data = {}

# 🔘 Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "🔍 Найти")
    markup.add("📋 Список клиентов", "✏️ Редактировать")
    markup.add("❌ Удалить клиента", "📤 Экспорт")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

# ➕ Добавление клиента
@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def add_client_start(message):
    user_state[message.chat.id] = "add_name"
    temp_data[message.chat.id] = {}
    bot.send_message(message.chat.id, "Введите имя клиента:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "add_name")
def add_phone(message):
    temp_data[message.chat.id]['name'] = message.text
    user_state[message.chat.id] = "add_phone"
    bot.send_message(message.chat.id, "Введите номер телефона:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "add_phone")
def add_description(message):
    temp_data[message.chat.id]['phone'] = message.text
    user_state[message.chat.id] = "add_description"
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "add_description")
def save_client(message):
    temp_data[message.chat.id]['description'] = message.text
    data = temp_data.pop(message.chat.id)
    user_state.pop(message.chat.id)

    cursor.execute("INSERT INTO clients (name, phone, description) VALUES (?, ?, ?)",
                   (data['name'], data['phone'], data['description']))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Клиент успешно добавлен!", reply_markup=main_menu())

# 🔍 Поиск
@bot.message_handler(func=lambda m: m.text == "🔍 Найти")
def search_start(message):
    user_state[message.chat.id] = "search"
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "search")
def search_client(message):
    query = message.text
    cursor.execute("SELECT * FROM clients WHERE phone LIKE ?", (f"%{query}",))
    results = cursor.fetchall()
    user_state.pop(message.chat.id, None)

    if results:
        for row in results:
            bot.send_message(message.chat.id, f"👤 {row[1]}\n📱 {row[2]}\n✏️ {row[3]}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

# 📋 Список всех
@bot.message_handler(func=lambda m: m.text == "📋 Список клиентов")
def list_clients(message):
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    if clients:
        for client in clients:
            bot.send_message(message.chat.id, f"👤 {client[1]}\n📱 {client[2]}\n✏️ {client[3]}")
    else:
        bot.send_message(message.chat.id, "📭 Клиенты отсутствуют.")

# ✏️ Редактирование
@bot.message_handler(func=lambda m: m.text == "✏️ Редактировать")
def edit_start(message):
    user_state[message.chat.id] = "edit_number"
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "edit_number")
def edit_choose_field(message):
    query = message.text
    cursor.execute("SELECT * FROM clients WHERE phone LIKE ?", (f"%{query}",))
    results = cursor.fetchall()

    if results:
        temp_data[message.chat.id] = {"id": results[0][0]}
        user_state[message.chat.id] = "edit_field"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Имя", "Телефон", "Описание")
        bot.send_message(message.chat.id, "Что вы хотите изменить?", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
        user_state.pop(message.chat.id, None)

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "edit_field")
def edit_value(message):
    temp_data[message.chat.id]["field"] = message.text.lower()
    user_state[message.chat.id] = "edit_value"
    bot.send_message(message.chat.id, "Введите новое значение:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "edit_value")
def apply_edit(message):
    client_id = temp_data[message.chat.id]["id"]
    field = temp_data[message.chat.id]["field"]
    value = message.text
    field_map = {"имя": "name", "телефон": "phone", "описание": "description"}

    if field in field_map:
        cursor.execute(f"UPDATE clients SET {field_map[field]} = ? WHERE id = ?", (value, client_id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Данные обновлены!", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "❌ Неверное поле.")
    
    user_state.pop(message.chat.id, None)
    temp_data.pop(message.chat.id, None)

# ❌ Удаление клиента
@bot.message_handler(func=lambda m: m.text == "❌ Удалить клиента")
def delete_start(message):
    user_state[message.chat.id] = "delete"
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "delete")
def delete_client(message):
    query = message.text
    cursor.execute("DELETE FROM clients WHERE phone LIKE ?", (f"%{query}",))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Клиент удалён (если был найден).", reply_markup=main_menu())
    user_state.pop(message.chat.id, None)

# 📤 Экспорт
@bot.message_handler(func=lambda m: m.text == "📤 Экспорт")
def export_clients(message):
    cursor.execute("SELECT * FROM clients")
    data = cursor.fetchall()
    if not data:
        bot.send_message(message.chat.id, "📭 Нет данных для экспорта.")
        return

    df = pd.DataFrame(data, columns=["ID", "Имя", "Телефон", "Описание"])
    path = f"clients_export_{message.chat.id}.xlsx"
    df.to_excel(path, index=False)

    with open(path, "rb") as f:
        bot.send_document(message.chat.id, f)

    os.remove(path)

# 🚀 Запуск
print("Бот запущен...")
bot.infinity_polling()
