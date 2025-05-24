from flask import Flask, request
import telebot
import os
import time
import json
from waitress import serve
from telebot.types import BotCommand

TOKEN = "7598214399:AAG18_9UqZoIys83qQalyXhAmhhvofZficA"
SERVICE_NAME = "client-notes-bot"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "clients.json"

# 📥 Загрузка клиентов из файла
def load_clients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 💾 Сохранение клиентов в файл
def save_clients():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(clients, f, indent=2, ensure_ascii=False)

clients = load_clients()

# 📋 Команды в меню Telegram
bot.set_my_commands([
    BotCommand("add", "➕ Добавить"),
    BotCommand("find", "🔍 Найти"),
    BotCommand("list", "📋 Список клиентов"),
    BotCommand("edit", "✏️ Редактировать"),
    BotCommand("delete", "🗑 Удалить клиента")
])

# 🔄 Вебхук
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Бот работает через production-сервер!"

# Команды

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот активен! Используйте меню или команды.")

@bot.message_handler(commands=["add"])
def add_client(message):
    msg = bot.send_message(message.chat.id, "Введите имя, номер и описание клиента через запятую:")
    bot.register_next_step_handler(msg, save_client)

def save_client(message):
    try:
        name, number, desc = map(str.strip, message.text.split(","))
        clients[number[-4:]] = {"name": name, "number": number, "desc": desc}
        save_clients()
        bot.send_message(message.chat.id, f"✅ Клиент {name} добавлен.")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Формат: Имя, Номер, Описание")

@bot.message_handler(commands=["find"])
def find_client(message):
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    bot.register_next_step_handler(msg, search_client)

def search_client(message):
    key = message.text.strip()
    client = clients.get(key)
    if client:
        bot.send_message(message.chat.id, f"👤 {client['name']}\n📞 {client['number']}\n💇 {client['desc']}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

@bot.message_handler(commands=["list"])
def list_clients(message):
    if not clients:
        bot.send_message(message.chat.id, "Список клиентов пуст.")
        return
    text = "\n\n".join([f"{v['name']} ({v['number']})\n💇 {v['desc']}" for v in clients.values()])
    bot.send_message(message.chat.id, f"📋 Список клиентов:\n\n{text}")

@bot.message_handler(commands=["delete"])
def delete_client(message):
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    bot.register_next_step_handler(msg, delete_by_number)

def delete_by_number(message):
    key = message.text.strip()
    if key in clients:
        deleted = clients.pop(key)
        save_clients()
        bot.send_message(message.chat.id, f"🗑 Клиент {deleted['name']} удалён.")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

@bot.message_handler(commands=["edit"])
def edit_client(message):
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента для редактирования:")
    bot.register_next_step_handler(msg, edit_step)

def edit_step(message):
    key = message.text.strip()
    if key in clients:
        msg = bot.send_message(message.chat.id, "Введите новое описание клиента:")
        bot.register_next_step_handler(msg, lambda m: apply_edit(m, key))
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

def apply_edit(message, key):
    clients[key]['desc'] = message.text.strip()
    save_clients()
    bot.send_message(message.chat.id, f"✏️ Описание клиента обновлено: {clients[key]['desc']}")

# 🔌 Запуск
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
