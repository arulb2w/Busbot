import requests
import logging
import time
from datetime import datetime

# -----------------------
# Logging
# -----------------------
logger = logging.getLogger("scrapers")
logging.basicConfig(level=logging.DEBUG)

# -----------------------
# Cache to reduce repeated API calls
# -----------------------
_cache = {}
CACHE_TTL = 300  # 5 minutes

# -----------------------
# City IDs
# -----------------------
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

# -----------------------
# Date formatting
# -----------------------
def format_dates(travel_date: str):
    """
    Convert dd-mm-yyyy (Telegram input) to API formats
    RedBus: dd-MMM-yyyy (12-Sep-2025)
    AbhiBus: dd-mm-yyyy (12-09-2025)
    """
    dt = datetime.strptime(travel_date, "%d-%m-%Y")
    redbus_date = dt.strftime("%d-%b-%Y")
    abhibus_date = dt.strftime("%d-%m-%Y")
    return redbus_date, abhibus_date

# -----------------------
# RedBus API Scraper
# -----------------------
def scrape_redbus_fares(from_city, to_city, travel_date):
    from_id = REDBUS_CITY_IDS.get(from_city)
    to_id = REDBUS_CITY_IDS.get(to_city)
    if not from_id or not to_id:
        logger.warning(f"RedBus city ID missing for {from_city} -> {to_city}")
        return None

    api_url = "https://www.redbus.in/rpw/api/searchResults"
    params = {
        "fromCity": from_id,
        "toCity": to_id,
        "DOJ": travel_date,
        "limit": 10,
        "offset": 0,
        "meta": "true",
        "groupId": 0,
        "sectionId": 0,
        "sort": 0,
        "sortOrder": 0,
        "from": "initialLoad",
        "getUuid": True,
        "bT": 1,
        "clearLMBFilter": "undefined"
    }
    payload = {
        "appliedFilterCount":0,
        "onlyShow":[],
        "dt":[],
        "SeaterType":[],
        "AcType":[],
        "travelsList":[],
        "amtList":[],
        "bpList":[],
        "dpList":[],
        "CampaignFilter":[],
        "at":[],
        "persuasionList":[],
        "bpIdentifier":[],
        "dpIdentifier":[],
        "bcf":[],
        "opBusTypeFilterList":[],
        "priceRange":[],
        "RouteIds":[],
        "bpKeys":[],
        "dpKeys":[],
        "streaksFilter":[],
        "preRouteFilters": None
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://www.redbus.in",
        "Referer": "https://www.redbus.in/bus-tickets/"
    }

    try:
        logger.debug(f"📡 RedBus API request: {params}")
        response = requests.post(api_url, json=payload, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        logger.debug(f"📊 RedBus returned {len(results)} results")
        fares = [bus["fare"] for bus in results if "fare" in bus]
        return min(fares) if fares else None
    except Exception as e:
        logger.warning(f"RedBus scraping failed: {e}")
        return None

# -----------------------
# AbhiBus API Scraper
# -----------------------
def scrape_abhibus_fares(from_city, to_city, travel_date):
    from_id = ABHIBUS_CITY_IDS.get(from_city)
    to_id = ABHIBUS_CITY_IDS.get(to_city)
    if not from_id or not to_id:
        logger.warning(f"AbhiBus city ID missing for {from_city} -> {to_city}")
        return None

    api_url = "https://www.abhibus.com/wap/GetBusList"
    payload = {
        "source": from_city,
        "sourceid": from_id,
        "destination": to_city,
        "destinationid": to_id,
        "jdate": travel_date,
        "prd": "mobile",
        "filters": 1,
        "isReturnJourney": "0",
        "api_exp": {
            "exp_ixigo_payment": "false",
            "exp_service_cards": "1",
            "exp_srp_outlier": "no"
        }
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://www.abhibus.com",
        "Referer": "https://www.abhibus.com/bus-tickets"
    }

    try:
        logger.debug(f"📡 AbhiBus API request: {payload}")
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        bus_list = data.get("BusList", [])
        logger.debug(f"📊 AbhiBus returned {len(bus_list)} buses")
        fares = [bus["Fares"] for bus in bus_list if "Fares" in bus]
        return min(fares) if fares else None
    except Exception as e:
        logger.warning(f"AbhiBus scraping failed: {e}")
        return None

# -----------------------
# Unified Fetch Function
# -----------------------
def fetch_bus_fares(from_city, to_city, travel_date):
    rb_date, ab_date = format_dates(travel_date)

    key = f"{from_city}-{to_city}-{travel_date}"
    now = time.time()
    if key in _cache and now - _cache[key]["time"] < CACHE_TTL:
        return _cache[key]["data"]

    data = {}

    # RedBus
    redbus_fare = scrape_redbus_fares(from_city, to_city, rb_date)
    if redbus_fare is not None:
        data["RedBus"] = redbus_fare

    # AbhiBus
    abhibus_fare = scrape_abhibus_fares(from_city, to_city, ab_date)
    if abhibus_fare is not None:
        data["AbhiBus"] = abhibus_fare

    _cache[key] = {"time": now, "data": data}
    return data
