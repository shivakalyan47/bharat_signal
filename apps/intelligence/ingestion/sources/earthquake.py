"""
USGS Earthquake Data Adapter
==============================

Fetches real-time earthquake data from the USGS FDSN Event Web Service.
No API key required. Free public API.

API Docs: https://earthquake.usgs.gov/fdsnws/event/1/

Filters for earthquakes near India/South Asia (lat 5-38, lon 65-100)
with magnitude >= 2.5 in the last 7 days.
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
MIN_MAGNITUDE = 2.0
LOOKBACK_DAYS = 30

USGS_SOURCE = SignalSource(
    id="SRC-USGS",
    name="USGS Earthquake Hazards Program",
    category=SourceCategory.SEISMIC,
    verification=VerificationStatus.VERIFIED,
)


def _get_region_name(lat: float, lon: float) -> str:
    """Approximate region name from coordinates."""
    if lat >= 28:
        return "North India"
    if lat <= 16:
        return "South India"
    if lon <= 75:
        return "West India"
    if lon >= 85:
        return "East India"
    return "Central India"


def _magnitude_to_severity(mag: float) -> float:
    """Convert earthquake magnitude to 0-1 severity scale."""
    if mag >= 7.0:
        return 1.0
    if mag >= 6.0:
        return 0.9
    if mag >= 5.0:
        return 0.8
    if mag >= 4.0:
        return 0.65
    if mag >= 3.0:
        return 0.5
    return 0.35


def fetch_usgs_earthquakes() -> list[Signal]:
    """
    Fetch recent earthquakes from USGS for the India/South Asia region.

    Returns a list of Signal objects with provenance OBSERVED.
    On API failure, returns an empty list and prints the error.
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=LOOKBACK_DAYS)

    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query?"
        f"format=geojson"
        f"&starttime={start_time.strftime('%Y-%m-%d')}"
        f"&endtime={end_time.strftime('%Y-%m-%d')}"
        f"&minmagnitude={MIN_MAGNITUDE}"
        f"&minlatitude={MIN_LAT}"
        f"&maxlatitude={MAX_LAT}"
        f"&minlongitude={MIN_LON}"
        f"&maxlongitude={MAX_LON}"
        f"&orderby=time"
        f"&limit=50"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "BharatSignal/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        print(f"  [USGS] API error: {e}")
        return []

    if "features" not in data:
        print("  [USGS] Unexpected response format (no 'features' key)")
        return []

    signals = []

    for i, feature in enumerate(data["features"]):
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [])

        if len(coords) < 2:
            continue

        lon = float(coords[0])
        lat = float(coords[1])
        depth_km = float(coords[2]) if len(coords) > 2 else None

        mag = props.get("mag")
        if mag is None:
            continue
        mag = float(mag)

        place = props.get("place", "Unknown location")
        time_ms = props.get("time")
        if time_ms is None:
            continue

        eq_time = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
        region = _get_region_name(lat, lon)
        severity = _magnitude_to_severity(mag)

        depth_str = f" Depth: {depth_km:.1f}km." if depth_km is not None else ""
        description = (
            f"Earthquake of magnitude {mag:.1f} detected. Location: {place}.{depth_str} "
            f"Seismic activity reported by USGS."
        )

        entities = ["earthquake", "seismic activity", "tremor"]
        if place and place != "Unknown location":
            entities.append(place)

        signal = Signal(
            id=f"SIG-USGS-EQ-{i:04d}",
            source=USGS_SOURCE,
            type=SignalType.SEISMIC,
            title=f"Earthquake M{mag:.1f} — {place}",
            description=description,
            location=SignalLocation(
                latitude=lat,
                longitude=lon,
                region=region,
                precision_km=10.0,
            ),
            timestamp=eq_time,
            entities=entities,
            severity=severity,
            provenance=ProvenanceLabel.OBSERVED,
            confidence=0.95,
            domain="seismic",
            tags=["usgs", "earthquake", "real-time"],
        )
        signals.append(signal)

    print(f"  [USGS] Fetched {len(signals)} earthquake signals (M>={MIN_MAGNITUDE}, last {LOOKBACK_DAYS} days)")
    return signals
