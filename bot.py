from flask import Flask, request
import telebot
from telebot import types
import os
import time
from waitress import serve

# Конфигурация
TOKEN = "7598214399:AAG18_9UqZoIys83qQalyXhAmhhvofZficA"
SERVICE_NAME = "client-notes-bot"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Вебхук
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# Обработчик старта
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("/add")
    btn2 = types.KeyboardButton("/find")
    markup.add(btn1, btn2)

    bot.send_message(message.chat.id, "✅ Бот активен! Выберите действие:", reply_markup=markup)

# Добавление клиента (заглушка — можно доработать)
@bot.message_handler(commands=['add'])
def add_client(message):
    bot.send_message(message.chat.id, "Введите данные клиента в формате:\nИмя, последние 4 цифры номера, описание стрижки")

# Поиск клиента (заглушка)
@bot.message_handler(commands=['find'])
def find_client(message):
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера для поиска клиента.")

# Обработка вебхука
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
