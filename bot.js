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

// --- Helper: convert "dd-mm-yyyy" → "yyyy-mm-dd" ---
function formatDate(dateStr) {
  const [dd, mm, yyyy] = dateStr.split("-");
  return `${yyyy}-${mm}-${dd}`;
}

// --- Parse time "hh:mm AM/PM" into minutes since midnight ---
function parseTime(timeStr) {
  if (!timeStr) return Number.MAX_SAFE_INTEGER;
  const [time, modifier] = timeStr.split(" ");
  let [hours, minutes] = time.split(":").map(Number);

  if (modifier === "PM" && hours < 12) hours += 12;
  if (modifier === "AM" && hours === 12) hours = 0;

  return hours * 60 + minutes;
}

// --- Fetch AbhiBus services ---
async function fetchAbhiBusServices(fromCity, toCity, travelDate, sortOrder = "fare") {
  const fromId = ABHIBUS_CITY_IDS[fromCity];
  const toId = ABHIBUS_CITY_IDS[toCity];
  if (!fromId || !toId) {
    return [`⚠️ City not found in mapping: ${fromCity} or ${toCity}`];
  }

  const payload = {
    source: fromCity,
    sourceid: fromId,
    destination: toCity,
    destinationid: toId,
    jdate: formatDate(travelDate), // yyyy-mm-dd
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
      return [`⚠️ AbhiBus API failed with status: ${response.status}`];
    }

    const data = await response.json();
    if (data.status !== "Success") {
      return [`⚠️ AbhiBus error: ${data.message}`];
    }

    let services = data.serviceDetailsList || [];
    if (services.length === 0) {
      return ["❌ No buses found for this route/date."];
    }

    // --- Sorting logic ---
    if (sortOrder === "fare") {
      services.sort((a, b) => (a.fare || 0) - (b.fare || 0));
    } else if (sortOrder === "time") {
      services.sort((a, b) => parseTime(a.startTime) - parseTime(b.startTime));
    }

    // --- Limit results (max 30) ---
    services = services.slice(0, 30);

    // --- Build formatted message ---
    const messages = [];
    let currentMessage = `🚌 Top ${services.length} Bus Services (sorted by ${sortOrder})\n\n`;

    services.forEach((s, idx) => {
      const fareStr = s.fare ? s.fare.toString().replace(".00", "") : "N/A";
      const line =
        `${idx + 1}) <b>${s.travelerAgentName}</b> | ${s.busTypeName}\n` +
        `${s.startTime} → ${s.arriveTime} | ${s.availableSeats} seats | <b>₹${fareStr}</b>\n\n`;

      if (currentMessage.length + line.length > 3500) {
        messages.push(currentMessage);
        currentMessage = "";
      }
      currentMessage += line;
    });

    if (currentMessage) messages.push(currentMessage);

    return messages;
  } catch (err) {
    return [`❌ Error fetching buses: ${err.message}`];
  }
}

// --- Telegram listener ---
bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text?.trim();

  if (!text) return;
  console.log("📩 Received message:", text);

  // Format: FromCity ToCity DD-MM-YYYY [fare|time]
  const parts = text.split(/\s+/);
  if (parts.length < 3) {
    bot.sendMessage(chatId, "❌ Invalid format. Use:\nFromCity ToCity DD-MM-YYYY [fare|time]");
    return;
  }

  const [fromCity, toCity, travelDate, sortOrder = "fare"] = parts;

  const result = await fetchAbhiBusServices(fromCity, toCity, travelDate, sortOrder.toLowerCase());

  for (const msgChunk of result) {
    await bot.sendMessage(chatId, msgChunk, { parse_mode: "HTML" });
  }
});
