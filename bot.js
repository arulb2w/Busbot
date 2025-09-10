// bot.js
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const moment = require('moment');

// Load bot token from environment variable
const BOT_TOKEN = process.env.BOT_TOKEN;
if (!BOT_TOKEN) {
    console.error("Error: BOT_TOKEN not set in environment variables");
    process.exit(1);
}

// Initialize bot
const bot = new TelegramBot(BOT_TOKEN, { polling: true });

// --- City ID mappings for AbhiBus ---
const ABHIBUS_CITY_IDS = {
    "Chennai": 6,
    "Bangalore": 7,
    "Ramnad": 1970,
    "Salem": 868,
    "Erode": 867,
    "Namakkal": 1859,
};

// --- Format date to yyyy-mm-dd ---
function formatDate(dateStr) {
    return moment(dateStr, 'DD-MM-YYYY').format('YYYY-MM-DD');
}

// --- Fetch AbhiBus services ---
async function fetchAbhibusServices(fromCity, toCity, travelDate) {
    const fromId = ABHIBUS_CITY_IDS[fromCity];
    const toId = ABHIBUS_CITY_IDS[toCity];

    if (!fromId || !toId) {
        console.warn("City ID missing for AbhiBus");
        return null;
    }

    const payload = {
        source: fromCity,
        sourceid: fromId,
        destination: toCity,
        destinationid: toId,
        jdate: formatDate(travelDate),
        prd: "mobile",
        filters: 1,
        isReturnJourney: "0",
    };

    try {
        const response = await axios.post(
            "https://www.abhibus.com/wap/GetBusList",
            payload,
            { headers: { "User-Agent": "Mozilla/5.0" }, timeout: 35000 }
        );
        console.info(`[DEBUG] AbhiBus HTTP status: ${response.status}`);

        const data = response.data;
        if (data.status !== "Success") {
            console.warn(`AbhiBus API failed: ${data.message}`);
            return null;
        }

        const services = data.serviceDetailsList.map(s => ({
            operator: s.travelerAgentName,
            busType: s.busTypeName,
            startTime: s.startTime,
            arriveTime: s.arriveTime,
            availableSeats: s.availableSeats,
            fare: s.fare,
            boardingPoints: s.boardingInfoList.map(bp => bp.placeName),
            droppingPoints: s.droppingInfoList.map(dp => dp.placeName),
        }));

        return services;

    } catch (error) {
        console.warn(`AbhiBus API fetch failed: ${error}`);
        return null;
    }
}

// --- Split long messages ---
function chunkMessage(text, maxLength = 4000) {
    const chunks = [];
    let start = 0;
    while (start < text.length) {
        chunks.push(text.slice(start, start + maxLength));
        start += maxLength;
    }
    return chunks;
}

// --- Handle Telegram messages ---
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text?.trim();

    if (!text) return;

    console.info(`Received message: ${text}`);

    // Expected format: Chennai-Erode-14-09-2025
    const parts = text.split("-");
    if (parts.length !== 3) {
        bot.sendMessage(chatId, "Invalid format. Use: FromCity-ToCity-DD-MM-YYYY");
        return;
    }

    const [fromCity, toCity, travelDate] = parts;

    try {
        const buses = await fetchAbhibusServices(fromCity, toCity, travelDate);
        if (!buses || buses.length === 0) {
            bot.sendMessage(chatId, "No buses found for this route/date.");
            return;
        }

        let messageText = "";
        for (const bus of buses) {
            messageText += `${bus.operator} | ${bus.busType} | ${bus.startTime} → ${bus.arriveTime} | Seats: ${bus.availableSeats} | Fare: ₹${bus.fare}\n`;
        }

        const messages = chunkMessage(messageText);
        for (const chunk of messages) {
            await bot.sendMessage(chatId, chunk);
        }

    } catch (error) {
        console.error(`Error fetching buses: ${error}`);
        bot.sendMessage(chatId, "Error fetching buses. Please try again later.");
    }
});
