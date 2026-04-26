from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
from openai import OpenAI


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

user_memory = {}
user_modes = {} 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Ask me anything 🤖")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Buyruqlar:\n"
        "/check - matnni tekshirish\n"
        "/explain - mavzuni tushuntirish\n"
        "Oddiy savol yozsangiz ham javob beraman 😊"
    )
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_modes[user_id] = "check"
    
    await update.message.reply_text("Matnni yuboring, men tekshiraman ✍️")

async def explain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args)

    prompt = f"Explain this topic simply for a student: {topic}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    await update.message.reply_text(response.choices[0].message.content)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_text = update.message.text

    mode = user_modes.get(user_id)

    # 🔥 CHECK MODE
    if mode == "check":
        prompt = f"Correct this sentence and explain mistakes: {user_text}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        reply = response.choices[0].message.content

        user_modes[user_id] = None  # reset mode

        await update.message.reply_text(reply)
        return

    # 🧠 NORMAL MEMORY CHAT
    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an Uzbek student assistant. You explain topics simply, step-by-step, like a teacher. You help with English, math, and school subjects. You give examples and exercises. Speak mostly in Uzbek, but switch to English or Russian if needed."}
        ] + user_memory[user_id]
    )

    reply = response.choices[0].message.content

    user_memory[user_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("check", check_command))
app.add_handler(CommandHandler("explain", explain_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


app.run_polling()