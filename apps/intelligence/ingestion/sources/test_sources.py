"""
Unit and integration tests for BharatSignal real-data ingestion adapters:
- USGS Earthquake adapter (earthquake.py)
- NASA EONET adapter (nasa_events.py)
- GDACS Disasters adapter (gdacs_disasters.py)
"""

import sys
import unittest
from datetime import datetime, timezone

from apps.intelligence.schemas.signal import (
    Signal,
    SignalType,
    SourceCategory,
    ProvenanceLabel,
)
from apps.intelligence.ingestion.sources.earthquake import (
    _get_region_name as eq_region,
    _magnitude_to_severity,
    fetch_usgs_earthquakes,
)
from apps.intelligence.ingestion.sources.nasa_events import (
    _is_in_india_region as nasa_in_region,
    _get_region_name as nasa_region,
    _event_severity,
    fetch_nasa_eonet_events,
)
from apps.intelligence.ingestion.sources.gdacs_disasters import (
    _is_in_india_region as gdacs_in_region,
    _get_region_name as gdacs_region,
    _alert_to_severity,
    fetch_gdacs_disasters,
)


class TestIngestionSources(unittest.TestCase):

    def test_earthquake_severity_mapping(self):
        self.assertAlmostEqual(_magnitude_to_severity(7.5), 1.0)
        self.assertAlmostEqual(_magnitude_to_severity(6.2), 0.9)
        self.assertAlmostEqual(_magnitude_to_severity(5.1), 0.8)
        self.assertAlmostEqual(_magnitude_to_severity(4.2), 0.65)
        self.assertAlmostEqual(_magnitude_to_severity(3.5), 0.5)
        self.assertAlmostEqual(_magnitude_to_severity(2.0), 0.35)

    def test_earthquake_region_mapping(self):
        self.assertEqual(eq_region(30.0, 78.0), "North India")
        self.assertEqual(eq_region(12.0, 77.0), "South India")
        self.assertEqual(eq_region(22.0, 71.0), "West India")
        self.assertEqual(eq_region(22.0, 88.0), "East India")
        self.assertEqual(eq_region(22.0, 80.0), "Central India")

    def test_nasa_eonet_bounding_box(self):
        # Coordinates in India region (lat 5-38, lon 65-100)
        self.assertTrue(nasa_in_region(12.97, 77.59))
        self.assertTrue(nasa_in_region(28.61, 77.20))
        # Coordinates outside India region
        self.assertFalse(nasa_in_region(51.50, -0.12))  # London
        self.assertFalse(nasa_in_region(40.71, -74.00))  # New York

    def test_gdacs_bounding_box(self):
        self.assertTrue(gdacs_in_region(19.07, 72.87))
        self.assertFalse(gdacs_in_region(-33.86, 151.20))  # Sydney

    def test_gdacs_alert_severity(self):
        self.assertAlmostEqual(_alert_to_severity("Red"), 0.90)
        self.assertAlmostEqual(_alert_to_severity("Orange"), 0.70)
        self.assertAlmostEqual(_alert_to_severity("Green"), 0.50)
        self.assertAlmostEqual(_alert_to_severity("Unknown"), 0.50)

    def test_live_adapters_smoke_test(self):
        """Smoke test fetching live data (handles network gracefully)."""
        print("\n--- Running live source fetch smoke test ---")
        eq_signals = fetch_usgs_earthquakes()
        self.assertIsInstance(eq_signals, list)
        for s in eq_signals:
            self.assertIsInstance(s, Signal)
            self.assertEqual(s.type, SignalType.SEISMIC)
            self.assertEqual(s.provenance, ProvenanceLabel.OBSERVED)
            self.assertTrue(5.0 <= s.location.latitude <= 38.0)
            self.assertTrue(65.0 <= s.location.longitude <= 100.0)

        nasa_signals = fetch_nasa_eonet_events()
        self.assertIsInstance(nasa_signals, list)
        for s in nasa_signals:
            self.assertIsInstance(s, Signal)
            self.assertEqual(s.provenance, ProvenanceLabel.OBSERVED)

        gdacs_signals = fetch_gdacs_disasters()
        self.assertIsInstance(gdacs_signals, list)
        for s in gdacs_signals:
            self.assertIsInstance(s, Signal)
            self.assertEqual(s.provenance, ProvenanceLabel.OBSERVED)


if __name__ == "__main__":
    unittest.main()
