import telebot
import json
import os
from telebot import types
from flask import Flask, request
from waitress import serve

TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "clients.json"

# Загрузка базы
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение базы
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

clients = load_data()

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить", "🔍 Найти")
    markup.add("📋 Список клиентов", "✏️ Редактировать", "❌ Удалить клиента")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

# ➕ Добавление клиента
@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def add_client(message):
    msg = bot.send_message(message.chat.id, "Введите имя клиента:")
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    name = message.text
    msg = bot.send_message(message.chat.id, "Введите номер телефона:")
    bot.register_next_step_handler(msg, get_phone, name)

def get_phone(message, name):
    phone = message.text
    msg = bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")
    bot.register_next_step_handler(msg, save_client, name, phone)

def save_client(message, name, phone):
    info = message.text
    clients[phone] = {"name": name, "info": info}
    save_data(clients)
    bot.send_message(message.chat.id, "✅ Клиент сохранён!", reply_markup=main_menu())

# 🔍 Поиск по последним 4 цифрам
@bot.message_handler(func=lambda m: m.text == "🔍 Найти")
def find_client(message):
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")
    bot.register_next_step_handler(msg, search_by_phone)

def search_by_phone(message):
    part = message.text.strip()[-4:]
    found = [f"📌 {data['name']} — {phone}\n💬 {data['info']}" for phone, data in clients.items() if phone.endswith(part)]
    if found:
        bot.send_message(message.chat.id, "\n\n".join(found), reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Ничего не найдено.", reply_markup=main_menu())

# 📋 Список всех клиентов
@bot.message_handler(func=lambda m: m.text == "📋 Список клиентов")
def list_clients(message):
    if not clients:
        bot.send_message(message.chat.id, "Список пуст.", reply_markup=main_menu())
        return
    result = "\n\n".join([f"📌 {d['name']} — {p}\n💬 {d['info']}" for p, d in clients.items()])
    bot.send_message(message.chat.id, result, reply_markup=main_menu())

# ✏️ Редактирование клиента
@bot.message_handler(func=lambda m: m.text == "✏️ Редактировать")
def ask_edit(message):
    msg = bot.send_message(message.chat.id, "Введите номер клиента для редактирования:")
    bot.register_next_step_handler(msg, edit_client)

def edit_client(message):
    phone = message.text
    if phone not in clients:
        bot.send_message(message.chat.id, "Клиент не найден.", reply_markup=main_menu())
        return
    msg = bot.send_message(message.chat.id, "Введите новые комментарии/инфо:")
    bot.register_next_step_handler(msg, save_edit, phone)

def save_edit(message, phone):
    clients[phone]['info'] = message.text
    save_data(clients)
    bot.send_message(message.chat.id, "✅ Информация обновлена.", reply_markup=main_menu())

# ❌ Удаление
@bot.message_handler(func=lambda m: m.text == "❌ Удалить клиента")
def ask_delete(message):
    msg = bot.send_message(message.chat.id, "Введите номер клиента для удаления:")
    bot.register_next_step_handler(msg, delete_client)

def delete_client(message):
    phone = message.text
    if phone in clients:
        del clients[phone]
        save_data(clients)
        bot.send_message(message.chat.id, "❌ Клиент удалён.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Клиент не найден.", reply_markup=main_menu())

# Webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Бот работает!"

if __name__ == "__main__":
    bot.remove_webhook()
    import time
    time.sleep(1)
    bot.set_webhook(url="https://client-notes-bot.onrender.com/" + TOKEN)
    serve(app, host="0.0.0.0", port=10000)
