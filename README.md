# Fuel Route Planner API

Backend Django Engineer assessment - Spotter

## What does this project do?

An API that:
1. Takes a start and finish location (e.g. "New York, NY" and "Los Angeles, CA")
2. Calculates the driving route between them (using a free routing API)
3. Finds the cheapest place to refuel every 500 miles along the route
4. Calculates the total fuel cost for the whole trip (assuming 10 miles per gallon)

## Which external APIs are used (both free, no paid key required)

- **Nominatim (OpenStreetMap)** - converts a place name into lat/lon coordinates (geocoding)
- **OSRM** - gets the driving route between two coordinates (routing) - only **1 call**

Fuel price data (`planner/data/fuel-prices.csv`) is loaded from a local file, so no external API call is needed for that. This keeps the total number of external calls low (the assignment asks for 1 ideally, 2-3 acceptable).

## Step-by-Step: Running it in VS Code

### Step 1: Open the folder in VS Code
- Open VS Code -> `File > Open Folder` -> select this `fuel_route_project` folder

### Step 2: Open the terminal
- Inside VS Code: `Terminal > New Terminal` (or shortcut: Ctrl+`)

### Step 3: Create a virtual environment (keeps this project's packages separate from your system)
```bash
python -m venv venv
```

Activate it:
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```
Once activated, you'll see `(venv)` at the start of the terminal line.

### Step 4: Install the required packages
```bash
pip install -r requirements.txt
```

### Step 5: Run the server
```bash
python manage.py runserver
```
You should see: `Starting development server at http://127.0.0.1:8000/`

This means the server is running! Don't close this terminal while you're testing.

## How to test the API (using Postman)

1. Open Postman (if you don't have it, download it free from postman.com)
2. Create a new request:
   - **Method:** POST
   - **URL:** `http://127.0.0.1:8000/api/route/`
   - Go to the **Body tab -> raw -> JSON**, and paste this:
   ```json
   {
       "start": "Chicago, IL",
       "finish": "Dallas, TX"
   }
   ```
3. Click **Send**

The response will include:
- Total distance & drive time
- Fuel stops (which state, which station, what price)
- Total fuel cost (USD)
- The full route path (coordinates, so it can be plotted on a map)

## Project Structure (what's in each file)

```
fuel_route_project/
├── manage.py                  # Django's entry point
├── requirements.txt           # List of required packages
├── fuel_route_api/
│   ├── settings.py            # Project settings
│   └── urls.py                # Main URL routing (routes /api/ to the planner app)
└── planner/                   # The actual app - all the logic lives here
    ├── views.py                 # API endpoint - the whole flow is combined here
    ├── services.py               # Geocoding + Routing (external API calls) + loading fuel CSV
    ├── geo_utils.py               # Math helper functions (distance calculation, state lookup)
    ├── urls.py                   # Defines the /api/route/ endpoint
    └── data/fuel-prices.csv       # The fuel prices file you were given
```

## Explanation of the logic (for the Loom video)

1. `services.geocode()` - converts the start and finish into lat/lon
2. `services.get_route()` - fetches the entire route (path + total distance) in a single API call
3. `geo_utils.build_cumulative_distances()` - calculates the distance travelled up to each point on the route
4. A stop point is generated every 500 miles (until the trip ends)
5. The state for that point is determined (`geo_utils.get_state_for_point`) - this is a local bounding-box check, no extra API call needed
6. The cheapest station in that state is looked up from the CSV data (`services.find_cheapest_station`)
7. Total cost is calculated: for each leg (segment), distance/10 = gallons needed, multiplied by that stop's price, then summed across all legs

**Assumption I made (mention this clearly in the video):** The vehicle already starts the trip with a full tank (that cost isn't counted in this trip) - the cost only counts the refuels that happen along the route.

## Next steps

1. Push this to GitHub (create a new repo, `git init`, `git add .`, `git commit`, `git push`)
2. Record a Loom video demoing it with Postman (max 5 min): first run a request to show it working, then give a quick walkthrough of the code
3. Send both links (GitHub + Loom) in the email reply