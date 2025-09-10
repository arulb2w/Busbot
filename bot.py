import logging
import sys
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from scrapers import fetch_abhibus_services

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("bot")

# --- Telegram Bot Token ---
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set in environment variables")
    raise SystemExit("TELEGRAM_BOT_TOKEN missing!")

# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "👋 Hi! Send me:\n\n`/bus FROM TO DATE`\n\nExample:\n`/bus Chennai Erode 13-09-2025`"
    print("📨 /start called by", update.effective_user.username)
    await update.message.reply_text(msg)

# --- /bus command ---
async def bus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 3:
            msg = "⚠️ Usage: `/bus FROM TO DATE`\nExample: `/bus Chennai Erode 13-09-2025`"
            print("⚠️ Wrong usage by", update.effective_user.username)
            await update.message.reply_text(msg, parse_mode="Markdown")
            return

        from_city, to_city, travel_date = args
        print(f"📡 Request: {from_city} → {to_city} on {travel_date}")
        logger.info(f"Fetching buses {from_city} → {to_city} on {travel_date}")

        buses = fetch_abhibus_services(from_city, to_city, travel_date)

        if not buses:
            msg = f"❌ No buses found from {from_city} to {to_city} on {travel_date}"
            print(msg)
            await update.message.reply_text(msg)
            return

        reply_lines = []
        for bus in buses[:10]:  # limit to 10 buses
            line = (
                f"🚌 {bus['operator']} ({bus['busType']})\n"
                f"⏰ {bus['startTime']} → {bus['arriveTime']}\n"
                f"💺 Seats: {bus['availableSeats']} | 💰 ₹{bus['fare']}\n"
            )
            reply_lines.append(line)

        reply_text = "\n".join(reply_lines)
        print(f"✅ Sending {len(buses[:10])} buses to user {update.effective_user.username}")
        await update.message.reply_text(reply_text)

    except Exception as e:
        logger.exception("Error in /bus command")
        print("🔥 Error in /bus:", e)
        await update.message.reply_text("⚠️ Sorry, something went wrong while fetching buses.")

# --- Main entry ---
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bus", bus))

    print("🚀 Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
