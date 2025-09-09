import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Simple in-memory cache ---
_cache = {}
CACHE_TTL = 600  # 10 minutes

# --- City ID mappings ---
REDBUS_CITY_IDS = {
    "Chennai": 123,
    "Bangalore": 122,
    "Madurai": 126,
    "Erode": 236,
    "Salem": 602,
    "Ramanathapuram": 80089,
    "Namakkal": 364,
}

ABHIBUS_CITY_IDS = {
    "Chennai": 6,
    "Bangalore": 7,
    "Ramnad": 1970,
    "Salem": 868,
    "Erode": 867,
    "Namakkal": 1859,
}

# --- Helper: format date ---
def format_date(date_str, fmt_out="%d-%b-%Y"):
    dt_obj = datetime.strptime(date_str, "%d-%m-%Y")
    return dt_obj.strftime(fmt_out)

# ---- RedBus URL ----
def format_redbus_url(from_city, to_city, travel_date):
    from_id = REDBUS_CITY_IDS.get(from_city)
    to_id = REDBUS_CITY_IDS.get(to_city)
    if not from_id or not to_id:
        logger.warning("City ID missing for RedBus")
        return None
    date_str = format_date(travel_date)
    url = (
        f"https://www.redbus.in/bus-tickets/{from_city.lower()}-to-{to_city.lower()}?"
        f"fromCityId={from_id}&fromCityName={from_city}&toCityId={to_id}&toCityName={to_city}"
        f"&onward={date_str}&doj={date_str}"
    )
    print(f"[DEBUG] Accessing RedBus URL: {url}")  # <-- Added print
    return url

# ---- AbhiBus URL ----
def format_abhibus_url(from_city, to_city, travel_date):
    from_id = ABHIBUS_CITY_IDS.get(from_city)
    to_id = ABHIBUS_CITY_IDS.get(to_city)
    if not from_id or not to_id:
        logger.warning("City ID missing for AbhiBus")
        return None
    url = f"https://www.abhibus.com/bus_search/{from_city}/{from_id}/{to_city}/{to_id}/{travel_date}/O"
    print(f"[DEBUG] Accessing AbhiBus URL: {url}")  # <-- Added print
    return url

# ---- Scrapers ----
def scrape_redbus_fares(from_city, to_city, travel_date):
    url = format_redbus_url(from_city, to_city, travel_date)
    if not url:
        return None
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=35)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        fares = []
        for price in soup.select(".fare, .fare d-block"):
            fare_text = price.get_text(strip=True).replace("₹", "").replace(",", "")
            if fare_text.isdigit():
                fares.append(int(fare_text))
        return min(fares) if fares else None
    except Exception as e:
        logger.warning(f"RedBus scraping failed: {e}")
        return None

def scrape_abhibus_fares(from_city, to_city, travel_date):
    url = format_abhibus_url(from_city, to_city, travel_date)
    if not url:
        return None
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=35)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        fares = []
        for price in soup.select(".bus-fare span, .fare"):
            fare_text = price.get_text(strip=True).replace("₹", "").replace(",", "")
            if fare_text.isdigit():
                fares.append(int(fare_text))
        return min(fares) if fares else None
    except Exception as e:
        logger.warning(f"AbhiBus scraping failed: {e}")
        return None

# ---- Unified fetch with caching ----
def fetch_bus_fares(from_city, to_city, travel_date):
    key = f"{from_city}-{to_city}-{travel_date}"
    now = time.time()

    # Return cached result if valid
    if key in _cache and now - _cache[key]["time"] < CACHE_TTL:
        logger.info(f"Using cached fares for {key}")
        return _cache[key]["data"]

    data = {}

    redbus_fare = scrape_redbus_fares(from_city, to_city, travel_date)
    if redbus_fare is not None:
        data["RedBus"] = redbus_fare

    abhibus_fare = scrape_abhibus_fares(from_city, to_city, travel_date)
    if abhibus_fare is not None:
        data["AbhiBus"] = abhibus_fare

    _cache[key] = {"time": now, "data": data}
    return data
