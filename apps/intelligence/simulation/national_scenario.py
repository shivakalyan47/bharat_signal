"""
BHARATSIGNAL NATIONAL SCENARIO
================================

A rich multi-city, multi-domain synthetic scenario spanning real
Indian geography to demonstrate national-scale signal intelligence.

SCENARIOS:
  1. Mumbai Monsoon Crisis    — Heavy rainfall → waterlogging → transport collapse
  2. Chennai Cyclone Approach — Cyclone warning → coastal flooding → evacuations
  3. Delhi NCR Industrial Fire — Factory fire → air quality emergency → hospital surge
  4. Uttarakhand Earthquake   — Seismic event → landslide → road/bridge damage

All data is fictional demonstration data.
It does NOT represent any real incident.
"""

from datetime import datetime, timedelta, timezone

from apps.intelligence.schemas.signal import (
    Signal,
    SignalLocation,
    SignalSource,
    SignalType,
    SourceCategory,
    VerificationStatus,
)


def _source(
    sid: str,
    name: str,
    category: SourceCategory,
    verification: VerificationStatus = VerificationStatus.REPUTABLE,
) -> SignalSource:
    return SignalSource(
        id=sid,
        name=name,
        category=category,
        verification=verification,
    )


def _signal(
    signal_id: str,
    source: SignalSource,
    signal_type: SignalType,
    title: str,
    description: str,
    timestamp: datetime,
    lat: float,
    lon: float,
    region: str,
    entities: list[str],
    severity: float = 0.5,
) -> Signal:
    return Signal(
        id=signal_id,
        source=source,
        type=signal_type,
        title=title,
        description=description,
        location=SignalLocation(
            latitude=lat,
            longitude=lon,
            region=region,
            precision_km=5.0,
        ),
        timestamp=timestamp,
        entities=entities,
        severity=severity,
    )


# ============================================================
# SOURCES
# ============================================================

IMD = _source("SRC-IMD", "India Meteorological Department", SourceCategory.WEATHER, VerificationStatus.VERIFIED)
NDMA = _source("SRC-NDMA", "National Disaster Management Authority", SourceCategory.OFFICIAL, VerificationStatus.VERIFIED)
INCOIS = _source("SRC-INCOIS", "Indian National Centre for Ocean Info", SourceCategory.WEATHER, VerificationStatus.VERIFIED)
CWC = _source("SRC-CWC", "Central Water Commission", SourceCategory.INFRASTRUCTURE, VerificationStatus.VERIFIED)
SEISMO = _source("SRC-SEISMO", "National Seismological Network", SourceCategory.SEISMIC, VerificationStatus.VERIFIED)
PUBLIC = _source("SRC-PUBLIC", "Citizen Reports Network", SourceCategory.PUBLIC, VerificationStatus.INDEPENDENT)
TRANSPORT = _source("SRC-TRANSPORT", "Transport Monitoring System", SourceCategory.TRANSPORT)
POWER = _source("SRC-POWER", "Power Grid Status Monitor", SourceCategory.INFRASTRUCTURE)
HEALTH = _source("SRC-HEALTH", "Health Surveillance System", SourceCategory.HEALTH)
INDUSTRIAL = _source("SRC-INDUSTRIAL", "Industrial Safety Monitor", SourceCategory.INDUSTRIAL)
ENV = _source("SRC-ENV", "Environmental Quality Monitor", SourceCategory.ENVIRONMENTAL)
MAINT = _source("SRC-MAINT", "Maintenance Scheduling System", SourceCategory.INFRASTRUCTURE)


def create_national_scenario() -> list[Signal]:
    """
    Create a national-scale synthetic signal scenario.

    Four simultaneous crises across India:
      Mumbai     — Monsoon flooding cascade
      Chennai    — Cyclone approach and coastal impact
      Delhi NCR  — Industrial fire with toxic air
      Uttarakhand — Earthquake and landslide

    Plus decoy/unrelated signals to test rejection.
    """

    base = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)

    signals = []

    # ==============================================================
    # MUMBAI MONSOON CRISIS (19.0760°N, 72.8777°E)
    # Signals: MUM-001 through MUM-008
    # ==============================================================

    signals.extend([
        _signal(
            "MUM-001", IMD, SignalType.WEATHER,
            "Heavy rainfall detected over Mumbai",
            "Sustained heavy rainfall of 120mm/hr observed across Mumbai metropolitan area. "
            "Torrential rain expected to continue for 6-8 hours.",
            base,
            19.0760, 72.8777, "Mumbai",
            ["Mumbai", "Arabian Sea", "heavy rainfall"],
            0.70,
        ),
        _signal(
            "MUM-002", NDMA, SignalType.OFFICIAL_ALERT,
            "Rainfall warning issued for Mumbai",
            "NDMA has issued a rainfall warning for Greater Mumbai. "
            "Citizens advised to avoid low-lying areas.",
            base + timedelta(minutes=15),
            19.0800, 72.8800, "Mumbai",
            ["Mumbai", "NDMA", "rainfall warning"],
            0.75,
        ),
        _signal(
            "MUM-003", CWC, SignalType.INFRASTRUCTURE,
            "Water level rising in Mithi River",
            "Water levels in the Mithi River are showing sustained increase. "
            "Currently at 3.2m, approaching danger mark of 4.0m.",
            base + timedelta(minutes=40),
            19.0720, 72.8650, "Mumbai",
            ["Mithi River", "Mumbai", "water level"],
            0.72,
        ),
        _signal(
            "MUM-004", PUBLIC, SignalType.PUBLIC_REPORT,
            "Waterlogging reported in Sion and Dadar",
            "Multiple citizen reports of severe waterlogging in Sion, Dadar, "
            "and Hindmata junction areas. Water entering ground-floor shops.",
            base + timedelta(minutes=55),
            19.0425, 72.8620, "Mumbai",
            ["Sion", "Dadar", "Hindmata", "waterlogging"],
            0.65,
        ),
        _signal(
            "MUM-005", TRANSPORT, SignalType.TRANSPORT,
            "Road disruption on Western Express Highway",
            "Western Express Highway experiencing road disruption between "
            "Andheri and Borivali due to waterlogging. Diversions in effect.",
            base + timedelta(minutes=70),
            19.1197, 72.8464, "Mumbai",
            ["Western Express Highway", "Andheri", "Borivali", "road disruption"],
            0.68,
        ),
        _signal(
            "MUM-006", TRANSPORT, SignalType.TRANSPORT,
            "Train delay on Mumbai suburban rail",
            "Central line suburban rail services experiencing transport disruption. "
            "Trains delayed by 45-60 minutes due to waterlogged tracks.",
            base + timedelta(minutes=85),
            19.0176, 72.8562, "Mumbai",
            ["Central Line", "Mumbai suburban rail", "transport disruption"],
            0.78,
        ),
        _signal(
            "MUM-007", PUBLIC, SignalType.PUBLIC_REPORT,
            "Additional waterlogging reported in Kurla",
            "Independent reports confirm continued waterlogging spreading to "
            "Kurla West and BKC connector road.",
            base + timedelta(minutes=100),
            19.0726, 72.8793, "Mumbai",
            ["Kurla", "BKC", "waterlogging"],
            0.62,
        ),
        _signal(
            "MUM-008", POWER, SignalType.INFRASTRUCTURE,
            "Power outage in parts of South Mumbai",
            "Power failure reported across Colaba, Fort, and Marine Lines areas. "
            "BEST estimates 4-6 hours for restoration.",
            base + timedelta(minutes=115),
            18.9220, 72.8347, "Mumbai",
            ["Colaba", "Fort", "Marine Lines", "BEST", "power outage"],
            0.60,
        ),
    ])

    # ==============================================================
    # CHENNAI CYCLONE APPROACH (13.0827°N, 80.2707°E)
    # Signals: CHN-001 through CHN-007
    # ==============================================================

    signals.extend([
        _signal(
            "CHN-001", IMD, SignalType.WEATHER,
            "Cyclonic storm developing in Bay of Bengal",
            "A cyclonic storm is intensifying in the Bay of Bengal, 380km "
            "southeast of Chennai. Expected to make landfall in 18-24 hours.",
            base + timedelta(minutes=10),
            13.0827, 80.2707, "Chennai",
            ["Bay of Bengal", "Chennai", "cyclone"],
            0.80,
        ),
        _signal(
            "CHN-002", NDMA, SignalType.OFFICIAL_ALERT,
            "Cyclone warning issued for Tamil Nadu coast",
            "NDMA has issued a cyclone warning for the northern Tamil Nadu coast. "
            "Fishermen advised not to venture into the sea.",
            base + timedelta(minutes=30),
            13.0500, 80.2800, "Chennai",
            ["Tamil Nadu", "Chennai", "cyclone", "NDMA"],
            0.85,
        ),
        _signal(
            "CHN-003", INCOIS, SignalType.WEATHER,
            "Storm surge warning for Chennai coast",
            "Storm surge of 1.5-2.0m expected along Chennai coast. "
            "Coastal flooding likely in low-lying areas.",
            base + timedelta(minutes=50),
            13.0600, 80.2900, "Chennai",
            ["Chennai coast", "coastal flooding", "storm surge"],
            0.82,
        ),
        _signal(
            "CHN-004", NDMA, SignalType.OFFICIAL_ALERT,
            "Evacuation warning for coastal Chennai zones",
            "Evacuation warning issued for Zone I and Zone II of coastal Chennai. "
            "Residents in low-lying areas to move to designated shelters.",
            base + timedelta(minutes=75),
            13.0450, 80.2850, "Chennai",
            ["Chennai Zone I", "Chennai Zone II", "evacuation warning"],
            0.88,
        ),
        _signal(
            "CHN-005", TRANSPORT, SignalType.TRANSPORT,
            "Flight cancellations at Chennai Airport",
            "14 flights cancelled at Chennai International Airport due to "
            "approaching cyclone. Flight cancellation advisory in effect.",
            base + timedelta(minutes=90),
            12.9941, 80.1709, "Chennai",
            ["Chennai Airport", "flight cancellation"],
            0.72,
        ),
        _signal(
            "CHN-006", POWER, SignalType.INFRASTRUCTURE,
            "Preventive power shutdown in coastal areas",
            "TANGEDCO initiating preventive power interruption in flood-prone "
            "coastal zones to prevent electrocution hazards.",
            base + timedelta(minutes=105),
            13.0700, 80.2750, "Chennai",
            ["TANGEDCO", "power interruption", "coastal zones"],
            0.65,
        ),
        _signal(
            "CHN-007", PUBLIC, SignalType.PUBLIC_REPORT,
            "Relief camp activated at Nehru Indoor Stadium",
            "Shelter activated at Nehru Indoor Stadium for displaced coastal residents. "
            "Rescue operation teams from NDRF positioned along Marina Beach.",
            base + timedelta(minutes=120),
            13.0622, 80.2730, "Chennai",
            ["Nehru Indoor Stadium", "NDRF", "shelter activated", "rescue operation"],
            0.70,
        ),
    ])

    # ==============================================================
    # DELHI NCR INDUSTRIAL FIRE (28.6139°N, 77.2090°E)
    # Signals: DEL-001 through DEL-006
    # ==============================================================

    signals.extend([
        _signal(
            "DEL-001", INDUSTRIAL, SignalType.INDUSTRIAL,
            "Industrial fire at Bawana chemical factory",
            "A major industrial fire has broken out at a chemical factory in "
            "Bawana Industrial Area. Fire tenders from 6 stations deployed.",
            base + timedelta(minutes=20),
            28.7950, 77.0510, "Delhi NCR",
            ["Bawana Industrial Area", "industrial fire", "chemical factory"],
            0.82,
        ),
        _signal(
            "DEL-002", ENV, SignalType.ENVIRONMENTAL,
            "Air quality deteriorating near Bawana",
            "Air quality index has crossed 400 (Severe+) in areas downwind of "
            "Bawana fire. Smog alert issued for Rohini and Pitampura.",
            base + timedelta(minutes=45),
            28.7350, 77.1200, "Delhi NCR",
            ["Bawana", "Rohini", "Pitampura", "air quality", "smog alert"],
            0.75,
        ),
        _signal(
            "DEL-003", NDMA, SignalType.OFFICIAL_ALERT,
            "Evacuation warning for Bawana industrial zone",
            "DDMA has issued an evacuation warning for a 2km radius around the "
            "Bawana industrial fire site due to toxic chemical leak risk.",
            base + timedelta(minutes=60),
            28.7950, 77.0510, "Delhi NCR",
            ["Bawana", "DDMA", "evacuation warning", "chemical leak"],
            0.85,
        ),
        _signal(
            "DEL-004", HEALTH, SignalType.HEALTH,
            "Hospital surge at Rohini Sector hospitals",
            "Hospitals in Rohini Sector 9 and Sector 16 reporting hospital surge "
            "with patients presenting respiratory distress symptoms.",
            base + timedelta(minutes=80),
            28.7270, 77.1180, "Delhi NCR",
            ["Rohini", "hospital surge", "respiratory distress"],
            0.72,
        ),
        _signal(
            "DEL-005", TRANSPORT, SignalType.TRANSPORT,
            "Road closure around Bawana fire site",
            "Road closure in effect on GT Karnal Road near Bawana due to "
            "fire-fighting operations. Severe traffic congestion building.",
            base + timedelta(minutes=95),
            28.7800, 77.0600, "Delhi NCR",
            ["GT Karnal Road", "Bawana", "road closure", "traffic congestion"],
            0.65,
        ),
        _signal(
            "DEL-006", ENV, SignalType.ENVIRONMENTAL,
            "Pollution emergency declared for North Delhi",
            "Pollution emergency declared by CPCB for North Delhi districts. "
            "AQI dangerous levels persisting. Schools ordered closed.",
            base + timedelta(minutes=130),
            28.7500, 77.1000, "Delhi NCR",
            ["North Delhi", "CPCB", "pollution emergency", "aqi dangerous"],
            0.78,
        ),
    ])

    # ==============================================================
    # UTTARAKHAND EARTHQUAKE (30.3165°N, 78.0322°E)
    # Signals: UTK-001 through UTK-006
    # ==============================================================

    signals.extend([
        _signal(
            "UTK-001", SEISMO, SignalType.SEISMIC,
            "Earthquake detected near Chamoli",
            "Seismic activity of magnitude 5.8 detected near Chamoli, "
            "Uttarakhand. Depth: 12km. Tremor felt across Garhwal region.",
            base + timedelta(minutes=5),
            30.3165, 78.0322, "Uttarakhand",
            ["Chamoli", "Garhwal", "earthquake", "tremor"],
            0.80,
        ),
        _signal(
            "UTK-002", PUBLIC, SignalType.PUBLIC_REPORT,
            "Structural damage reported in Chamoli town",
            "Citizen reports of structural damage and building damage in Chamoli "
            "market area. Several old buildings showing cracks.",
            base + timedelta(minutes=25),
            30.4050, 79.3250, "Uttarakhand",
            ["Chamoli", "structural damage", "building damage"],
            0.70,
        ),
        _signal(
            "UTK-003", PUBLIC, SignalType.PUBLIC_REPORT,
            "Landslide on Badrinath Highway",
            "A major landslide has been reported on Badrinath Highway near "
            "Pipalkoti. Road blocked by debris and boulders.",
            base + timedelta(minutes=35),
            30.4250, 79.4300, "Uttarakhand",
            ["Badrinath Highway", "Pipalkoti", "landslide", "road blocked"],
            0.75,
        ),
        _signal(
            "UTK-004", TRANSPORT, SignalType.TRANSPORT,
            "Road disruption on NH-7 near Joshimath",
            "Road disruption confirmed on NH-7 near Joshimath. "
            "Stranded tourists being assisted by SDRF.",
            base + timedelta(minutes=50),
            30.5570, 79.5640, "Uttarakhand",
            ["NH-7", "Joshimath", "SDRF", "road disruption"],
            0.72,
        ),
        _signal(
            "UTK-005", POWER, SignalType.INFRASTRUCTURE,
            "Power failure across Chamoli district",
            "Power outage reported across Chamoli district following earthquake. "
            "Electricity disruption affecting hospitals and communication towers.",
            base + timedelta(minutes=45),
            30.4200, 79.3400, "Uttarakhand",
            ["Chamoli district", "power outage", "electricity disruption"],
            0.68,
        ),
        _signal(
            "UTK-006", NDMA, SignalType.OFFICIAL_ALERT,
            "Evacuation advisory for Chamoli riverside settlements",
            "Evacuation advisory issued for settlements along Alaknanda river "
            "in Chamoli district due to potential landslide-dam breach risk.",
            base + timedelta(minutes=65),
            30.3900, 79.3100, "Uttarakhand",
            ["Alaknanda", "Chamoli", "evacuation advisory"],
            0.82,
        ),
    ])

    # ==============================================================
    # DECOY SIGNALS — Unrelated events
    # ==============================================================

    signals.extend([
        _signal(
            "DCY-001", MAINT, SignalType.INFRASTRUCTURE,
            "Scheduled road maintenance on NH-48 Pune",
            "Planned road maintenance on NH-48 near Lonavala. "
            "One lane closed between 10 PM and 5 AM.",
            base + timedelta(minutes=42),
            18.7546, 73.4062, "Pune",
            ["NH-48", "Lonavala", "scheduled maintenance"],
            0.20,
        ),
        _signal(
            "DCY-002", TRANSPORT, SignalType.TRANSPORT,
            "Vehicle breakdown on Hyderabad ORR",
            "A vehicle breakdown on Hyderabad Outer Ring Road causing "
            "minor traffic congestion near Shamshabad exit.",
            base + timedelta(minutes=60),
            17.2403, 78.4294, "Hyderabad",
            ["ORR", "Shamshabad", "vehicle breakdown", "traffic congestion"],
            0.30,
        ),
        _signal(
            "DCY-003", HEALTH, SignalType.HEALTH,
            "Routine vaccination drive in Kolkata",
            "District health authorities conducting routine vaccination "
            "drive across North 24 Parganas district.",
            base + timedelta(minutes=80),
            22.5726, 88.3639, "Kolkata",
            ["Kolkata", "North 24 Parganas", "vaccination"],
            0.15,
        ),
    ])

    return signals


def create_confirmation_signals() -> list[Signal]:
    """
    Signals that arrive AFTER the forecast is made.

    These are used by the Reality Loop to check whether
    predictions actually materialised.
    """

    base = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)

    return [
        # Mumbai: Traffic congestion confirmed (predicted by forecast)
        _signal(
            "CONF-MUM-001", TRANSPORT, SignalType.TRANSPORT,
            "Massive traffic congestion across Mumbai",
            "Traffic congestion and gridlock reported across major Mumbai "
            "arterial roads. Average speeds below 5 km/h.",
            base + timedelta(hours=3),
            19.0600, 72.8700, "Mumbai",
            ["Mumbai", "traffic congestion", "gridlock"],
            0.75,
        ),
        # Mumbai: Supply chain disruption confirmed
        _signal(
            "CONF-MUM-002", TRANSPORT, SignalType.TRANSPORT,
            "Supply chain delay affecting Mumbai markets",
            "Supply disruption to APMC wholesale market. Truck movement "
            "halted due to waterlogged approach roads.",
            base + timedelta(hours=4),
            19.0300, 72.8600, "Mumbai",
            ["APMC", "supply disruption", "logistics disruption"],
            0.60,
        ),
        # Chennai: Shelter activated confirmed
        _signal(
            "CONF-CHN-001", PUBLIC, SignalType.PUBLIC_REPORT,
            "Multiple shelters activated across Chennai",
            "Shelter activated at 12 locations across Chennai. Relief camp "
            "operations underway with NDRF coordination.",
            base + timedelta(hours=3, minutes=30),
            13.0550, 80.2600, "Chennai",
            ["Chennai", "shelter activated", "relief camp"],
            0.68,
        ),
        # Delhi: Air quality worsens (extends prediction)
        _signal(
            "CONF-DEL-001", ENV, SignalType.ENVIRONMENTAL,
            "Air quality reaches hazardous levels in West Delhi",
            "AQI dangerous levels now spreading to West Delhi. "
            "Smog alert extended to Dwarka and Janakpuri.",
            base + timedelta(hours=4),
            28.6200, 77.0300, "Delhi NCR",
            ["West Delhi", "Dwarka", "Janakpuri", "aqi dangerous", "smog alert"],
            0.80,
        ),
        # Uttarakhand: Bridge damage confirmed
        _signal(
            "CONF-UTK-001", PUBLIC, SignalType.PUBLIC_REPORT,
            "Bridge damage reported near Pipalkoti",
            "Bridge damage confirmed on Alaknanda bridge near Pipalkoti. "
            "Bridge washed away by debris flow following landslide.",
            base + timedelta(hours=2, minutes=30),
            30.4300, 79.4400, "Uttarakhand",
            ["Pipalkoti", "Alaknanda", "bridge damage", "bridge washed away"],
            0.78,
        ),
    ]


def main() -> None:
    """Print summary of national scenario."""
    signals = create_national_scenario()
    confirmation = create_confirmation_signals()

    print(f"Generated {len(signals)} primary signals + {len(confirmation)} confirmation signals")
    print("=" * 100)

    regions = {}
    for s in signals:
        r = s.location.region
        regions[r] = regions.get(r, 0) + 1

    print("\nSIGNAL DISTRIBUTION BY REGION:")
    for region, count in sorted(regions.items(), key=lambda x: -x[1]):
        print(f"  {region:20} → {count} signals")

    print(f"\nSIGNAL TIMELINE:")
    for s in sorted(signals, key=lambda x: x.timestamp):
        print(
            f"  {s.timestamp.strftime('%H:%M')} | "
            f"{s.id:10} | "
            f"{s.type.value:18} | "
            f"{s.location.region:15} | "
            f"{s.title}"
        )


if __name__ == "__main__":
    main()
