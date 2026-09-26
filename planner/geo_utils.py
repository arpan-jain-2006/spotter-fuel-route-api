"""
Geo helper functions used by the route/fuel planning logic.

Everything in this file is pure math / local lookups - NO external API
calls happen here. This keeps our external API usage down to just the
geocoding + routing calls (see services.py), which is what the
assignment asks for ("one call ideal, two-three acceptable").
"""
import math

# Approximate bounding box (min_lat, max_lat, min_lon, max_lon) for each
# US state. These are rough rectangles - good enough to figure out
# "which state is this point roughly in" without calling any external
# reverse-geocoding API for every single point on the route.
STATE_BOUNDS = {
    'AL': (30.1, 35.0, -88.5, -84.9), 'AK': (51.0, 71.5, -179.2, -129.9),
    'AZ': (31.3, 37.0, -114.9, -109.0), 'AR': (33.0, 36.5, -94.7, -89.6),
    'CA': (32.5, 42.1, -124.5, -114.1), 'CO': (36.9, 41.1, -109.1, -102.0),
    'CT': (40.9, 42.1, -73.8, -71.7), 'DE': (38.4, 39.9, -75.8, -75.0),
    'FL': (24.4, 31.1, -87.7, -79.9), 'GA': (30.3, 35.1, -85.7, -80.7),
    'HI': (18.8, 22.3, -160.6, -154.7), 'ID': (41.9, 49.1, -117.3, -111.0),
    'IL': (36.9, 42.6, -91.6, -87.0), 'IN': (37.7, 41.8, -88.1, -84.7),
    'IA': (40.3, 43.6, -96.7, -90.1), 'KS': (36.9, 40.1, -102.1, -94.5),
    'KY': (36.4, 39.2, -89.6, -81.9), 'LA': (28.8, 33.1, -94.1, -88.7),
    'ME': (42.9, 47.5, -71.2, -66.8), 'MD': (37.8, 39.8, -79.5, -75.0),
    'MA': (41.1, 43.0, -73.6, -69.8), 'MI': (41.6, 48.3, -90.5, -82.1),
    'MN': (43.4, 49.5, -97.3, -89.4), 'MS': (30.1, 35.1, -91.7, -88.0),
    'MO': (35.9, 40.7, -95.9, -89.0), 'MT': (44.3, 49.1, -116.2, -103.9),
    'NE': (39.9, 43.1, -104.2, -95.2), 'NV': (34.9, 42.1, -120.1, -113.9),
    'NH': (42.6, 45.4, -72.6, -70.6), 'NJ': (38.8, 41.4, -75.7, -73.8),
    'NM': (31.2, 37.1, -109.2, -102.9), 'NY': (40.4, 45.1, -79.9, -71.7),
    'NC': (33.7, 36.7, -84.4, -75.3), 'ND': (45.8, 49.1, -104.2, -96.4),
    'OH': (38.3, 42.4, -85.0, -80.4), 'OK': (33.5, 37.1, -103.1, -94.3),
    'OR': (41.9, 46.4, -124.7, -116.3), 'PA': (39.6, 42.4, -80.6, -74.6),
    'RI': (41.1, 42.1, -71.9, -71.0), 'SC': (32.0, 35.3, -83.5, -78.4),
    'SD': (42.4, 46.1, -104.2, -96.3), 'TN': (34.9, 36.8, -90.4, -81.6),
    'TX': (25.7, 36.6, -106.8, -93.4), 'UT': (36.9, 42.1, -114.2, -108.9),
    'VT': (42.6, 45.1, -73.5, -71.4), 'VA': (36.5, 39.6, -83.7, -75.1),
    'WA': (45.4, 49.1, -124.9, -116.9), 'WV': (37.1, 40.7, -82.7, -77.6),
    'WI': (42.4, 47.2, -93.0, -86.6), 'WY': (40.9, 45.1, -111.1, -104.0),
    'DC': (38.79, 39.0, -77.15, -76.9),
}


def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in miles."""
    r = 3958.8  # Earth radius in miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def build_cumulative_distances(coords):
    """
    coords: list of (lat, lon) points along the route, IN ORDER.
    Returns a parallel list of cumulative distance (miles) travelled
    to reach each point from the start.
    """
    cumulative = [0.0]
    for i in range(1, len(coords)):
        lat1, lon1 = coords[i - 1]
        lat2, lon2 = coords[i]
        d = haversine_miles(lat1, lon1, lat2, lon2)
        cumulative.append(cumulative[-1] + d)
    return cumulative


def point_at_distance(coords, cumulative, target_miles):
    """
    Find the (lat, lon) point on the route that is approximately
    `target_miles` from the start, by walking the cumulative distance
    list and interpolating between the two nearest points.
    """
    if target_miles <= 0:
        return coords[0]
    if target_miles >= cumulative[-1]:
        return coords[-1]

    for i in range(1, len(cumulative)):
        if cumulative[i] >= target_miles:
            seg_start_dist = cumulative[i - 1]
            seg_end_dist = cumulative[i]
            seg_len = seg_end_dist - seg_start_dist
            ratio = 0.0 if seg_len == 0 else (target_miles - seg_start_dist) / seg_len
            lat1, lon1 = coords[i - 1]
            lat2, lon2 = coords[i]
            lat = lat1 + (lat2 - lat1) * ratio
            lon = lon1 + (lon2 - lon1) * ratio
            return (lat, lon)
    return coords[-1]


def get_state_for_point(lat, lon):
    """
    Return the 2-letter state code whose bounding box contains this
    point. If multiple boxes match (they can slightly overlap), return
    the first match. If none match, return None.
    """
    for state, (min_lat, max_lat, min_lon, max_lon) in STATE_BOUNDS.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return state
    return None
