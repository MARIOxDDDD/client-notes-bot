import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import os

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ADD_NAME, ADD_PHONE, ADD_DESC = range(3)
NOTE_PHONE, NOTE_TEXT = range(2)
FIND_PHONE = range(1)

client_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для заметок о клиентах. Используй /add, /note, /find.")

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите имя клиента:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите номер телефона клиента:")
    return ADD_PHONE

async def add_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Введите описание стрижки или заметку:")
    return ADD_DESC

async def add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = context.user_data['phone']
    client_data[phone] = {
        'name': context.user_data['name'],
        'desc': update.message.text,
        'notes': []
    }
    await update.message.reply_text("Клиент добавлен!")
    return ConversationHandler.END

async def note_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите последние 4 цифры номера клиента:")
    return NOTE_PHONE

async def note_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suffix = update.message.text.strip()
    for phone in client_data:
        if phone.endswith(suffix):
            context.user_data['current_phone'] = phone
            await update.message.reply_text("Введите заметку о визите:")
            return NOTE_TEXT
    await update.message.reply_text("Клиент не найден.")
    return ConversationHandler.END

async def note_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.text
    phone = context.user_data['current_phone']
    client_data[phone]['notes'].append(note)
    await update.message.reply_text("Заметка добавлена!")
    return ConversationHandler.END

async def find_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите последние 4 цифры номера клиента:")
    return FIND_PHONE

async def find_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suffix = update.message.text.strip()
    for phone in client_data:
        if phone.endswith(suffix):
            client = client_data[phone]
            notes = "\n".join(client['notes']) if client['notes'] else "Нет заметок."
            await update.message.reply_text(
                f"Имя: {client['name']}\nТелефон: {phone}\nОписание: {client['desc']}\nЗаметки:\n{notes}"
            )
            return ConversationHandler.END
    await update.message.reply_text("Клиент не найден.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_phone)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    note_conv = ConversationHandler(
        entry_points=[CommandHandler("note", note_start)],
        states={
            NOTE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, note_phone)],
            NOTE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, note_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    find_conv = ConversationHandler(
        entry_points=[CommandHandler("find", find_start)],
        states={
            FIND_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, find_client)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_conv)
    app.add_handler(note_conv)
    app.add_handler(find_conv)

    app.run_polling()

if __name__ == "__main__":
    main()
