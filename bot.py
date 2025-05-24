from flask import Flask, request
import telebot
import os
import time
from waitress import serve  # Production-сервер

# Конфиг (ваши данные уже вставлены)
TOKEN = "7598214399:AAG18_9UqZoIys83qQalyXhAmhhvofZficA"
SERVICE_NAME = "client-notes-bot"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Вебхук
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def home():
    return "Бот работает через production-сервер!"

if __name__ == '__main__':
    # Production-режим (Waitress вместо Flask-сервера)
    serve(app, host="0.0.0.0", port=10000)
