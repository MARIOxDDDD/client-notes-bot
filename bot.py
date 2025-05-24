from flask import Flask, request
import telebot
import os
import time
import csv
from tinydb import TinyDB, Query
from waitress import serve
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
SERVICE_NAME = "clientnotesbot-mario"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

db = TinyDB("clients.json")
user_states = {}

# ---------- Меню ----------
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("➕ Добавить"),
        KeyboardButton("🔍 Найти"),
    )
    markup.add(
        KeyboardButton("📋 Список клиентов"),
        KeyboardButton("✏️ Редактировать"),
        KeyboardButton("🗑️ Удалить"),
    )
    markup.add(
        KeyboardButton("📤 Экспорт в Excel")
    )
    return markup

# ---------- Обработка start ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

# ---------- Добавить клиента ----------
@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить")
def add_client(message):
    user_states[message.from_user.id] = {}
    bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_states[message.from_user.id]["name"] = message.text
    bot.send_message(message.chat.id, "Введите номер телефона:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_states[message.from_user.id]["phone"] = message.text
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")
    bot.register_next_step_handler(message, get_comment)

def get_comment(message):
    user_id = message.from_user.id
    user_states[user_id]["comment"] = message.text
    db.insert(user_states[user_id])
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=main_menu())
    del user_states[user_id]

# ---------- Найти клиента ----------
@bot.message_handler(func=lambda msg: msg.text == "🔍 Найти")
def find_client(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")
    bot.register_next_step_handler(message, search_by_phone)

def search_by_phone(message):
    query = Query()
    results = db.search(query.phone.test(lambda x: x.endswith(message.text)))
    if results:
        for client in results:
            bot.send_message(message.chat.id, f"👤 {client['name']}\n📱 {client['phone']}\n✂️ {client['comment']}")
    else:
        bot.send_message(message.chat.id, "❌ Клиент не найден.")

# ---------- Список клиентов ----------
@bot.message_handler(func=lambda msg: msg.text == "📋 Список клиентов")
def list_clients(message):
    clients = db.all()
    if not clients:
        bot.send_message(message.chat.id, "📭 База клиентов пуста.")
        return
    text = "\n\n".join([f"👤 {c['name']}\n📱 {c['phone']}\n✂️ {c['comment']}" for c in clients])
    bot.send_message(message.chat.id, text)

# ---------- Экспорт ----------
@bot.message_handler(func=lambda msg: msg.text == "📤 Экспорт в Excel")
def export_excel(message):
    filename = "clients_export.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Имя", "Телефон", "Комментарий"])
        for c in db.all():
            writer.writerow([c["name"], c["phone"], c["comment"]])
    with open(filename, "rb") as file:
        bot.send_document(message.chat.id, file)

# ---------- Вебхук ----------
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
    return "Бот работает через Render!", 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
