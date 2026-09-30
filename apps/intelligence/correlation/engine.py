from math import exp, radians, sin, cos, sqrt, atan2

from apps.intelligence.schemas.signal import Signal, SignalType


# ============================================================
# GEOGRAPHIC SIMILARITY
# ============================================================

def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two coordinates.
    """

    earth_radius_km = 6371.0

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad)
        * cos(lat2_rad)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a),
    )

    return earth_radius_km * c


def geographic_similarity(
    signal_a: Signal,
    signal_b: Signal,
) -> float:
    """
    Convert geographic distance into a similarity score.

    Uses a regional subcontinental scale (~120km) appropriate
    for national threat monitoring, with regional affinity.
    """

    distance_km = haversine_distance_km(
        signal_a.location.latitude,
        signal_a.location.longitude,
        signal_b.location.latitude,
        signal_b.location.longitude,
    )

    base = exp(-distance_km / 120.0)

    # Regional affinity bonus for signals in the same administrative/geographical zone
    if (
        signal_a.location.region
        and signal_b.location.region
        and signal_a.location.region == signal_b.location.region
    ):
        base = min(1.0, base + 0.15)

    return base


# ============================================================
# TEMPORAL SIMILARITY
# ============================================================

def temporal_similarity(
    signal_a: Signal,
    signal_b: Signal,
) -> float:
    """
    Convert time difference into a similarity score.

    Smaller time difference = higher similarity.
    """

    # Normalize timestamps to ensure both are timezone-aware (UTC)
    from datetime import timezone as _tz
    ts_a = signal_a.timestamp
    ts_b = signal_b.timestamp
    if ts_a.tzinfo is None:
        ts_a = ts_a.replace(tzinfo=_tz.utc)
    if ts_b.tzinfo is None:
        ts_b = ts_b.replace(tzinfo=_tz.utc)

    difference_seconds = abs(
        (ts_a - ts_b).total_seconds()
    )

    difference_minutes = difference_seconds / 60.0

    return exp(-difference_minutes / 60.0)


# ============================================================
# DOMAIN CONCEPT EXTRACTION
# ============================================================

def extract_concepts(
    signal: Signal,
) -> set[str]:
    """
    Extract transparent domain concepts from a signal.

    This prototype intentionally uses explicit keywords
    rather than opaque model-generated similarity.
    """

    text = (
        f"{signal.title} {signal.description}"
    ).lower()

    concept_keywords = {
        # Weather
        "heavy_rainfall": [
            "heavy rainfall",
            "sustained heavy rainfall",
            "torrential rain",
            "downpour", "cloudburst", "incessant rain", "rain havoc", "deluge", "monsoon fury",
        ],
        "rainfall_warning": [
            "rainfall warning",
            "rain alert",
        ],
        "cyclone": [
            "cyclone",
            "cyclonic storm",
            "tropical storm",
            "hurricane", "typhoon", "depression", "low pressure", "storm warning",
        ],
        "heatwave": [
            "heatwave",
            "heat wave",
            "extreme heat",
            "temperature surge",
            "scorching", "mercury soaring", "heat alert", "record temperature", "sweltering",
        ],
        "cold_wave": [
            "cold wave",
            "cold snap",
            "freezing temperatures",
        ],
        "thunderstorm": [
            "thunderstorm",
            "lightning storm",
        ],
        "temperature_update": [
            "temperature", "degrees celsius", "weather update", "forecast",
        ],

        # Water
        "water_level": [
            "water level",
            "water levels",
            "river level",
        ],
        "waterlogging": [
            "waterlogging",
            "water logging",
            "streets flooded", "knee deep water", "submerged", "inundated",
        ],
        "river_flooding": [
            "river flooding",
            "river overflow",
            "river breach",
        ],
        "dam_overflow": [
            "dam overflow",
            "dam release",
            "reservoir overflow",
        ],
        "coastal_flooding": [
            "coastal flooding",
            "storm surge",
            "tidal flooding",
        ],
        "flood_risk": [
            "flood warning", "flood alert", "flash flood", "flood situation", "flood fury", "flood havoc", "flood affected", "marooned",
        ],

        # Earth
        "earthquake": [
            "earthquake",
            "seismic activity",
            "tremor",
            "quake", "aftershock", "richter", "magnitude", "epicenter", "epicentre",
        ],
        "landslide": [
            "landslide",
            "land slide",
            "mudslide",
            "slope failure",
            "debris flow", "rockfall", "hill collapse", "soil erosion",
        ],

        # Transport
        "road_disruption": [
            "road disruption",
            "road closure",
            "road blocked",
            "road cave in", "pothole", "road damage", "road washed away", "highway blocked",
        ],
        "transport_disruption": [
            "transport disruption",
            "train delay",
            "rail disruption",
            "flight cancellation",
        ],
        "traffic_congestion": [
            "traffic congestion",
            "traffic jam",
            "gridlock",
        ],
        "vehicle_breakdown": [
            "vehicle breakdown",
        ],
        "bridge_damage": [
            "bridge damage",
            "bridge collapse",
            "bridge washed away",
        ],
        "train_accident": [
            "train derailment", "train accident", "rail accident", "train collision", "train crash",
        ],
        "road_accident": [
            "road accident", "bus accident", "truck accident", "car crash", "vehicle collision", "pile up", "road mishap", "fatal accident",
        ],

        # Infrastructure
        "power_interruption": [
            "power interruption",
            "power outage",
            "blackout",
            "power failure",
            "electricity disruption",
            "load shedding", "grid failure", "transformer burst", "power cut",
        ],
        "telecom_disruption": [
            "telecom disruption",
            "network outage",
            "communication failure",
            "mobile network down",
        ],
        "water_supply_disruption": [
            "water supply disruption",
            "water supply cut",
            "pipeline burst",
        ],
        "structural_damage": [
            "structural damage",
            "building collapse",
            "wall collapse",
            "building damage",
            "roof collapse", "structure collapse", "cave in",
        ],
        "supply_chain_delay": [
            "supply chain delay",
            "supply disruption",
            "logistics disruption",
        ],
        "building_collapse": [
            "building collapse", "structure collapse", "floor collapse", "building cave in", "under construction collapse",
        ],

        # Industrial
        "industrial_fire": [
            "industrial fire",
            "factory fire",
            "warehouse fire",
            "blaze", "inferno", "fire broke out", "gutted", "engulfed in flames", "fire accident",
        ],
        "chemical_leak": [
            "chemical leak",
            "gas leak",
            "toxic release",
            "hazardous material",
        ],

        # Health
        "disease_outbreak": [
            "disease outbreak",
            "epidemic",
            "infection cluster",
            "dengue", "malaria", "cholera", "covid", "virus", "pandemic", "infected", "cases reported",
        ],
        "hospital_surge": [
            "hospital surge",
            "hospital overcrowding",
            "emergency ward full",
            "hospital overwhelmed", "icu full", "bed shortage", "medical emergency", "ambulance",
        ],
        "air_quality_emergency": [
            "air quality",
            "aqi dangerous",
            "smog alert",
            "pollution emergency",
            "smog", "toxic fumes", "gas leak", "aqi", "hazardous air", "visibility drop",
        ],

        # Maintenance/Scheduled
        "scheduled_maintenance": [
            "scheduled road maintenance",
            "planned road maintenance",
            "planned outage",
        ],

        # Evacuations and Alerts
        "evacuation_warning": [
            "evacuation warning",
            "evacuation order",
            "evacuation advisory",
            "evacuated", "mass evacuation", "people moved", "shifted to shelter", "relief camp",
        ],
        "shelter_activated": [
            "shelter activated",
            "relief camp",
            "rescue operation",
        ],

        # New Concepts
        "storm_risk": [
            "storm", "severe storm", "thunderstorm warning", "hailstorm", "dust storm", "norweaster",
        ],
        "terror_attack": [
            "terror attack", "terrorist", "bomb blast", "explosion", "ied", "naxal", "encounter", "militant",
        ],
        "protest": [
            "protest", "agitation", "bandh", "strike", "demonstration", "rally", "blockade",
        ],
        "security_alert": [
            "security alert", "high alert", "red alert", "security threat", "curfew", "section 144",
        ],
        "drought": [
            "drought", "water crisis", "water scarcity", "dry spell", "no rain", "parched",
        ],
        "crop_failure": [
            "crop damage", "crop loss", "harvest destroyed", "agricultural loss", "farmer distress",
        ],
        "economic_disruption": [
            "market crash", "economic impact", "business loss", "shutdown", "supply shortage",
        ],
        "forest_fire": [
            "forest fire", "wildfire", "jungle fire", "bush fire", "fire in forest",
        ],
        "oil_spill": [
            "oil spill", "oil leak", "petroleum leak", "crude oil",
        ],
        "mining_accident": [
            "mine collapse", "mining accident", "mine blast", "trapped in mine",
        ],
        "dam_breach": [
            "dam breach", "dam break", "dam burst", "dam failure",
        ],
        "tsunami_warning": [
            "tsunami", "tsunami warning", "tidal wave",
        ],
        "nuclear_incident": [
            "nuclear", "radiation leak", "nuclear accident",
        ],
        "pandemic": [
            "pandemic", "epidemic", "outbreak", "public health emergency",
        ],
        "cyber_attack": [
            "cyber attack", "ransomware", "data breach", "hacking", "server down",
        ],
        "public_panic": [
            "stampede", "panic", "rumour", "fake news", "mass hysteria",
        ],
        "rescue_operation": [
            "rescue operation", "ndrf", "sdrf", "rescue team", "search and rescue", "relief work", "relief operation",
        ],
    }

    concepts = set()

    for concept, keywords in concept_keywords.items():
        if any(
            keyword in text
            for keyword in keywords
        ):
            concepts.add(concept)

    return concepts


# ============================================================
# SEMANTIC SIMILARITY
# ============================================================

def semantic_similarity(
    signal_a: Signal,
    signal_b: Signal,
) -> float:
    """
    Estimate semantic relatedness between two signals
    using transparent domain concept relationships.

    This is a prototype knowledge layer, not an
    AI-generated causal inference.
    """

    concepts_a = extract_concepts(signal_a)
    concepts_b = extract_concepts(signal_b)

    if not concepts_a or not concepts_b:
        return 0.0

    # --------------------------------------------------------
    # Exact concept match
    # --------------------------------------------------------

    if concepts_a & concepts_b:
        return 1.0

    # --------------------------------------------------------
    # Related domain concepts
    # --------------------------------------------------------

    related_concepts = {
        # Weather cascades
        frozenset({"heavy_rainfall", "rainfall_warning"}): 0.85,
        frozenset({"heavy_rainfall", "water_level"}): 0.65,
        frozenset({"rainfall_warning", "water_level"}): 0.70,
        frozenset({"water_level", "waterlogging"}): 0.85,
        frozenset({"waterlogging", "road_disruption"}): 0.80,
        frozenset({"road_disruption", "transport_disruption"}): 0.85,
        frozenset({"waterlogging", "transport_disruption"}): 0.65,
        frozenset({"waterlogging", "traffic_congestion"}): 0.25,
        frozenset({"vehicle_breakdown", "traffic_congestion"}): 0.85,
        frozenset({"storm_risk", "power_interruption"}): 0.65,
        frozenset({"storm_risk", "heavy_rainfall"}): 0.75,

        # Cyclone cascades
        frozenset({"cyclone", "heavy_rainfall"}): 0.90,
        frozenset({"cyclone", "coastal_flooding"}): 0.85,
        frozenset({"cyclone", "power_interruption"}): 0.75,
        frozenset({"cyclone", "structural_damage"}): 0.70,
        frozenset({"cyclone", "transport_disruption"}): 0.80,
        frozenset({"cyclone", "telecom_disruption"}): 0.65,

        # Flooding cascades
        frozenset({"heavy_rainfall", "river_flooding"}): 0.75,
        frozenset({"river_flooding", "dam_overflow"}): 0.60,
        frozenset({"river_flooding", "bridge_damage"}): 0.70,
        frozenset({"dam_overflow", "evacuation_warning"}): 0.85,
        frozenset({"river_flooding", "evacuation_warning"}): 0.75,
        frozenset({"coastal_flooding", "evacuation_warning"}): 0.80,
        frozenset({"flood_risk", "evacuation_warning"}): 0.80,
        frozenset({"flood_risk", "waterlogging"}): 0.85,
        frozenset({"dam_breach", "river_flooding"}): 0.90,
        frozenset({"tsunami_warning", "coastal_flooding"}): 0.90,

        # Earthquake cascades
        frozenset({"earthquake", "structural_damage"}): 0.80,
        frozenset({"earthquake", "landslide"}): 0.65,
        frozenset({"earthquake", "power_interruption"}): 0.55,
        frozenset({"earthquake", "telecom_disruption"}): 0.50,
        frozenset({"earthquake", "road_disruption"}): 0.60,
        frozenset({"landslide", "road_disruption"}): 0.85,
        frozenset({"landslide", "bridge_damage"}): 0.60,

        # Heatwave cascades
        frozenset({"heatwave", "power_interruption"}): 0.65,
        frozenset({"heatwave", "water_supply_disruption"}): 0.55,
        frozenset({"heatwave", "hospital_surge"}): 0.60,

        # Infrastructure cascades
        frozenset({"power_interruption", "telecom_disruption"}): 0.50,
        frozenset({"power_interruption", "water_supply_disruption"}): 0.45,
        frozenset({"structural_damage", "evacuation_warning"}): 0.70,
        frozenset({"bridge_damage", "road_disruption"}): 0.90,
        frozenset({"road_disruption", "supply_chain_delay"}): 0.65,
        frozenset({"transport_disruption", "supply_chain_delay"}): 0.75,
        frozenset({"building_collapse", "structural_damage"}): 0.95,
        frozenset({"building_collapse", "evacuation_warning"}): 0.75,

        # Transport/Accident cascades
        frozenset({"train_accident", "transport_disruption"}): 0.90,
        frozenset({"road_accident", "traffic_congestion"}): 0.85,
        frozenset({"road_accident", "hospital_surge"}): 0.70,
        frozenset({"train_accident", "hospital_surge"}): 0.75,

        # Industrial cascades
        frozenset({"industrial_fire", "air_quality_emergency"}): 0.70,
        frozenset({"chemical_leak", "evacuation_warning"}): 0.85,
        frozenset({"chemical_leak", "hospital_surge"}): 0.65,
        frozenset({"industrial_fire", "evacuation_warning"}): 0.60,
        frozenset({"oil_spill", "environmental"}): 0.80,
        frozenset({"mining_accident", "structural_damage"}): 0.75,

        # Health cascades
        frozenset({"disease_outbreak", "hospital_surge"}): 0.80,
        frozenset({"waterlogging", "disease_outbreak"}): 0.40,
        frozenset({"air_quality_emergency", "hospital_surge"}): 0.55,
        frozenset({"pandemic", "hospital_surge"}): 0.85,

        # Evacuation cascades
        frozenset({"evacuation_warning", "shelter_activated"}): 0.85,
        frozenset({"evacuation_warning", "traffic_congestion"}): 0.70,
        frozenset({"rescue_operation", "evacuation_warning"}): 0.80,

        # Security/Other cascades
        frozenset({"terror_attack", "security_alert"}): 0.90,
        frozenset({"protest", "road_disruption"}): 0.75,
        frozenset({"protest", "traffic_congestion"}): 0.70,
        frozenset({"drought", "water_supply_disruption"}): 0.80,
        frozenset({"forest_fire", "air_quality_emergency"}): 0.85,
        frozenset({"public_panic", "security_alert"}): 0.65,
        frozenset({"crop_failure", "economic_disruption"}): 0.70,
        frozenset({"cyber_attack", "telecom_disruption"}): 0.80,
    }

    best_relationship = 0.0

    for concept_a in concepts_a:
        for concept_b in concepts_b:

            relationship = related_concepts.get(
                frozenset({
                    concept_a,
                    concept_b,
                }),
                0.0,
            )

            best_relationship = max(
                best_relationship,
                relationship,
            )

    return best_relationship


# ============================================================
# ENTITY OVERLAP
# ============================================================

def entity_overlap(
    signal_a: Signal,
    signal_b: Signal,
) -> float:
    """
    Calculate Jaccard overlap between signal entities.
    """

    entities_a = set(signal_a.entities)
    entities_b = set(signal_b.entities)

    if not entities_a or not entities_b:
        return 0.0

    intersection = entities_a & entities_b
    union = entities_a | entities_b

    return len(intersection) / len(union)


# ============================================================
# CONTEXTUAL COMPATIBILITY
# ============================================================

def contextual_compatibility(
    signal_a: Signal,
    signal_b: Signal,
) -> float:
    """
    Estimate whether two signal types can plausibly
    participate in the same evolving situation.

    This is a transparent prototype prior,
    not a causal claim.
    """

    pair = frozenset({
        signal_a.type,
        signal_b.type,
    })

    compatibility = {
        frozenset({SignalType.SEISMIC, SignalType.SEISMIC}): 0.90,
        frozenset({SignalType.WEATHER, SignalType.WEATHER}): 0.85,
        frozenset({SignalType.ENVIRONMENTAL, SignalType.ENVIRONMENTAL}): 0.80,
        frozenset({SignalType.WEATHER, SignalType.OFFICIAL_ALERT}): 0.90,
        frozenset({SignalType.WEATHER, SignalType.INFRASTRUCTURE}): 0.70,
        frozenset({SignalType.OFFICIAL_ALERT, SignalType.INFRASTRUCTURE}): 0.80,
        frozenset({SignalType.INFRASTRUCTURE, SignalType.PUBLIC_REPORT}): 0.80,
        frozenset({SignalType.PUBLIC_REPORT, SignalType.TRANSPORT}): 0.80,
        frozenset({SignalType.INFRASTRUCTURE, SignalType.TRANSPORT}): 0.75,
        frozenset({SignalType.SEISMIC, SignalType.INFRASTRUCTURE}): 0.85,
        frozenset({SignalType.SEISMIC, SignalType.PUBLIC_REPORT}): 0.75,
        frozenset({SignalType.WEATHER, SignalType.TRANSPORT}): 0.70,
        frozenset({SignalType.WEATHER, SignalType.ENVIRONMENTAL}): 0.85,
        frozenset({SignalType.INDUSTRIAL, SignalType.HEALTH}): 0.70,
        frozenset({SignalType.INDUSTRIAL, SignalType.ENVIRONMENTAL}): 0.80,
        frozenset({SignalType.HEALTH, SignalType.PUBLIC_REPORT}): 0.75,
        frozenset({SignalType.ENVIRONMENTAL, SignalType.HEALTH}): 0.70,
        frozenset({SignalType.OFFICIAL_ALERT, SignalType.TRANSPORT}): 0.75,
        frozenset({SignalType.SEISMIC, SignalType.OFFICIAL_ALERT}): 0.85,
        frozenset({SignalType.WEATHER, SignalType.SEISMIC}): 0.35,
    }

    return compatibility.get(pair, 0.40)


# ============================================================
# RELATIONSHIP SCORE
# ============================================================

def calculate_relationship_score(
    signal_a: Signal,
    signal_b: Signal,
) -> dict:
    """
    Calculate the relationship between two signals.

    Dimensions:

    - geographic similarity
    - temporal similarity
    - semantic similarity
    - entity overlap
    - contextual compatibility

    All five dimensions currently receive equal weight.
    """

    geographic = geographic_similarity(
        signal_a,
        signal_b,
    )

    temporal = temporal_similarity(
        signal_a,
        signal_b,
    )

    semantic = semantic_similarity(
        signal_a,
        signal_b,
    )

    entities = entity_overlap(
        signal_a,
        signal_b,
    )

    contextual = contextual_compatibility(
        signal_a,
        signal_b,
    )

    # --------------------------------------------------------
    # Weighted relationship score
    # --------------------------------------------------------

    score = (
        0.20 * geographic
        + 0.20 * temporal
        + 0.20 * semantic
        + 0.20 * entities
        + 0.20 * contextual
    )

    # --------------------------------------------------------
    # Evidence gate
    #
    # Geographic and temporal proximity alone should not
    # create a meaningful relationship.
    # --------------------------------------------------------

    if semantic < 0.15 and entities == 0:
        score = min(
            score,
            0.44,
        )

    # --------------------------------------------------------
    # Relationship strength
    # --------------------------------------------------------

    if score >= 0.70:
        relationship_strength = "strong"

    elif score >= 0.45:
        relationship_strength = "moderate"

    else:
        relationship_strength = "weak"

    # --------------------------------------------------------
    # Explainability reasons
    # --------------------------------------------------------

    reasons = []

    if geographic >= 0.70:
        reasons.append(
            "Signals are geographically close."
        )

    if temporal >= 0.70:
        reasons.append(
            "Signals occurred within a similar time window."
        )

    if semantic >= 0.50:
        reasons.append(
            "Signals share related domain concepts."
        )

    elif semantic >= 0.15:
        reasons.append(
            "Signals contain partially related domain concepts."
        )

    if entities > 0:
        reasons.append(
            "Signals share one or more entities."
        )

    if contextual >= 0.70:
        reasons.append(
            "Signal types are contextually compatible."
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "signal_a": signal_a.id,
        "signal_b": signal_b.id,

        "score": round(
            score,
            4,
        ),

        "relationship_strength": relationship_strength,

        "geographic_similarity": round(
            geographic,
            4,
        ),

        "temporal_similarity": round(
            temporal,
            4,
        ),

        "semantic_similarity": round(
            semantic,
            4,
        ),

        "entity_overlap": round(
            entities,
            4,
        ),

        "contextual_compatibility": round(
            contextual,
            4,
        ),

        "reasons": reasons,
    }