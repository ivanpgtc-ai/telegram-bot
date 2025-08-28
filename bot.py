import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from openai import OpenAI

# --- ENV ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PUBLIC_URL     = os.getenv("PUBLIC_URL")  # напр. https://telegram-bot-emnu.onrender.com
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_PATH   = "/webhook"

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Команды ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я на базе OpenAI. Пиши запрос — отвечу по делу ⚙️"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я отвечаю на любые вопросы и помогаю с рабочими задачами.\n"
        "▪️ /start — запуск\n"
        "▪️ Просто напиши текст — получишь ответ ИИ"
    )

# --- AI-ответ на любой текст ---
async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = (update.message.text or "").strip()
    if not user_text:
        return

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник по продажам электроники. "
                        "Отвечай по-деловому, честно, без воды; допускается корпоративный жаргон. "
                        "Смотри в будущее, предлагай следующие шаги. Отвечай по-русски."
                    )
                },
                {"role": "user", "content": user_text},
            ],
            temperature=0.3,
            max_tokens=600,
        )
        answer = resp.choices[0].message.content.strip()
        await update.message.reply_text(answer[:4000])  # лимит телеги
    except Exception as e:
        await update.message.reply_text("⚠️ Ошибка при запросе к ИИ. Проверь токен/лимиты.")
        print("OpenAI error:", e)

# --- Health-check ---
async def health(_request): return web.Response(text="OK")

# --- Обработка вебхука от Telegram ---
async def tg_webhook(request):
    data = await request.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return web.Response(text="ok")

# --- Главная корутина ---
async def main():
    global application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).updater(None).build()

    # Хендлеры
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))

    # Обязательная инициализация до старта
    await application.initialize()

    # AIOHTTP-сервер
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post(WEBHOOK_PATH, tg_webhook)

    # Вебхук
    webhook_url = f"{PUBLIC_URL}{WEBHOOK_PATH}"
    await application.bot.set_webhook(url=webhook_url, drop_pending_updates=True)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("🚀 Bot is running with webhook:", webhook_url)
    await application.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
