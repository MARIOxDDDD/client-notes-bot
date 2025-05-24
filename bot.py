from flask import Flask, request
import telebot
import os
import time

# Настройка бота
TOKEN = os.getenv('BOT_TOKEN')  # Токен из переменных окружения Render
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 1. Удаляем старый вебхук (если был)
bot.remove_webhook()
time.sleep(1)  # Ждём 1 секунду

# 2. Устанавливаем новый вебхук
WEBHOOK_URL = f"https://your-service-name.onrender.com/{TOKEN}"
bot.set_webhook(url=WEBHOOK_URL)

# 3. Обработчик входящих сообщений от Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

# 4. Тестовая страница (для проверки работы)
@app.route('/')
def home():
    return "Бот работает через вебхук! URL: " + WEBHOOK_URL

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
