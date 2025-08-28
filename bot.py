import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from openai import OpenAI

# --- Конфиги ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PUBLIC_URL = os.getenv("PUBLIC_URL")  # https://telegram-bot-xxx.onrender.com
WEBHOOK_PATH = "/webhook"  # безопасный путь

client = OpenAI(api_key=OPENAI_API_KEY)
SYSTEM_PROMPT = "Ты помощник для компании GTC Rus. Отвечай четко и по делу."

# --- Хендлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет 👋 Я твой Telegram-бот GTC!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            max_tokens=200,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"Ошибка OpenAI: {e}"

    await update.message.reply_text(answer)

# --- Webhook + сервер ---
async def tg_webhook(request: web.Request):
    data = await request.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return web.Response(text="ok")

async def health(request):
    return web.Response(text="OK")

async def main():
    global application
    application = (
        ApplicationBuilder().token(TELEGRAM_TOKEN).updater(None).build()
    )

    # команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # aiohttp server
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post(WEBHOOK_PATH, tg_webhook)

    # webhook url
    webhook_url = f"{PUBLIC_URL}{WEBHOOK_PATH}"
    await application.bot.set_webhook(url=webhook_url, drop_pending_updates=True)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

    print("🚀 Bot is running with webhook:", webhook_url)
    await application.start()
    await asyncio.Event().wait()  # не даём процессу завершиться

if __name__ == "__main__":
    asyncio.run(main())
