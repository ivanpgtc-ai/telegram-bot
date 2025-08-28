import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Настройки ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://telegram-bot-emu.onrender.com")
WEBHOOK_PATH = "/webhook"

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает через Webhook 🚀")

# --- Health-check ---
async def health(request):
    return web.Response(text="OK")

# --- Обработка вебхука ---
async def tg_webhook(request):
    data = await request.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return web.Response(text="ok")

# --- Главная функция ---
async def main():
    global application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).updater(None).build()

    # Инициализация приложения
    await application.initialize()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))

    # Создаём aiohttp-сервер
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post(WEBHOOK_PATH, tg_webhook)

    # Подключаем webhook
    webhook_url = f"{PUBLIC_URL}{WEBHOOK_PATH}"
    await application.bot.set_webhook(url=webhook_url, drop_pending_updates=True)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

    print("🚀 Bot is running with webhook:", webhook_url)

    # Запускаем бота
    await application.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

