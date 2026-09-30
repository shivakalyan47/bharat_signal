from itertools import combinations

from apps.intelligence.correlation.clustering import cluster_signals
from apps.intelligence.correlation.engine import calculate_relationship_score
from apps.intelligence.correlation.dna import extract_incident_dna
from apps.intelligence.simulation.scenario import create_flood_evolution_scenario


def main() -> None:
    signals = create_flood_evolution_scenario()
    signal_lookup = {s.id: s for s in signals}

    relationships = []
    for signal_a, signal_b in combinations(signals, 2):
        relationships.append(calculate_relationship_score(signal_a, signal_b))

    clusters = cluster_signals(signals, relationships)

    print("BHARATSIGNAL INCIDENT DNA EXTRACTION TEST")
    print("=" * 90)

    for cluster_data in clusters:
        incident_id = cluster_data["cluster_id"]
        cluster_signals_list = [
            signal_lookup[sid] for sid in cluster_data["signal_ids"]
        ]
        
        dna = extract_incident_dna(incident_id, cluster_signals_list)
        
        print(f"[{dna.incident_id}] DNA PROFILE")
        print(f"  Signals:   {dna.signal_count}")
        print(f"  Duration:  {dna.duration_minutes} minutes")
        print(f"  Centroid:  ({dna.centroid_lat}, {dna.centroid_lon})")
        print(f"  Evolution: {' -> '.join(dna.evolution_pattern)}")
        
        print("  Core Concepts:")
        for concept in dna.core_concepts:
            print(f"    - {concept.concept:22} (weight: {concept.weight:.2f})")
            
        print()


if __name__ == "__main__":
    main()
