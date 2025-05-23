import telebot
import os
import requests
import logging

# Настройка логирования (чтобы видеть ошибки)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (Render возьмёт его из переменных окружения)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Принудительный сброс старых подключений
try:
    bot.remove_webhook()
    requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1")
    logger.info("✅ Предыдущие соединения сброшены")
except Exception as e:
    logger.error(f"❌ Ошибка сброса: {e}")

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Я работаю без ошибок!")

# Запуск бота
if __name__ == '__main__':
    logger.info("🔄 Бот запускается...")
    bot.polling(none_stop=True, skip_pending=True, interval=1)
