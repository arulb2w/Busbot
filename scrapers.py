import requests
import logging
import sys
from datetime import datetime

# --- Configure logging to stdout ---
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("scrapers")

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
    # Supports both dd-mm-yyyy and yyyy-mm-dd
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            dt_obj = datetime.strptime(date_str, fmt)
            return dt_obj.strftime(fmt_out)
        except ValueError:
            continue
    raise ValueError(f"Date format not supported: {date_str}")

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
        logger.debug(f"AbhiBus HTTP status: {response.status_code}")
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "Success":
            logger.error(f"AbhiBus API failed: {data.get('message')}")
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
        logger.exception(f"AbhiBus API fetch failed: {e}")
        return None

# ---- Example usage ----
if __name__ == "__main__":
    buses = fetch_abhibus_services("Chennai", "Erode", "13-09-2025")
    for bus in buses or []:
        print(f"{bus['operator']} | {bus['busType']} | {bus['startTime']} → {bus['arriveTime']} | "
              f"Seats: {bus['availableSeats']} | Fare: ₹{bus['fare']}")
