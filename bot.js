import TelegramBot from "node-telegram-bot-api";
import fetch from "node-fetch";
import dotenv from "dotenv";

dotenv.config();

const BOT_TOKEN = process.env.BOT_TOKEN;
if (!BOT_TOKEN) {
  console.error("❌ BOT_TOKEN not set in environment variables");
  process.exit(1);
}

const bot = new TelegramBot(BOT_TOKEN, { polling: true });

console.log("✅ Bot is running...");

// --- City ID mappings for AbhiBus ---
const ABHIBUS_CITY_IDS = {
  Chennai: 6,
  Bangalore: 7,
  Ramnad: 1970,
  Salem: 868,
  Erode: 867,
  Namakkal: 1859,
};

// --- Fetch AbhiBus services ---
async function fetchAbhiBusServices(fromCity, toCity, travelDate) {
  const fromId = ABHIBUS_CITY_IDS[fromCity];
  const toId = ABHIBUS_CITY_IDS[toCity];
  if (!fromId || !toId) {
    return `⚠️ City not found in mapping: ${fromCity} or ${toCity}`;
  }

  const payload = {
    source: fromCity,
    sourceid: fromId,
    destination: toCity,
    destinationid: toId,
    jdate: travelDate.split("-").reverse().join("-"), // dd-mm-yyyy → yyyy-mm-dd
    prd: "mobile",
    filters: 1,
    isReturnJourney: "0",
  };

  try {
    const response = await fetch("https://www.abhibus.com/wap/GetBusList", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      return `⚠️ AbhiBus API failed with status: ${response.status}`;
    }

    const data = await response.json();
    if (data.status !== "Success") {
      return `⚠️ AbhiBus error: ${data.message}`;
    }

    let services = data.serviceDetailsList || [];
    if (services.length === 0) {
      return "❌ No buses found for this route/date.";
    }

    // --- sort by fare and pick top 20 ---
    services = services.sort((a, b) => a.fare - b.fare).slice(0, 20);

    // --- Build Markdown table ---
    let header = `*Top ${services.length} Cheapest Bus Services*\n`;
    header += "`Operator             | Type        | Start → Arrive | Seats | Fare`\n";
    header += "`--------------------|-------------|----------------|-------|-------`\n";

    const messages = [];
    let currentMessage = header;

    for (const s of services) {
      const operator =
        s.travelerAgentName.length > 20
          ? s.travelerAgentName.substring(0, 17) + "..."
          : s.travelerAgentName;

      const line =
        `\`${operator.padEnd(20)}|` +
        `${s.busTypeName.padEnd(12)}|` +
        `${s.startTime.padEnd(8)}→${s.arriveTime.padEnd(8)}|` +
        `${String(s.availableSeats).padEnd(7)}|` +
        `₹${s.fare}\`\n`;

      if (currentMessage.length + line.length > 3500) {
        messages.push(currentMessage);
        currentMessage = header;
      }

      currentMessage += line;
    }

    if (currentMessage.trim() !== "") {
      messages.push(currentMessage);
    }

    return messages;
  } catch (err) {
    return `❌ Error fetching buses: ${err.message}`;
  }
}

// --- Telegram listener ---
bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text?.trim();

  if (!text) return;

  console.log("📩 Received message:", text);

  // Expected format: FromCity ToCity DD-MM-YYYY
  const parts = text.split(/\s+/);
  if (parts.length !== 3) {
    bot.sendMessage(
      chatId,
      "❌ Invalid format. Use:\nFromCity ToCity DD-MM-YYYY"
    );
    return;
  }

  const [fromCity, toCity, travelDate] = parts;

  const result = await fetchAbhiBusServices(fromCity, toCity, travelDate);

  if (Array.isArray(result)) {
    for (const msgChunk of result) {
      await bot.sendMessage(chatId, msgChunk, { parse_mode: "MarkdownV2" });
    }
  } else {
    await bot.sendMessage(chatId, result);
  }
});