import telegram
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
import tracemalloc
import logging

# Почни со следење на меморијата (Memory trace)
tracemalloc.start()

# Вашиот Telegram Bot Token
TOKEN = '7629158366:AAF1u_AZahxm3DuCgaUqJRSRAuLzpnQ7MTY'
CHAT_ID = '924330214'  # ID на групата или индивидуалниот контакт

# Асинхрона функција за испраќање пораки на Telegram
async def send_telegram_message(message: str, bot):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)  # Испраќа порака на дефинираниот чат ID
        print("Пораката беше успешно испратена до Telegram")  # Потврда во конзолата
    except Exception as e:
        print(f"Грешка при испраќање порака: {e}")  # Прикажување на грешка во случај на неуспех

# Функција за обработка на пораката
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Ова е одговор од ботот!"  # Пораката која ќе се испрати
    await send_telegram_message(message, context.bot)  # Испраќање на пораката

# Функција за обработка на командата за статистика
async def send_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, results=None):
    # Создавање на порака со статистика
    message = "Просечно потрошувачка по старосни групи:\n"
    for age_range, avg_spent in results.items():  # Преработка на резултатите
        message += f"{age_range}: {avg_spent}\n"

    # Испраќање на статистиката до Telegram
    await send_telegram_message(message, context.bot)

    # Порака за потврда дека статистиките се испратени
    await update.message.reply_text("Статистиките се испратени до менаџментот!")  # Потврда до корисникот

# Главна извршна логика
if __name__ == '__main__':
    print('Стартува ботот....')  # Потврда во конзолата дека ботот започнал
    app = Application.builder().token(TOKEN).build()  # Инициализирање на Telegram апликацијата

    # Додавање на хендлери за командите
    app.add_handler(CommandHandler('send_stats', send_stats_command))  # Команда за испраќање статистика

    # Започни со работа на ботот
    app.run_polling()  # Започнување на ботот за да почне да прима и одговара на пораки
