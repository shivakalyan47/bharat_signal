import urllib.request
import urllib.parse
import urllib.error
import json
import datetime
from typing import List

from apps.intelligence.schemas.signal import (
    Signal,
    SignalSource,
    SignalLocation,
    SignalType,
    SourceCategory,
    VerificationStatus,
    ProvenanceLabel
)

API_KEY = "02f0f52d26af0d84140b3b9f7504b7c1"

INDIA_CITIES = [
    {'name': 'Delhi', 'lat': 28.6139, 'lon': 77.2090, 'region': 'North India'},
    {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777, 'region': 'West India'},
    {'name': 'Chennai', 'lat': 13.0827, 'lon': 80.2707, 'region': 'South India'},
    {'name': 'Kolkata', 'lat': 22.5726, 'lon': 88.3639, 'region': 'East India'},
    {'name': 'Bengaluru', 'lat': 12.9716, 'lon': 77.5946, 'region': 'South India'},
    {'name': 'Hyderabad', 'lat': 17.3850, 'lon': 78.4867, 'region': 'South India'},
    {'name': 'Ahmedabad', 'lat': 23.0225, 'lon': 72.5714, 'region': 'West India'},
    {'name': 'Jaipur', 'lat': 26.9124, 'lon': 75.7873, 'region': 'North India'},
    {'name': 'Lucknow', 'lat': 26.8467, 'lon': 80.9462, 'region': 'North India'},
    {'name': 'Bhopal', 'lat': 23.2599, 'lon': 77.4126, 'region': 'Central India'},
    {'name': 'Patna', 'lat': 25.5941, 'lon': 85.1376, 'region': 'East India'},
    {'name': 'Guwahati', 'lat': 26.1445, 'lon': 91.7362, 'region': 'Northeast India'},
    {'name': 'Bhubaneswar', 'lat': 20.2961, 'lon': 85.8245, 'region': 'East India'},
    {'name': 'Srinagar', 'lat': 34.0837, 'lon': 74.7973, 'region': 'North India'},
    {'name': 'Thiruvananthapuram', 'lat': 8.5241, 'lon': 76.9366, 'region': 'South India'},
    {'name': 'Pune', 'lat': 18.5204, 'lon': 73.8567, 'region': 'West India'},
    {'name': 'Nagpur', 'lat': 21.1458, 'lon': 79.0882, 'region': 'Central India'},
    {'name': 'Indore', 'lat': 22.7196, 'lon': 75.8577, 'region': 'Central India'},
    {'name': 'Visakhapatnam', 'lat': 17.6868, 'lon': 83.2185, 'region': 'South India'},
    {'name': 'Chandigarh', 'lat': 30.7333, 'lon': 76.7794, 'region': 'North India'},
    {'name': 'Dehradun', 'lat': 30.3165, 'lon': 78.0322, 'region': 'North India'},
    {'name': 'Ranchi', 'lat': 23.3441, 'lon': 85.3096, 'region': 'East India'},
    {'name': 'Raipur', 'lat': 21.2514, 'lon': 81.6296, 'region': 'Central India'},
    {'name': 'Kochi', 'lat': 9.9312, 'lon': 76.2673, 'region': 'South India'},
    {'name': 'Coimbatore', 'lat': 11.0168, 'lon': 76.9558, 'region': 'South India'},
    {'name': 'Varanasi', 'lat': 25.3176, 'lon': 82.9739, 'region': 'North India'},
    {'name': 'Amritsar', 'lat': 31.6340, 'lon': 74.8723, 'region': 'North India'},
    {'name': 'Imphal', 'lat': 24.8170, 'lon': 93.9368, 'region': 'Northeast India'},
    {'name': 'Gangtok', 'lat': 27.3389, 'lon': 88.6065, 'region': 'Northeast India'},
    {'name': 'Shimla', 'lat': 31.1048, 'lon': 77.1734, 'region': 'North India'},
]

def fetch_openweather_signals() -> List[Signal]:
    signals: List[Signal] = []
    signal_index = 1
    
    source = SignalSource(
        id='openweathermap',
        name='OpenWeatherMap',
        category=SourceCategory.WEATHER,
        verification=VerificationStatus.VERIFIED
    )

    for city in INDIA_CITIES:
        print(f"Fetching weather for {city['name']}...")
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={city['lat']}&lon={city['lon']}&appid={API_KEY}&units=metric"
        
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8.0) as response:
                data = json.loads(response.read().decode('utf-8'))
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"Failed to fetch data for {city['name']}: {e}")
            continue

        temp = data.get('main', {}).get('temp', 0)
        humidity = data.get('main', {}).get('humidity', 0)
        
        # OWM wind speed is in m/s, convert to km/h
        wind_speed_ms = data.get('wind', {}).get('speed', 0)
        wind_speed_kmh = wind_speed_ms * 3.6
        
        rain_1h = data.get('rain', {}).get('1h', 0)
        weather_list = data.get('weather', [])
        weather_code = weather_list[0]['id'] if weather_list else 0
        weather_desc = weather_list[0]['description'] if weather_list else "unknown"

        base_description = (
            f"Temperature: {temp}°C, Humidity: {humidity}%, "
            f"Wind: {wind_speed_kmh:.1f} km/h, Conditions: {weather_desc}"
        )
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        location = SignalLocation(latitude=city['lat'], longitude=city['lon'], region=city['region'])
        entities = [city['name']]

        # 10. Baseline signal
        sig_id_base = f"SIG-OWM-{city['name'].upper()}-{signal_index:03d}"
        signal_index += 1
        signals.append(Signal(
            id=sig_id_base,
            source=source,
            type=SignalType.WEATHER,
            title=f"Current Weather in {city['name']}: {temp}°C",
            description=base_description,
            location=location,
            timestamp=timestamp,
            entities=entities,
            severity=0.2,
            domain='weather',
            provenance=ProvenanceLabel.OBSERVED,
            confidence=0.95,
            tags=['weather', 'baseline']
        ))

        # Alert Conditions
        alert_title = None
        alert_severity = None
        tags = []
        
        if temp > 40:
            alert_title = f"Heatwave Alert: {city['name']} records {temp}°C"
            alert_severity = 0.8
            tags.append('heatwave')
        elif temp < 5:
            alert_title = f"Cold Wave Alert: {city['name']} records {temp}°C"
            alert_severity = 0.6
            tags.append('cold-wave')
            
        if wind_speed_kmh > 40:
            alert_title = f"High Wind Alert in {city['name']}: {wind_speed_kmh:.1f} km/h"
            alert_severity = max(alert_severity or 0, 0.6)
            tags.append('high-wind')
            
        if rain_1h > 10:
            alert_title = f"Heavy Rainfall in {city['name']} — {rain_1h}mm/hr"
            alert_severity = max(alert_severity or 0, 0.75)
            tags.append('heavy-rain')
            
        if humidity > 90:
            if not alert_title:
                alert_title = f"High Humidity Alert in {city['name']}: {humidity}%"
            alert_severity = max(alert_severity or 0, 0.3)
            tags.append('humidity')

        if 200 <= weather_code <= 232:
            alert_title = f"Thunderstorm Alert in {city['name']}"
            alert_severity = max(alert_severity or 0, 0.7)
            tags.append('thunderstorm')
        elif 500 <= weather_code <= 531 and not (rain_1h > 10):
            if not alert_title:
                alert_title = f"Rainfall in {city['name']}"
            alert_severity = max(alert_severity or 0, 0.5)
            tags.append('rain')
        elif 600 <= weather_code <= 622:
            alert_title = f"Snowfall Alert in {city['name']}"
            alert_severity = max(alert_severity or 0, 0.5)
            tags.append('snow')
        elif weather_code in (762, 771, 781):
            alert_title = f"Extreme Weather Alert in {city['name']}: {weather_desc.title()}"
            alert_severity = 0.9
            tags.append('extreme-weather')

        if alert_title:
            sig_id_alert = f"SIG-OWM-{city['name'].upper()}-{signal_index:03d}"
            signal_index += 1
            signals.append(Signal(
                id=sig_id_alert,
                source=source,
                type=SignalType.WEATHER,
                title=alert_title,
                description=base_description,
                location=location,
                timestamp=timestamp,
                entities=entities,
                severity=alert_severity,
                domain='weather',
                provenance=ProvenanceLabel.OBSERVED,
                confidence=0.95,
                tags=tags
            ))

    return signals
