#!/usr/bin/env python3

import json
import os
import requests
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
from caldav import DAVClient

load_dotenv()

WEATHER_API_URL = f"{os.getenv('WEATHER_API_URL')}?latitude={os.getenv('WEATHER_LAT')}&longitude={os.getenv('WEATHER_LONG')}&hourly=temperature_2m,wind_speed_10m,precipitation_probability&forecast_days=2"
PUBLIC_TRANSPORT_API_URL = f"{os.getenv('PUBLIC_TRANSPORT_API_URL')}/{os.getenv('PUBLIC_TRANSPORT_STATION_ID')}?key={os.getenv('PUBLIC_TRANSPORT_API_KEY')}"
CALENDAR_API_URL = os.getenv("CALENDAR_API_URL")
CALENDAR_USERNAME = os.getenv("CALENDAR_USERNAME")
CALENDAR_APP_PASSWORD = os.getenv("CALENDAR_APP_PASSWORD")

def get_weather_api_response():
    try:
        response = requests.get(WEATHER_API_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Weather API error: {e}")
        return None
    
def get_public_transport_api_response():
    try:
        response = requests.get(PUBLIC_TRANSPORT_API_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Public Transport API error: {e}")
        return None

def get_next_event_api_response():
    client = DAVClient(url=CALENDAR_API_URL, username=CALENDAR_USERNAME, password=CALENDAR_APP_PASSWORD)
    principal = client.principal()
    calendars = principal.calendars()

    if not calendars:
        print("No calendars found!")
        return None

    calendar = calendars[int(os.getenv("CALENDAR_NUMBER", 0))]
    today = datetime.now()
    future = today + timedelta(days=30)
    results = calendar.search(start=today, end=future)

    if results:
        next_event = results[0]
        return next_event
    else:
        print("No upcoming events found")
        return None

def get_display_data():
    weather_api_response = get_weather_api_response()
    if weather_api_response and "hourly" in weather_api_response:
        weather = process_weather(weather_api_response)
    else:
        weather = {
            "current_temp": "N/A",
            "wind_kmh": "N/A",
            "later_temp": "N/A",
            "later_temp_time": "N/A",
            "wind_condition": "N/A",
            "precipitation": "N/A"
        }

    public_transport = get_public_transport_api_response()
    if public_transport:
        buses = process_public_transport(public_transport)
    else:
        buses = []

    next_event = get_next_event_api_response()
    if next_event:
        calendar = process_next_event(next_event)
    else:
        calendar = {}

    return {
        "buses": buses,
        "weather": weather,
        "calendar": calendar
    }

def process_public_transport(api_response):
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(os.getenv("LOCAL_TIMEZONE", "Europe/Stockholm"))
    except ImportError:
        import pytz
        tz = pytz.timezone(os.getenv("LOCAL_TIMEZONE", "Europe/Stockholm"))
    allowed_dest = os.getenv("PUBLIC_TRANSPORT_SELECT_DESTINATIONS", "").split(",")
    allowed_dest = [d.strip() for d in allowed_dest if d.strip()]
    now = datetime.now(tz)
    result = []
    for dep in api_response.get("departures", []):
        if dep.get("canceled", False):
            continue
        dest_name = dep.get("route", {}).get("destination", {}).get("name", "")
        if not dest_name or (allowed_dest and dest_name not in allowed_dest):
            continue
        number = dep.get("route", {}).get("designation", "")
        realtime_str = dep.get("realtime", dep.get("scheduled"))
        try:
            realtime_dt = datetime.fromisoformat(realtime_str)
            if realtime_dt.tzinfo is None:
                realtime_dt = realtime_dt.replace(tzinfo=tz)
            else:
                realtime_dt = realtime_dt.astimezone(tz)
        except Exception:
            continue
        diff_min = int((realtime_dt - now).total_seconds() // 60)
        time_val = realtime_dt.strftime("%H:%M")
        if 0 <= diff_min < 30:
            if diff_min == 0:
                minutes_val = "now"
            else:
                minutes_val = f"{diff_min} min"
        else:
            minutes_val = None
        result.append({
            "number": number,
            "destination": dest_name,
            "minutes": minutes_val,
            "time": time_val
        })
    return result

def process_weather(api_response):
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Stockholm")
    except ImportError:
        import pytz
        tz = pytz.timezone("Europe/Stockholm")
    hourly = api_response["hourly"]
    times = hourly["time"]
    temps = hourly["temperature_2m"]
    winds = hourly["wind_speed_10m"]
    precs = hourly["precipitation_probability"]

    now = datetime.now(tz)
    now_str = now.strftime("%Y-%m-%dT%H:00")
    try:
        idx = times.index(now_str)
    except ValueError:
        idx = 0  

    current_temp = temps[idx]
    wind_kmh = winds[idx]
    later_idx = min(idx + 4, len(temps) - 1)
    later_temp = temps[later_idx]
    later_temp_time_raw = times[later_idx]
    try:
        hour = int(later_temp_time_raw[11:13])
    except Exception:
        hour = 12
    if 10 <= hour < 15:
        later_temp_time = "noon"
    elif 15 <= hour < 21:
        later_temp_time = "afternoon"
    else:
        later_temp_time = "night"
    prec_window = precs[idx:later_idx + 1]
    precipitation = max(prec_window)

    if wind_kmh <= 5:
        wind_condition = "Calm"
    elif wind_kmh <= 15:
        wind_condition = "Breeze"
    elif wind_kmh <= 30:
        wind_condition = "Fresh breeze"
    elif wind_kmh <= 60:
        wind_condition = "Windy"
    elif wind_kmh <= 90:
        wind_condition = "Gusty"
    elif wind_kmh <= 120:
        wind_condition = "Stormy"
    else:
        wind_condition = "Twister"

    return {
        "current_temp": f"{current_temp}°C",
        "wind_kmh": f"{wind_kmh} km/h",
        "wind_condition": wind_condition,
        "later_temp": f"{later_temp}°C",
        "later_temp_time": later_temp_time,
        "precipitation": f"{precipitation}%"
    }

def process_next_event(api_response):
    try:
        event_date_raw = api_response.vobject_instance.vevent.dtstart.value
        desc = api_response.vobject_instance.vevent.summary.value
        # Handle escaped unicode (e.g., '\ud83d\udea2')
        if isinstance(desc, str) and '\\u' in desc:
            try:
                desc = desc.encode('utf-8').decode('unicode_escape')
            except Exception:
                pass
        # Format event_date
        from datetime import datetime, timedelta
        if isinstance(event_date_raw, datetime):
            event_date_dt = event_date_raw.date()
        else:
            event_date_dt = event_date_raw
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        if event_date_dt == today:
            event_date = "today"
        elif event_date_dt == tomorrow:
            event_date = "tomorrow"
        else:
            event_date = event_date_dt.strftime("%d%b").upper()
        if len(desc) > 21:
            split_idx = desc.rfind(" ", 0, 21)
            if split_idx == -1:
                split_idx = 21
            event_desc_1 = desc[:split_idx].strip()
            event_desc_2 = desc[split_idx:].strip()
        else:
            event_desc_1 = desc
            event_desc_2 = ""
        return {
            "event_date": event_date,
            "event_desc_1": event_desc_1,
            "event_desc_2": event_desc_2
        }
    except Exception as e:
        print(f"Next Event processing error: {e}")
        return {}
class SimpleHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self._set_headers()
            self.wfile.write(json.dumps({"success": True}).encode())
        elif self.path == "/display":
            self._set_headers()
            self.wfile.write(json.dumps(get_display_data()).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

if __name__ == "__main__":
    server_address = ('', int(os.getenv("PORT", 3000)))
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"Serving on port {server_address[1]}")
    httpd.serve_forever()
