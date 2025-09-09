import requests
from bs4 import BeautifulSoup

# ---- RedBus ----
def scrape_redbus_fares(from_city, to_city, travel_date):
    try:
        url = f"https://www.redbus.in/bus-tickets/{from_city}-to-{to_city}?onward={travel_date}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        fares = []

        for price in soup.select(".fare, .fare d-block"):
            fare_text = price.get_text(strip=True).replace("₹", "").replace(",", "")
            if fare_text.isdigit():
                fares.append(int(fare_text))

        return min(fares) if fares else None
    except Exception as e:
        print(f"RedBus scraping error: {e}")
        return None


# ---- AbhiBus ----
def scrape_abhibus_fares(from_city, to_city, travel_date):
    try:
        url = f"https://www.abhibus.com/bus_search/{from_city}/{to_city}/{travel_date}/0/0"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        fares = []

        for price in soup.select(".bus-fare span, .fare"):
            fare_text = price.get_text(strip=True).replace("₹", "").replace(",", "")
            if fare_text.isdigit():
                fares.append(int(fare_text))

        return min(fares) if fares else None
    except Exception as e:
        print(f"AbhiBus scraping error: {e}")
        return None


# ---- MakeMyTrip ----
def scrape_mmt_fares(from_city, to_city, travel_date):
    try:
        url = f"https://www.makemytrip.com/bus/search/{from_city}/{to_city}/{travel_date}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        fares = []

        for price in soup.select(".actual-price, .fare"):
            fare_text = price.get_text(strip=True).replace("₹", "").replace(",", "")
            if fare_text.isdigit():
                fares.append(int(fare_text))

        return min(fares) if fares else None
    except Exception as e:
        print(f"MMT scraping error: {e}")
        return None


# ---- Unified Fetch Function ----
def fetch_bus_fares(from_city, to_city, travel_date):
    data = {}

    redbus_fare = scrape_redbus_fares(from_city, to_city, travel_date)
    if redbus_fare: data["RedBus"] = redbus_fare

    abhibus_fare = scrape_abhibus_fares(from_city, to_city, travel_date)
    if abhibus_fare: data["AbhiBus"] = abhibus_fare

    mmt_fare = scrape_mmt_fares(from_city, to_city, travel_date)
    if mmt_fare: data["MakeMyTrip"] = mmt_fare

    return data
