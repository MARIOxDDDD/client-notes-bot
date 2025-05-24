from flask import Flask, request
import telebot
import os
import time

# Конфигурация (уже с вашим токеном!)
TOKEN = "7598214399:AAG18_9UqZoIys83qQalyXhAmhhvofZficA"
SERVICE_NAME = "client-notes-bot"  # Имя вашего сервиса на Render
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Удаляем старый вебхук и устанавливаем новый
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# Обработчик Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

# Тестовая страница
@app.route('/')
def home():
    return f"""
    <h1>Бот client-notes-bot работает!</h1>
    <p>Вебхук: <code>{WEBHOOK_URL}</code></p>
    <p>Отправьте боту /start в Telegram.</p>
    """

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Бот активен! Используйте /add для добавления клиента.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
