from flask import Flask, request
import telebot
from telebot import types
import pandas as pd
import os
import time
from waitress import serve

# 🔐 Твой токен и имя сервиса
TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
SERVICE_NAME = "client-notes-bot"
WEBHOOK_URL = f"https://{SERVICE_NAME}.onrender.com/{TOKEN}"

# 📂 Файл, где хранятся данные
DATA_FILE = "clients_data.xlsx"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 📌 Временное хранилище состояний
user_data = {}

# 📤 Вебхук
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

# 🔘 Главное меню
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "🔍 Найти", "📋 Список", "✏️ Редактировать", "🗑️ Удалить", "📤 Экспорт")
    bot.send_message(chat_id, "✅ Бот запущен! Выберите действие:", reply_markup=markup)

# 🚀 /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    show_main_menu(message.chat.id)

# 👂 Обработка кнопок
@bot.message_handler(func=lambda msg: msg.text in ["➕ Добавить", "🔍 Найти", "📋 Список", "✏️ Редактировать", "🗑️ Удалить", "📤 Экспорт"])
def menu_handler(message):
    chat_id = message.chat.id
    user_data[chat_id] = {"action": message.text}

    if message.text == "➕ Добавить":
        bot.send_message(chat_id, "Введите имя клиента:")
    elif message.text == "🔍 Найти":
        bot.send_message(chat_id, "Введите последние 4 цифры номера:")
    elif message.text == "📋 Список":
        send_full_list(chat_id)
    elif message.text == "📤 Экспорт":
        export_to_excel(chat_id)
    else:
        bot.send_message(chat_id, "Пока эта функция в разработке.")

# 📥 Обработка ввода (добавление клиента)
@bot.message_handler(func=lambda msg: True)
def handle_input(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        show_main_menu(chat_id)
        return

    state = user_data[chat_id]

    if state["action"] == "➕ Добавить":
        if "name" not in state:
            state["name"] = message.text
            bot.send_message(chat_id, "Введите номер телефона:")
        elif "phone" not in state:
            state["phone"] = message.text
            bot.send_message(chat_id, "Опишите стрижку или комментарии:")
        else:
            state["comment"] = message.text
            save_client(state["name"], state["phone"], state["comment"])
            bot.send_message(chat_id, "✅ Клиент добавлен!")
            show_main_menu(chat_id)
            user_data.pop(chat_id)

    elif state["action"] == "🔍 Найти":
        phone_tail = message.text.strip()[-4:]
        result = search_client(phone_tail)
        bot.send_message(chat_id, result)
        show_main_menu(chat_id)
        user_data.pop(chat_id)

# 💾 Сохраняем клиента
def save_client(name, phone, comment):
    df = pd.DataFrame([[name, phone, comment]], columns=["Имя", "Телефон", "Комментарий"])
    if os.path.exists(DATA_FILE):
        existing = pd.read_excel(DATA_FILE)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(DATA_FILE, index=False)

# 🔍 Поиск по последним 4 цифрам
def search_client(phone_tail):
    if not os.path.exists(DATA_FILE):
        return "❌ Клиентов пока нет."

    df = pd.read_excel(DATA_FILE)
    matches = df[df["Телефон"].astype(str).str.endswith(phone_tail)]

    if matches.empty:
        return "❌ Клиенты не найдены."

    return "\n\n".join([f"👤 {row['Имя']}\n📱 {row['Телефон']}\n💬 {row['Комментарий']}" for _, row in matches.iterrows()])

# 📋 Полный список
def send_full_list(chat_id):
    if not os.path.exists(DATA_FILE):
        bot.send_message(chat_id, "📂 Клиентов пока нет.")
        return

    df = pd.read_excel(DATA_FILE)
    if df.empty:
        bot.send_message(chat_id, "📂 Клиентов пока нет.")
        return

    message = "\n\n".join([f"👤 {row['Имя']}\n📱 {row['Телефон']}\n💬 {row['Комментарий']}" for _, row in df.iterrows()])
    bot.send_message(chat_id, message[:4000])  # Ограничение Telegram

# 📤 Экспорт
def export_to_excel(chat_id):
    if not os.path.exists(DATA_FILE):
        bot.send_message(chat_id, "📂 Нет данных для экспорта.")
        return

    with open(DATA_FILE, "rb") as f:
        bot.send_document(chat_id, f)

# 🌐 Webhook обработка
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Бот работает!"

# 🚀 Запуск сервера
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
