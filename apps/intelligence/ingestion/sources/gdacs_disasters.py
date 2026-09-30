"""
GDACS Disaster Alert Adapter
==============================

Fetches real-time disaster alerts from the Global Disaster Alert
and Coordination System (GDACS) API.

No API key required. Free public API.

API Docs: https://www.gdacs.org/gdacsapi/swagger/

Covers: earthquakes (EQ), tropical cyclones (TC), floods (FL),
        volcanoes (VO), droughts (DR), wildfires (WF).

Filters to events relevant to India/South Asia.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

from apps.intelligence.schemas.signal import (
    Signal,
    SignalLocation,
    SignalSource,
    SignalType,
    SourceCategory,
    VerificationStatus,
    ProvenanceLabel,
)


# India territory + immediate boundary zones
MIN_LAT = 6.5
MAX_LAT = 35.5
MIN_LON = 68.5
MAX_LON = 97.5

GDACS_SOURCE = SignalSource(
    id="SRC-GDACS",
    name="Global Disaster Alert System (GDACS)",
    category=SourceCategory.OFFICIAL,
    verification=VerificationStatus.VERIFIED,
)

# Map GDACS event types to BharatSignal signal types and concepts
GDACS_TYPE_MAP = {
    "EQ": {
        "type": SignalType.SEISMIC,
        "concepts": ["earthquake", "seismic activity"],
        "label": "Earthquake",
    },
    "TC": {
        "type": SignalType.WEATHER,
        "concepts": ["cyclone", "tropical storm"],
        "label": "Tropical Cyclone",
    },
    "FL": {
        "type": SignalType.WEATHER,
        "concepts": ["river flooding", "coastal flooding"],
        "label": "Flood",
    },
    "VO": {
        "type": SignalType.SEISMIC,
        "concepts": ["seismic activity"],
        "label": "Volcano",
    },
    "DR": {
        "type": SignalType.ENVIRONMENTAL,
        "concepts": ["water shortage"],
        "label": "Drought",
    },
    "WF": {
        "type": SignalType.ENVIRONMENTAL,
        "concepts": ["industrial fire"],
        "label": "Wildfire",
    },
}


def _get_region_name(lat: float, lon: float) -> str:
    if lat >= 28:
        return "North India"
    if lat <= 16:
        return "South India"
    if lon <= 75:
        return "West India"
    if lon >= 85:
        return "East India"
    return "Central India"


def _is_in_india_region(lat: float, lon: float) -> bool:
    return MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON


def _alert_to_severity(alert_level: str) -> float:
    """Convert GDACS alert level to 0-1 severity."""
    levels = {
        "Red": 0.9,
        "Orange": 0.7,
        "Green": 0.5,
    }
    return levels.get(alert_level, 0.5)


def fetch_gdacs_disasters() -> list[Signal]:
    """
    Fetch recent disaster alerts from GDACS for the India region.

    Returns a list of Signal objects with provenance OBSERVED.
    On API failure, returns an empty list and prints the error.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)

    url = (
        "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?"
        f"fromdate={start_date.strftime('%Y-%m-%d')}"
        f"&todate={end_date.strftime('%Y-%m-%d')}"
        f"&alertlevel=Green;Orange;Red"
    )

    req = urllib.request.Request(url, headers={
        "User-Agent": "BharatSignal/1.0",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        print(f"  [GDACS] API error: {e}")
        return []

    # GDACS returns events under "features" (GeoJSON-like) or "result"
    features = []
    if isinstance(data, dict):
        if "features" in data:
            features = data["features"]
        elif "result" in data:
            features = data["result"] if isinstance(data["result"], list) else []
    elif isinstance(data, list):
        features = data

    signals = []
    signal_count = 0

    for feature in features:
        try:
            # Handle both GeoJSON-style and flat-style responses
            if "geometry" in feature and "properties" in feature:
                # GeoJSON format
                props = feature["properties"]
                geom = feature["geometry"]
                coords = geom.get("coordinates", [])
                if len(coords) >= 2:
                    lon = float(coords[0])
                    lat = float(coords[1])
                else:
                    continue
            elif "lat" in feature and "lng" in feature:
                # Flat format
                props = feature
                lat = float(feature["lat"])
                lon = float(feature["lng"])
            elif "fromdate" in feature:
                # Another GDACS format with nested geo data
                props = feature
                lat = float(feature.get("lat", feature.get("latitude", 0)))
                lon = float(feature.get("lng", feature.get("longitude", 0)))
                if lat == 0 and lon == 0:
                    continue
            else:
                continue

            if not _is_in_india_region(lat, lon):
                continue

            event_type = str(props.get("eventtype", props.get("type", ""))).upper()
            type_info = GDACS_TYPE_MAP.get(event_type)
            if type_info is None:
                continue

            alert_level = str(props.get("alertlevel", props.get("severity", "Green")))
            event_name = str(props.get("eventname", props.get("name", props.get("title", "Unknown event"))))
            country = str(props.get("country", props.get("countryname", "")))
            description_text = str(props.get("description", props.get("htmldescription", "")))

            # Parse timestamp
            date_str = props.get("fromdate", props.get("date", props.get("eventdate", "")))
            try:
                if date_str:
                    # Handle various date formats
                    date_str = str(date_str).replace("Z", "+00:00")
                    if "T" in date_str:
                        event_time = datetime.fromisoformat(date_str)
                    else:
                        event_time = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    event_time = datetime.now(timezone.utc)
            except (ValueError, AttributeError):
                event_time = datetime.now(timezone.utc)

            # Ensure timezone-aware
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)

            region = _get_region_name(lat, lon)
            severity = _alert_to_severity(alert_level)

            entities = list(type_info["concepts"])
            if event_name and event_name != "Unknown event":
                entities.append(event_name)
            if country:
                entities.append(country)

            # Clean up description
            if not description_text or description_text == "None":
                description_text = (
                    f"GDACS {type_info['label']} alert ({alert_level} level). "
                    f"Event: {event_name}. Location near ({lat:.2f}, {lon:.2f})."
                )

            signal = Signal(
                id=f"SIG-GDACS-{signal_count:04d}",
                source=GDACS_SOURCE,
                type=type_info["type"],
                title=f"GDACS {type_info['label']}: {event_name}",
                description=description_text[:500],  # Truncate overly long descriptions
                location=SignalLocation(
                    latitude=lat,
                    longitude=lon,
                    region=region,
                    precision_km=50.0,
                ),
                timestamp=event_time,
                entities=entities,
                severity=severity,
                provenance=ProvenanceLabel.OBSERVED,
                confidence=0.85,
                domain="disaster",
                tags=["gdacs", event_type.lower(), alert_level.lower(), "real-time"],
            )
            signals.append(signal)
            signal_count += 1

        except (KeyError, ValueError, TypeError) as e:
            # Skip malformed entries silently
            continue

    print(f"  [GDACS] Fetched {len(signals)} disaster alert signals in India region")
    return signals
