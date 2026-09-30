from datetime import datetime
from pydantic import BaseModel

from apps.intelligence.correlation.dna import IncidentDNA
from apps.intelligence.correlation.engine import haversine_distance_km


# ============================================================
# PROTOTYPE CAUSAL KNOWLEDGE BASE
# ============================================================
# Maps (Cause Concept, Effect Concept) -> Causal Strength
#
# This is a transparent, auditable knowledge layer.
# Every transition is a hypothesis that the Reality Loop
# will test against observed outcomes.
# ============================================================

CAUSAL_TRANSITIONS = {
    # Weather → Water
    ("heavy_rainfall", "water_level"): 0.90,
    ("heavy_rainfall", "waterlogging"): 0.80,
    ("heavy_rainfall", "river_flooding"): 0.75,
    ("rainfall_warning", "water_level"): 0.60,
    ("water_level", "waterlogging"): 0.95,
    ("water_level", "river_flooding"): 0.70,

    # Water → Transport / Infrastructure
    ("waterlogging", "road_disruption"): 0.85,
    ("waterlogging", "transport_disruption"): 0.80,
    ("waterlogging", "traffic_congestion"): 0.60,
    ("waterlogging", "power_interruption"): 0.40,
    ("waterlogging", "disease_outbreak"): 0.35,
    ("road_disruption", "traffic_congestion"): 0.70,
    ("vehicle_breakdown", "traffic_congestion"): 0.90,
    ("transport_disruption", "supply_chain_delay"): 0.75,
    ("road_disruption", "supply_chain_delay"): 0.65,

    # Cyclone cascades
    ("cyclone", "heavy_rainfall"): 0.95,
    ("cyclone", "coastal_flooding"): 0.90,
    ("cyclone", "power_interruption"): 0.80,
    ("cyclone", "structural_damage"): 0.75,
    ("cyclone", "transport_disruption"): 0.85,
    ("cyclone", "telecom_disruption"): 0.70,
    ("coastal_flooding", "evacuation_warning"): 0.85,

    # Flooding cascades
    ("river_flooding", "bridge_damage"): 0.70,
    ("river_flooding", "evacuation_warning"): 0.75,
    ("dam_overflow", "river_flooding"): 0.90,
    ("dam_overflow", "evacuation_warning"): 0.90,
    ("bridge_damage", "road_disruption"): 0.95,
    ("flood_risk", "evacuation_warning"): 0.80,
    ("flood_risk", "road_disruption"): 0.75,
    ("flood_risk", "waterlogging"): 0.85,
    ("storm_risk", "power_interruption"): 0.65,
    ("storm_risk", "heavy_rainfall"): 0.75,
    ("dam_breach", "river_flooding"): 0.95,
    ("dam_breach", "evacuation_warning"): 0.90,
    ("tsunami_warning", "evacuation_warning"): 0.95,
    ("tsunami_warning", "coastal_flooding"): 0.90,

    # Earthquake cascades
    ("earthquake", "structural_damage"): 0.85,
    ("earthquake", "landslide"): 0.60,
    ("earthquake", "power_interruption"): 0.55,
    ("earthquake", "telecom_disruption"): 0.50,
    ("earthquake", "road_disruption"): 0.60,
    ("landslide", "road_disruption"): 0.90,
    ("landslide", "bridge_damage"): 0.65,
    ("structural_damage", "evacuation_warning"): 0.70,

    # Heatwave cascades
    ("heatwave", "power_interruption"): 0.65,
    ("heatwave", "water_supply_disruption"): 0.55,
    ("heatwave", "hospital_surge"): 0.60,

    # Infrastructure cascades
    ("power_interruption", "telecom_disruption"): 0.50,
    ("power_interruption", "water_supply_disruption"): 0.45,
    ("power_interruption", "hospital_surge"): 0.30,
    ("building_collapse", "structural_damage"): 0.95,
    ("building_collapse", "evacuation_warning"): 0.80,
    ("building_collapse", "hospital_surge"): 0.70,
    ("drought", "water_supply_disruption"): 0.85,
    ("drought", "crop_failure"): 0.75,

    # Transport / Accident cascades
    ("train_accident", "transport_disruption"): 0.90,
    ("train_accident", "hospital_surge"): 0.75,
    ("road_accident", "traffic_congestion"): 0.85,
    ("road_accident", "hospital_surge"): 0.65,

    # Industrial cascades
    ("industrial_fire", "air_quality_emergency"): 0.75,
    ("industrial_fire", "evacuation_warning"): 0.65,
    ("chemical_leak", "evacuation_warning"): 0.90,
    ("chemical_leak", "hospital_surge"): 0.70,
    ("air_quality_emergency", "hospital_surge"): 0.55,
    ("oil_spill", "coastal_flooding"): 0.50,
    ("oil_spill", "air_quality_emergency"): 0.60,
    ("mining_accident", "structural_damage"): 0.80,
    ("mining_accident", "hospital_surge"): 0.70,

    # Health cascades
    ("disease_outbreak", "hospital_surge"): 0.80,
    ("pandemic", "hospital_surge"): 0.85,
    ("pandemic", "economic_disruption"): 0.70,
    ("pandemic", "supply_chain_delay"): 0.65,

    # Evacuation cascades
    ("evacuation_warning", "shelter_activated"): 0.85,
    ("evacuation_warning", "traffic_congestion"): 0.70,
    ("rescue_operation", "traffic_congestion"): 0.50,

    # Water level alerts
    ("water_level", "evacuation_warning"): 0.50,

    # Security / Social cascades
    ("terror_attack", "security_alert"): 0.95,
    ("terror_attack", "evacuation_warning"): 0.80,
    ("terror_attack", "hospital_surge"): 0.70,
    ("protest", "road_disruption"): 0.80,
    ("protest", "traffic_congestion"): 0.75,
    ("protest", "security_alert"): 0.60,
    ("public_panic", "traffic_congestion"): 0.70,
    ("public_panic", "security_alert"): 0.65,

    # Economic cascades
    ("crop_failure", "economic_disruption"): 0.70,
    ("crop_failure", "supply_chain_delay"): 0.60,
    ("forest_fire", "air_quality_emergency"): 0.85,
    ("forest_fire", "evacuation_warning"): 0.75,
    ("cyber_attack", "telecom_disruption"): 0.80,
    ("cyber_attack", "power_interruption"): 0.55,
}


MAX_LINKAGE_DISTANCE_KM = 50.0
MAX_LINKAGE_TIME_GAP_HOURS = 24.0


class SituationLinkage(BaseModel):
    source_incident_id: str
    target_incident_id: str
    causal_score: float
    temporal_gap_minutes: float
    distance_km: float
    reasons: list[str]


class Situation(BaseModel):
    situation_id: str
    incidents: list[IncidentDNA]
    linkages: list[SituationLinkage]
    
    start_time: datetime
    end_time: datetime
    
    def get_summary(self) -> str:
        dna_ids = [inc.incident_id for inc in self.incidents]
        return f"Situation {self.situation_id} encompassing {len(self.incidents)} incidents: {', '.join(dna_ids)}"


def evaluate_causal_link(
    incident_a: IncidentDNA,
    incident_b: IncidentDNA,
) -> SituationLinkage | None:
    """
    Evaluate if Incident A is a plausible cause/precursor to Incident B.
    Returns a SituationLinkage if a meaningful connection exists.
    """
    
    # 1. Temporal Check: Cause must start before effect (or roughly at the same time)
    # Allow a small negative buffer in case of delayed reporting
    time_gap_minutes = (incident_b.start_time - incident_a.start_time).total_seconds() / 60.0
    
    if time_gap_minutes < -30:
        return None  # B started well before A, A cannot be the cause
        
    if time_gap_minutes > (MAX_LINKAGE_TIME_GAP_HOURS * 60):
        return None  # Too much time has passed
        
    # 2. Spatial Check
    distance_km = haversine_distance_km(
        incident_a.centroid_lat,
        incident_a.centroid_lon,
        incident_b.centroid_lat,
        incident_b.centroid_lon,
    )
    
    if distance_km > MAX_LINKAGE_DISTANCE_KM:
        return None
        
    # 3. Causal Concept Transition Check
    best_causal_score = 0.0
    best_transition = None
    
    for concept_a in incident_a.core_concepts:
        for concept_b in incident_b.core_concepts:
            transition = (concept_a.concept, concept_b.concept)
            score = CAUSAL_TRANSITIONS.get(transition, 0.0)
            
            # Weight the transition score by the prominence of the concepts in the incidents
            weighted_score = score * (concept_a.weight + concept_b.weight) / 2.0
            
            if weighted_score > best_causal_score:
                best_causal_score = weighted_score
                best_transition = transition
                
    if best_causal_score < 0.2:
        return None
        
    reasons = [
        f"Causal transition identified: '{best_transition[0]}' frequently leads to '{best_transition[1]}'.",
        f"Geographically proximate ({distance_km:.1f} km apart).",
        f"Temporal sequence aligns ({time_gap_minutes:.0f} mins apart)."
    ]
    
    return SituationLinkage(
        source_incident_id=incident_a.incident_id,
        target_incident_id=incident_b.incident_id,
        causal_score=round(best_causal_score, 4),
        temporal_gap_minutes=round(time_gap_minutes, 1),
        distance_km=round(distance_km, 2),
        reasons=reasons,
    )


def evolve_situations(incidents: list[IncidentDNA]) -> list[Situation]:
    """
    Groups Incident DNA profiles into broader, evolving Situations
    using causal graphs.
    """
    
    if not incidents:
        return []
        
    # Sort incidents chronologically by start time
    sorted_incidents = sorted(incidents, key=lambda inc: inc.start_time)
    
    situations: list[Situation] = []
    
    for incident in sorted_incidents:
        absorbed = False
        
        # Try to link this incident to an existing situation
        for situation in situations:
            
            # Check linkage against all incidents currently in the situation
            for existing_incident in situation.incidents:
                linkage = evaluate_causal_link(existing_incident, incident)
                
                if linkage:
                    situation.incidents.append(incident)
                    situation.linkages.append(linkage)
                    
                    # Update situation temporal bounds
                    situation.start_time = min(situation.start_time, incident.start_time)
                    situation.end_time = max(situation.end_time, incident.end_time)
                    
                    absorbed = True
                    break  # Found a home for this incident
                    
            if absorbed:
                break
                
        # If it doesn't link to any existing situation, spawn a new one
        if not absorbed:
            new_situation = Situation(
                situation_id=f"SIT-{len(situations) + 1:03d}",
                incidents=[incident],
                linkages=[],
                start_time=incident.start_time,
                end_time=incident.end_time,
            )
            situations.append(new_situation)
            
    return situations
