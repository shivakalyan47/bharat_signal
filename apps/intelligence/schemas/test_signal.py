from datetime import datetime, timezone

from apps.intelligence.schemas.signal import (
    Signal,
    SignalLocation,
    SignalSource,
    SignalType,
    SourceCategory,
    VerificationStatus,
)


def main():
    signal = Signal(
        id="SIG-001",
        source=SignalSource(
            id="SRC-WEATHER-001",
            name="Synthetic Weather Source",
            category=SourceCategory.WEATHER,
            verification=VerificationStatus.VERIFIED,
        ),
        type=SignalType.WEATHER,
        title="Heavy rainfall detected",
        description="Heavy rainfall observed across multiple locations.",
        location=SignalLocation(
            latitude=12.9716,
            longitude=77.5946,
            region="Bengaluru",
            precision_km=5.0,
        ),
        timestamp=datetime.now(timezone.utc),
        entities=["Bengaluru"],
        severity=0.7,
    )

    print("✅ Signal created successfully")
    print()
    print(signal.model_dump_json(indent=2))


if __name__ == "__main__":
    main()