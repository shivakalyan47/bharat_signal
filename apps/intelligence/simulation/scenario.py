from datetime import datetime, timedelta, timezone

from apps.intelligence.schemas.signal import (
    Signal,
    SignalLocation,
    SignalSource,
    SignalType,
    SourceCategory,
    VerificationStatus,
)


def create_source(
    source_id: str,
    name: str,
    category: SourceCategory,
    verification: VerificationStatus,
) -> SignalSource:
    return SignalSource(
        id=source_id,
        name=name,
        category=category,
        verification=verification,
    )


def create_signal(
    signal_id: str,
    source: SignalSource,
    signal_type: SignalType,
    title: str,
    description: str,
    timestamp: datetime,
    latitude: float,
    longitude: float,
    region: str,
    entities: list[str],
    severity: float | None = None,
) -> Signal:
    return Signal(
        id=signal_id,
        source=source,
        type=signal_type,
        title=title,
        description=description,
        location=SignalLocation(
            latitude=latitude,
            longitude=longitude,
            region=region,
            precision_km=5.0,
        ),
        timestamp=timestamp,
        entities=entities,
        severity=severity,
    )


def create_flood_evolution_scenario() -> list[Signal]:
    """
    Create a deterministic synthetic national-signal scenario.

    The scenario contains:
    - 7 signals belonging to one evolving situation
    - 2 unrelated signals
    - 1 separate nearby situation

    All data is fictional demonstration data.
    It does NOT represent a real incident.
    """

    start = datetime(
        2026,
        9,
        26,
        9,
        0,
        tzinfo=timezone.utc,
    )

    # ------------------------------------------------------------------
    # SOURCES
    # ------------------------------------------------------------------

    weather_source = create_source(
        "SRC-WEATHER-001",
        "Synthetic Weather Monitor",
        SourceCategory.WEATHER,
        VerificationStatus.VERIFIED,
    )

    alert_source = create_source(
        "SRC-ALERT-001",
        "Synthetic Official Alert",
        SourceCategory.OFFICIAL,
        VerificationStatus.VERIFIED,
    )

    water_source = create_source(
        "SRC-WATER-001",
        "Synthetic Water Monitor",
        SourceCategory.INFRASTRUCTURE,
        VerificationStatus.REPUTABLE,
    )

    public_source = create_source(
        "SRC-PUBLIC-001",
        "Synthetic Public Reports",
        SourceCategory.PUBLIC,
        VerificationStatus.INDEPENDENT,
    )

    transport_source = create_source(
        "SRC-TRANSPORT-001",
        "Synthetic Transport Monitor",
        SourceCategory.TRANSPORT,
        VerificationStatus.REPUTABLE,
    )

    maintenance_source = create_source(
        "SRC-MAINTENANCE-001",
        "Synthetic Road Maintenance Monitor",
        SourceCategory.INFRASTRUCTURE,
        VerificationStatus.REPUTABLE,
    )

    power_source = create_source(
        "SRC-POWER-001",
        "Synthetic Power Monitor",
        SourceCategory.INFRASTRUCTURE,
        VerificationStatus.REPUTABLE,
    )

    # ------------------------------------------------------------------
    # SIGNALS
    # ------------------------------------------------------------------

    signals = [

        # ==============================================================
        # PRIMARY SITUATION
        # Heavy rainfall → water level → waterlogging → transport impact
        # ==============================================================

        create_signal(
            "SIG-001",
            weather_source,
            SignalType.WEATHER,
            "Heavy rainfall detected",
            "Sustained heavy rainfall has been observed across the monitored area.",
            start,
            12.9716,
            77.5946,
            "Demo Region",
            ["heavy rainfall"],
            0.55,
        ),

        create_signal(
            "SIG-002",
            alert_source,
            SignalType.OFFICIAL_ALERT,
            "Rainfall warning issued",
            "A rainfall-related warning has been issued for the monitored area.",
            start + timedelta(minutes=18),
            12.9730,
            77.5960,
            "Demo Region",
            ["rainfall warning"],
            0.65,
        ),

        create_signal(
            "SIG-003",
            water_source,
            SignalType.INFRASTRUCTURE,
            "Water level increasing",
            "Water levels are showing a sustained increase in the monitored area.",
            start + timedelta(minutes=34),
            12.9750,
            77.5925,
            "Demo Region",
            ["water level"],
            0.70,
        ),

        create_signal(
            "SIG-004",
            public_source,
            SignalType.PUBLIC_REPORT,
            "Waterlogging reported",
            "A public report indicates significant waterlogging.",
            start + timedelta(minutes=47),
            12.9695,
            77.5980,
            "Demo Region",
            ["waterlogging"],
            0.60,
        ),

        create_signal(
            "SIG-005",
            transport_source,
            SignalType.TRANSPORT,
            "Road disruption reported",
            "A transport route is experiencing disruption.",
            start + timedelta(minutes=63),
            12.9680,
            77.6000,
            "Demo Region",
            ["road disruption"],
            0.65,
        ),

        create_signal(
            "SIG-006",
            transport_source,
            SignalType.TRANSPORT,
            "Transport disruption increasing",
            "Transport disruption is expanding within the monitored area.",
            start + timedelta(minutes=81),
            12.9665,
            77.6015,
            "Demo Region",
            ["transport disruption"],
            0.72,
        ),

        create_signal(
            "SIG-007",
            public_source,
            SignalType.PUBLIC_REPORT,
            "Additional waterlogging reported",
            "A second independent report indicates continued waterlogging.",
            start + timedelta(minutes=95),
            12.9725,
            77.5990,
            "Demo Region",
            ["waterlogging"],
            0.68,
        ),

        # ==============================================================
        # DECOY 1
        # Nearby, but semantically unrelated
        # ==============================================================

        create_signal(
            "SIG-008",
            maintenance_source,
            SignalType.INFRASTRUCTURE,
            "Scheduled road maintenance",
            "Planned road maintenance is causing a temporary lane closure.",
            start + timedelta(minutes=42),
            12.9780,
            77.6050,
            "Demo Region",
            ["scheduled maintenance"],
            0.35,
        ),

        # ==============================================================
        # DECOY 2
        # Same region, unrelated infrastructure issue
        # ==============================================================

        create_signal(
            "SIG-009",
            power_source,
            SignalType.INFRASTRUCTURE,
            "Local power interruption",
            "A localized power interruption has been reported.",
            start + timedelta(minutes=70),
            12.9600,
            77.5850,
            "Demo Region",
            ["power interruption"],
            0.45,
        ),

        # ==============================================================
        # SEPARATE NEARBY SITUATION
        # Transport issue, but not caused by the primary situation
        # ==============================================================

        create_signal(
            "SIG-010",
            transport_source,
            SignalType.TRANSPORT,
            "Vehicle breakdown causing congestion",
            "A vehicle breakdown has caused localized traffic congestion.",
            start + timedelta(minutes=76),
            12.9500,
            77.5700,
            "Nearby Region",
            ["vehicle breakdown", "traffic congestion"],
            0.50,
        ),
    ]

    return signals


def main() -> None:
    signals = create_flood_evolution_scenario()

    print(f"Generated {len(signals)} synthetic signals")
    print("=" * 80)

    for signal in signals:
        print(
            f"{signal.timestamp.isoformat()} | "
            f"{signal.id} | "
            f"{signal.type.value:18} | "
            f"{signal.location.region:15} | "
            f"{signal.title}"
        )


if __name__ == "__main__":
    main()