import os
import telebot
from telebot import types
from flask import Flask, request
from waitress import serve
from tinydb import TinyDB, Query
import time
import openpyxl
from telebot.types import InputFile

TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
SERVICE_NAME = "client-notes-bot"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db = TinyDB(os.path.join(BASE_DIR, 'clients.json'))
User = Query()

# Удалим вебхук и установим новый
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "🔍 Найти")
    markup.add("📋 Список клиентов", "❌ Удалить")
    markup.add("📤 Экспорт в Excel")
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

# Добавление клиента
client_data = {}

@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить")
def add_client(message):
    bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    client_data["name"] = message.text
    bot.send_message(message.chat.id, "Введите номер телефона:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    client_data["phone"] = message.text
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")
    bot.register_next_step_handler(message, get_comment)

def get_comment(message):
    client_data["comment"] = message.text
    db.insert(client_data.copy())
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=main_menu())

# Поиск клиента
@bot.message_handler(func=lambda msg: msg.text == "🔍 Найти")
def find_client(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")
    bot.register_next_step_handler(message, search_client)

def search_client(message):
    query = message.text.strip()
    results = db.search(User.phone.test(lambda val: val.endswith(query)))
    if results:
        response = "🔎 Найдено:\n\n"
        for c in results:
            response += f"👤 {c['name']}\n📱 {c['phone']}\n💬 {c['comment']}\n\n"
    else:
        response = "❗️Клиент не найден."
    bot.send_message(message.chat.id, response, reply_markup=main_menu())

# Показать всех клиентов
@bot.message_handler(func=lambda msg: msg.text == "📋 Список клиентов")
def show_all(message):
    clients = db.all()
    if clients:
        msg = "📋 Все клиенты:\n\n"
        for c in clients:
            msg += f"👤 {c['name']}\n📱 {c['phone']}\n💬 {c['comment']}\n\n"
    else:
        msg = "Список пуст."
    bot.send_message(message.chat.id, msg, reply_markup=main_menu())

# Удаление клиента
@bot.message_handler(func=lambda msg: msg.text == "❌ Удалить")
def delete_client(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера для удаления:")
    bot.register_next_step_handler(message, delete_by_last_digits)

def delete_by_last_digits(message):
    query = message.text.strip()
    deleted = db.remove(User.phone.test(lambda val: val.endswith(query)))
    if deleted:
        bot.send_message(message.chat.id, "✅ Клиент удалён.")
    else:
        bot.send_message(message.chat.id, "❗️Клиент не найден.")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_menu())

# Экспорт в Excel
@bot.message_handler(func=lambda msg: msg.text == "📤 Экспорт в Excel")
def export_excel(message):
    clients = db.all()
    if not clients:
        bot.send_message(message.chat.id, "Список клиентов пуст.")
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Клиенты"
    ws.append(["Имя", "Телефон", "Комментарий"])
    for c in clients:
        ws.append([c["name"], c["phone"], c["comment"]])

    file_path = os.path.join(BASE_DIR, "clients_export.xlsx")
    wb.save(file_path)

    with open(file_path, "rb") as f:
        bot.send_document(message.chat.id, InputFile(f, filename="Клиенты.xlsx"))

# Webhook обработка
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Бот работает!"

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
