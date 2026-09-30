"""
BharatSignal Automated Live Ingestion Worker
============================================
Runs continuously in the background, querying real-world incident APIs
(NewsAPI, WorldNewsAPI, USGS, NASA EONET, GDACS, Open-Meteo) at a scheduled interval
(default: every 2 minutes), correlating signals, running the ML pipeline,
and updating pipeline_data.json for the dashboard.

News APIs are the PRIMARY data source, supplemented by weather and disaster APIs.

Usage:
  python -m apps.intelligence.live_worker
  python -m apps.intelligence.live_worker --interval 120
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime, timezone, timedelta

from apps.intelligence.pipeline import (
    _fetch_live_incident_signals,
    run_pipeline,
    export_pipeline_json,
)
from apps.intelligence.ingestion.live_weather import (
    create_live_signals,
    create_confirmation_signals,
)
from apps.intelligence.ingestion.sources.news_api import fetch_all_news_signals
from apps.intelligence.ingestion.sources.gnews_currents import fetch_extra_news_signals
from apps.intelligence.ingestion.sources.openweather import fetch_openweather_signals
from apps.intelligence.ingestion.sources.tomtom_traffic import fetch_tomtom_traffic_signals


def get_ist_time_str() -> str:
    """Return formatted current time in Indian Standard Time (UTC+5:30)."""
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d %H:%M:%S IST")


def execute_cycle(cycle_num: int) -> dict:
    """Execute a single live ingestion and pipeline processing cycle."""
    timestamp = get_ist_time_str()
    print(f"\n{'=' * 70}", flush=True)
    print(f"  [CYCLE #{cycle_num}] BHARATSIGNAL LIVE INGESTION — {timestamp}", flush=True)
    print(f"{'=' * 70}", flush=True)

    # PRIMARY SOURCE: News APIs
    print("  [PRIMARY] Fetching live news (NewsAPI + WorldNewsAPI)...", flush=True)
    try:
        news_signals = fetch_all_news_signals()
        print(f"  -> {len(news_signals)} news signals ingested", flush=True)
    except Exception as e:
        news_signals = []
        print(f"  [NEWS] Source failed (non-fatal): {e}", flush=True)

    # SUPPLEMENTARY: Disaster APIs
    print("  [SUPPLEMENTARY] Fetching USGS, NASA, GDACS data...", flush=True)
    try:
        real_signals = _fetch_live_incident_signals()
        print(f"  -> {len(real_signals)} disaster API signals ingested", flush=True)
    except Exception as e:
        real_signals = []
        print(f"  [DISASTER APIS] Source failed (non-fatal): {e}", flush=True)

    # WEATHER: Open-Meteo
    print("  [WEATHER] Fetching live weather grid from Open-Meteo...", flush=True)
    try:
        live_signals = create_live_signals()
        print(f"  -> {len(live_signals)} Open-Meteo weather signals ingested", flush=True)
    except Exception as e:
        live_signals = []
        print(f"  [WEATHER] Source failed (non-fatal): {e}", flush=True)

    # EXTRA NEWS: GNews + CurrentsAPI
    print("  [NEWS+] Fetching extra news (GNews + CurrentsAPI)...", flush=True)
    try:
        extra_news = fetch_extra_news_signals()
        print(f"  -> {len(extra_news)} extra news signals ingested", flush=True)
    except Exception as e:
        extra_news = []
        print(f"  [GNEWS/CURRENTS] Source failed (non-fatal): {e}", flush=True)

    # OpenWeatherMap (real-time weather for 30 Indian cities)
    print("  [OPENWEATHER] Fetching OpenWeatherMap data...", flush=True)
    try:
        owm_signals = fetch_openweather_signals()
        print(f"  -> {len(owm_signals)} OpenWeather signals ingested", flush=True)
    except Exception as e:
        owm_signals = []
        print(f"  [OPENWEATHER] Source failed (non-fatal): {e}", flush=True)

    # TomTom Traffic (live traffic congestion for 20 Indian cities)
    print("  [TRAFFIC] Fetching TomTom traffic data...", flush=True)
    try:
        traffic_signals = fetch_tomtom_traffic_signals()
        print(f"  -> {len(traffic_signals)} traffic signals ingested", flush=True)
    except Exception as e:
        traffic_signals = []
        print(f"  [TOMTOM] Source failed (non-fatal): {e}", flush=True)

    # Combine ALL sources — news is primary, lower severity threshold
    MIN_SEVERITY = 0.15
    combined = news_signals + real_signals + live_signals + extra_news + owm_signals + traffic_signals
    all_signals = [s for s in combined if s.severity and s.severity >= MIN_SEVERITY]
    print(f"  -> Combined: {len(all_signals)} signals above severity threshold {MIN_SEVERITY}", flush=True)

    all_confirmations = create_confirmation_signals()

    if not all_signals:
        print("  [WARNING] No signals fetched from any source. Pipeline will produce empty report.", flush=True)

    print(f"  Running intelligence pipeline on {len(all_signals)} active signals...", flush=True)
    result = run_pipeline(all_signals, all_confirmations)

    # Export to dashboard
    data = export_pipeline_json(result)
    data["pipeline_mode"] = "live"
    data["last_updated_ist"] = timestamp
    data["cycle_number"] = cycle_num
    data["source_breakdown"] = {
        "news_api": len(news_signals),
        "gnews_currents": len(extra_news),
        "disaster_apis": len(real_signals),
        "open_meteo": len(live_signals),
        "openweather": len(owm_signals),
        "tomtom_traffic": len(traffic_signals),
        "total_raw": len(combined),
        "after_filter": len(all_signals),
    }

    output_path = "apps/intelligence/dashboard/pipeline_data.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    stats = data.get("stats", {})
    print(f"\n  [CYCLE #{cycle_num} COMPLETE]", flush=True)
    print(f"  Signals: {stats.get('total_signals', 0)} | Incidents: {stats.get('incidents_detected', 0)} | Situations: {stats.get('situations_tracked', 0)} | Forecasts: {stats.get('forecasts_generated', 0)}", flush=True)
    print(f"  Accuracy: {stats.get('prediction_accuracy_percent', 'N/A')}%", flush=True)
    print(f"  Reality Checks: {stats.get('reality_checks', 0)}", flush=True)
    print(f"  Updated: {output_path}", flush=True)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="BharatSignal Live Background Worker")
    parser.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Update interval in seconds (default: 120 = 2 minutes)",
    )
    args = parser.parse_args()
    interval = args.interval

    print("\n" + "#" * 70, flush=True)
    print("  BHARATSIGNAL AUTOMATED LIVE WORKER v2.0", flush=True)
    print(f"  Primary Source: NewsAPI + WorldNewsAPI", flush=True)
    print(f"  Supplementary: USGS, NASA EONET, GDACS, Open-Meteo", flush=True)
    print(f"  Polling every {interval} seconds ({interval / 60:.1f} minutes)", flush=True)
    print("  Press Ctrl+C to stop the worker.", flush=True)
    print("#" * 70, flush=True)

    cycle = 1
    try:
        while True:
            start_t = time.time()
            try:
                execute_cycle(cycle)
            except Exception as e:
                print(f"  [ERROR] Ingestion cycle #{cycle} encountered an error: {e}", file=sys.stderr, flush=True)
                import traceback
                traceback.print_exc()

            elapsed = time.time() - start_t
            sleep_time = max(0.0, interval - elapsed)
            next_run_ist = (
                datetime.now(timezone.utc)
                + timedelta(hours=5, minutes=30)
                + timedelta(seconds=sleep_time)
            ).strftime("%H:%M:%S IST")

            print(f"  [SLEEP] Next cycle at {next_run_ist} (in {int(sleep_time)}s)...", flush=True)
            time.sleep(sleep_time)
            cycle += 1

    except KeyboardInterrupt:
        print("\n\n  Live ingestion worker stopped cleanly by user.", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
