from http.server import BaseHTTPRequestHandler
import json
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import parse_qs

class BusAPIClient:
    def __init__(self, api_url: str, target_stop: str = "Ward", target_direction: str = "Outbound"):
        self.api_url = api_url
        self.target_stop = target_stop
        self.target_direction = target_direction
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def fetch_bus_data(self) -> Optional[Dict]:
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching API data: {e}")
            return None

    def parse_bus_times(self, data: Dict) -> List[Dict]:
        upcoming_buses = []
        current_time = datetime.now(timezone.utc)
        rides = data.get('rides', [])

        for ride in rides:
            state = ride.get('state', {})
            if not ('Active' in state or 'Accepted' in state):
                continue

            route_name = ride.get('routeName', 'Unknown Route')
            vehicle_name = ride.get('vehicleName', 'Unknown Vehicle')
            direction = ride.get('direction', 'Unknown Direction')

            if self.target_direction and direction != self.target_direction:
                continue

            stop_status = ride.get('stopStatus', [])

            for stop in stop_status:
                if 'Awaiting' in stop:
                    stop_info = stop['Awaiting']
                    stop_id = stop_info.get('stopId')
                    via_idx = stop_info.get('viaIdx', 0)

                    stop_name = "Unknown Stop"
                    vias = ride.get('vias', [])
                    if via_idx < len(vias) and 'ViaStop' in vias[via_idx]:
                        stop_name = vias[via_idx]['ViaStop']['stop'].get('name', 'Unknown Stop')

                    if self.target_stop and stop_name != self.target_stop:
                        continue

                    expected_arrival = stop_info.get('expectedArrivalTime')
                    if expected_arrival:
                        departure_time = datetime.fromisoformat(expected_arrival.replace('Z', '+00:00'))

                        if departure_time > current_time:
                            upcoming_buses.append({
                                'route_name': route_name,
                                'vehicle_name': vehicle_name,
                                'direction': direction,
                                'stop_name': stop_name,
                                'departure_time': departure_time,
                                'rider_status': stop_info.get('riderStatus', 'Unknown'),
                                'minutes_until': int((departure_time - current_time).total_seconds() / 60)
                            })

        upcoming_buses.sort(key=lambda x: x['departure_time'])
        return upcoming_buses

def get_current_date():
    return datetime.now().strftime('%Y-%m-%d')

def build_api_url(route_id: str, current_date: str = None):
    if current_date is None:
        current_date = get_current_date()
    return f"https://northwestern.tripshot.com/v2/p/routeSummary/{route_id}?day={current_date}&withNavigation=true&embedStops=true"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            query_string = self.path.split('?', 1)[1] if '?' in self.path else ''
            params = parse_qs(query_string)

            route = params.get('route', ['both'])[0]

            # Route configurations
            route_configs = {
                "outbound": {
                    "id": "23174203-507c-48fe-811a-5d13fcf7be65",
                    "target_stop": "Ward",
                    "target_direction": "Outbound",
                    "display_name": "Ward"
                },
                "inbound": {
                    "id": "EBEE9228-C993-4279-B7CE-8FCA0A46CA65",
                    "target_stop": "Sheridan/Noyes (IB)",
                    "target_direction": "Inbound",
                    "display_name": "Tech"
                }
            }

            results = {}
            current_date = get_current_date()

            # Determine which routes to fetch
            routes_to_fetch = []
            if route == 'both':
                routes_to_fetch = ['outbound', 'inbound']
            elif route in route_configs:
                routes_to_fetch = [route]
            else:
                raise ValueError(f"Invalid route: {route}")

            # Fetch data for each route
            for route_name in routes_to_fetch:
                config = route_configs[route_name]
                api_url = build_api_url(config["id"], current_date)

                client = BusAPIClient(
                    api_url,
                    config["target_stop"],
                    config["target_direction"]
                )

                data = client.fetch_bus_data()
                if data:
                    upcoming_buses = client.parse_bus_times(data)

                    # Format the response
                    formatted_buses = []
                    for bus in upcoming_buses[:2]:  # Next 2 buses
                        departure_time = bus['departure_time'].astimezone()
                        formatted_buses.append({
                            'time': departure_time.strftime('%I:%M %p'),
                            'minutes': bus['minutes_until'],
                            'status': bus['rider_status']
                        })

                    results[route_name] = {
                        'stop_name': config["display_name"],
                        'buses': formatted_buses,
                        'action': 'arriving at' if config["target_direction"] == "Outbound" else "departing from"
                    }
                else:
                    results[route_name] = {
                        'stop_name': config["display_name"],
                        'buses': [],
                        'error': 'Failed to fetch data',
                        'action': 'arriving at' if config["target_direction"] == "Outbound" else "departing from"
                    }

            # Add timestamp
            results['timestamp'] = datetime.now(timezone.utc).strftime('%I:%M:%S %p UTC on %B %d, %Y')

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            response_json = json.dumps(results)
            self.wfile.write(response_json.encode())

        except Exception as e:
            # Error response
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = json.dumps({
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).strftime('%I:%M:%S %p UTC')
            })
            self.wfile.write(error_response.encode())

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()