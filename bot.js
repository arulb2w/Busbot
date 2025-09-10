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

// --- Helper: Parse "HH:MM AM/PM" to Date ---
function parseTime(timeStr) {
  const [time, modifier] = timeStr.split(" ");
  let [hours, minutes] = time.split(":").map(Number);

  if (modifier === "PM" && hours < 12) hours += 12;
  if (modifier === "AM" && hours === 12) hours = 0;

  const date = new Date();
  date.setHours(hours, minutes, 0, 0);
  return date;
}

// --- Fetch AbhiBus services ---
async function fetchAbhiBusServices(fromCity, toCity, travelDate, sortOrder) {
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

    // --- Sorting ---
    if (sortOrder === "fare") {
      services.sort((a, b) => parseFloat(a.fare) - parseFloat(b.fare));
    } else if (sortOrder === "time") {
      services.sort((a, b) => parseTime(a.startTime) - parseTime(b.startTime));
    }

    // Limit results
    services = services.slice(0, 30);

    // Emoji numbers for 1–10
    const numberEmojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"];

    // Build response
    const header = `🚌 Top ${services.length} Bus Services (sorted by ${sortOrder})\n\n`;
    let message = header;

    services.forEach((s, i) => {
      const indexNum = i < 10 ? numberEmojis[i] : `${i + 1}.`;
      message += `${indexNum} ${s.travelerAgentName} | ${s.busTypeName}\n`;
      message += `${s.startTime} → ${s.arriveTime} | ${s.availableSeats} seats | ₹${s.fare}\n\n`;
    });

    return message;
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
  if (parts.length < 3) {
    bot.sendMessage(chatId, "❌ Invalid format. Use:\nFromCity ToCity DD-MM-YYYY [fare|time]");
    return;
  }

  const [fromCity, toCity, travelDate, sortOrderRaw] = parts;
  const sortOrder = (sortOrderRaw || "fare").toLowerCase();

  const result = await fetchAbhiBusServices(fromCity, toCity, travelDate, sortOrder);

  await bot.sendMessage(chatId, result);
});
