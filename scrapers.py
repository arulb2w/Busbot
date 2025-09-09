import requests
from bs4 import BeautifulSoup
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Simple in-memory cache ---
_cache = {}

CACHE_TTL = 600  # 10 minutes

# ---- RedBus ----
def scrape_redbus_fares(from_city, to_city, travel_date):
    try:
        url = f"https://www.redbus.in/bus-tickets/{from_city}-to-{to_city}?onward={travel_date}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
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

# ---- AbhiBus ----
def scrape_abhibus_fares(from_city, to_city, travel_date):
    try:
        url = f"https://www.abhibus.com/bus_search/{from_city}/{to_city}/{travel_date}/0/0"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
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

# ---- MakeMyTrip ----
def scrape_mmt_fares(from_city, to_city, travel_date):
    try:
        url = f"https://www.makemytrip.com/bus/search/{from_city}/{to_city}/{travel_date}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        fares = []

        for price in soup.select(".actual-price, .fare"):
            fare_text = price.get_text(strip=True).replace("₹", "").replace(",", "")
            if fare_text.isdigit():
                fares.append(int(fare_text))

        return min(fares) if fares else None
    except Exception as e:
        logger.warning(f"MMT scraping failed: {e}")
        return None

# ---- Unified Fetch Function with caching ----
def fetch_bus_fares(from_city, to_city, travel_date):
    key = f"{from_city}-{to_city}-{travel_date}"
    now = time.time()

    # Return cached result if still valid
    if key in _cache and now - _cache[key]["time"] < CACHE_TTL:
        logger.info(f"Using cached fares for {key}")
        return _cache[key]["data"]

    data = {}

    # Scrape each site individually
    redbus_fare = scrape_redbus_fares(from_city, to_city, travel_date)
    if redbus_fare is not None:
        data["RedBus"] = redbus_fare

    abhibus_fare = scrape_abhibus_fares(from_city, to_city, travel_date)
    if abhibus_fare is not None:
        data["AbhiBus"] = abhibus_fare

    mmt_fare = scrape_mmt_fares(from_city, to_city, travel_date)
    if mmt_fare is not None:
        data["MakeMyTrip"] = mmt_fare

    # Save to cache
    _cache[key] = {"time": now, "data": data}

    return data
