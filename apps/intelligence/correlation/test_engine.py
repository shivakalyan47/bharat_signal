from itertools import combinations

from apps.intelligence.correlation.engine import (
    calculate_relationship_score,
)
from apps.intelligence.simulation.scenario import (
    create_flood_evolution_scenario,
)


def main() -> None:
    signals = create_flood_evolution_scenario()

    results = []

    for signal_a, signal_b in combinations(signals, 2):
        result = calculate_relationship_score(
            signal_a,
            signal_b,
        )

        results.append(result)

    results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    print("BHARATSIGNAL SIGNAL NETWORK TEST")
    print("=" * 90)

    print(f"Signals: {len(signals)}")
    print(f"Comparisons: {len(results)}")

    print()
    print("RELATIONSHIPS")
    print("=" * 90)

    for result in results:
        print(
            f"{result['signal_a']:7} ↔ "
            f"{result['signal_b']:7} | "
            f"{result['score']:.4f} | "
            f"{result['relationship_strength']:8}"
        )

    print()
    print("MODERATE OR STRONG RELATIONSHIPS")
    print("=" * 90)

    meaningful = [
        result
        for result in results
        if result["relationship_strength"] in {
            "moderate",
            "strong",
        }
    ]

    for result in meaningful:
        print(
            f"{result['signal_a']:7} ↔ "
            f"{result['signal_b']:7} | "
            f"{result['score']:.4f} | "
            f"{result['relationship_strength']}"
        )

    print()
    print(f"Meaningful relationships: {len(meaningful)}")


if __name__ == "__main__":
    main()