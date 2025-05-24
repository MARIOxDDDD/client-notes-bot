from flask import Flask, request
import telebot
from telebot import types
import os
import time
import json
from waitress import serve

# === Конфиг ===
TOKEN = "7598214399:AAG18_9UqZoIys83qQalyXhAmhhvofZficA"
SERVICE_NAME = "client-notes-bot"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"
DATA_FILE = "clients.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Вебхук
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# === Вспомогательные функции ===
def load_clients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_clients(clients):
    with open(DATA_FILE, "w") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)

# === Команды ===
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("/add"), types.KeyboardButton("/find"))
    bot.send_message(message.chat.id, "✅ Бот активен! Выберите действие:", reply_markup=markup)

@bot.message_handler(commands=['add'])
def add_client(message):
    bot.send_message(message.chat.id, "Введите клиента в формате:\nИмя, последние 4 цифры номера, описание стрижки")
    bot.register_next_step_handler(message, save_client_data)

def save_client_data(message):
    try:
        name, last4, desc = [x.strip() for x in message.text.split(",", 2)]
        clients = load_clients()
        clients.append({"name": name, "last4": last4, "desc": desc})
        save_clients(clients)
        bot.send_message(message.chat.id, f"✅ Клиент {name} сохранён!")
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка! Убедитесь, что формат: Имя, 1234, описание")

@bot.message_handler(commands=['find'])
def find_client(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    bot.register_next_step_handler(message, search_client)

def search_client(message):
    last4 = message.text.strip()
    clients = load_clients()
    found = [c for c in clients if c["last4"] == last4]
    if found:
        for client in found:
            bot.send_message(message.chat.id,
                f"👤 {client['name']}\n📞 ...{client['last4']}\n✂️ {client['desc']}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

# === Вебхук ===
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def home():
    return "Бот работает через production-сервер!"

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=10000)
