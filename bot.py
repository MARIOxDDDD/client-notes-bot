import os
import json
import telebot
from flask import Flask, request, send_file
from waitress import serve
import pandas as pd
from telebot import types

# Конфигурация бота
TOKEN = "8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
WEBHOOK_URL = "https://clientnotesmarioxd.onrender.com/8036531554:AAGyyLFsy8LyW--jPsdZuqnSl-3AfcAFWz0"
JSON_FILE = "clients.json"
EXCEL_FILE = "clients.xlsx"

# Инициализация
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Создаем JSON файл если его нет
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'w') as f:
        json.dump([], f)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def load_clients():
    """Загрузить список клиентов из JSON"""
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

def save_clients(clients):
    """Сохранить список клиентов в JSON"""
    with open(JSON_FILE, 'w') as f:
        json.dump(clients, f, indent=2)

def find_clients_by_phone(last_digits):
    """Найти клиентов по последним цифрам телефона"""
    clients = load_clients()
    return [c for c in clients if str(c['phone']).endswith(last_digits)]

def generate_keyboard():
    """Главное меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton('➕ Добавить'), types.KeyboardButton('🔍 Найти'))
    markup.row(types.KeyboardButton('📋 Список клиентов'), types.KeyboardButton('✏️ Редактировать'))
    markup.row(types.KeyboardButton('❌ Удалить'), types.KeyboardButton('📤 Экспорт'))
    return markup

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """Обработчик вебхука"""
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(commands=['start'])
def start(message):
    """Обработчик команды /start"""
    bot.send_message(message.chat.id, 
                    "📒 *Client Notes Mario Bot* готов к работе!\n"
                    "Выберите действие в меню ниже:",
                    reply_markup=generate_keyboard(),
                    parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '➕ Добавить')
def add_client_start(message):
    """Начало добавления клиента"""
    msg = bot.send_message(message.chat.id, "Введите имя клиента:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, add_client_name)

def add_client_name(message):
    """Шаг 1: Получение имени"""
    if not message.text:
        bot.send_message(message.chat.id, "Имя не может быть пустым!", reply_markup=generate_keyboard())
        return
    
    client = {'name': message.text}
    msg = bot.send_message(message.chat.id, "Введите номер телефона (только цифры):")
    bot.register_next_step_handler(msg, add_client_phone, client)

def add_client_phone(message, client):
    """Шаг 2: Получение телефона"""
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Номер должен содержать только цифры!", reply_markup=generate_keyboard())
        return
    
    client['phone'] = message.text
    msg = bot.send_message(message.chat.id, "Введите описание (стрижка, комментарии):")
    bot.register_next_step_handler(msg, add_client_finish, client)

def add_client_finish(message, client):
    """Шаг 3: Сохранение клиента"""
    client['description'] = message.text
    clients = load_clients()
    clients.append(client)
    save_clients(clients)
    
    bot.send_message(message.chat.id, 
                    f"✅ Клиент *{client['name']}* успешно добавлен!",
                    reply_markup=generate_keyboard(),
                    parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '🔍 Найти')
def find_client_start(message):
    """Поиск клиента по номеру"""
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, find_client_result)

def find_client_result(message):
    """Вывод результатов поиска"""
    clients = find_clients_by_phone(message.text)
    if not clients:
        bot.send_message(message.chat.id, "❌ Клиенты не найдены", reply_markup=generate_keyboard())
        return
    
    response = "🔍 *Найдены клиенты:*\n\n"
    for client in clients:
        response += (f"👤 *Имя:* {client['name']}\n"
                    f"📞 *Телефон:* {client['phone']}\n"
                    f"📝 *Описание:* {client['description']}\n\n")
    
    bot.send_message(message.chat.id, response, reply_markup=generate_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '📋 Список клиентов')
def list_clients(message):
    """Показать всех клиентов"""
    clients = load_clients()
    if not clients:
        bot.send_message(message.chat.id, "📭 Список клиентов пуст", reply_markup=generate_keyboard())
        return
    
    response = "📋 *Список клиентов:*\n\n"
    for client in clients:
        response += (f"👤 *{client['name']}*\n"
                    f"📞 {client['phone']}\n"
                    f"📝 {client['description']}\n\n")
    
    bot.send_message(message.chat.id, response, reply_markup=generate_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '✏️ Редактировать')
def edit_client_start(message):
    """Начало редактирования"""
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, edit_client_select)

def edit_client_select(message):
    """Выбор клиента для редактирования"""
    clients = find_clients_by_phone(message.text)
    if not clients:
        bot.send_message(message.chat.id, "❌ Клиенты не найдены", reply_markup=generate_keyboard())
        return
    
    if len(clients) > 1:
        response = "Найдено несколько клиентов:\n"
        for i, client in enumerate(clients, 1):
            response += f"{i}. {client['name']} - {client['phone']}\n"
        msg = bot.send_message(message.chat.id, response + "\nВведите номер клиента для редактирования:")
        bot.register_next_step_handler(msg, edit_client_choose_from_list, clients)
    else:
        msg = bot.send_message(message.chat.id, f"Редактируем клиента {clients[0]['name']}. Введите новое описание:")
        bot.register_next_step_handler(msg, edit_client_finish, clients[0])

def edit_client_choose_from_list(message, clients):
    """Выбор клиента из списка"""
    try:
        index = int(message.text) - 1
        if 0 <= index < len(clients):
            msg = bot.send_message(message.chat.id, f"Редактируем клиента {clients[index]['name']}. Введите новое описание:")
            bot.register_next_step_handler(msg, edit_client_finish, clients[index])
        else:
            bot.send_message(message.chat.id, "❌ Неверный номер", reply_markup=generate_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число", reply_markup=generate_keyboard())

def edit_client_finish(message, client):
    """Сохранение изменений"""
    clients = load_clients()
    for i, c in enumerate(clients):
        if c['phone'] == client['phone']:
            clients[i]['description'] = message.text
            break
    
    save_clients(clients)
    bot.send_message(message.chat.id, "✅ Описание обновлено!", reply_markup=generate_keyboard())

@bot.message_handler(func=lambda m: m.text == '❌ Удалить')
def delete_client_start(message):
    """Начало удаления"""
    msg = bot.send_message(message.chat.id, "Введите последние 4 цифры номера клиента:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, delete_client_confirm)

def delete_client_confirm(message):
    """Подтверждение удаления"""
    clients = find_clients_by_phone(message.text)
    if not clients:
        bot.send_message(message.chat.id, "❌ Клиенты не найдены", reply_markup=generate_keyboard())
        return
    
    markup = types.InlineKeyboardMarkup()
    for client in clients:
        markup.add(types.InlineKeyboardButton(
            text=f"Удалить {client['name']} ({client['phone']})",
            callback_data=f"delete_{client['phone']}"))
    
    bot.send_message(message.chat.id, "Выберите клиента для удаления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_client_final(call):
    """Финальное удаление"""
    phone = call.data.split('_')[1]
    clients = load_clients()
    clients = [c for c in clients if c['phone'] != phone]
    save_clients(clients)
    
    bot.edit_message_text("✅ Клиент удален", call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Главное меню:", reply_markup=generate_keyboard())

@bot.message_handler(func=lambda m: m.text == '📤 Экспорт')
def export_clients(message):
    """Экспорт в Excel"""
    try:
        clients = load_clients()
        if not clients:
            bot.send_message(message.chat.id, "❌ Нет данных для экспорта", reply_markup=generate_keyboard())
            return
        
        df = pd.DataFrame(clients)
        df.to_excel(EXCEL_FILE, index=False)
        
        with open(EXCEL_FILE, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📤 Список клиентов")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка экспорта: {str(e)}", reply_markup=generate_keyboard())

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == '__main__':
    print("Удаляем старый вебхук...")
    bot.remove_webhook()
    time.sleep(1)
    
    print(f"Устанавливаем вебхук: {WEBHOOK_URL}")
    bot.set_webhook(url=WEBHOOK_URL)
    
    print("Запускаем сервер...")
    serve(app, host="0.0.0.0", port=10000)
