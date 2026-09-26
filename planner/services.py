"""
This file has 3 jobs:
1. geocode()      -> turn a place name ("Dallas, TX") into lat/lon
                      (Nominatim / OpenStreetMap - free, no API key)
2. get_route()    -> given 2 lat/lon points, get the driving route
                      (OSRM - free, no API key)
3. fuel price stuff -> load the CSV once, and find the cheapest
                      station in a given state (no external API - all
                      local, so this costs us ZERO extra API calls)
"""
import csv
import os
import requests
from django.conf import settings

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"

# Nominatim's usage policy requires a descriptive User-Agent header.
HEADERS = {"User-Agent": "fuel-route-assessment-app/1.0"}

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "fuel-prices.csv")

# Cached in memory after first load, so the CSV (8000+ rows) is only
# ever parsed once per server run, not on every request.
_FUEL_DATA_BY_STATE = None


class ExternalAPIError(Exception):
    pass


def geocode(place_name):
    """
    Turn a human place name like "Denver, CO" into (lat, lon).
    Calls the free Nominatim geocoding API - ONE call per place.
    """
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    }
    resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        raise ExternalAPIError(f"Geocoding failed for '{place_name}'")

    results = resp.json()
    if not results:
        raise ExternalAPIError(f"Could not find location: '{place_name}'")

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    return lat, lon


def get_route(start_coords, end_coords):
    """
    Get the driving route between two (lat, lon) points.
    Calls the free OSRM routing API - ONE call total.

    Returns:
        {
            "distance_miles": float,
            "duration_minutes": float,
            "coords": [(lat, lon), (lat, lon), ...]  # full route path
        }
    """
    lat1, lon1 = start_coords
    lat2, lon2 = end_coords
    url = OSRM_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    params = {"overview": "full", "geometries": "geojson"}

    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        raise ExternalAPIError("Routing service failed")

    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ExternalAPIError("No route found between these locations")

    route = data["routes"][0]
    distance_miles = route["distance"] / 1609.34  # meters -> miles
    duration_minutes = route["duration"] / 60  # seconds -> minutes

    # GeoJSON gives [lon, lat] pairs - we flip to (lat, lon) for our own use.
    coords = [(pt[1], pt[0]) for pt in route["geometry"]["coordinates"]]

    return {
        "distance_miles": distance_miles,
        "duration_minutes": duration_minutes,
        "coords": coords,
    }


def _load_fuel_data():
    """
    Load the fuel prices CSV once and group stations by state, sorted
    cheapest-first within each state. Cached in memory after first call.
    """
    global _FUEL_DATA_BY_STATE
    if _FUEL_DATA_BY_STATE is not None:
        return _FUEL_DATA_BY_STATE

    by_state = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                price = float(row["Retail Price"])
            except (ValueError, KeyError):
                continue
            state = row.get("State", "").strip().upper()
            if not state:
                continue
            by_state.setdefault(state, []).append({
                "name": row.get("Truckstop Name", "").strip(),
                "address": row.get("Address", "").strip(),
                "city": row.get("City", "").strip(),
                "state": state,
                "price": price,
            })

    # Sort each state's stations cheapest-first so lookups are instant.
    for state in by_state:
        by_state[state].sort(key=lambda s: s["price"])

    _FUEL_DATA_BY_STATE = by_state
    return by_state


def find_cheapest_station(state):
    """
    Return the cheapest fuel station dict for the given state.
    If that state has no stations in our data, fall back to the
    overall cheapest station nationwide (better than failing the request).
    """
    by_state = _load_fuel_data()

    if state and state in by_state and by_state[state]:
        return by_state[state][0]

    # Fallback: cheapest station across all states.
    cheapest = None
    for stations in by_state.values():
        if stations and (cheapest is None or stations[0]["price"] < cheapest["price"]):
            cheapest = stations[0]
    return cheapest
