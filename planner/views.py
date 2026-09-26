from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from . import services
from . import geo_utils

VEHICLE_RANGE_MILES = 500
VEHICLE_MPG = 10


class RouteFuelPlanView(APIView):
    """
    POST /api/route/
    Body: { "start": "New York, NY", "finish": "Los Angeles, CA" }

    Returns the route + optimal (cheapest) fuel stops along the way +
    total estimated fuel cost.
    """

    def post(self, request):
        start_place = request.data.get("start")
        finish_place = request.data.get("finish")

        if not start_place or not finish_place:
            return Response(
                {"error": "Both 'start' and 'finish' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # --- Step 1: turn place names into coordinates ---
            start_coords = services.geocode(start_place)
            finish_coords = services.geocode(finish_place)

            # --- Step 2: get the driving route (1 external call) ---
            route = services.get_route(start_coords, finish_coords)
        except services.ExternalAPIError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        total_miles = route["distance_miles"]
        coords = route["coords"]
        cumulative = geo_utils.build_cumulative_distances(coords)

        # --- Step 3: figure out where fuel stops are needed ---
        # We need a stop every 500 miles until we're within 500 miles
        # of the finish (no need to stop for the final leg if it fits
        # in the remaining tank range).
        stop_mile_marks = []
        next_mark = VEHICLE_RANGE_MILES
        while next_mark < total_miles:
            stop_mile_marks.append(next_mark)
            next_mark += VEHICLE_RANGE_MILES

        # --- Step 4: for each stop, find the cheapest nearby station ---
        stops = []
        for mile_mark in stop_mile_marks:
            lat, lon = geo_utils.point_at_distance(coords, cumulative, mile_mark)
            state = geo_utils.get_state_for_point(lat, lon)
            station = services.find_cheapest_station(state)
            stops.append({
                "mile_mark": round(mile_mark, 1),
                "latitude": lat,
                "longitude": lon,
                "state": state,
                "station": station,
            })

        # --- Step 5: calculate total fuel cost ---
        # Assumption: the vehicle starts with a full tank already paid
        # for (not part of this trip's cost). Every stop refuels the
        # vehicle for the NEXT leg of the journey. Cost of each leg =
        # (leg distance / mpg) * price paid at the stop that starts it.
        total_cost = 0.0
        boundaries = [0.0] + [s["mile_mark"] for s in stops] + [total_miles]
        for i, stop in enumerate(stops):
            leg_distance = boundaries[i + 2] - boundaries[i + 1]
            gallons_needed = leg_distance / VEHICLE_MPG
            price = stop["station"]["price"] if stop["station"] else 0
            total_cost += gallons_needed * price

        response_data = {
            "start": start_place,
            "finish": finish_place,
            "total_distance_miles": round(total_miles, 1),
            "estimated_drive_time_minutes": round(route["duration_minutes"], 1),
            "vehicle_range_miles": VEHICLE_RANGE_MILES,
            "vehicle_mpg": VEHICLE_MPG,
            "number_of_fuel_stops": len(stops),
            "fuel_stops": stops,
            "total_fuel_cost_usd": round(total_cost, 2),
            "route_map": {
                "start_coords": {"lat": start_coords[0], "lon": start_coords[1]},
                "finish_coords": {"lat": finish_coords[0], "lon": finish_coords[1]},
                # Full path so the frontend/Postman/you can plot it on a map
                "path": [{"lat": c[0], "lon": c[1]} for c in coords],
            },
        }
        return Response(response_data, status=status.HTTP_200_OK)
