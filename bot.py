import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from scrapers import fetch_bus_fares   # 👈 Import unified fetch function

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

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi, I’m BusSaver – your smart bus fare comparison assistant!\n\n"
        "Use the command like this:\n"
        "👉 /compare Chennai Bangalore 15-09-2025"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong! The bot is alive.")

# --- Compare command ---
async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3:
            await update.message.reply_text(
                "⚠️ Please use the format:\n"
                "`/compare <from_city> <to_city> <dd-mm-yyyy>`",
                parse_mode="Markdown"
            )
            return

        from_city = context.args[0].capitalize()
        to_city = context.args[1].capitalize()
        travel_date = context.args[2]

        # 🔍 Fetch real fares using scrapers
        fares = fetch_bus_fares(from_city, to_city, travel_date)

        if not fares:
            await update.message.reply_text("❌ No fares found. Please try again later.")
            return

        # Find cheapest
        cheapest_app = min(fares, key=fares.get)
        cheapest_price = fares[cheapest_app]

        # Format response
        result = f"🚌 *Fare Comparison*\nRoute: {from_city} → {to_city}\nDate: {travel_date}\n\n"
        for app, price in fares.items():
            result += f"🔹 {app}: ₹{price}\n"
        result += f"\n💡 Best Deal → *{cheapest_app}* (₹{cheapest_price})"

        await update.message.reply_text(result, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in /compare: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again.")

# --- Handle free text ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"User said: {user_text}")
    await update.message.reply_text(
        "ℹ️ Use /compare instead, e.g.:\n"
        "`/compare Chennai Bangalore 15-09-2025`",
        parse_mode="Markdown"
    )

# --- Main app ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("compare", compare))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run bot
    logger.info("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
