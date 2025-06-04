import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler, CallbackQueryHandler
)

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

# Этапы диалога
ASK_ORDER, CONFIRM_ORDER = range(2)

# Список заказов (в реальности будет база данных)
orders = []

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в StuDO — студенческую биржу заданий!\n"
        "Чтобы разместить заказ, напиши /order\n"
        "Чтобы стать исполнителем, напиши /tasks"
    )

# Диалог размещения заказа
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Опиши, что тебе нужно сделать (чем подробнее, тем лучше):")
    return ASK_ORDER

async def receive_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_text"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_order")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_order")]
    ]
    await update.message.reply_text(
        f"Ты хочешь разместить заказ:\n\n{update.message.text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order = {
        "user_id": query.from_user.id,
        "username": query.from_user.username,
        "description": context.user_data.get("order_text")
    }
    orders.append(order)
    await query.edit_message_text("✅ Заказ размещён! Ожидай откликов.")
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("❌ Заказ отменён.")
    return ConversationHandler.END

# Команда для исполнителей
async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not orders:
        await update.message.reply_text("Пока нет заказов.")
        return

    msg = "📋 Активные заказы:\n\n"
    for i, order in enumerate(orders, start=1):
        msg += (
            f"{i}. {order['description']}\n"
            f"— @{order['username']} (ID: {order['user_id']})\n\n"
        )
    await update.message.reply_text(msg)

# Команда /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Главная функция
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Хэндлер для размещения заказа
    order_conv = ConversationHandler(
        entry_points=[CommandHandler("order", order_start)],
        states={
            ASK_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_order)],
            CONFIRM_ORDER: [CallbackQueryHandler(confirm_order, pattern="confirm_order"),
                            CallbackQueryHandler(cancel_order, pattern="cancel_order")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(order_conv)
    app.add_handler(CommandHandler("tasks", list_orders))
    app.add_handler(CommandHandler("cancel", cancel))

    app.run_polling()

if __name__ == "__main__":
    main()
