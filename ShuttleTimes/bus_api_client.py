#!/usr/bin/env python3
"""
Northwestern Bus API Client
Makes API calls to get bus times and extracts the next upcoming bus departure
"""

import requests
import json
from datetime import datetime, timezone
import sys
from typing import List, Dict, Optional

class BusAPIClient:
    def __init__(self, api_url: str, target_stop: str = "Ward", target_direction: str = "Outbound", headers: Optional[Dict] = None):
        """Initialize the API client with URL, target stop, direction and optional headers"""
        self.api_url = api_url
        self.target_stop = target_stop
        self.target_direction = target_direction
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()

    def fetch_bus_data(self) -> Optional[Dict]:
        """Make API call to fetch bus data"""
        try:
           # print(f"Fetching bus data from: {self.api_url}")
            response = self.session.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
           # print(f"Successfully fetched data with {len(data.get('rides', []))} rides")
            return data

        except requests.RequestException as e:
            print(f"Error fetching API data: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None

    def parse_bus_times(self, data: Dict, filter_target_stop: bool = True) -> List[Dict]:
        """Parse bus data to extract upcoming departure times for target stop"""
        upcoming_buses = []
        current_time = datetime.now(timezone.utc)

        rides = data.get('rides', [])

        for ride in rides:
            # Only process active or accepted rides
            state = ride.get('state', {})
            if not ('Active' in state or 'Accepted' in state):
                continue

            route_name = ride.get('routeName', 'Unknown Route')
            vehicle_name = ride.get('vehicleName', 'Unknown Vehicle')
            direction = ride.get('direction', 'Unknown Direction')

            # Filter by direction if specified
            if self.target_direction and direction != self.target_direction:
                continue

            stop_status = ride.get('stopStatus', [])

            for stop in stop_status:
                # Look for upcoming stops (Awaiting status)
                if 'Awaiting' in stop:
                    stop_info = stop['Awaiting']

                    # Get the stop details from vias
                    stop_id = stop_info.get('stopId')
                    via_idx = stop_info.get('viaIdx', 0)

                    # Find stop name from vias
                    stop_name = "Unknown Stop"
                    vias = ride.get('vias', [])
                    if via_idx < len(vias) and 'ViaStop' in vias[via_idx]:
                        stop_name = vias[via_idx]['ViaStop']['stop'].get('name', 'Unknown Stop')

                    # Filter by target stop if specified and filtering is enabled
                    if filter_target_stop and self.target_stop and stop_name != self.target_stop:
                        continue

                    # Parse departure time
                    expected_arrival = stop_info.get('expectedArrivalTime')
                    scheduled_departure = stop_info.get('scheduledDepartureTime')

                    if expected_arrival:
                        departure_time = datetime.fromisoformat(expected_arrival.replace('Z', '+00:00'))

                        # Only include future departures
                        if departure_time > current_time:
                            upcoming_buses.append({
                                'route_name': route_name,
                                'vehicle_name': vehicle_name,
                                'direction': direction,
                                'stop_name': stop_name,
                                'stop_id': stop_id,
                                'departure_time': departure_time,
                                'scheduled_time': scheduled_departure,
                                'rider_status': stop_info.get('riderStatus', 'Unknown'),
                                'minutes_until': int((departure_time - current_time).total_seconds() / 60)
                            })

        # Sort by departure time
        upcoming_buses.sort(key=lambda x: x['departure_time'])
        return upcoming_buses

    def get_next_bus(self, data: Dict = None) -> Optional[Dict]:
        """Get the next upcoming bus departure"""
        if data is None:
            data = self.fetch_bus_data()
            if not data:
                return None

        upcoming_buses = self.parse_bus_times(data)

        if upcoming_buses:
            return upcoming_buses[0]  # Return the earliest departure
        return None

    def format_bus_info(self, bus_info: Dict) -> str:
        """Format bus information for display"""
        departure_time = bus_info['departure_time']
        local_time = departure_time.astimezone()  # Convert to local timezone

        time_str = local_time.strftime('%I:%M %p')
        minutes = bus_info['minutes_until']

        if minutes <= 0:
            time_until = "Now"
        elif minutes == 1:
            time_until = "1 minute"
        else:
            time_until = f"{minutes} minutes"

        # Determine if this is arrival or departure based on direction
        if self.target_direction == "Outbound":
            action = f"Arrival at {self.target_stop}"
        else:
            action = f"Departure from {self.target_stop}"

        return f"""Next Bus for {self.target_stop}:
  Route: {bus_info['route_name']} ({bus_info['direction']})
  Vehicle: {bus_info['vehicle_name']}
  {action}: {time_str} ({time_until})
  Status: {bus_info['rider_status']}
"""

    def get_all_available_stops(self, data: Dict) -> List[str]:
        """Get all available stops from the data for debugging"""
        stops = set()
        rides = data.get('rides', [])

        for ride in rides:
            direction = ride.get('direction', 'Unknown Direction')
            if self.target_direction and direction != self.target_direction:
                continue

            vias = ride.get('vias', [])
            for via in vias:
                if 'ViaStop' in via:
                    stop_name = via['ViaStop']['stop'].get('name', 'Unknown Stop')
                    stops.add(stop_name)

        return sorted(list(stops))

    def load_sample_data(self, file_path: str) -> Optional[Dict]:
        """Load sample data from JSON file for testing"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sample data: {e}")
            return None

def get_current_date():
    """Get current date in YYYY-MM-DD format"""
    return datetime.now().strftime('%Y-%m-%d')

def build_api_url(route_id: str, current_date: str = None):
    """Build API URL with current date"""
    if current_date is None:
        current_date = get_current_date()
    return f"https://northwestern.tripshot.com/v2/p/routeSummary/{route_id}?day={current_date}&withNavigation=true&embedStops=true"

def main():
    # Route IDs for Northwestern bus routes
    route_ids = {
        "outbound": "23174203-507c-48fe-811a-5d13fcf7be65",
        "inbound": "EBEE9228-C993-4279-B7CE-8FCA0A46CA65"
    }

    # Preset configurations for Northwestern bus routes
    current_date = get_current_date()
    presets = {
        "outbound": {
            "target_stop": "Ward",
            "target_direction": "Outbound",
            "description": "Outbound route - when buses arrive at Ward",
            "api_url": build_api_url(route_ids["outbound"], current_date)
        },
        "inbound": {
            "target_stop": "Sheridan/Noyes (IB)",
            "target_direction": "Inbound",
            "description": "Inbound route - when buses depart from Tech",
            "api_url": build_api_url(route_ids["inbound"], current_date),
            "display_name": "Tech"
        }
    }

    # Default configuration
    api_url = "YOUR_API_URL_HERE"
    target_stop = "Ward"
    target_direction = "Outbound"
    display_stop = None

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1].endswith('.json'):
            # Test with local JSON file
            # Check for preset configuration first
            if len(sys.argv) > 2 and sys.argv[2].lower() in presets:
                preset = presets[sys.argv[2].lower()]
                target_stop = preset["target_stop"]
                target_direction = preset["target_direction"]
                display_stop = preset.get("display_name", target_stop)
            elif len(sys.argv) > 2:
                # Manual stop and direction specification
                target_stop = sys.argv[2]
                if len(sys.argv) > 3:
                    target_direction = sys.argv[3]

            client = BusAPIClient("dummy_url", target_stop, target_direction)

            data = client.load_sample_data(sys.argv[1])
            if data:
                # Show all upcoming buses to the target stop
                upcoming_buses = client.parse_bus_times(data)
                if upcoming_buses:
                    action_word = "arriving at" if target_direction == "Outbound" else "departing from"
                    stop_name = display_stop if display_stop else target_stop
                    num_to_show = min(2, len(upcoming_buses))

                    print(f"Next {num_to_show} bus{'es' if num_to_show > 1 else ''} {action_word} {stop_name}:")
                    for i, bus in enumerate(upcoming_buses[:2], 1):
                        departure_time = bus['departure_time'].astimezone()
                        time_str = departure_time.strftime('%I:%M %p')
                        print(f"  {i}. {time_str} ({bus['minutes_until']} min) - {bus['rider_status']}")
                else:
                    stop_name = display_stop if display_stop else target_stop
                    print(f"No upcoming buses found for {stop_name} stop on {target_direction} route.")
            return
        elif sys.argv[1].lower() in presets:
            # Using preset with API
            preset = presets[sys.argv[1].lower()]
            target_stop = preset["target_stop"]
            target_direction = preset["target_direction"]
            display_stop = preset.get("display_name", target_stop)
            if len(sys.argv) > 2:
                api_url = sys.argv[2]
            elif preset.get("api_url"):
                api_url = preset["api_url"]
        else:
            api_url = sys.argv[1]
            if len(sys.argv) > 2:
                target_stop = sys.argv[2]
            if len(sys.argv) > 3:
                target_direction = sys.argv[3]

    if api_url == "YOUR_API_URL_HERE":
        print("Please provide an API URL as a command line argument or JSON file for testing")
        print("\nUsage options:")
        print("  python bus_api_client.py <JSON_FILE> [outbound|inbound]  # Use presets with sample data")
        print("  python bus_api_client.py <JSON_FILE> [STOP_NAME] [DIRECTION]  # Manual with sample data")
        print("  python bus_api_client.py [outbound|inbound]  # Live API with stored URLs")
        print("  python bus_api_client.py [outbound|inbound] <API_URL>  # Live API with custom URL")
        print("  python bus_api_client.py <API_URL> [STOP_NAME] [DIRECTION]  # Live API manual")
        print("\nPresets:")
        for name, preset in presets.items():
            print(f"  {name}: {preset['description']}")
        return

    # Use actual API
    client = BusAPIClient(api_url, target_stop, target_direction)
    upcoming_buses = client.parse_bus_times(client.fetch_bus_data())

    if upcoming_buses:
        action_word = "arriving at" if target_direction == "Outbound" else "departing from"
        stop_name = display_stop if display_stop else target_stop
        num_to_show = min(2, len(upcoming_buses))

        print(f"Next {num_to_show} bus{'es' if num_to_show > 1 else ''} {action_word} {stop_name}:")
        for i, bus in enumerate(upcoming_buses[:2], 1):
            departure_time = bus['departure_time'].astimezone()
            time_str = departure_time.strftime('%I:%M %p')
            print(f"  {i}. {time_str} ({bus['minutes_until']} min) - {bus['rider_status']}")
    else:
        stop_name = display_stop if display_stop else target_stop
        print(f"No upcoming buses found for {stop_name} stop or error fetching data.")

if __name__ == "__main__":
    main()