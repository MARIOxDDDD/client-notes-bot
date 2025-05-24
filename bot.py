from telebot import TeleBot, types
import psycopg2
import pandas as pd
import os
from datetime import datetime

TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
bot = TeleBot(TOKEN)

# Подключение к PostgreSQL
conn = psycopg2.connect("postgresql://client_notes_db_user:ujSU0BBRQ6swQwzRLwZ315LFWmYomGcn@dpg-d0p2rnuuk2gs7398b9s0-a/client_notes_db")
cursor = conn.cursor()

# Создание таблицы, если нет
cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id SERIAL PRIMARY KEY,
        name TEXT,
        phone TEXT,
        comment TEXT
    )
''')
conn.commit()

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Добавить", "🔍 Найти")
    markup.row("📋 Список клиентов", "✏️ Редактировать", "❌ Удалить")
    markup.row("📤 Экспорт")
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

# Состояния
user_state = {}
temp_data = {}

@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить")
def add_client(message):
    user_state[message.chat.id] = "add_name"
    bot.send_message(message.chat.id, "Введите имя клиента:")

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == "add_name")
def add_name(message):
    temp_data[message.chat.id] = {"name": message.text}
    user_state[message.chat.id] = "add_phone"
    bot.send_message(message.chat.id, "Введите номер телефона:")

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == "add_phone")
def add_phone(message):
    temp_data[message.chat.id]["phone"] = message.text
    user_state[message.chat.id] = "add_comment"
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == "add_comment")
def add_comment(message):
    data = temp_data.pop(message.chat.id)
    data["comment"] = message.text
    cursor.execute("INSERT INTO clients (name, phone, comment) VALUES (%s, %s, %s)",
                   (data["name"], data["phone"], data["comment"]))
    conn.commit()
    user_state.pop(message.chat.id)
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: msg.text == "🔍 Найти")
def find_client(message):
    user_state[message.chat.id] = "find"
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == "find")
def do_find(message):
    digits = message.text[-4:]
    cursor.execute("SELECT name, phone, comment FROM clients WHERE phone LIKE %s", ('%' + digits,))
    results = cursor.fetchall()
    user_state.pop(message.chat.id)

    if results:
        for row in results:
            bot.send_message(message.chat.id, f"👤 {row[0]}\n📞 {row[1]}\n💬 {row[2]}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

@bot.message_handler(func=lambda msg: msg.text == "📋 Список клиентов")
def list_clients(message):
    cursor.execute("SELECT name, phone FROM clients")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "Список пуст.")
    else:
        reply = "\n\n".join([f"👤 {name} — 📞 {phone}" for name, phone in rows])
        bot.send_message(message.chat.id, reply)

@bot.message_handler(func=lambda msg: msg.text == "📤 Экспорт")
def export_clients(message):
    cursor.execute("SELECT name, phone, comment FROM clients")
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "Нет данных для экспорта.")
        return

    df = pd.DataFrame(rows, columns=["Имя", "Телефон", "Комментарий"])
    filename = f"clients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)

    with open(filename, "rb") as file:
        bot.send_document(message.chat.id, file)

    os.remove(filename)

# Заглушки для будущих функций
@bot.message_handler(func=lambda msg: msg.text == "✏️ Редактировать")
def edit_placeholder(message):
    bot.send_message(message.chat.id, "🔧 Функция редактирования пока в разработке.")

@bot.message_handler(func=lambda msg: msg.text == "❌ Удалить")
def delete_placeholder(message):
    bot.send_message(message.chat.id, "🗑️ Функция удаления пока в разработке.")

# Запуск
print("Бот запущен.")
bot.polling(none_stop=True)
