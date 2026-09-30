from apps.intelligence.schemas.signal import Signal
from apps.intelligence.correlation.engine import haversine_distance_km


# ============================================================
# CLUSTERING CONFIGURATION
# ============================================================

MIN_RELATIONSHIP_SCORE = 0.40
MIN_CLUSTER_SUPPORT = 2
MAX_CLUSTER_RADIUS_KM = 250.0  # Regional scale: allows neighboring districts to group into coherent incidents


# ============================================================
# RELATIONSHIP LOOKUP
# ============================================================

def build_relationship_lookup(
    relationships: list[dict],
) -> dict[tuple[str, str], dict]:
    """
    Store relationships so that signal pairs can be
    queried in either direction.
    """

    lookup: dict[tuple[str, str], dict] = {}

    for relationship in relationships:

        signal_a = relationship["signal_a"]
        signal_b = relationship["signal_b"]

        lookup[(signal_a, signal_b)] = relationship
        lookup[(signal_b, signal_a)] = relationship

    return lookup


# ============================================================
# STRONGEST SEED
# ============================================================

def find_strongest_seed(
    remaining_ids: set[str],
    relationships: list[dict],
) -> tuple[str, str] | None:
    """
    Find the strongest remaining relationship.

    This relationship becomes the initial seed for a
    candidate incident cluster.
    """

    candidates = [
        relationship
        for relationship in relationships
        if (
            relationship["signal_a"] in remaining_ids
            and relationship["signal_b"] in remaining_ids
            and relationship["score"] >= MIN_RELATIONSHIP_SCORE
        )
    ]

    if not candidates:
        return None

    strongest = max(
        candidates,
        key=lambda relationship: relationship["score"],
    )

    return (
        strongest["signal_a"],
        strongest["signal_b"],
    )


# ============================================================
# CLUSTER SUPPORT
# ============================================================

def cluster_support(
    signal_id: str,
    cluster: set[str],
    lookup: dict[tuple[str, str], dict],
) -> list[dict]:
    """
    Return the relationships supporting a signal's membership
    in the current cluster.
    """

    supporting_relationships = []

    for member_id in cluster:

        relationship = lookup.get(
            (signal_id, member_id)
        )

        if relationship is None:
            continue

        if relationship["score"] >= MIN_RELATIONSHIP_SCORE:
            supporting_relationships.append(
                relationship
            )

    return supporting_relationships


# ============================================================
# COHERENT CLUSTER GROWTH
# ============================================================
def cluster_coherence(
    signal_id: str,
    cluster: set[str],
    lookup: dict[tuple[str, str], dict],
) -> dict:
    """
    Measure how coherently a candidate signal fits
    the existing cluster as a whole.

    This evaluates the candidate against ALL cluster members
    to ensure it matches the overall 'Incident DNA', rather
    than just appending it based on a single strong edge.
    """

    if not cluster:
        return {
            "support_count": 0,
            "average_score": 0.0,
            "average_semantic": 0.0,
        }

    support_count = 0
    total_score = 0.0
    total_semantic = 0.0

    for member_id in cluster:
        relationship = lookup.get((signal_id, member_id))

        if relationship is None:
            continue

        if relationship.get("score", 0.0) >= MIN_RELATIONSHIP_SCORE:
            support_count += 1

        total_score += relationship.get("score", 0.0)
        total_semantic += relationship.get("semantic_similarity", 0.0)

    cluster_size = len(cluster)

    return {
        "support_count": support_count,
        "average_score": round(total_score / cluster_size, 4),
        "average_semantic": round(total_semantic / cluster_size, 4),
    }
def grow_cluster(
    cluster: set[str],
    remaining_ids: set[str],
    lookup: dict[tuple[str, str], dict],
    signal_lookup: dict[str, Signal] | None = None,
) -> set[str]:
    """
    Grow a cluster only when a new signal has sufficient
    internal support, semantic coherence, and spatial proximity
    to the cluster centroid.
    """

    changed = True

    while changed:

        changed = False

        candidates = sorted(
            remaining_ids - cluster
        )

        # Calculate cluster centroid for spatial boundary check
        centroid_lat = None
        centroid_lon = None
        if signal_lookup and cluster:
            cluster_signals = [
                signal_lookup[sid]
                for sid in cluster
                if sid in signal_lookup
            ]
            if cluster_signals:
                centroid_lat = sum(
                    s.location.latitude for s in cluster_signals
                ) / len(cluster_signals)
                centroid_lon = sum(
                    s.location.longitude for s in cluster_signals
                ) / len(cluster_signals)

        best_candidate = None
        best_support = []
        best_candidate_score = -1.0

        for signal_id in candidates:

            # ---- Spatial Boundary Check ----
            # Reject candidate if it is too far from cluster centroid
            if (
                signal_lookup
                and centroid_lat is not None
                and signal_id in signal_lookup
            ):
                candidate_signal = signal_lookup[signal_id]
                dist = haversine_distance_km(
                    centroid_lat,
                    centroid_lon,
                    candidate_signal.location.latitude,
                    candidate_signal.location.longitude,
                )
                if dist > MAX_CLUSTER_RADIUS_KM:
                    continue

            support = cluster_support(
                signal_id,
                cluster,
                lookup,
            )

            coherence = cluster_coherence(
                signal_id,
                cluster,
                lookup,
            )

            if coherence["support_count"] < MIN_CLUSTER_SUPPORT:
                continue

            if coherence["average_semantic"] < 0.25:
                continue

            total_score = (
                coherence["average_score"]
                + coherence["average_semantic"]
            )

            if (
                best_candidate is None
                or total_score > best_candidate_score
            ):
                best_candidate = signal_id
                best_support = support
                best_candidate_score = total_score

        if best_candidate is None:
            break

        cluster.add(best_candidate)
        changed = True

    return cluster



# ============================================================
# INCIDENT CLUSTERING
# ============================================================

def cluster_signals(
    signals: list[Signal],
    relationships: list[dict],
) -> list[dict]:
    """
    Build candidate incident clusters using coherent
    graph growth rather than raw connected components.

    A signal must have at least two meaningful relationships
    with existing cluster members before being absorbed.
    
    Additionally, a spatial boundary check prevents signals
    from different geographic regions from being merged into
    the same cluster.
    """

    signal_ids = {
        signal.id
        for signal in signals
    }

    # Build signal lookup for spatial boundary checks
    signal_lookup = {s.id: s for s in signals}

    remaining_ids = set(signal_ids)

    lookup = build_relationship_lookup(
        relationships
    )

    clusters = []

    cluster_number = 1

    while True:

        seed = find_strongest_seed(
            remaining_ids,
            relationships,
        )

        if seed is None:
            break

        cluster = {
            seed[0],
            seed[1],
        }

        cluster = grow_cluster(
            cluster,
            remaining_ids,
            lookup,
            signal_lookup,
        )

        clusters.append(
            {
                "cluster_id": f"INC-{cluster_number:03d}",
                "signal_ids": sorted(cluster),
                "member_count": len(cluster),
            }
        )

        remaining_ids -= cluster

        cluster_number += 1

    return clusters