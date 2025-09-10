const axios = require('axios');
const TelegramBot = require('node-telegram-bot-api');

// Load token from environment variable
const BOT_TOKEN = process.env.BOT_TOKEN;

if (!BOT_TOKEN) {
    console.error("Error: BOT_TOKEN environment variable not set");
    process.exit(1);
}

// Create Telegram bot
const bot = new TelegramBot(BOT_TOKEN, { polling: true });

// AbhiBus City IDs
const ABHIBUS_CITY_IDS = {
    "Chennai": 6,
    "Bangalore": 7,
    "Ramnad": 1970,
    "Salem": 868,
    "Erode": 867,
    "Namakkal": 1859
};

// Helper to format date from dd-mm-yyyy → yyyy-mm-dd
function formatDate(dateStr) {
    const [dd, mm, yyyy] = dateStr.split("-");
    return `${yyyy}-${mm}-${dd}`;
}

// Fetch AbhiBus services
async function fetchAbhibusServices(fromCity, toCity, travelDate) {
    const fromId = ABHIBUS_CITY_IDS[fromCity];
    const toId = ABHIBUS_CITY_IDS[toCity];

    if (!fromId || !toId) {
        console.warn("City ID missing for AbhiBus");
        return [];
    }

    const payload = {
        source: fromCity,
        sourceid: fromId,
        destination: toCity,
        destinationid: toId,
        jdate: formatDate(travelDate),
        prd: "mobile",
        filters: 1,
        isReturnJourney: "0"
    };

    try {
        const response = await axios.post(
            "https://www.abhibus.com/wap/GetBusList",
            payload,
            { headers: { "User-Agent": "Mozilla/5.0" }, timeout: 35000 }
        );

        console.log(`[DEBUG] AbhiBus HTTP status: ${response.status}`);

        const data = response.data;

        if (data.status !== "Success") {
            console.warn(`AbhiBus API failed: ${data.message}`);
            return [];
        }

        const services = data.serviceDetailsList.map(s => ({
            operator: s.travelerAgentName,
            busType: s.busTypeName,
            startTime: s.startTime,
            arriveTime: s.arriveTime,
            availableSeats: s.availableSeats,
            fare: s.fare,
            boardingPoints: s.boardingInfoList.map(bp => bp.placeName),
            droppingPoints: s.droppingInfoList.map(dp => dp.placeName)
        }));

        return services;

    } catch (err) {
        console.error(`Error fetching AbhiBus: ${err.message}`);
        return [];
    }
}

// Handle Telegram messages
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    console.log(`Received message: ${text}`);

    // Expecting format: from-to-date (e.g., Chennai-Erode-13-09-2025)
    const match = text.match(/^(\w+)-(\w+)-(\d{2}-\d{2}-\d{4})$/);
    if (!match) {
        bot.sendMessage(chatId, "Invalid format. Use: FromCity-ToCity-dd-mm-yyyy\nExample: Chennai-Erode-13-09-2025");
        return;
    }

    const [, fromCity, toCity, travelDate] = match;

    bot.sendMessage(chatId, `Fetching buses from ${fromCity} → ${toCity} on ${travelDate}...`);

    const services = await fetchAbhibusServices(fromCity, toCity, travelDate);

    if (services.length === 0) {
        bot.sendMessage(chatId, "No services found or API failed.");
        return;
    }

    const reply = services.map(bus =>
        `${bus.operator} | ${bus.busType} | ${bus.startTime} → ${bus.arriveTime} | Seats: ${bus.availableSeats} | Fare: ₹${bus.fare}`
    ).join("\n\n");

    bot.sendMessage(chatId, reply);
});
