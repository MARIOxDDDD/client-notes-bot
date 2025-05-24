import telebot
from telebot import types
from flask import Flask, request
from waitress import serve
import psycopg2
import pandas as pd
import os
from io import BytesIO

# === Конфигурация ===
TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
WEBHOOK_URL = f"https://client-notes-bot.onrender.com/{TOKEN}"

# === Подключение к PostgreSQL ===
DB_URL = "postgresql://client_notes_db_user:ujSU0BBRQ6swQwzRLwZ315LFWmYomGcn@dpg-d0p2rnuuk2gs7398b9s0-a/client_notes_db"
conn = psycopg2.connect(DB_URL, sslmode='require')
cur = conn.cursor()

# === Создание таблицы, если не существует ===
cur.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name TEXT,
    phone TEXT,
    notes TEXT
);
""")
conn.commit()

# === Клавиатура ===
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Добавить", "🔍 Найти")
    markup.row("📋 Список", "📃 Экспорт")
    markup.row("✏️ Редактировать", "🗑️ Удалить")
    return markup

# === Состояния ===
user_state = {}

# === Команды ===
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_keyboard())

# === Добавление клиента ===
@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def add_client(message):
    user_state[message.chat.id] = {"action": "add"}
    bot.send_message(message.chat.id, "Введите имя клиента:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "add" and "name" not in user_state[m.chat.id])
def get_name(message):
    user_state[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Введите номер телефона:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "add" and "phone" not in user_state[m.chat.id])
def get_phone(message):
    user_state[message.chat.id]["phone"] = message.text
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "add" and "notes" not in user_state[m.chat.id])
def get_notes(message):
    data = user_state[message.chat.id]
    data["notes"] = message.text
    cur.execute("INSERT INTO clients (name, phone, notes) VALUES (%s, %s, %s)", (data["name"], data["phone"], data["notes"]))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Клиент сохранён!", reply_markup=main_keyboard())
    user_state.pop(message.chat.id)

# === Поиск клиента ===
@bot.message_handler(func=lambda m: m.text == "🔍 Найти")
def search_prompt(message):
    user_state[message.chat.id] = {"action": "search"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "search")
def perform_search(message):
    query = f"%{message.text[-4:]}%"
    cur.execute("SELECT name, phone, notes FROM clients WHERE phone LIKE %s", (query,))
    results = cur.fetchall()
    if results:
        for r in results:
            bot.send_message(message.chat.id, f"👤 {r[0]}\n📞 {r[1]}\n💬 {r[2]}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
    user_state.pop(message.chat.id)

# === Список клиентов ===
@bot.message_handler(func=lambda m: m.text == "📋 Список")
def list_clients(message):
    cur.execute("SELECT name, phone FROM clients")
    rows = cur.fetchall()
    if rows:
        text = "\n".join([f"{i+1}. {r[0]} ({r[1]})" for i, r in enumerate(rows)])
        bot.send_message(message.chat.id, f"👥 Клиенты:\n{text}")
    else:
        bot.send_message(message.chat.id, "Список пуст.")

# === Экспорт в Excel ===
@bot.message_handler(func=lambda m: m.text == "📃 Экспорт")
def export_excel(message):
    cur.execute("SELECT name, phone, notes FROM clients")
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["Имя", "Телефон", "Комментарий"])
    bio = BytesIO()
    bio.name = "clients.xlsx"
    df.to_excel(bio, index=False)
    bio.seek(0)
    bot.send_document(message.chat.id, bio)

# === Удаление клиента ===
@bot.message_handler(func=lambda m: m.text == "🗑️ Удалить")
def delete_prompt(message):
    user_state[message.chat.id] = {"action": "delete"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента для удаления:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "delete")
def delete_client(message):
    query = f"%{message.text[-4:]}%"
    cur.execute("DELETE FROM clients WHERE phone LIKE %s", (query,))
    deleted = cur.rowcount
    conn.commit()
    if deleted:
        bot.send_message(message.chat.id, f"🗑️ Удалено {deleted} клиент(ов).")
    else:
        bot.send_message(message.chat.id, "❌ Ничего не найдено.")
    user_state.pop(message.chat.id)

# === Редактирование ===
@bot.message_handler(func=lambda m: m.text == "✏️ Редактировать")
def edit_prompt(message):
    user_state[message.chat.id] = {"action": "edit"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента для редактирования:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "edit" and "target" not in user_state[m.chat.id])
def edit_target(message):
    query = f"%{message.text[-4:]}%"
    cur.execute("SELECT id, name, phone, notes FROM clients WHERE phone LIKE %s", (query,))
    result = cur.fetchone()
    if result:
        user_state[message.chat.id]["target"] = result[0]
        bot.send_message(message.chat.id, "Введите новое имя:")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
        user_state.pop(message.chat.id)

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "edit" and "new_name" not in user_state[m.chat.id])
def edit_name(message):
    user_state[message.chat.id]["new_name"] = message.text
    bot.send_message(message.chat.id, "Введите новый номер:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "edit" and "new_phone" not in user_state[m.chat.id])
def edit_phone(message):
    user_state[message.chat.id]["new_phone"] = message.text
    bot.send_message(message.chat.id, "Введите новый комментарий:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("action") == "edit" and "new_notes" not in user_state[m.chat.id])
def edit_notes(message):
    state = user_state[message.chat.id]
    cur.execute(
        "UPDATE clients SET name = %s, phone = %s, notes = %s WHERE id = %s",
        (state["new_name"], state["new_phone"], message.text, state["target"])
    )
    conn.commit()
    bot.send_message(message.chat.id, "✏️ Данные обновлены.", reply_markup=main_keyboard())
    user_state.pop(message.chat.id)

# === Вебхук для Render ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Бот работает!"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
