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
  Coimbatore: 794,
  Bangalore: 7,
  Ramnad: 1970,
  Salem: 868,
  Erode: 867,
  Namakkal: 1859,
  Tirupathi: 12,
  Tiruvannamalai: 3197,
  Tirupattur: 2127,
  Madurai: 1016,
  Polur: 8187,
  Thirunalveli: 2123,
  Thiruchendur: 3179,
  Trichy: 795,
  Tiruchirappalli: 795,
};

// --- Fetch AbhiBus services ---
async function fetchAbhiBusServices(fromCity, toCity, travelDate, sortBy = "fare") {
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

    // Sorting
    if (sortBy === "time") {
      services = services.sort(
        (a, b) => new Date(`1970-01-01T${a.startTime}`) - new Date(`1970-01-01T${b.startTime}`)
      );
    } else {
      services = services.sort((a, b) => parseInt(a.fare) - parseInt(b.fare));
    }

    // Limit to top 30
    services = services.slice(0, 30);

    // Format messages
    const messages = [];
    let currentMessage = `🚌 *Top 30 Bus Services (sorted by ${sortBy})*\n\n`;
    let counter = 1;

    for (const s of services) {
      const line = `${counter}️⃣ ${s.travelerAgentName} | ${s.busTypeName}\n   ${s.startTime} → ${s.arriveTime} | ${s.availableSeats} seats | ₹${s.fare}\n\n`;

      if (currentMessage.length + line.length > 3500) {
        messages.push(currentMessage);
        currentMessage = "";
      }

      currentMessage += line;
      counter++;
    }

    if (currentMessage) messages.push(currentMessage);

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

  // Expected format: FromCity ToCity DD-MM-YYYY [fare|time]
  const parts = text.split(/\s+/);
  if (parts.length < 3 || parts.length > 4) {
    bot.sendMessage(chatId, "❌ Invalid format. Use:\nFromCity ToCity DD-MM-YYYY [fare|time]");
    return;
  }

  const [fromCity, toCity, travelDate, sortByInput] = parts;
  const sortBy = sortByInput?.toLowerCase() === "time" ? "time" : "fare";

  const result = await fetchAbhiBusServices(fromCity, toCity, travelDate, sortBy);

  if (Array.isArray(result)) {
    for (const msgChunk of result) {
      await bot.sendMessage(chatId, msgChunk, { parse_mode: "Markdown" });
    }
  } else {
    await bot.sendMessage(chatId, result);
  }
});
