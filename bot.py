import telebot
import os
import logging
from flask import Flask

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("❌ Токен бота не найден! Проверьте переменные окружения.")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает! Порт 10000 открыт."

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔄 Бот запущен и готов к работе!")

if __name__ == '__main__':
    try:
        logger.info("Запуск бота...")
        # Для Render Web Service
        import threading
        threading.Thread(
            target=app.run,
            kwargs={'host':'0.0.0.0','port':10000}
        ).start()
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        exit(1)
