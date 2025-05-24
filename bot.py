import telebot
import os
from flask import Flask

app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Минимальный веб-сервер для Render
@app.route('/')
def home():
    return "Бот работает! Порт 10000 открыт."

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ Я снова работаю! Напиши /add чтобы добавить клиента.")

# Запуск
if __name__ == '__main__':
    import threading
    threading.Thread(target=app.run, kwargs={'host':'0.0.0.0','port':10000}).start()
    bot.polling(none_stop=True)
