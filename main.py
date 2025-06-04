import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes, filters, MessageHandler
)

# Хранение данных (в реальной жизни - БД)
orders = []  # каждый заказ: {id, author_id, description, price, executor_id, status}
order_id_counter = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот биржи проектов для студентов.\n\n"
        "Команды:\n"
        "/neworder - создать новый заказ\n"
        "/orders - посмотреть доступные заказы\n"
        "/myorders - мои заказы\n"
        "/takeorder <id> - взять заказ в работу\n"
        "/payorder <id> - подтвердить оплату заказа\n"
    )

async def neworder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ожидаем, что дальше пользователь пришлёт описание и цену в одном сообщении через |
    await update.message.reply_text(
        "Отправь заказ в формате:\n"
        "описание | цена\n"
        "Например:\n"
        "Сделать проект по математике | 3000"
    )
    return

async def handle_neworder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_id_counter
    text = update.message.text

    if '|' not in text:
        await update.message.reply_text("Неправильный формат. Используйте 'описание | цена'")
        return

    description, price_str = map(str.strip, text.split('|', 1))

    if not price_str.isdigit():
        await update.message.reply_text("Цена должна быть числом.")
        return

    order = {
        "id": order_id_counter,
        "author_id": update.message.from_user.id,
        "description": description,
        "price": int(price_str),
        "executor_id": None,
        "status": "open"  # open, taken, paid
    }
    orders.append(order)
    await update.message.reply_text(f"Заказ создан с ID {order_id_counter}.")
    order_id_counter += 1

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    open_orders = [o for o in orders if o['status'] == 'open']
    if not open_orders:
        await update.message.reply_text("Нет доступных заказов.")
        return
    msg = "Доступные заказы:\n"
    for o in open_orders:
        msg += f"\nID: {o['id']}\nОписание: {o['description']}\nЦена: {o['price']} тенге\n"
    msg += "\nЧтобы взять заказ, используй команду: /takeorder <ID>"
    await update.message.reply_text(msg)

async def take_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Используй: /takeorder <ID>")
        return
    order_id = int(context.args[0])
    user_id = update.message.from_user.id
    for order in orders:
        if order['id'] == order_id:
            if order['status'] != 'open':
                await update.message.reply_text("Этот заказ уже взят или оплачен.")
                return
            if order['author_id'] == user_id:
                await update.message.reply_text("Ты не можешь взять свой же заказ.")
                return
            order['executor_id'] = user_id
            order['status'] = 'taken'
            await update.message.reply_text(f"Ты взял заказ ID {order_id} в работу.")
            return
    await update.message.reply_text("Заказ с таким ID не найден.")

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_orders = [o for o in orders if o['author_id'] == user_id]
    if not user_orders:
        await update.message.reply_text("У тебя нет заказов.")
        return
    msg = "Твои заказы:\n"
    for o in user_orders:
        status = o['status']
        executor = o['executor_id'] if o['executor_id'] else "нет"
        msg += (
            f"\nID: {o['id']}\nОписание: {o['description']}\nЦена: {o['price']} тенге\n"
            f"Исполнитель: {executor}\nСтатус: {status}\n"
        )
    await update.message.reply_text(msg)

async def pay_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Используй: /payorder <ID>")
        return
    order_id = int(context.args[0])
    user_id = update.message.from_user.id
    for order in orders:
        if order['id'] == order_id:
            if order['author_id'] != user_id:
                await update.message.reply_text("Ты не можешь оплачивать чужие заказы.")
                return
            if order['status'] != 'taken':
                await update.message.reply_text("Заказ не взят в работу или уже оплачен.")
                return
            order['status'] = 'paid'
            await update.message.reply_text(f"Заказ ID {order_id} оплачен. Спасибо!")
            return
    await update.message.reply_text("Заказ с таким ID не найден.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Неизвестная команда. Используй /start чтобы увидеть команды.")

def main():
    TOKEN = os.getenv("7641233572:AAE-Zc5luR1OmPZuEAJ1okElewpkUXEVJ4c")
    app = ApplicationBuilder().token("7641233572:AAE-Zc5luR1OmPZuEAJ1okElewpkUXEVJ4c").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("neworder", neworder))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_neworder))
    app.add_handler(CommandHandler("orders", list_orders))
    app.add_handler(CommandHandler("takeorder", take_order))
    app.add_handler(CommandHandler("myorders", my_orders))
    app.add_handler(CommandHandler("payorder", pay_order))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    app.run_polling()

if __name__ == '__main__':
    main()
