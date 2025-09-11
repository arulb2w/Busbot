import fetch from "node-fetch";

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

function formatDate(dateStr) {
  const [dd, mm, yyyy] = dateStr.split("-");
  return `${yyyy}-${mm}-${dd}`;
}

function parseTime(timeStr) {
  if (!timeStr) return Number.MAX_SAFE_INTEGER;
  const [time, modifier] = timeStr.split(" ");
  let [hours, minutes] = time.split(":").map(Number);

  if (modifier === "PM" && hours < 12) hours += 12;
  if (modifier === "AM" && hours === 12) hours = 0;

  return hours * 60 + minutes;
}

export async function fetchAbhiBusServices(fromCity, toCity, travelDate, sortOrder = "fare") {
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
    jdate: formatDate(travelDate),
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

    // Sort results
    if (sortOrder === "fare") {
      services.sort((a, b) => (a.fare || 0) - (b.fare || 0));
    } else if (sortOrder === "time") {
      services.sort((a, b) => parseTime(a.startTime) - parseTime(b.startTime));
    }

    return services.slice(0, 30); // raw list, frontend/Telegram will format
  } catch (err) {
    return [`❌ Error fetching buses: ${err.message}`];
  }
}
