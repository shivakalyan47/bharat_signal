import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from apps.intelligence.schemas.signal import (
    Signal, SignalSource, SignalLocation, SourceCategory, VerificationStatus,
    SignalType, ProvenanceLabel
)

TOMTOM_KEY = "3qwIIi32CDaGTE72omm9PaClrUEIk33a"

TRAFFIC_CITIES = [
    {'name': 'Delhi', 'lat': 28.6139, 'lon': 77.2090, 'region': 'North India'},
    {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777, 'region': 'West India'},
    {'name': 'Bengaluru', 'lat': 12.9716, 'lon': 77.5946, 'region': 'South India'},
    {'name': 'Chennai', 'lat': 13.0827, 'lon': 80.2707, 'region': 'South India'},
    {'name': 'Kolkata', 'lat': 22.5726, 'lon': 88.3639, 'region': 'East India'},
    {'name': 'Hyderabad', 'lat': 17.3850, 'lon': 78.4867, 'region': 'South India'},
    {'name': 'Ahmedabad', 'lat': 23.0225, 'lon': 72.5714, 'region': 'West India'},
    {'name': 'Pune', 'lat': 18.5204, 'lon': 73.8567, 'region': 'West India'},
    {'name': 'Jaipur', 'lat': 26.9124, 'lon': 75.7873, 'region': 'North India'},
    {'name': 'Lucknow', 'lat': 26.8467, 'lon': 80.9462, 'region': 'North India'},
    {'name': 'Chandigarh', 'lat': 30.7333, 'lon': 76.7794, 'region': 'North India'},
    {'name': 'Nagpur', 'lat': 21.1458, 'lon': 79.0882, 'region': 'Central India'},
    {'name': 'Indore', 'lat': 22.7196, 'lon': 75.8577, 'region': 'Central India'},
    {'name': 'Bhopal', 'lat': 23.2599, 'lon': 77.4126, 'region': 'Central India'},
    {'name': 'Kochi', 'lat': 9.9312, 'lon': 76.2673, 'region': 'South India'},
    {'name': 'Coimbatore', 'lat': 11.0168, 'lon': 76.9558, 'region': 'South India'},
    {'name': 'Visakhapatnam', 'lat': 17.6868, 'lon': 83.2185, 'region': 'South India'},
    {'name': 'Patna', 'lat': 25.5941, 'lon': 85.1376, 'region': 'East India'},
    {'name': 'Guwahati', 'lat': 26.1445, 'lon': 91.7362, 'region': 'Northeast India'},
    {'name': 'Surat', 'lat': 21.1702, 'lon': 72.8311, 'region': 'West India'},
]

def fetch_tomtom_traffic_signals() -> list[Signal]:
    signals = []
    
    source = SignalSource(
        id='tomtom-traffic',
        name='TomTom Traffic',
        category=SourceCategory.TRANSPORT,
        verification=VerificationStatus.VERIFIED
    )

    for index, city in enumerate(TRAFFIC_CITIES, start=1):
        try:
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={city['lat']},{city['lon']}&key={TOMTOM_KEY}&unit=KMPH"
            print(f"Fetching TomTom traffic data for {city['name']}...")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    flow_data = data.get('flowSegmentData', {})
                    if not flow_data:
                        continue
                    
                    current_speed = flow_data.get('currentSpeed')
                    free_flow_speed = flow_data.get('freeFlowSpeed')
                    
                    if current_speed is None or free_flow_speed is None or free_flow_speed == 0:
                        continue
                        
                    congestion = 1.0 - (current_speed / free_flow_speed)
                    api_confidence = flow_data.get('confidence', 1.0)
                    
                    if congestion >= 0.7:
                        prefix = "Severe Traffic Jam"
                        severity = 0.85
                    elif congestion >= 0.5:
                        prefix = "Heavy Traffic Congestion"
                        severity = 0.65
                    elif congestion >= 0.3:
                        prefix = "Moderate Traffic"
                        severity = 0.45
                    else:
                        prefix = "Normal Traffic Flow"
                        severity = 0.2
                        
                    title = f"{prefix} in {city['name']} — Speed {current_speed} km/h (Free flow: {free_flow_speed} km/h)"
                    description = f"Traffic flow data for {city['name']}. Current speed is {current_speed} km/h compared to free flow speed of {free_flow_speed} km/h. Congestion ratio: {congestion:.0%}. Confidence: {api_confidence}."
                    
                    tags = []
                    if congestion >= 0.3:
                        tags.append('traffic_congestion')
                    if congestion >= 0.7:
                        tags.append('road_disruption')
                    
                    signal = Signal(
                        id=f"SIG-TRAFFIC-{city['name'].upper()}-{index:03d}",
                        source=source,
                        type=SignalType.TRANSPORT,
                        title=title,
                        description=description,
                        location=SignalLocation(
                            latitude=city['lat'],
                            longitude=city['lon'],
                            region=city['region']
                        ),
                        timestamp=datetime.now(timezone.utc),
                        entities=[city['name'], 'traffic', 'congestion'],
                        severity=severity,
                        provenance=ProvenanceLabel.OBSERVED,
                        confidence=api_confidence,
                        domain='transport',
                        tags=tags
                    )
                    signals.append(signal)
        except Exception as e:
            print(f"Failed to fetch or process data for {city['name']}: {e}")
            continue

    return signals
