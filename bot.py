from flask import Flask, request
import telebot
import psycopg2
import pandas as pd
from telebot import types
from datetime import datetime
from waitress import serve

# === КОНФИГ ===
TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
DATABASE_URL = "postgresql://client_notes_db_user:ujSU0BBRQ6swQwzRLwZ315LFWmYomGcn@dpg-d0p2rnuuk2gs7398b9s0-a/client_notes_db"
WEBHOOK_URL = f"https://client-notes-bot.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === БАЗА ДАННЫХ ===
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name TEXT,
    phone TEXT,
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")
conn.commit()

user_states = {}

# === МЕНЮ ===
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "🔍 Найти")
    markup.add("📋 Список клиентов", "📤 Экспорт")
    markup.add("📝 Редактировать", "❌ Удалить")
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

# === ДОБАВИТЬ КЛИЕНТА ===
@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def add_client(message):
    bot.send_message(message.chat.id, "Введите имя клиента:")
    user_states[message.chat.id] = {"step": "name"}

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "name")
def step_name(message):
    user_states[message.chat.id]["name"] = message.text
    user_states[message.chat.id]["step"] = "phone"
    bot.send_message(message.chat.id, "Введите номер телефона:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "phone")
def step_phone(message):
    user_states[message.chat.id]["phone"] = message.text
    user_states[message.chat.id]["step"] = "comment"
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "comment")
def step_comment(message):
    state = user_states.pop(message.chat.id)
    cur.execute("INSERT INTO clients (name, phone, comment) VALUES (%s, %s, %s)",
                (state["name"], state["phone"], message.text))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=main_menu())

# === ПОИСК ===
@bot.message_handler(func=lambda m: m.text == "🔍 Найти")
def find_client(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")
    user_states[message.chat.id] = {"step": "find"}

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "find")
def step_find(message):
    query = f"%{message.text}"
    cur.execute("SELECT name, phone, comment FROM clients WHERE phone LIKE %s", (query,))
    results = cur.fetchall()
    user_states.pop(message.chat.id, None)

    if results:
        for r in results:
            bot.send_message(message.chat.id, f"👤 {r[0]}\n📞 {r[1]}\n💈 {r[2]}")
    else:
        bot.send_message(message.chat.id, "❌ Клиентов не найдено.")

# === СПИСОК КЛИЕНТОВ ===
@bot.message_handler(func=lambda m: m.text == "📋 Список клиентов")
def list_clients(message):
    cur.execute("SELECT name, phone, comment FROM clients ORDER BY created_at DESC LIMIT 10")
    clients = cur.fetchall()
    if clients:
        for c in clients:
            bot.send_message(message.chat.id, f"👤 {c[0]}\n📞 {c[1]}\n💈 {c[2]}")
    else:
        bot.send_message(message.chat.id, "Список пуст.")

# === ЭКСПОРТ ===
@bot.message_handler(func=lambda m: m.text == "📤 Экспорт")
def export_clients(message):
    cur.execute("SELECT name, phone, comment, created_at FROM clients")
    data = cur.fetchall()
    df = pd.DataFrame(data, columns=["Имя", "Телефон", "Комментарий", "Дата"])
    file_path = "clients_export.xlsx"
    df.to_excel(file_path, index=False)

    with open(file_path, "rb") as file:
        bot.send_document(message.chat.id, file)

# === РЕДАКТИРОВАНИЕ ===
@bot.message_handler(func=lambda m: m.text == "📝 Редактировать")
def start_edit(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    user_states[message.chat.id] = {"step": "edit_find"}

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "edit_find")
def step_edit_find(message):
    query = f"%{message.text}"
    cur.execute("SELECT id, name, phone, comment FROM clients WHERE phone LIKE %s", (query,))
    result = cur.fetchone()
    if result:
        user_states[message.chat.id] = {
            "step": "edit_name", "id": result[0]
        }
        bot.send_message(message.chat.id, f"Клиент найден:\n👤 {result[1]}\n📞 {result[2]}\n💈 {result[3]}\n\nВведите новое имя:")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
        user_states.pop(message.chat.id, None)

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "edit_name")
def edit_name(message):
    user_states[message.chat.id]["name"] = message.text
    user_states[message.chat.id]["step"] = "edit_phone"
    bot.send_message(message.chat.id, "Введите новый номер:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "edit_phone")
def edit_phone(message):
    user_states[message.chat.id]["phone"] = message.text
    user_states[message.chat.id]["step"] = "edit_comment"
    bot.send_message(message.chat.id, "Введите новый комментарий:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "edit_comment")
def edit_comment(message):
    state = user_states.pop(message.chat.id)
    cur.execute("UPDATE clients SET name=%s, phone=%s, comment=%s WHERE id=%s",
                (state["name"], state["phone"], message.text, state["id"]))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Клиент обновлён.", reply_markup=main_menu())

# === УДАЛЕНИЕ ===
@bot.message_handler(func=lambda m: m.text == "❌ Удалить")
def delete_start(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    user_states[message.chat.id] = {"step": "delete_find"}

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "delete_find")
def delete_find(message):
    query = f"%{message.text}"
    cur.execute("SELECT id, name FROM clients WHERE phone LIKE %s", (query,))
    result = cur.fetchone()
    if result:
        user_states[message.chat.id] = {"step": "confirm_delete", "id": result[0]}
        bot.send_message(message.chat.id, f"Удалить клиента {result[1]}? (да/нет)")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
        user_states.pop(message.chat.id, None)

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("step") == "confirm_delete")
def confirm_delete(message):
    if message.text.lower() == "да":
        client_id = user_states[message.chat.id]["id"]
        cur.execute("DELETE FROM clients WHERE id=%s", (client_id,))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Клиент удалён.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "❌ Отменено.", reply_markup=main_menu())
    user_states.pop(message.chat.id, None)

# === ВЕБХУК ===
bot.remove_webhook()
import time; time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Бот работает!"

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
