from itertools import combinations

from apps.intelligence.correlation.clustering import cluster_signals
from apps.intelligence.correlation.engine import calculate_relationship_score
from apps.intelligence.correlation.dna import extract_incident_dna
from apps.intelligence.correlation.situation import evolve_situations
from apps.intelligence.correlation.forecasting import generate_forecast
from apps.intelligence.simulation.scenario import create_flood_evolution_scenario


def main() -> None:
    # 1. Pipeline execution
    signals = create_flood_evolution_scenario()
    signal_lookup = {s.id: s for s in signals}

    relationships = []
    for signal_a, signal_b in combinations(signals, 2):
        relationships.append(calculate_relationship_score(signal_a, signal_b))

    clusters = cluster_signals(signals, relationships)

    incident_dnas = []
    for cluster_data in clusters:
        cluster_signals_list = [
            signal_lookup[sid] for sid in cluster_data["signal_ids"]
        ]
        incident_dnas.append(extract_incident_dna(cluster_data["cluster_id"], cluster_signals_list))

    situations = evolve_situations(incident_dnas)

    # 2. Forecasting
    print("BHARATSIGNAL SITUATION FORECASTING TEST")
    print("=" * 90)

    for situation in situations:
        forecast = generate_forecast(situation)
        
        print(f"[{forecast.situation_id}] FORECAST")
        print(f"  Current Status: {forecast.current_status}")
        
        if not forecast.predictions:
            print("  Predictions:    No confident predictions for future evolution.")
            
        for i, pred in enumerate(forecast.predictions, 1):
            print(f"\n  Prediction {i}: {pred.predicted_concept.upper()}")
            print(f"  Probability:  {pred.probability * 100:.1f}%")
            print("  Evidence:")
            for reason in pred.reasons:
                print(f"    - {reason}")
                
        print("=" * 90)


if __name__ == "__main__":
    main()
