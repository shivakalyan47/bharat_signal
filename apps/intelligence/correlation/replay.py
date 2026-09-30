from datetime import datetime
from pydantic import BaseModel
from apps.intelligence.schemas.signal import Signal
from apps.intelligence.correlation.dna import IncidentDNA

class ReplaySnapshot(BaseModel):
    snapshot_time: datetime
    signals_known: int
    incidents_detected: int
    situations_active: int
    forecasts_made: int
    signal_ids: list[str]
    incident_ids: list[str]
    situation_ids: list[str]
    active_forecasts: list[dict]  # simplified forecast data
    what_changed: list[str]  # human-readable changes from previous snapshot

class IncidentReplayTimeline(BaseModel):
    incident_id: str
    total_snapshots: int
    snapshots: list[ReplaySnapshot]
    timeline_start: datetime
    timeline_end: datetime

def generate_replay_timeline(
    incident_id: str,
    all_signals: list[Signal],
    clusters: list[dict],
    incident_dnas: list[IncidentDNA],
    situations: list,
    forecasts: list,
) -> IncidentReplayTimeline:
    """
    Generate a timeline replay of how the system's understanding
    evolved over time for a specific incident.
    
    At each signal arrival time, we capture what the system knew,
    what it had detected, and what it was predicting.
    """
    # Find the cluster for this incident
    cluster_data = None
    for c in clusters:
        if c['cluster_id'] == incident_id:
            cluster_data = c
            break
    
    if not cluster_data:
        raise ValueError(f"Incident {incident_id} not found")
    
    # Get signals belonging to this incident, sorted chronologically
    incident_signal_ids = set(cluster_data['signal_ids'])
    incident_signals = sorted(
        [s for s in all_signals if s.id in incident_signal_ids],
        key=lambda s: s.timestamp,
    )
    
    if not incident_signals:
        raise ValueError(f"No signals found for incident {incident_id}")
    
    snapshots = []
    prev_snapshot = None
    
    for i, signal in enumerate(incident_signals):
        signals_so_far = incident_signals[:i + 1]
        signal_ids_so_far = [s.id for s in signals_so_far]
        
        # What changed since last snapshot
        changes = []
        if prev_snapshot is None:
            changes.append(f"First signal detected: {signal.id} - {signal.title}")
        else:
            changes.append(f"New signal arrived: {signal.id} - {signal.title}")
            if len(signal_ids_so_far) >= 2 and len(prev_snapshot.signal_ids) < 2:
                changes.append("Sufficient signals to form incident cluster")
        
        # Find relevant situations and forecasts
        relevant_sit_ids = []
        for sit in situations:
            if incident_id in [inc.incident_id for inc in sit.incidents]:
                relevant_sit_ids.append(sit.situation_id)
        
        active_fc = []
        for fc in forecasts:
            if fc.situation_id in relevant_sit_ids:
                for pred in fc.predictions:
                    active_fc.append({
                        'concept': pred.predicted_concept,
                        'probability': pred.probability,
                    })
        
        snapshot = ReplaySnapshot(
            snapshot_time=signal.timestamp,
            signals_known=len(signals_so_far),
            incidents_detected=1 if len(signals_so_far) >= 2 else 0,
            situations_active=len(relevant_sit_ids) if len(signals_so_far) >= 2 else 0,
            forecasts_made=len(active_fc) if len(signals_so_far) >= 2 else 0,
            signal_ids=signal_ids_so_far,
            incident_ids=[incident_id] if len(signals_so_far) >= 2 else [],
            situation_ids=relevant_sit_ids if len(signals_so_far) >= 2 else [],
            active_forecasts=active_fc if len(signals_so_far) >= 2 else [],
            what_changed=changes,
        )
        snapshots.append(snapshot)
        prev_snapshot = snapshot
    
    return IncidentReplayTimeline(
        incident_id=incident_id,
        total_snapshots=len(snapshots),
        snapshots=snapshots,
        timeline_start=incident_signals[0].timestamp,
        timeline_end=incident_signals[-1].timestamp,
    )
