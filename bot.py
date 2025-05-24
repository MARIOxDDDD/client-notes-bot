import os
import json
import time
import logging
from flask import Flask, request, send_file
from waitress import serve
import pandas as pd
import telebot
from telebot import types

# ========== НАСТРОЙКА ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
WEBHOOK_URL = "https://clientnotesmarioxd.onrender.com/8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
JSON_FILE = "clients.json"
EXCEL_FILE = "clients.xlsx"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ========== РАБОТА С ДАННЫМИ ==========
def init_data():
    """Инициализация файла данных"""
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as f:
            json.dump([], f)
        logger.info("Создан новый файл clients.json")

init_data()

def load_clients():
    """Загрузка клиентов из JSON"""
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

def save_clients(clients):
    """Сохранение клиентов в JSON"""
    with open(JSON_FILE, 'w') as f:
        json.dump(clients, f, indent=2)

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    """Главное меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        '➕ Добавить', '🔍 Найти',
        '📋 Список', '✏️ Редактировать',
        '❌ Удалить', '📤 Экспорт'
    ]
    return markup.add(*buttons, row_width=2)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
                   "📒 *Client Notes Mario Bot* готов к работе!",
                   reply_markup=main_keyboard(),
                   parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '➕ Добавить')
def add_client(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_add_name)

def process_add_name(message):
    if not message.text.strip():
        bot.send_message(message.chat.id, "❌ Имя не может быть пустым!", reply_markup=main_keyboard())
        return
    
    client = {'name': message.text}
    msg = bot.send_message(message.chat.id, "Введите номер телефона:")
    bot.register_next_step_handler(msg, process_add_phone, client)

def process_add_phone(message, client):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "❌ Некорректный номер!", reply_markup=main_keyboard())
        return
    
    client['phone'] = message.text
    msg = bot.send_message(message.chat.id, "Введите описание:")
    bot.register_next_step_handler(msg, process_add_finish, client)

def process_add_finish(message, client):
    client['description'] = message.text
    clients = load_clients()
    clients.append(client)
    save_clients(clients)
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=main_keyboard())

# [Аналогичные обработчики для других кнопок...]

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == '__main__':
    logger.info("Сбрасываем старый вебхук...")
    bot.remove_webhook()
    time.sleep(1)
    
    logger.info(f"Устанавливаем новый вебхук: {WEBHOOK_URL}")
    bot.set_webhook(url=WEBHOOK_URL)
    
    logger.info("Запускаем production-сервер...")
    serve(app, host="0.0.0.0", port=10000)
