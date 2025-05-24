import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
from waitress import serve
import openpyxl
from io import BytesIO
import time
from database import SessionLocal, Client

TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
WEBHOOK_HOST = "client-notes-bot.onrender.com"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{TOKEN}"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Вебхук
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=WEBHOOK_URL)

user_states = {}

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Добавить", "🔍 Найти", "📄 Список клиентов")
    markup.row("✏️ Редактировать", "❌ Удалить", "📤 Экспорт")
    return markup

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Бот работает!"

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "✅ Бот запущен! Выберите действие:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "➕ Добавить")
def add_start(message):
    user_states[message.chat.id] = {"state": "add_name"}
    bot.send_message(message.chat.id, "Введите имя клиента:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("state") == "add_name")
def add_phone(message):
    user_states[message.chat.id]["name"] = message.text
    user_states[message.chat.id]["state"] = "add_phone"
    bot.send_message(message.chat.id, "Введите номер телефона (4 последние цифры):")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("state") == "add_phone")
def add_description(message):
    user_states[message.chat.id]["phone_last4"] = message.text
    user_states[message.chat.id]["state"] = "add_description"
    bot.send_message(message.chat.id, "Опишите стрижку или комментарии:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("state") == "add_description")
def finish_add(message):
    data = user_states.pop(message.chat.id, {})
    db = SessionLocal()
    client = Client(
        name=data["name"],
        phone_last4=data["phone_last4"],
        description=message.text
    )
    db.add(client)
    db.commit()
    db.close()
    bot.send_message(message.chat.id, "✅ Клиент добавлен!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🔍 Найти")
def search_client_prompt(message):
    user_states[message.chat.id] = {"state": "search"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("state") == "search")
def search_client(message):
    phone = message.text
    db = SessionLocal()
    client = db.query(Client).filter(Client.phone_last4 == phone).first()
    db.close()
    if client:
        bot.send_message(message.chat.id, f"👤 Имя: {client.name}\n📞 Тел: ****{client.phone_last4}\n💈 Стрижка: {client.description}", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "❗ Клиент не найден", reply_markup=main_menu())
    user_states.pop(message.chat.id, None)

@bot.message_handler(func=lambda m: m.text == "📄 Список клиентов")
def list_clients(message):
    db = SessionLocal()
    clients = db.query(Client).all()
    db.close()
    if clients:
        text = "\n\n".join([f"👤 {c.name}, 📞 ****{c.phone_last4}, 💈 {c.description}" for c in clients])
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Список пуст.")

@bot.message_handler(func=lambda m: m.text == "📤 Экспорт")
def export_clients(message):
    db = SessionLocal()
    clients = db.query(Client).all()
    db.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Имя", "Телефон", "Описание"])
    for c in clients:
        ws.append([c.name, c.phone_last4, c.description])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    bot.send_document(message.chat.id, output, visible_file_name="clients.xlsx")

@bot.message_handler(func=lambda m: m.text == "❌ Удалить")
def delete_prompt(message):
    user_states[message.chat.id] = {"state": "delete"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера для удаления:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("state") == "delete")
def delete_client(message):
    db = SessionLocal()
    client = db.query(Client).filter(Client.phone_last4 == message.text).first()
    if client:
        db.delete(client)
        db.commit()
        bot.send_message(message.chat.id, "🗑️ Клиент удалён", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "❗ Клиент не найден", reply_markup=main_menu())
    db.close()
    user_states.pop(message.chat.id, None)

@bot.message_handler(func=lambda m: m.text == "✏️ Редактировать")
def edit_prompt(message):
    user_states[message.chat.id] = {"state": "edit_search"}
    bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("state") == "edit_search")
def edit_description(message):
    db = SessionLocal()
    client = db.query(Client).filter(Client.phone_last4 == message.text).first()
    if client:
        user_states[message.chat.id] = {"state": "edit", "client_id": client.id}
        bot.send_message(message.chat.id, "Введите новое описание:")
    else:
        bot.send_message(message.chat.id, "❗ Клиент не найден", reply_markup=main_menu())
    db.close()

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get("state") == "edit")
def update_description(message):
    db = SessionLocal()
    client = db.query(Client).filter(Client.id == user_states[message.chat.id]["client_id"]).first()
    if client:
        client.description = message.text
        db.commit()
        bot.send_message(message.chat.id, "✏️ Описание обновлено!", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "Ошибка при обновлении.")
    db.close()
    user_states.pop(message.chat.id, None)

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
