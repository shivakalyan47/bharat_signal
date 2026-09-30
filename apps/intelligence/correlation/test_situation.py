from itertools import combinations

from apps.intelligence.correlation.clustering import cluster_signals
from apps.intelligence.correlation.engine import calculate_relationship_score
from apps.intelligence.correlation.dna import extract_incident_dna
from apps.intelligence.correlation.situation import evolve_situations
from apps.intelligence.simulation.scenario import create_flood_evolution_scenario


def main() -> None:
    # 1. Generate Synthetic Scenario
    signals = create_flood_evolution_scenario()
    signal_lookup = {s.id: s for s in signals}

    # 2. Correlation Engine (Pairwise Scores)
    relationships = []
    for signal_a, signal_b in combinations(signals, 2):
        relationships.append(calculate_relationship_score(signal_a, signal_b))

    # 3. Incident Clustering (Grouping signals into local events)
    clusters = cluster_signals(signals, relationships)

    # 4. Incident DNA Extraction (Summarizing the core identity of clusters)
    incident_dnas = []
    for cluster_data in clusters:
        incident_id = cluster_data["cluster_id"]
        cluster_signals_list = [
            signal_lookup[sid] for sid in cluster_data["signal_ids"]
        ]
        incident_dnas.append(extract_incident_dna(incident_id, cluster_signals_list))

    # 5. Situation Evolution (Linking causal incidents over time)
    situations = evolve_situations(incident_dnas)

    # 6. Display Output
    print("BHARATSIGNAL SITUATION EVOLUTION TEST")
    print("=" * 90)
    
    print(f"Total Incidents Discovered: {len(incident_dnas)}")
    print(f"Total Situations Tracked:   {len(situations)}\n")

    for situation in situations:
        print(f"[{situation.situation_id}] SITUATION EVOLUTION")
        print(f"  Incidents involved: {len(situation.incidents)}")
        print(f"  Start Time:         {situation.start_time.isoformat()}")
        print(f"  End Time:           {situation.end_time.isoformat()}")
        
        if not situation.linkages:
            print(f"  Linkages:           None (Standalone Incident)")
            
        for linkage in situation.linkages:
            print(f"  Linkage:            {linkage.source_incident_id} --> {linkage.target_incident_id}")
            print(f"    - Causal Score:   {linkage.causal_score:.2f}")
            for reason in linkage.reasons:
                print(f"    - {reason}")
                
        print()
        
        print("  Constituent Incident DNAs:")
        for dna in situation.incidents:
            print(f"    [{dna.incident_id}] {dna.start_time.strftime('%H:%M')} | "
                  f"Evolution: {' -> '.join(dna.evolution_pattern)}")
            
        print("=" * 90)


if __name__ == "__main__":
    main()
