"""
NASA EONET Natural Events Adapter
===================================

Fetches real-time natural event data from NASA's Earth Observatory
Natural Event Tracker (EONET) API v3.

No API key required. Free public API.

API Docs: https://eonet.gsfc.nasa.gov/docs/v3

Covers: wildfires, severe storms, volcanoes, floods, landslides.
Filters events to India/South Asia bounding box.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

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

NASA_SOURCE = SignalSource(
    id="SRC-NASA-EONET",
    name="NASA Earth Observatory (EONET)",
    category=SourceCategory.ENVIRONMENTAL,
    verification=VerificationStatus.VERIFIED,
)

# Map EONET category IDs to BharatSignal signal types and concepts
EONET_CATEGORY_MAP = {
    "wildfires": {
        "type": SignalType.ENVIRONMENTAL,
        "concepts": ["industrial fire"],
        "source_category": SourceCategory.ENVIRONMENTAL,
    },
    "severeStorms": {
        "type": SignalType.WEATHER,
        "concepts": ["cyclone", "thunderstorm"],
        "source_category": SourceCategory.WEATHER,
    },
    "volcanoes": {
        "type": SignalType.SEISMIC,
        "concepts": ["seismic activity"],
        "source_category": SourceCategory.SEISMIC,
    },
    "floods": {
        "type": SignalType.WEATHER,
        "concepts": ["river flooding", "coastal flooding"],
        "source_category": SourceCategory.WEATHER,
    },
    "landslides": {
        "type": SignalType.SEISMIC,
        "concepts": ["landslide"],
        "source_category": SourceCategory.SEISMIC,
    },
    "earthquakes": {
        "type": SignalType.SEISMIC,
        "concepts": ["earthquake"],
        "source_category": SourceCategory.SEISMIC,
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


def _event_severity(category_id: str) -> float:
    """Assign a reasonable default severity based on event category."""
    severity_map = {
        "wildfires": 0.7,
        "severeStorms": 0.75,
        "volcanoes": 0.85,
        "floods": 0.7,
        "landslides": 0.7,
        "earthquakes": 0.8,
    }
    return severity_map.get(category_id, 0.6)


def fetch_nasa_eonet_events() -> list[Signal]:
    """
    Fetch recent natural events from NASA EONET for the India region.

    Returns a list of Signal objects with provenance OBSERVED.
    On API failure, returns an empty list and prints the error.
    """
    # Fetch only currently open (active) events, limited to recent ones
    url = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=100"

    req = urllib.request.Request(url, headers={"User-Agent": "BharatSignal/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        print(f"  [NASA EONET] API error: {e}")
        return []

    if "events" not in data:
        print("  [NASA EONET] Unexpected response format (no 'events' key)")
        return []

    signals = []
    signal_count = 0

    for event in data["events"]:
        event_id = event.get("id", "unknown")
        title = event.get("title", "Unknown event")
        categories = event.get("categories", [])
        geometries = event.get("geometry", [])

        if not geometries:
            continue

        # Determine category
        category_id = categories[0].get("id", "unknown") if categories else "unknown"
        cat_info = EONET_CATEGORY_MAP.get(category_id)
        if cat_info is None:
            # Unknown category, use generic defaults
            signal_type = SignalType.ENVIRONMENTAL
            concepts = []
        else:
            signal_type = cat_info["type"]
            concepts = list(cat_info["concepts"])

        # Use the most recent geometry point
        latest_geom = geometries[-1]
        geom_coords = latest_geom.get("coordinates", [])
        geom_date = latest_geom.get("date", "")

        if not geom_coords:
            continue

        # EONET returns [lon, lat] or [[lon, lat], ...] for polygons
        if isinstance(geom_coords[0], list):
            # Polygon or multi-point — use first coordinate
            lon = float(geom_coords[0][0])
            lat = float(geom_coords[0][1])
        else:
            lon = float(geom_coords[0])
            lat = float(geom_coords[1])

        if not _is_in_india_region(lat, lon):
            continue

        # Parse timestamp
        try:
            event_time = datetime.fromisoformat(geom_date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            event_time = datetime.now(timezone.utc)

        region = _get_region_name(lat, lon)
        severity = _event_severity(category_id)

        entities = concepts.copy()
        if title:
            entities.append(title)

        signal = Signal(
            id=f"SIG-EONET-{signal_count:04d}",
            source=NASA_SOURCE,
            type=signal_type,
            title=title,
            description=f"NASA EONET event: {title}. Category: {category_id}. Detected via satellite observation.",
            location=SignalLocation(
                latitude=lat,
                longitude=lon,
                region=region,
                precision_km=25.0,
            ),
            timestamp=event_time,
            entities=entities,
            severity=severity,
            provenance=ProvenanceLabel.OBSERVED,
            confidence=0.9,
            domain="natural_event",
            tags=["nasa", "eonet", category_id, "real-time"],
        )
        signals.append(signal)
        signal_count += 1

    print(f"  [NASA EONET] Fetched {len(signals)} natural event signals in India region")
    return signals
