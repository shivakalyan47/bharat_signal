"""
BHARATSIGNAL NATIONAL SCALE SCENARIO
================================

A large multi-city, multi-domain synthetic scenario spanning real
Indian geography to demonstrate national-scale signal intelligence.
"""

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
    language: str = "en",
    provenance: ProvenanceLabel = ProvenanceLabel.OBSERVED,
    contradicts: list[str] = None
) -> Signal:
    sig = Signal(
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
        language=language,
        provenance=provenance,
    )
    if contradicts:
        sig.contradicts = contradicts
    return sig


# SOURCES
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
LOCAL_NEWS = _source("SRC-NEWS", "Local News Aggregator", SourceCategory.MEDIA)
TECH_MON = _source("SRC-TECH", "Tech Infrastructure Monitor", SourceCategory.INFRASTRUCTURE)

def create_national_scale_scenario() -> list[Signal]:
    base = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)
    signals = []

    # MUMBAI (12 signals)
    signals.extend([
        _signal("MUM-001", IMD, SignalType.WEATHER, "Heavy rainfall detected over Mumbai", "Sustained heavy rainfall of 120mm/hr observed.", base, 19.0760, 72.8777, "Mumbai", ["Mumbai", "Arabian Sea", "heavy rainfall"], 0.70),
        _signal("MUM-002", NDMA, SignalType.OFFICIAL_ALERT, "Rainfall warning issued for Mumbai", "NDMA has issued a rainfall warning.", base + timedelta(minutes=15), 19.0800, 72.8800, "Mumbai", ["Mumbai", "NDMA", "rainfall warning"], 0.75),
        _signal("MUM-003", CWC, SignalType.INFRASTRUCTURE, "Water level rising in Mithi River", "Mithi River water levels rising.", base + timedelta(minutes=40), 19.0720, 72.8650, "Mumbai", ["Mithi River", "Mumbai", "water level"], 0.72),
        _signal("MUM-004", PUBLIC, SignalType.PUBLIC_REPORT, "Waterlogging reported in Sion and Dadar", "Severe waterlogging in Sion.", base + timedelta(minutes=55), 19.0425, 72.8620, "Mumbai", ["Sion", "Dadar", "waterlogging"], 0.65),
        _signal("MUM-005", TRANSPORT, SignalType.TRANSPORT, "Road disruption on Western Express Highway", "WEH road disruption.", base + timedelta(minutes=70), 19.1197, 72.8464, "Mumbai", ["Western Express Highway", "road disruption"], 0.68),
        _signal("MUM-006", TRANSPORT, SignalType.TRANSPORT, "Train delay on Mumbai suburban rail", "Central line delayed.", base + timedelta(minutes=85), 19.0176, 72.8562, "Mumbai", ["Central Line", "transport disruption"], 0.78),
        _signal("MUM-007", PUBLIC, SignalType.PUBLIC_REPORT, "Waterlogging in Kurla", "Kurla West waterlogging.", base + timedelta(minutes=100), 19.0726, 72.8793, "Mumbai", ["Kurla", "waterlogging"], 0.62),
        _signal("MUM-008", POWER, SignalType.INFRASTRUCTURE, "Power outage in South Mumbai", "Power failure in Colaba.", base + timedelta(minutes=115), 18.9220, 72.8347, "Mumbai", ["Colaba", "power outage"], 0.60),
        _signal("MUM-009", LOCAL_NEWS, SignalType.MEDIA, "मुंबईत मुसळधार पाऊस", "Heavy rains in Mumbai.", base + timedelta(minutes=120), 19.076, 72.877, "Mumbai", ["Mumbai", "heavy rainfall"], 0.7, "mr"), # Marathi
        _signal("MUM-010", PUBLIC, SignalType.PUBLIC_REPORT, "Airport operations normal", "Airport seems fine.", base + timedelta(minutes=130), 19.099, 72.868, "Mumbai", ["Mumbai Airport"], 0.1),
        _signal("MUM-011", TRANSPORT, SignalType.TRANSPORT, "Airport delays start", "Flights delayed due to visibility.", base + timedelta(minutes=140), 19.099, 72.868, "Mumbai", ["Mumbai Airport", "flight cancellation"], 0.5, contradicts=["MUM-010"]),
        _signal("MUM-012", HEALTH, SignalType.HEALTH, "Ambulances stuck", "Ambulances unable to reach hospitals.", base + timedelta(minutes=150), 19.05, 72.85, "Mumbai", ["hospital surge", "traffic congestion"], 0.8),
    ])

    # CHENNAI (10 signals)
    signals.extend([
        _signal("CHN-001", IMD, SignalType.WEATHER, "Cyclonic storm developing", "Storm 380km from Chennai.", base + timedelta(minutes=10), 13.0827, 80.2707, "Chennai", ["Chennai", "cyclone"], 0.80),
        _signal("CHN-002", NDMA, SignalType.OFFICIAL_ALERT, "Cyclone warning issued", "NDMA warning for TN coast.", base + timedelta(minutes=30), 13.0500, 80.2800, "Chennai", ["Chennai", "cyclone"], 0.85),
        _signal("CHN-003", INCOIS, SignalType.WEATHER, "Storm surge warning", "Surge of 1.5-2.0m expected.", base + timedelta(minutes=50), 13.0600, 80.2900, "Chennai", ["Chennai coast", "coastal flooding"], 0.82),
        _signal("CHN-004", NDMA, SignalType.OFFICIAL_ALERT, "Evacuation warning", "Evacuation for Zone I.", base + timedelta(minutes=75), 13.0450, 80.2850, "Chennai", ["evacuation warning"], 0.88),
        _signal("CHN-005", TRANSPORT, SignalType.TRANSPORT, "Flight cancellations", "14 flights cancelled.", base + timedelta(minutes=90), 12.9941, 80.1709, "Chennai", ["Chennai Airport", "flight cancellation"], 0.72),
        _signal("CHN-006", POWER, SignalType.INFRASTRUCTURE, "Power shutdown", "Preventive power cut.", base + timedelta(minutes=105), 13.0700, 80.2750, "Chennai", ["power interruption"], 0.65),
        _signal("CHN-007", PUBLIC, SignalType.PUBLIC_REPORT, "Relief camp activated", "Nehru Indoor Stadium.", base + timedelta(minutes=120), 13.0622, 80.2730, "Chennai", ["shelter activated"], 0.70),
        _signal("CHN-008", PUBLIC, SignalType.PUBLIC_REPORT, "No surge seen", "Beach looks normal so far.", base + timedelta(minutes=130), 13.05, 80.28, "Chennai", ["Chennai coast"], 0.2),
        _signal("CHN-009", LOCAL_NEWS, SignalType.MEDIA, "புயல் எச்சரிக்கை", "Cyclone warning in Tamil.", base + timedelta(minutes=140), 13.08, 80.27, "Chennai", ["cyclone"], 0.8, "ta"), # Tamil
        _signal("CHN-010", INCOIS, SignalType.WEATHER, "Waves increasing", "Surge has begun.", base + timedelta(minutes=150), 13.06, 80.29, "Chennai", ["coastal flooding"], 0.85, contradicts=["CHN-008"]),
    ])

    # DELHI (9 signals)
    signals.extend([
        _signal("DEL-001", INDUSTRIAL, SignalType.INDUSTRIAL, "Industrial fire", "Bawana fire.", base + timedelta(minutes=20), 28.7950, 77.0510, "Delhi NCR", ["Bawana", "industrial fire"], 0.82),
        _signal("DEL-002", ENV, SignalType.ENVIRONMENTAL, "Air quality deteriorating", "AQI severe.", base + timedelta(minutes=45), 28.7350, 77.1200, "Delhi NCR", ["Bawana", "smog alert"], 0.75),
        _signal("DEL-003", NDMA, SignalType.OFFICIAL_ALERT, "Evacuation warning", "2km radius evacuation.", base + timedelta(minutes=60), 28.7950, 77.0510, "Delhi NCR", ["evacuation warning"], 0.85),
        _signal("DEL-004", HEALTH, SignalType.HEALTH, "Hospital surge", "Rohini Sector 9.", base + timedelta(minutes=80), 28.7270, 77.1180, "Delhi NCR", ["hospital surge"], 0.72),
        _signal("DEL-005", TRANSPORT, SignalType.TRANSPORT, "Road closure", "GT Karnal Road.", base + timedelta(minutes=95), 28.7800, 77.0600, "Delhi NCR", ["road closure"], 0.65),
        _signal("DEL-006", ENV, SignalType.ENVIRONMENTAL, "Pollution emergency", "North Delhi districts.", base + timedelta(minutes=130), 28.7500, 77.1000, "Delhi NCR", ["pollution emergency"], 0.78),
        _signal("DEL-007", LOCAL_NEWS, SignalType.MEDIA, "भयानक आग", "Terrible fire in Bawana.", base + timedelta(minutes=140), 28.79, 77.05, "Delhi NCR", ["Bawana", "industrial fire"], 0.8, "hi"), # Hindi
        _signal("DEL-008", PUBLIC, SignalType.PUBLIC_REPORT, "Fire controlled", "Looks like smoke is less.", base + timedelta(minutes=150), 28.79, 77.05, "Delhi NCR", ["Bawana"], 0.3),
        _signal("DEL-009", INDUSTRIAL, SignalType.INDUSTRIAL, "Secondary explosion", "New explosion at site.", base + timedelta(minutes=160), 28.79, 77.05, "Delhi NCR", ["industrial fire"], 0.9, contradicts=["DEL-008"]),
    ])

    # UTTARAKHAND (8 signals)
    signals.extend([
        _signal("UTK-001", SEISMO, SignalType.SEISMIC, "Earthquake detected", "Magnitude 5.8.", base + timedelta(minutes=5), 30.3165, 78.0322, "Uttarakhand", ["Chamoli", "earthquake"], 0.80),
        _signal("UTK-002", PUBLIC, SignalType.PUBLIC_REPORT, "Structural damage", "Chamoli market.", base + timedelta(minutes=25), 30.4050, 79.3250, "Uttarakhand", ["structural damage"], 0.70),
        _signal("UTK-003", PUBLIC, SignalType.PUBLIC_REPORT, "Landslide", "Badrinath Highway.", base + timedelta(minutes=35), 30.4250, 79.4300, "Uttarakhand", ["landslide"], 0.75),
        _signal("UTK-004", TRANSPORT, SignalType.TRANSPORT, "Road disruption", "NH-7 blocked.", base + timedelta(minutes=50), 30.5570, 79.5640, "Uttarakhand", ["road disruption"], 0.72),
        _signal("UTK-005", POWER, SignalType.INFRASTRUCTURE, "Power failure", "Chamoli district.", base + timedelta(minutes=45), 30.4200, 79.3400, "Uttarakhand", ["power outage"], 0.68),
        _signal("UTK-006", NDMA, SignalType.OFFICIAL_ALERT, "Evacuation advisory", "Alaknanda river settlements.", base + timedelta(minutes=65), 30.3900, 79.3100, "Uttarakhand", ["evacuation advisory"], 0.82),
        _signal("UTK-007", HEALTH, SignalType.HEALTH, "Missing Data Health", "Hospitals reporting unknown status", base + timedelta(minutes=90), 30.3, 79.3, "Uttarakhand", ["health"], None), # Missing severity
        _signal("UTK-008", PUBLIC, SignalType.PUBLIC_REPORT, "Bridge intact", "Bridge near Pipalkoti seems okay.", base + timedelta(minutes=100), 30.43, 79.44, "Uttarakhand", ["bridge damage"], 0.2),
    ])

    # KOLKATA (5 signals)
    signals.extend([
        _signal("KOL-001", IMD, SignalType.WEATHER, "Cloudburst warning", "Heavy rainfall approaching.", base + timedelta(minutes=5), 22.5726, 88.3639, "Kolkata", ["Kolkata", "heavy rainfall"], 0.75),
        _signal("KOL-002", PUBLIC, SignalType.PUBLIC_REPORT, "Street flooding", "Park street flooded.", base + timedelta(minutes=25), 22.55, 88.35, "Kolkata", ["waterlogging"], 0.7),
        _signal("KOL-003", TRANSPORT, SignalType.TRANSPORT, "Tram service stopped", "Waterlogged tracks.", base + timedelta(minutes=40), 22.56, 88.36, "Kolkata", ["transport disruption"], 0.65),
        _signal("KOL-004", POWER, SignalType.INFRASTRUCTURE, "Substation underwater", "CESC cut power.", base + timedelta(minutes=60), 22.57, 88.36, "Kolkata", ["power outage"], 0.8),
        _signal("KOL-005", LOCAL_NEWS, SignalType.MEDIA, "বন্যা পরিস্থিতি", "Flood situation worsening.", base + timedelta(minutes=70), 22.57, 88.36, "Kolkata", ["waterlogging"], 0.8, "bn"), # Bengali
    ])

    # RAJASTHAN (4 signals)
    signals.extend([
        _signal("RAJ-001", IMD, SignalType.WEATHER, "Extreme Heatwave", "Temperatures over 48C.", base + timedelta(minutes=10), 26.9124, 75.7873, "Rajasthan", ["Jaipur", "heatwave"], 0.8),
        _signal("RAJ-002", POWER, SignalType.INFRASTRUCTURE, "Grid overload", "High AC usage causing faults.", base + timedelta(minutes=30), 26.9, 75.8, "Rajasthan", ["power outage"], 0.75),
        _signal("RAJ-003", HEALTH, SignalType.HEALTH, "Heatstroke cases", "Hospitals overwhelmed.", base + timedelta(minutes=50), 26.92, 75.8, "Rajasthan", ["hospital surge"], 0.85),
        _signal("RAJ-004", PUBLIC, SignalType.PUBLIC_REPORT, "Water shortage", "No municipal water supply.", base + timedelta(minutes=70), 26.9, 75.75, "Rajasthan", ["water shortage"], 0.9),
    ])

    # BANGALORE (4 signals)
    signals.extend([
        _signal("BLR-001", TECH_MON, SignalType.INFRASTRUCTURE, "ISP Outage", "Major fiber cut in Whitefield.", base + timedelta(minutes=15), 12.9698, 77.7499, "Bangalore", ["Whitefield", "internet outage"], 0.8),
        _signal("BLR-002", PUBLIC, SignalType.PUBLIC_REPORT, "Traffic gridlock", "Signals down.", base + timedelta(minutes=35), 12.97, 77.75, "Bangalore", ["traffic congestion"], 0.7),
        _signal("BLR-003", POWER, SignalType.INFRASTRUCTURE, "Tech park power cut", "DG sets running.", base + timedelta(minutes=55), 12.97, 77.75, "Bangalore", ["power outage"], 0.6),
        _signal("BLR-004", TRANSPORT, SignalType.TRANSPORT, "Metro delay", "Purple line delayed.", base + timedelta(minutes=75), 12.97, 77.75, "Bangalore", ["transport disruption"], 0.5),
    ])

    # GOA (3 signals)
    signals.extend([
        _signal("GOA-001", ENV, SignalType.ENVIRONMENTAL, "Oil spill detected", "Offshore spill moving towards coast.", base + timedelta(minutes=20), 15.4909, 73.8278, "Goa", ["oil spill"], 0.85),
        _signal("GOA-002", PUBLIC, SignalType.PUBLIC_REPORT, "Tar balls on beach", "Beaches affected.", base + timedelta(minutes=40), 15.5, 73.8, "Goa", ["beach pollution"], 0.7),
        _signal("GOA-003", NDMA, SignalType.OFFICIAL_ALERT, "Fishing ban", "No fishing advised.", base + timedelta(minutes=60), 15.5, 73.8, "Goa", ["fishing ban"], 0.8),
    ])

    # DECOYS (5 signals)
    signals.extend([
        _signal("DCY-001", MAINT, SignalType.INFRASTRUCTURE, "Road maintenance", "Pune NH-48.", base + timedelta(minutes=42), 18.7546, 73.4062, "Pune", ["scheduled maintenance"], 0.20),
        _signal("DCY-002", TRANSPORT, SignalType.TRANSPORT, "Vehicle breakdown", "Hyderabad ORR.", base + timedelta(minutes=60), 17.2403, 78.4294, "Hyderabad", ["traffic congestion"], 0.30),
        _signal("DCY-003", HEALTH, SignalType.HEALTH, "Vaccination drive", "Kolkata North 24 Parganas.", base + timedelta(minutes=80), 22.5726, 88.3639, "Kolkata", ["vaccination"], 0.15),
        _signal("DCY-004", PUBLIC, SignalType.PUBLIC_REPORT, "Concert noise", "Loud music in Ahmedabad.", base + timedelta(minutes=90), 23.0225, 72.5714, "Ahmedabad", ["noise"], 0.1),
        _signal("DCY-005", PUBLIC, SignalType.PUBLIC_REPORT, "Festival crowd", "Crowds in Mysore.", base + timedelta(minutes=100), 12.2958, 76.6394, "Mysore", ["crowd"], 0.2),
    ])

    return signals


def create_national_scale_confirmations() -> list[Signal]:
    base = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)
    return [
        _signal("CONF-MUM-001", TRANSPORT, SignalType.TRANSPORT, "Massive traffic congestion", "Confirmed.", base + timedelta(hours=3), 19.06, 72.87, "Mumbai", ["traffic congestion"], 0.75),
        _signal("CONF-MUM-002", TRANSPORT, SignalType.TRANSPORT, "Supply chain delay", "Confirmed.", base + timedelta(hours=4), 19.03, 72.86, "Mumbai", ["supply disruption"], 0.60),
        _signal("CONF-CHN-001", PUBLIC, SignalType.PUBLIC_REPORT, "Shelters activated", "Confirmed.", base + timedelta(hours=3, minutes=30), 13.055, 80.26, "Chennai", ["shelter activated"], 0.68),
        _signal("CONF-DEL-001", ENV, SignalType.ENVIRONMENTAL, "Air quality hazardous", "Confirmed.", base + timedelta(hours=4), 28.62, 77.03, "Delhi NCR", ["aqi dangerous"], 0.80),
        _signal("CONF-UTK-001", PUBLIC, SignalType.PUBLIC_REPORT, "Bridge washed away", "Confirmed, contradicts UTK-008.", base + timedelta(hours=2, minutes=30), 30.43, 79.44, "Uttarakhand", ["bridge damage"], 0.78, contradicts=["UTK-008"]),
        _signal("CONF-KOL-001", HEALTH, SignalType.HEALTH, "Waterborne diseases rise", "Confirmed.", base + timedelta(hours=5), 22.57, 88.36, "Kolkata", ["hospital surge"], 0.7),
        _signal("CONF-RAJ-001", HEALTH, SignalType.HEALTH, "Heatstroke deaths reported", "Confirmed.", base + timedelta(hours=6), 26.9, 75.8, "Rajasthan", ["hospital surge"], 0.9),
        _signal("CONF-BLR-001", TECH_MON, SignalType.INFRASTRUCTURE, "Internet restored partially", "Confirmed.", base + timedelta(hours=4), 12.97, 77.75, "Bangalore", ["internet outage"], 0.3),
        _signal("CONF-GOA-001", PUBLIC, SignalType.PUBLIC_REPORT, "Beach cleanup started", "Confirmed.", base + timedelta(hours=5), 15.5, 73.8, "Goa", ["beach pollution"], 0.5),
        _signal("CONF-MUM-003", HEALTH, SignalType.HEALTH, "Hospitals receiving patients", "Confirmed.", base + timedelta(hours=5), 19.05, 72.85, "Mumbai", ["hospital surge"], 0.8),
    ]

def main() -> None:
    signals = create_national_scale_scenario()
    confirmations = create_national_scale_confirmations()
    print(f"Generated {len(signals)} primary signals + {len(confirmations)} confirmation signals")

if __name__ == "__main__":
    main()
