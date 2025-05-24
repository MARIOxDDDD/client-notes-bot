from flask import Flask, request
from telebot.types import BotCommand
import telebot
import os
from waitress import serve

# Конфигурация
TOKEN = "7598214399:AAG18_9UqZoIys83qQalyXhAmhhvofZficA"
SERVICE_NAME = "client-notes-bot"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Команды для меню
bot.set_my_commands([
    BotCommand("add", "➕ Добавить"),
    BotCommand("find", "🔍 Найти"),
    BotCommand("list", "📋 Список клиентов"),
    BotCommand("edit", "✏️ Редактировать"),
    BotCommand("delete", "🗑 Удалить клиента")
])

# Простая база данных в виде словаря (для примера)
clients = {}

# Обработка /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Бот активен!\nВыберите команду из меню или введите /add чтобы добавить клиента.")

# Добавить клиента
@bot.message_handler(commands=['add'])
def add_client(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента, номер телефона и описание стрижки через запятую:")
    bot.register_next_step_handler(msg, save_client)

def save_client(message):
    try:
        name, phone, description = [x.strip() for x in message.text.split(',')]
        clients[phone[-4:]] = {
            'name': name,
            'phone': phone,
            'description': description
        }
        bot.send_message(message.chat.id, f"✅ Клиент {name} добавлен!")
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка. Пожалуйста, используйте формат: имя, номер, описание")

# Найти клиента
@bot.message_handler(commands=['find'])
def find_client(message):
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")
    bot.register_next_step_handler(msg, search_client)

def search_client(message):
    key = message.text.strip()
    client = clients.get(key)
    if client:
        bot.send_message(message.chat.id, f"👤 Клиент: {client['name']}\n📞 Телефон: {client['phone']}\n✂️ Стрижка: {client['description']}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

# Показать всех
@bot.message_handler(commands=['list'])
def list_clients(message):
    if not clients:
        bot.send_message(message.chat.id, "📭 Список клиентов пуст.")
        return
    text = "📋 Клиенты:\n"
    for c in clients.values():
        text += f"- {c['name']} ({c['phone']})\n"
    bot.send_message(message.chat.id, text)

# Удалить клиента
@bot.message_handler(commands=['delete'])
def delete_client(message):
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента для удаления:")
    bot.register_next_step_handler(msg, do_delete)

def do_delete(message):
    key = message.text.strip()
    if clients.pop(key, None):
        bot.send_message(message.chat.id, f"✅ Клиент с окончанием {key} удалён.")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

# Webhook и запуск Flask
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Бот работает."

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    serve(app, host="0.0.0.0", port=10000)
