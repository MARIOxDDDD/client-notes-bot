from flask import Flask, request, send_file
import telebot
from telebot import types
import os
import json
import time
import pandas as pd
from waitress import serve

TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
SERVICE_NAME = "clientnotesmarioxd"  # подставь имя Render-проекта без https и слеша
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "clients.json"
user_states = {}

# --- Утилиты ---

def load_clients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_clients(clients):
    with open(DATA_FILE, "w") as f:
        json.dump(clients, f, indent=2)

def export_to_excel():
    clients = load_clients()
    df = pd.DataFrame(clients)
    df.to_excel("clients.xlsx", index=False)

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "🔍 Найти")
    markup.add("📋 Список клиентов", "✏️ Редактировать", "❌ Удалить")
    markup.add("📤 Экспорт")
    return markup

# --- Обработчики ---

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить")
def add_start(message):
    bot.send_message(message.chat.id, "Введите имя клиента:")
    user_states[message.chat.id] = {"action": "add"}
    bot.register_next_step_handler(message, add_name)

def add_name(message):
    user_states[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "Введите номер телефона:")
    bot.register_next_step_handler(message, add_phone)

def add_phone(message):
    user_states[message.chat.id]["phone"] = message.text
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")
    bot.register_next_step_handler(message, add_description)

def add_description(message):
    data = user_states.pop(message.chat.id)
    client = {
        "name": data["name"],
        "phone": data["phone"],
        "description": message.text
    }
    clients = load_clients()
    clients.append(client)
    save_clients(clients)
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "🔍 Найти")
def find_start(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")
    bot.register_next_step_handler(message, find_client)

def find_client(message):
    last_digits = message.text.strip()
    clients = load_clients()
    found = [c for c in clients if c["phone"].endswith(last_digits)]
    if found:
        for c in found:
            bot.send_message(message.chat.id, f"👤 {c['name']}\n📞 {c['phone']}\n✂️ {c['description']}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "📋 Список клиентов")
def list_clients(message):
    clients = load_clients()
    if not clients:
        bot.send_message(message.chat.id, "Список клиентов пуст.")
    else:
        text = ""
        for c in clients:
            text += f"👤 {c['name']} | 📞 {c['phone']} | ✂️ {c['description']}\n"
        bot.send_message(message.chat.id, text)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "✏️ Редактировать")
def edit_start(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    bot.register_next_step_handler(message, edit_find)

def edit_find(message):
    digits = message.text.strip()
    clients = load_clients()
    for i, c in enumerate(clients):
        if c["phone"].endswith(digits):
            user_states[message.chat.id] = {"index": i}
            bot.send_message(message.chat.id, f"Новый комментарий для {c['name']}:")
            bot.register_next_step_handler(message, edit_comment)
            return
    bot.send_message(message.chat.id, "Клиент не найден.", reply_markup=get_main_menu())

def edit_comment(message):
    index = user_states.pop(message.chat.id)["index"]
    clients = load_clients()
    clients[index]["description"] = message.text
    save_clients(clients)
    bot.send_message(message.chat.id, "Комментарий обновлён!", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "❌ Удалить")
def delete_start(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    bot.register_next_step_handler(message, delete_client)

def delete_client(message):
    digits = message.text.strip()
    clients = load_clients()
    for i, c in enumerate(clients):
        if c["phone"].endswith(digits):
            del clients[i]
            save_clients(clients)
            bot.send_message(message.chat.id, "Клиент удалён!", reply_markup=get_main_menu())
            return
    bot.send_message(message.chat.id, "Клиент не найден.", reply_markup=get_main_menu())

@bot.message_handler(func=lambda msg: msg.text == "📤 Экспорт")
def export_excel(message):
    export_to_excel()
    bot.send_document(message.chat.id, open("clients.xlsx", "rb"), caption="📤 Экспорт завершён.")

# --- Webhook Flask ---

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
    time.sleep(1)
    bot.set_webhook(url=WEBHOOK_URL)
    serve(app, host="0.0.0.0", port=10000)
