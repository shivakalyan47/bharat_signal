from datetime import datetime
from pydantic import BaseModel

from apps.intelligence.schemas.signal import Signal
from apps.intelligence.correlation.engine import extract_concepts


class ConceptSignature(BaseModel):
    concept: str
    weight: float
    first_seen: datetime


class IncidentDNA(BaseModel):
    incident_id: str
    signal_count: int
    
    # Temporal Footprint
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    
    # Spatial Footprint
    centroid_lat: float
    centroid_lon: float
    
    # Semantic Signature
    core_concepts: list[ConceptSignature]
    evolution_pattern: list[str]  # Ordered sequence of new concepts
    
    # Impact
    entities: list[str]
    max_severity: float


def extract_incident_dna(
    incident_id: str, 
    signals: list[Signal],
) -> IncidentDNA:
    """
    Extract the 'DNA' signature of an incident from its constituent signals.
    
    The DNA captures the spatial, temporal, semantic, and evolutionary
    characteristics of the incident, making it easy to match against
    historical templates or predict future evolution.
    """
    
    if not signals:
        raise ValueError("Cannot extract DNA from an empty list of signals.")
        
    # Sort signals chronologically to build evolution pattern
    sorted_signals = sorted(signals, key=lambda s: s.timestamp)
    
    start_time = sorted_signals[0].timestamp
    end_time = sorted_signals[-1].timestamp
    duration_minutes = (end_time - start_time).total_seconds() / 60.0
    
    # Spatial Centroid
    centroid_lat = sum(s.location.latitude for s in signals) / len(signals)
    centroid_lon = sum(s.location.longitude for s in signals) / len(signals)
    
    # Entities and Severity
    entities = list({entity for s in signals for entity in s.entities})
    severities = [s.severity for s in signals if s.severity is not None]
    max_severity = max(severities) if severities else 0.0
    
    # Semantic Signature and Evolution
    concept_counts = {}
    concept_first_seen = {}
    evolution_pattern = []
    
    for signal in sorted_signals:
        concepts = extract_concepts(signal)
        for concept in concepts:
            # Update counts for weights
            concept_counts[concept] = concept_counts.get(concept, 0) + 1
            
            # Track evolution
            if concept not in concept_first_seen:
                concept_first_seen[concept] = signal.timestamp
                evolution_pattern.append(concept)
                
    # Normalize concept weights
    core_concepts = []
    for concept, count in concept_counts.items():
        weight = count / len(signals)
        core_concepts.append(
            ConceptSignature(
                concept=concept,
                weight=round(weight, 4),
                first_seen=concept_first_seen[concept],
            )
        )
        
    # Sort core concepts by weight (descending)
    core_concepts.sort(key=lambda c: c.weight, reverse=True)
    
    return IncidentDNA(
        incident_id=incident_id,
        signal_count=len(signals),
        start_time=start_time,
        end_time=end_time,
        duration_minutes=round(duration_minutes, 2),
        centroid_lat=round(centroid_lat, 4),
        centroid_lon=round(centroid_lon, 4),
        core_concepts=core_concepts,
        evolution_pattern=evolution_pattern,
        entities=sorted(entities),
        max_severity=round(max_severity, 2),
    )
