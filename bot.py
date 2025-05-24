import telebot
import json
import os
import time
import pandas as pd
from flask import Flask, request
from telebot import types
from waitress import serve

# === НАСТРОЙКИ ===
TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
WEBHOOK_URL = f"https://clientnotesmarioxd.onrender.com/{TOKEN}"
DATA_FILE = "clients.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === ИНИЦИАЛИЗАЦИЯ ХРАНИЛИЩА ===
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# === КНОПКИ МЕНЮ ===
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Добавить", "🔍 Найти")
    markup.row("📋 Список клиентов", "✏️ Редактировать", "❌ Удалить")
    markup.row("📤 Экспорт")
    return markup

# === ЗАГРУЗКА / СОХРАНЕНИЕ ДАННЫХ ===
def load_clients():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_clients(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# === КОМАНДА /start ===
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

# === СОСТОЯНИЯ ===
user_state = {}

# === ДОБАВЛЕНИЕ КЛИЕНТА ===
@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить")
def add_client(message):
    user_state[message.chat.id] = {"action": "add"}
    bot.send_message(message.chat.id, "Введите имя клиента:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "add_name")
def get_phone(message):
    user_state[message.chat.id]["name"] = message.text
    user_state[message.chat.id]["action"] = "add_phone"
    bot.send_message(message.chat.id, "Введите номер телефона:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "add_phone")
def get_comment(message):
    user_state[message.chat.id]["phone"] = message.text
    user_state[message.chat.id]["action"] = "add_comment"
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "add_comment")
def save_client(message):
    user = user_state[message.chat.id]
    clients = load_clients()
    clients.append({
        "name": user["name"],
        "phone": user["phone"],
        "comment": message.text
    })
    save_clients(clients)
    user_state.pop(message.chat.id)
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=main_menu())

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "add")
def get_name(message):
    user_state[message.chat.id]["action"] = "add_name"
    get_phone(message)

# === ПОИСК КЛИЕНТА ===
@bot.message_handler(func=lambda msg: msg.text == "🔍 Найти")
def search_client(message):
    user_state[message.chat.id] = {"action": "search"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "search")
def do_search(message):
    digits = message.text.strip()[-4:]
    clients = load_clients()
    found = [c for c in clients if c["phone"][-4:] == digits]
    if found:
        for c in found:
            bot.send_message(message.chat.id, f"👤 {c['name']}\n📞 {c['phone']}\n💬 {c['comment']}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
    user_state.pop(message.chat.id)

# === СПИСОК КЛИЕНТОВ ===
@bot.message_handler(func=lambda msg: msg.text == "📋 Список клиентов")
def list_clients(message):
    clients = load_clients()
    if clients:
        for c in clients:
            bot.send_message(message.chat.id, f"👤 {c['name']}\n📞 {c['phone']}\n💬 {c['comment']}")
    else:
        bot.send_message(message.chat.id, "Список клиентов пуст.")

# === РЕДАКТИРОВАНИЕ КЛИЕНТА ===
@bot.message_handler(func=lambda msg: msg.text == "✏️ Редактировать")
def edit_client(message):
    user_state[message.chat.id] = {"action": "edit"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "edit")
def get_edit_comment(message):
    digits = message.text.strip()[-4:]
    user_state[message.chat.id] = {"action": "edit_comment", "digits": digits}
    bot.send_message(message.chat.id, "Введите новый комментарий:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "edit_comment")
def do_edit(message):
    data = user_state.pop(message.chat.id)
    clients = load_clients()
    found = False
    for c in clients:
        if c["phone"][-4:] == data["digits"]:
            c["comment"] = message.text
            found = True
    if found:
        save_clients(clients)
        bot.send_message(message.chat.id, "✅ Комментарий обновлён.")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

# === УДАЛЕНИЕ КЛИЕНТА ===
@bot.message_handler(func=lambda msg: msg.text == "❌ Удалить")
def delete_client(message):
    user_state[message.chat.id] = {"action": "delete"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")

@bot.message_handler(func=lambda msg: user_state.get(msg.chat.id, {}).get("action") == "delete")
def do_delete(message):
    digits = message.text.strip()[-4:]
    clients = load_clients()
    updated = [c for c in clients if c["phone"][-4:] != digits]
    if len(updated) < len(clients):
        save_clients(updated)
        bot.send_message(message.chat.id, "✅ Клиент удалён.")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
    user_state.pop(message.chat.id)

# === ЭКСПОРТ В EXCEL ===
@bot.message_handler(func=lambda msg: msg.text == "📤 Экспорт")
def export_excel(message):
    clients = load_clients()
    if not clients:
        bot.send_message(message.chat.id, "Список клиентов пуст.")
        return
    df = pd.DataFrame(clients)
    file_path = "clients.xlsx"
    df.to_excel(file_path, index=False)
    with open(file_path, 'rb') as f:
        bot.send_document(message.chat.id, f)
    os.remove(file_path)

# === ОБРАБОТКА ВЕБХУКА ===
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Бот запущен!"

# === ЗАПУСК (Webhook) ===
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
