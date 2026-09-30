from itertools import combinations

from apps.intelligence.correlation.clustering import (
    cluster_signals,
)
from apps.intelligence.correlation.engine import (
    calculate_relationship_score,
)
from apps.intelligence.simulation.scenario import (
    create_flood_evolution_scenario,
)


def main() -> None:

    signals = create_flood_evolution_scenario()

    relationships = []

    for signal_a, signal_b in combinations(
        signals,
        2,
    ):
        relationships.append(
            calculate_relationship_score(
                signal_a,
                signal_b,
            )
        )

    clusters = cluster_signals(
        signals,
        relationships,
    )

    print("BHARATSIGNAL INCIDENT CLUSTERING TEST")
    print("=" * 90)

    print(f"Signals: {len(signals)}")
    print(f"Relationships: {len(relationships)}")
    print(f"Clusters: {len(clusters)}")
    print()

    print("CANDIDATE INCIDENTS")
    print("=" * 90)

    for cluster in clusters:

        print(
            f"{cluster['cluster_id']} | "
            f"signals={cluster['signal_ids']} | "
            f"members={cluster['member_count']}"
        )


if __name__ == "__main__":
    main()