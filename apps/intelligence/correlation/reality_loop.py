"""
BHARATSIGNAL REALITY LOOP
==========================

The Reality Loop is BharatSignal's self-correcting intelligence layer.

After the Forecasting Engine predicts what signals should appear next,
the Reality Loop watches the incoming signal stream to see whether
those predictions actually materialise. When they do, the system
reinforces the causal rules that produced the correct forecast.
When they don't, it penalises those rules. Over time this creates
a self-improving national intelligence system whose confidence
calibration improves with every observed outcome.

Architecture:
    Forecast → Watch Window → Incoming Signals → Score → Adjust Weights
"""

from datetime import datetime, timedelta
from pydantic import BaseModel

from apps.intelligence.schemas.signal import Signal
from apps.intelligence.correlation.engine import extract_concepts
from apps.intelligence.correlation.forecasting import Forecast, SituationForecast


# ============================================================
# OBSERVATION RESULT
# ============================================================

class ObservationResult(BaseModel):
    """A single forecast-vs-reality comparison."""
    predicted_concept: str
    predicted_probability: float
    observed: bool
    observed_signal_id: str | None = None
    observed_at: datetime | None = None
    distance_km: float | None = None
    verdict: str  # "CONFIRMED", "MISSED", "PENDING"


class RealityLoopReport(BaseModel):
    """Full reality-loop evaluation for one situation forecast."""
    situation_id: str
    forecast_time: datetime
    evaluation_time: datetime
    watch_window_hours: float
    observations: list[ObservationResult]
    accuracy_score: float  # 0.0 to 1.0
    calibration_delta: float  # How well-calibrated were the probabilities
    verdict_summary: str


# ============================================================
# CAUSAL WEIGHT LEDGER
# ============================================================

class CausalWeightAdjustment(BaseModel):
    """Record of a weight adjustment made by the Reality Loop."""
    cause_concept: str
    effect_concept: str
    original_weight: float
    adjusted_weight: float
    adjustment_reason: str


class CausalLedger:
    """
    Tracks cumulative adjustments to the causal knowledge base.
    
    Instead of mutating the base weights directly, the ledger
    records a transparent audit trail of every adjustment,
    making the system's learning process fully explainable.
    """

    def __init__(self) -> None:
        self.adjustments: list[CausalWeightAdjustment] = []
        self.overrides: dict[tuple[str, str], float] = {}

    def record_adjustment(
        self,
        cause: str,
        effect: str,
        original: float,
        adjusted: float,
        reason: str,
    ) -> None:
        self.adjustments.append(
            CausalWeightAdjustment(
                cause_concept=cause,
                effect_concept=effect,
                original_weight=round(original, 4),
                adjusted_weight=round(adjusted, 4),
                adjustment_reason=reason,
            )
        )
        self.overrides[(cause, effect)] = round(adjusted, 4)

    def get_effective_weight(
        self,
        cause: str,
        effect: str,
        base_weight: float,
    ) -> float:
        return self.overrides.get((cause, effect), base_weight)


# ============================================================
# REALITY LOOP ENGINE
# ============================================================

WATCH_WINDOW_HOURS = 6.0
REINFORCEMENT_RATE = 0.05
PENALTY_RATE = 0.08


def evaluate_forecast_against_reality(
    forecast: SituationForecast,
    incoming_signals: list[Signal],
    forecast_time: datetime,
    evaluation_time: datetime,
    centroid_lat: float,
    centroid_lon: float,
) -> RealityLoopReport:
    """
    Compare a situation forecast against signals that actually
    arrived within the watch window.

    For each prediction, the loop checks whether any incoming
    signal carries the predicted concept within the spatial
    and temporal neighbourhood of the situation.
    """

    from apps.intelligence.correlation.engine import haversine_distance_km

    observations: list[ObservationResult] = []

    for prediction in forecast.predictions:
        matched = False

        for signal in incoming_signals:
            # Check temporal window
            signal_age = (signal.timestamp - forecast_time).total_seconds() / 3600.0
            if signal_age < 0 or signal_age > WATCH_WINDOW_HOURS:
                continue

            # Check spatial proximity
            dist = haversine_distance_km(
                centroid_lat,
                centroid_lon,
                signal.location.latitude,
                signal.location.longitude,
            )
            if dist > 100.0:
                continue

            # Check concept match
            concepts = extract_concepts(signal)
            if prediction.predicted_concept in concepts:
                observations.append(
                    ObservationResult(
                        predicted_concept=prediction.predicted_concept,
                        predicted_probability=prediction.probability,
                        observed=True,
                        observed_signal_id=signal.id,
                        observed_at=signal.timestamp,
                        distance_km=round(dist, 2),
                        verdict="CONFIRMED",
                    )
                )
                matched = True
                break

        if not matched:
            observations.append(
                ObservationResult(
                    predicted_concept=prediction.predicted_concept,
                    predicted_probability=prediction.probability,
                    observed=False,
                    verdict="MISSED",
                )
            )

    # --------------------------------------------------------
    # Accuracy and Calibration
    # --------------------------------------------------------
    if not observations:
        accuracy = 0.0
        calibration_delta = 0.0
    else:
        confirmed = [o for o in observations if o.observed]
        accuracy = len(confirmed) / len(observations)

        # Calibration: how close were predicted probabilities to actual hit rates?
        # Perfect calibration: predicting 0.34 and hitting 34% of the time
        predicted_avg = sum(o.predicted_probability for o in observations) / len(observations)
        actual_avg = accuracy
        calibration_delta = round(actual_avg - predicted_avg, 4)

    confirmed_count = sum(1 for o in observations if o.observed)
    missed_count = sum(1 for o in observations if not o.observed)

    if confirmed_count > 0 and missed_count == 0:
        summary = f"All {confirmed_count} predictions confirmed. Forecast was accurate."
    elif confirmed_count > 0:
        summary = (
            f"{confirmed_count} of {len(observations)} predictions confirmed. "
            f"{missed_count} predictions did not materialise within the watch window."
        )
    else:
        summary = f"None of the {len(observations)} predictions were confirmed within the watch window."

    return RealityLoopReport(
        situation_id=forecast.situation_id,
        forecast_time=forecast_time,
        evaluation_time=evaluation_time,
        watch_window_hours=WATCH_WINDOW_HOURS,
        observations=observations,
        accuracy_score=round(accuracy, 4),
        calibration_delta=calibration_delta,
        verdict_summary=summary,
    )


def apply_reality_loop_adjustments(
    report: RealityLoopReport,
    causal_transitions: dict[tuple[str, str], float],
    ledger: CausalLedger,
) -> dict[tuple[str, str], float]:
    """
    Adjust causal weights based on reality-loop observations.

    Confirmed predictions → small reinforcement.
    Missed predictions → larger penalty.

    The asymmetric rates ensure the system becomes more
    conservative over time, which is the correct posture
    for a national intelligence platform.
    """

    updated = dict(causal_transitions)

    for obs in report.observations:
        # Find all transitions that could have produced this prediction
        for (cause, effect), weight in causal_transitions.items():
            if effect == obs.predicted_concept:
                original = weight

                if obs.observed:
                    # Reinforce
                    new_weight = min(1.0, weight + REINFORCEMENT_RATE)
                    reason = (
                        f"Prediction '{effect}' was CONFIRMED by signal "
                        f"{obs.observed_signal_id}. Reinforcing transition "
                        f"'{cause}' → '{effect}'."
                    )
                else:
                    # Penalise
                    new_weight = max(0.05, weight - PENALTY_RATE)
                    reason = (
                        f"Prediction '{effect}' was NOT observed within "
                        f"the {report.watch_window_hours}h watch window. "
                        f"Penalising transition '{cause}' → '{effect}'."
                    )

                updated[(cause, effect)] = round(new_weight, 4)
                ledger.record_adjustment(cause, effect, original, new_weight, reason)

    return updated
