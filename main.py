from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# Словари для хранения данных (в реальной жизни - база данных)
users = {}       # user_id: {"role": "client" или "freelancer"}
tasks = []       # список задач: {"id": int, "title": str, "description": str, "author_id": int, "responses": [user_id]}

task_id_counter = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Я заказчик", callback_data="role_client")],
        [InlineKeyboardButton("Я исполнитель", callback_data="role_freelancer")]
    ]
    await update.message.reply_text("Привет! Выбери свою роль:", reply_markup=InlineKeyboardMarkup(keyboard))

async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    role = "client" if query.data == "role_client" else "freelancer"
    users[user_id] = {"role": role}
    await query.edit_message_text(f"Вы выбрали роль: {role}.")
    
    if role == "client":
        await query.message.reply_text("Теперь вы можете добавить задание командой /addtask")
    else:
        await query.message.reply_text("Вы можете просмотреть задания командой /tasks")

async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users or users[user_id]["role"] != "client":
        await update.message.reply_text("Только заказчики могут добавлять задания.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Используйте команду в формате:\n/addtask <название задания> | <описание>")
        return
    
    # Пример: /addtask Дизайн логотипа | Нужно разработать логотип для сайта
    text = update.message.text.split(' ', 1)[1]
    if '|' not in text:
        await update.message.reply_text("Используйте разделитель | между названием и описанием.")
        return
    
    global task_id_counter
    title, description = map(str.strip, text.split('|', 1))
    
    tasks.append({
        "id": task_id_counter,
        "title": title,
        "description": description,
        "author_id": user_id,
        "responses": []
    })
    
    await update.message.reply_text(f"Задание добавлено с ID {task_id_counter}.")
    task_id_counter += 1

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users:
        await update.message.reply_text("Сначала выберите роль командой /start")
        return
    
    if not tasks:
        await update.message.reply_text("Пока нет доступных заданий.")
        return
    
    msg = "Доступные задания:\n"
    for task in tasks:
        msg += f"\nID: {task['id']}\nНазвание: {task['title']}\nОписание: {task['description']}\n"
        msg += f"Откликнуться: /respond {task['id']}\n"
    await update.message.reply_text(msg)

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users or users[user_id]["role"] != "freelancer":
        await update.message.reply_text("Только исполнители могут откликаться на задания.")
        return
    
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Используйте команду в формате:\n/respond <ID задания>")
        return
    
    task_id = int(context.args[0])
    for task in tasks:
        if task["id"] == task_id:
            if user_id in task["responses"]:
                await update.message.reply_text("Вы уже откликнулись на это задание.")
                return

task["responses"].append(user_id)
            await update.message.reply_text(f"Вы откликнулись на задание {task['title']}.")
            # Можно уведомить заказчика (автора задания)
            return
    await update.message.reply_text("Задание с таким ID не найдено.")

async def mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users or users[user_id]["role"] != "client":
        await update.message.reply_text("Только заказчики могут просматривать свои задания.")
        return
    
    my_tasks = [task for task in tasks if task["author_id"] == user_id]
    if not my_tasks:
        await update.message.reply_text("У вас пока нет заданий.")
        return
    
    msg = "Ваши задания:\n"
    for task in my_tasks:
        msg += f"\nID: {task['id']}\nНазвание: {task['title']}\nОписание: {task['description']}\nОтклики: {len(task['responses'])}\n"
    await update.message.reply_text(msg)

app = ApplicationBuilder().token("ТВОЙ_ТОКЕН").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(set_role, pattern="role_"))
app.add_handler(CommandHandler("addtask", addtask))
app.add_handler(CommandHandler("tasks", list_tasks))
app.add_handler(CommandHandler("respond", respond))
app.add_handler(CommandHandler("mytasks", mytasks))

app.run_polling()
