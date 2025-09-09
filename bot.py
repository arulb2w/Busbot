import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load Bot Token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is missing!")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi, I’m BusSaver – your smart bus fare comparison assistant!\n\n"
        "Just tell me:\n"
        "1️⃣ From city\n"
        "2️⃣ To city\n"
        "3️⃣ Date of travel (DD-MM-YYYY)\n\n"
        "And I’ll find you the best deals 🚍💰"
    )

# Handle text messages (basic echo for now)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"User said: {user_text}")

    # TODO: Replace with API call to fetch bus fares
    await update.message.reply_text(
        f"🔎 You entered: {user_text}\n\n"
        "👉 (Later this will show bus fare comparisons here!)"
    )

# Health check command
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! The bot is alive.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run bot
    logger.info("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
