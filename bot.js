import TelegramBot from "node-telegram-bot-api";
import dotenv from "dotenv";
import { fetchAbhiBusServices } from "./busService.js";

dotenv.config();

const BOT_TOKEN = process.env.BOT_TOKEN;
if (!BOT_TOKEN) {
  console.error("❌ BOT_TOKEN not set in environment variables");
  process.exit(1);
}

const bot = new TelegramBot(BOT_TOKEN, { polling: true });
console.log("✅ Bot is running...");

bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text?.trim();
  if (!text) return;

  const parts = text.split(/\s+/);
  if (parts.length < 3) {
    bot.sendMessage(chatId, "❌ Invalid format. Use:\nFromCity ToCity DD-MM-YYYY [fare|time]");
    return;
  }

  const [fromCity, toCity, travelDate, sortOrder = "fare"] = parts;

  const result = await fetchAbhiBusServices(fromCity, toCity, travelDate, sortOrder.toLowerCase());

  if (Array.isArray(result) && typeof result[0] === "string") {
    // error messages
    for (const msgChunk of result) {
      await bot.sendMessage(chatId, msgChunk, { parse_mode: "HTML" });
    }
  } else {
    // success – format results
    let message = `🚌 Top ${result.length} Bus Services (sorted by ${sortOrder})\n\n`;
    result.forEach((s, idx) => {
      const fareStr = s.fare ? s.fare.toString().replace(".00", "") : "N/A";
      message +=
        `${idx + 1}) <b>${s.travelerAgentName}</b> | ${s.busTypeName}\n` +
        `${s.startTime} → ${s.arriveTime} | ${s.availableSeats} seats | <b>₹${fareStr}</b>\n\n`;
    });

    await bot.sendMessage(chatId, message, { parse_mode: "HTML" });
  }
});
