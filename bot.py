import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from scrapers import fetch_bus_fares

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Command handler ---
async def buses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Allow user input like: /buses Chennai Erode 13-09-2025
        if len(context.args) >= 3:
            from_city = context.args[0]
            to_city = context.args[1]
            travel_date = context.args[2]
        else:
            await update.message.reply_text("⚠️ Usage: /buses <from_city> <to_city> <dd-mm-yyyy>")
            return

        result = fetch_bus_fares(from_city, to_city, travel_date)

        if not result or "services" not in result:
            await update.message.reply_text("⚠️ No buses found.")
            return

        # Build response
        response_lines = []
        for bus in result["services"][:10]:  # show only first 10 buses
            response_lines.append(
                f"{bus['operator']} | {bus['busType']} | "
                f"{bus['startTime']} → {bus['arriveTime']} | "
                f"Seats: {bus['availableSeats']} | Fare: ₹{bus['fare']}"
            )

        await update.message.reply_text("\n".join(response_lines))

    except Exception as e:
        logger.error(f"Error fetching buses: {e}")
        await update.message.reply_text("❌ Something went wrong while fetching bus details.")

# --- Main entrypoint ---
def main():
    # ✅ Use the same token logic as your old bot.py
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable not set!")

    app = Application.builder().token(token).build()

    # Register commands
    app.add_handler(CommandHandler("buses", buses))

    # Start bot (keeps waiting for user commands)
    logger.info("🚀 Bot started and waiting for commands...")
    app.run_polling()

if __name__ == "__main__":
    main()
