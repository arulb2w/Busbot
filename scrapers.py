import requests
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Simple in-memory cache ---
_cache = {}
CACHE_TTL = 600  # 10 minutes

# --- City ID mappings for AbhiBus ---
ABHIBUS_CITY_IDS = {
    "Chennai": 6,
    "Bangalore": 7,
    "Ramnad": 1970,
    "Salem": 868,
    "Erode": 867,
    "Namakkal": 1859,
}

# --- Helper: format date ---
def format_date(date_str, fmt_out="%Y-%m-%d"):
    dt_obj = datetime.strptime(date_str, "%d-%m-%Y")
    return dt_obj.strftime(fmt_out)

# --- AbhiBus API POST ---
def fetch_abhibus_services(from_city, to_city, travel_date):
    from_id = ABHIBUS_CITY_IDS.get(from_city)
    to_id = ABHIBUS_CITY_IDS.get(to_city)
    if not from_id or not to_id:
        logger.warning("City ID missing for AbhiBus")
        return None

    payload = {
        "source": from_city,
        "sourceid": from_id,
        "destination": to_city,
        "destinationid": to_id,
        "jdate": format_date(travel_date),  # yyyy-mm-dd
        "prd": "mobile",
        "filters": 1,
        "isReturnJourney": "0",
    }

    try:
        response = requests.post(
            "https://www.abhibus.com/wap/GetBusList",
            json=payload,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=35,
        )
        logger.info(f"[DEBUG] AbhiBus HTTP status: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "Success":
            logger.warning(f"AbhiBus API failed: {data.get('message')}")
            return None

        services = []
        for s in data.get("serviceDetailsList", []):
            services.append({
                "operator": s.get("travelerAgentName"),
                "busType": s.get("busTypeName"),
                "startTime": s.get("startTime"),
                "arriveTime": s.get("arriveTime"),
                "availableSeats": s.get("availableSeats"),
                "fare": s.get("fare"),
                "boardingPoints": [bp["placeName"] for bp in s.get("boardingInfoList", [])],
                "droppingPoints": [dp["placeName"] for dp in s.get("droppingInfoList", [])],
            })
        return services

    except Exception as e:
        logger.warning(f"AbhiBus API fetch failed: {e}")
        return None

# --- Unified fetch with caching ---
def fetch_bus_fares(from_city, to_city, travel_date):
    key = f"{from_city.strip().lower()}-{to_city.strip().lower()}-{travel_date}"
    now = time.time()

    # Return cached result if valid
    if key in _cache and now - _cache[key]["time"] < CACHE_TTL:
        logger.info(f"Using cached result for {key}")
        return _cache[key]["data"]

    services = fetch_abhibus_services(from_city, to_city, travel_date)

    _cache[key] = {"time": now, "data": services}
    logger.info(f"[DEBUG] Cached services for {key}")
    return services

# ---- Example usage ----
if __name__ == "__main__":
    buses = fetch_bus_fares("Chennai", "Erode", "13-09-2025")
    for bus in buses or []:
        print(f"{bus['operator']} | {bus['busType']} | {bus['startTime']} → {bus['arriveTime']} | "
              f"Seats: {bus['availableSeats']} | Fare: ₹{bus['fare']}")
